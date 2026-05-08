from django.db.models import Q
from rest_framework import decorators, mixins, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Customer, Debt, Installment
from .serializers import (
    ChargeActionSerializer,
    CustomerSerializer,
    DebtSerializer,
    InstallmentSerializer,
    MoneyActionSerializer,
)
from .services import (
    add_debt_charge,
    customer_reputation,
    dashboard_summary,
    flag_overdue_installments,
    mark_installment_paid,
    record_debt_payment,
)


class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer

    def get_queryset(self):
        flag_overdue_installments(self.request.user)
        queryset = (
            Customer.objects.filter(merchant=self.request.user)
            .prefetch_related("debts__installments")
            .order_by("name")
        )
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(phone__icontains=search))
        return queryset

    def perform_create(self, serializer):
        serializer.save(merchant=self.request.user)

    @decorators.action(detail=True, methods=["get"])
    def profile(self, request, pk=None):
        customer = self.get_object()
        reputation = customer_reputation(customer)
        debts = (
            Debt.objects.filter(merchant=request.user, customer=customer)
            .select_related("customer")
            .prefetch_related("installments", "activities")
            .order_by("-created_at")
        )
        recent_installments = (
            Installment.objects.filter(merchant=request.user, debt__customer=customer)
            .select_related("debt", "debt__customer")
            .order_by("-updated_at")[:12]
        )
        return Response(
            {
                "customer": CustomerSerializer(customer, context={"request": request}).data,
                "reputation": reputation,
                "debts": DebtSerializer(debts, many=True, context={"request": request}).data,
                "recent_installments": InstallmentSerializer(recent_installments, many=True).data,
            }
        )


class DebtViewSet(viewsets.ModelViewSet):
    serializer_class = DebtSerializer

    def get_queryset(self):
        flag_overdue_installments(self.request.user)
        queryset = (
            Debt.objects.filter(merchant=self.request.user)
            .select_related("customer")
            .prefetch_related("installments", "activities")
            .order_by("-created_at")
        )
        customer_id = self.request.query_params.get("customer")
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        return queryset

    @decorators.action(detail=True, methods=["get"])
    def installments(self, request, pk=None):
        debt = self.get_object()
        serializer = InstallmentSerializer(debt.installments.all(), many=True)
        return Response(serializer.data)

    @decorators.action(detail=True, methods=["post"], url_path="record-payment")
    def record_payment(self, request, pk=None):
        debt = self.get_object()
        serializer = MoneyActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            record_debt_payment(
                debt,
                serializer.validated_data["amount"],
                serializer.validated_data.get("note", ""),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        debt.refresh_from_db()
        return Response(self.get_serializer(debt).data)

    @decorators.action(detail=True, methods=["post"], url_path="add-charge")
    def add_charge(self, request, pk=None):
        debt = self.get_object()
        serializer = ChargeActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            add_debt_charge(
                debt,
                serializer.validated_data["amount"],
                serializer.validated_data.get("note", ""),
                serializer.validated_data.get("due_date"),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        debt.refresh_from_db()
        return Response(self.get_serializer(debt).data)


class InstallmentViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = InstallmentSerializer

    def get_queryset(self):
        flag_overdue_installments(self.request.user)
        queryset = (
            Installment.objects.filter(merchant=self.request.user)
            .select_related("debt", "debt__customer")
            .order_by("due_date", "id")
        )
        status_filter = self.request.query_params.get("status")
        if status_filter in Installment.Status.values:
            queryset = queryset.filter(status=status_filter)
        return queryset

    @decorators.action(detail=True, methods=["post"], url_path="mark-paid")
    def mark_paid(self, request, pk=None):
        installment = self.get_object()
        mark_installment_paid(installment, request.data.get("note", ""))
        serializer = self.get_serializer(installment)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DashboardView(APIView):
    def get(self, request):
        summary = dashboard_summary(request.user)
        return Response(
            {
                "total_debts": summary["total_debts"],
                "paid_amount": summary["paid_amount"],
                "unpaid_amount": summary["unpaid_amount"],
                "overdue_amount": summary["overdue_amount"],
                "customers_count": summary["customers_count"],
                "debts_count": summary["debts_count"],
                "upcoming_count": summary["upcoming_count"],
                "overdue_count": summary["overdue_count"],
                "upcoming_installments": InstallmentSerializer(
                    summary["upcoming_installments"], many=True
                ).data,
                "overdue_installments": InstallmentSerializer(
                    summary["overdue_installments"], many=True
                ).data,
                "committed_customers": summary["committed_customers"],
                "risky_customers": summary["risky_customers"],
            }
        )


class RemindersView(APIView):
    def get(self, request):
        flag_overdue_installments(request.user)
        queryset = (
            Installment.objects.filter(
                merchant=request.user,
                status__in=[Installment.Status.UNPAID, Installment.Status.LATE],
            )
            .select_related("debt", "debt__customer")
            .order_by("due_date")[:50]
        )
        return Response(
            {
                "count": queryset.count(),
                "items": InstallmentSerializer(queryset, many=True).data,
            }
        )
