from django.db import transaction
from decimal import Decimal
from rest_framework import serializers

from .models import Customer, Debt, DebtActivity, Installment
from .services import build_installments, customer_reputation


class CustomerSerializer(serializers.ModelSerializer):
    debts_count = serializers.SerializerMethodField()
    unpaid_amount = serializers.SerializerMethodField()
    commitment_score = serializers.SerializerMethodField()
    risk_level = serializers.SerializerMethodField()
    late_installments = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = (
            "id",
            "name",
            "phone",
            "notes",
            "debts_count",
            "unpaid_amount",
            "commitment_score",
            "risk_level",
            "late_installments",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "debts_count",
            "unpaid_amount",
            "commitment_score",
            "risk_level",
            "late_installments",
        )

    def _reputation(self, obj):
        if not hasattr(obj, "_reputation_cache"):
            obj._reputation_cache = customer_reputation(obj)
        return obj._reputation_cache

    def get_debts_count(self, obj):
        return obj.debts.count()

    def get_unpaid_amount(self, obj):
        return self._reputation(obj)["outstanding_amount"]

    def get_commitment_score(self, obj):
        return self._reputation(obj)["commitment_score"]

    def get_risk_level(self, obj):
        return self._reputation(obj)["risk_level"]

    def get_late_installments(self, obj):
        return self._reputation(obj)["late_installments"]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name is required.")
        return value

    def validate_phone(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Phone number is required.")
        return value


class CustomerSummarySerializer(serializers.ModelSerializer):
    commitment_score = serializers.SerializerMethodField()
    risk_level = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = ("id", "name", "phone", "commitment_score", "risk_level")

    def get_commitment_score(self, obj):
        return customer_reputation(obj)["commitment_score"]

    def get_risk_level(self, obj):
        return customer_reputation(obj)["risk_level"]


class InstallmentSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="debt.customer.name", read_only=True)
    debt_description = serializers.CharField(source="debt.description", read_only=True)
    remaining_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Installment
        fields = (
            "id",
            "debt",
            "amount",
            "paid_amount",
            "remaining_amount",
            "due_date",
            "status",
            "paid_at",
            "customer_name",
            "debt_description",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class DebtActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DebtActivity
        fields = ("id", "activity_type", "amount", "note", "created_at")
        read_only_fields = fields


class DebtSerializer(serializers.ModelSerializer):
    customer_detail = CustomerSummarySerializer(source="customer", read_only=True)
    installments = InstallmentSerializer(many=True, read_only=True)
    activities = DebtActivitySerializer(many=True, read_only=True)
    receipt_url = serializers.SerializerMethodField()
    paid_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    remaining_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Debt
        fields = (
            "id",
            "customer",
            "customer_detail",
            "total_amount",
            "description",
            "start_date",
            "installment_count",
            "receipt_image",
            "receipt_url",
            "status",
            "paid_amount",
            "remaining_amount",
            "installments",
            "activities",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "customer_detail",
            "receipt_url",
            "status",
            "paid_amount",
            "remaining_amount",
            "installments",
            "activities",
            "created_at",
            "updated_at",
        )

    def get_receipt_url(self, obj):
        if not obj.receipt_image:
            return None
        request = self.context.get("request")
        url = obj.receipt_image.url
        return request.build_absolute_uri(url) if request and url.startswith("/") else url

    def validate_total_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Total amount must be greater than zero.")
        return value

    def validate_installment_count(self, value):
        if value < 1 or value > 60:
            raise serializers.ValidationError("Installment count must be between 1 and 60.")
        return value

    def validate(self, attrs):
        request = self.context["request"]
        customer = attrs.get("customer") or getattr(self.instance, "customer", None)
        if customer and customer.merchant_id != request.user.id:
            raise serializers.ValidationError({"customer": "Customer was not found."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]
        debt = Debt.objects.create(merchant=request.user, **validated_data)
        build_installments(debt)
        DebtActivity.objects.create(
            merchant=request.user,
            debt=debt,
            activity_type=DebtActivity.Type.CHARGE,
            amount=debt.total_amount,
            note="Initial debt",
        )
        return debt

    @transaction.atomic
    def update(self, instance, validated_data):
        schedule_fields = {"total_amount", "start_date", "installment_count"}
        schedule_changed = any(
            field in validated_data and validated_data[field] != getattr(instance, field)
            for field in schedule_fields
        )

        if schedule_changed and instance.installments.filter(paid_amount__gt=0).exists():
            raise serializers.ValidationError(
                "Debt schedule cannot be changed after a payment is recorded. Use payment or extra charge controls instead."
            )

        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()

        if schedule_changed:
            instance.installments.all().delete()
            build_installments(instance)

        return instance


class MoneyActionSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    note = serializers.CharField(required=False, allow_blank=True, max_length=255)


class ChargeActionSerializer(MoneyActionSerializer):
    due_date = serializers.DateField(required=False)
