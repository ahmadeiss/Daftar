from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CustomerViewSet,
    DashboardView,
    DebtViewSet,
    InstallmentViewSet,
    RemindersView,
)


router = DefaultRouter()
router.register("customers", CustomerViewSet, basename="customer")
router.register("debts", DebtViewSet, basename="debt")
router.register("installments", InstallmentViewSet, basename="installment")

urlpatterns = [
    path("", include(router.urls)),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("reminders/", RemindersView.as_view(), name="reminders"),
]
