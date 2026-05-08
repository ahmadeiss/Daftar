from decimal import Decimal
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


def receipt_upload_path(instance, filename):
    suffix = filename.split(".")[-1].lower()
    return f"receipts/user_{instance.merchant_id}/{uuid.uuid4().hex}.{suffix}"


class Customer(models.Model):
    merchant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customers",
    )
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=32)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["merchant", "name"]),
            models.Index(fields=["merchant", "phone"]),
        ]

    def __str__(self):
        return self.name


class Debt(models.Model):
    merchant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="debts",
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="debts",
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255)
    start_date = models.DateField()
    installment_count = models.PositiveIntegerField(default=1)
    receipt_image = models.ImageField(upload_to=receipt_upload_path, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["merchant", "created_at"]),
            models.Index(fields=["customer", "created_at"]),
        ]

    def __str__(self):
        return f"{self.customer.name} - {self.total_amount}"

    @property
    def paid_amount(self):
        paid = self.installments.aggregate(total=models.Sum("paid_amount"))["total"]
        return paid or Decimal("0.00")

    @property
    def remaining_amount(self):
        return max(self.total_amount - self.paid_amount, Decimal("0.00"))

    @property
    def status(self):
        if self.remaining_amount <= 0:
            return "paid"
        unpaid = self.installments.exclude(status=Installment.Status.PAID)
        if unpaid.filter(due_date__lt=timezone.localdate()).exists():
            return "late"
        return "unpaid"


class Installment(models.Model):
    class Status(models.TextChoices):
        PAID = "paid", "Paid"
        UNPAID = "unpaid", "Unpaid"
        LATE = "late", "Late"

    merchant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="installments",
    )
    debt = models.ForeignKey(
        Debt,
        on_delete=models.CASCADE,
        related_name="installments",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    due_date = models.DateField()
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.UNPAID,
    )
    paid_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["due_date", "id"]
        indexes = [
            models.Index(fields=["merchant", "status", "due_date"]),
            models.Index(fields=["debt", "due_date"]),
        ]

    def __str__(self):
        return f"{self.debt_id} - {self.amount} due {self.due_date}"

    @property
    def is_overdue(self):
        return self.paid_amount < self.amount and self.due_date < timezone.localdate()

    @property
    def remaining_amount(self):
        return max(self.amount - self.paid_amount, Decimal("0.00"))

    def refresh_status(self, save=True):
        next_status = self.Status.PAID
        if self.paid_amount < self.amount:
            next_status = self.Status.LATE if self.is_overdue else self.Status.UNPAID
        if next_status != self.status:
            self.status = next_status
            if save:
                self.save(update_fields=["status", "updated_at"])
        return self.status

    def mark_paid(self):
        self.paid_amount = self.amount
        self.status = self.Status.PAID
        self.paid_at = timezone.now()
        self.save(update_fields=["paid_amount", "status", "paid_at", "updated_at"])

    def apply_payment(self, amount):
        amount = min(amount, self.remaining_amount)
        if amount <= 0:
            return Decimal("0.00")
        self.paid_amount += amount
        if self.paid_amount >= self.amount:
            self.paid_amount = self.amount
            self.status = self.Status.PAID
            self.paid_at = timezone.now()
        else:
            self.refresh_status(save=False)
        self.save(update_fields=["paid_amount", "status", "paid_at", "updated_at"])
        return amount


class DebtActivity(models.Model):
    class Type(models.TextChoices):
        PAYMENT = "payment", "Payment"
        CHARGE = "charge", "Charge"
        NOTE = "note", "Note"

    merchant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="debt_activities",
    )
    debt = models.ForeignKey(
        Debt,
        on_delete=models.CASCADE,
        related_name="activities",
    )
    activity_type = models.CharField(max_length=12, choices=Type.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["merchant", "activity_type", "created_at"]),
            models.Index(fields=["debt", "created_at"]),
        ]

    def __str__(self):
        return f"{self.activity_type} {self.amount} on debt {self.debt_id}"
