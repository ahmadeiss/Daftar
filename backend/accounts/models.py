from django.conf import settings
from django.db import models
from django.utils import timezone


class MerchantProfile(models.Model):
    class BusinessType(models.TextChoices):
        GROCERY = "grocery", "Grocery"
        PHARMACY = "pharmacy", "Pharmacy"
        ELECTRONICS = "electronics", "Electronics"
        MERCHANT = "merchant", "Small merchant"
        INDIVIDUAL = "individual", "Individual seller"
        OTHER = "other", "Other"

    class SubscriptionStatus(models.TextChoices):
        TRIAL = "trial", "Trial"
        ACTIVE = "active", "Active"
        PAST_DUE = "past_due", "Past due"
        SUSPENDED = "suspended", "Suspended"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="merchant_profile",
    )
    store_name = models.CharField(max_length=150)
    owner_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    business_type = models.CharField(
        max_length=24,
        choices=BusinessType.choices,
        default=BusinessType.MERCHANT,
    )
    plan = models.ForeignKey(
        "SubscriptionPlan",
        on_delete=models.SET_NULL,
        related_name="merchants",
        blank=True,
        null=True,
    )
    city = models.CharField(max_length=80, blank=True)
    address = models.CharField(max_length=255, blank=True)
    subscription_status = models.CharField(
        max_length=16,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.TRIAL,
    )
    subscription_started_at = models.DateField(blank=True, null=True)
    subscription_expires_at = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["store_name"]
        indexes = [
            models.Index(fields=["store_name"]),
            models.Index(fields=["subscription_status"]),
            models.Index(fields=["business_type"]),
        ]

    def __str__(self):
        return self.store_name or self.user.email or self.user.username

    @property
    def email(self):
        return self.user.email

    @property
    def is_active(self):
        return self.user.is_active

    @property
    def billing_state(self):
        today = timezone.localdate()
        if not self.user.is_active or self.subscription_status == self.SubscriptionStatus.SUSPENDED:
            return "suspended"
        if self.subscription_status == self.SubscriptionStatus.TRIAL:
            return "trial"
        if self.subscription_expires_at and self.subscription_expires_at >= today:
            return "paid"
        return "overdue"

    @property
    def days_until_expiry(self):
        if not self.subscription_expires_at:
            return None
        return (self.subscription_expires_at - timezone.localdate()).days


class SubscriptionPlan(models.Model):
    class BillingCycle(models.TextChoices):
        MONTHLY = "monthly", "Monthly"
        YEARLY = "yearly", "Yearly"

    name = models.CharField(max_length=80)
    slug = models.SlugField(unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=8, default="ILS")
    billing_cycle = models.CharField(
        max_length=16,
        choices=BillingCycle.choices,
        default=BillingCycle.MONTHLY,
    )
    max_customers = models.PositiveIntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["price", "name"]

    def __str__(self):
        return f"{self.name} - {self.price} {self.currency}"


class SubscriptionPayment(models.Model):
    class Status(models.TextChoices):
        PAID = "paid", "Paid"
        PENDING = "pending", "Pending"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    class Method(models.TextChoices):
        CASH = "cash", "Cash"
        BANK = "bank", "Bank transfer"
        CARD = "card", "Card"
        OTHER = "other", "Other"

    merchant = models.ForeignKey(
        MerchantProfile,
        on_delete=models.CASCADE,
        related_name="subscription_payments",
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        related_name="payments",
        blank=True,
        null=True,
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=8, default="ILS")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PAID)
    paid_on = models.DateField(default=timezone.localdate)
    period_start = models.DateField()
    period_end = models.DateField()
    payment_method = models.CharField(
        max_length=16,
        choices=Method.choices,
        default=Method.CASH,
    )
    reference = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-paid_on", "-created_at"]
        indexes = [
            models.Index(fields=["status", "paid_on"]),
            models.Index(fields=["period_end"]),
            models.Index(fields=["merchant", "period_end"]),
        ]

    def __str__(self):
        return f"{self.merchant.store_name} - {self.amount} {self.currency}"
