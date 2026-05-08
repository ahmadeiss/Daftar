from datetime import timedelta

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count, Q, Sum
from django.template.response import TemplateResponse
from django.urls import path
from django.utils import timezone

from .forms import MerchantProfileChangeForm, MerchantProfileCreateForm
from .models import MerchantProfile, SubscriptionPayment, SubscriptionPlan


User = get_user_model()


class MerchantProfileInline(admin.StackedInline):
    model = MerchantProfile
    can_delete = False
    extra = 0
    fieldsets = (
        (
            "Store details",
            {
                "fields": (
                    "store_name",
                    "owner_name",
                    "phone",
                    "business_type",
                    "plan",
                    "city",
                    "address",
                    "subscription_status",
                    "subscription_started_at",
                    "subscription_expires_at",
                    "notes",
                )
            },
        ),
    )


class SubscriptionPaymentInline(admin.TabularInline):
    model = SubscriptionPayment
    extra = 0
    fields = (
        "plan",
        "amount",
        "currency",
        "status",
        "paid_on",
        "period_start",
        "period_end",
        "payment_method",
        "reference",
    )


try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class MerchantUserAdmin(UserAdmin):
    inlines = (MerchantProfileInline,)
    list_display = (
        "username",
        "email",
        "store_name",
        "is_active",
        "is_staff",
        "customers_count",
        "debts_count",
    )
    list_filter = ("is_active", "is_staff", "is_superuser")
    search_fields = ("username", "email", "first_name", "merchant_profile__store_name")
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "first_name",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                ),
            },
        ),
    )

    @admin.display(description="Store")
    def store_name(self, obj):
        profile = getattr(obj, "merchant_profile", None)
        return profile.store_name if profile else "-"

    @admin.display(description="Customers")
    def customers_count(self, obj):
        return obj.customers.count() if hasattr(obj, "customers") else 0

    @admin.display(description="Debts")
    def debts_count(self, obj):
        return obj.debts.count() if hasattr(obj, "debts") else 0


@admin.register(MerchantProfile)
class MerchantProfileAdmin(admin.ModelAdmin):
    add_form = MerchantProfileCreateForm
    form = MerchantProfileChangeForm
    inlines = (SubscriptionPaymentInline,)
    list_display = (
        "store_name",
        "email",
        "phone",
        "business_type",
        "plan",
        "subscription_status",
        "billing_state",
        "subscription_expires_at",
        "days_left",
        "is_active",
        "customers_count",
        "debts_count",
        "overdue_installments",
    )
    list_filter = ("subscription_status", "plan", "business_type", "user__is_active")
    search_fields = ("store_name", "owner_name", "phone", "user__email", "user__username")
    readonly_fields = (
        "created_at",
        "updated_at",
        "customers_count",
        "debts_count",
        "overdue_installments",
        "billing_state",
        "days_left",
    )
    fieldsets = (
        (
            "Merchant account",
            {
                "fields": (
                    "user",
                    "plan",
                    "subscription_status",
                    "subscription_started_at",
                    "subscription_expires_at",
                )
            },
        ),
        (
            "Store details",
            {
                "fields": (
                    "store_name",
                    "owner_name",
                    "phone",
                    "business_type",
                    "city",
                    "address",
                    "notes",
                )
            },
        ),
        (
            "Store metrics",
            {
                "fields": (
                    "customers_count",
                    "debts_count",
                    "overdue_installments",
                    "billing_state",
                    "days_left",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
    add_fieldsets = (
        (
            "Create merchant login",
            {
                "fields": (
                    "email",
                    "password",
                )
            },
        ),
        (
            "Store details",
            {
                "fields": (
                    "store_name",
                    "owner_name",
                    "phone",
                    "business_type",
                    "plan",
                    "city",
                    "address",
                    "subscription_status",
                    "subscription_started_at",
                    "subscription_expires_at",
                    "notes",
                )
            },
        ),
    )

    def get_form(self, request, obj=None, **kwargs):
        kwargs["form"] = self.add_form if obj is None else self.form
        return super().get_form(request, obj, **kwargs)

    def get_fieldsets(self, request, obj=None):
        return self.add_fieldsets if obj is None else self.fieldsets

    def save_model(self, request, obj, form, change):
        if not change:
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            user = User(username=email, email=email, first_name=obj.store_name)
            user.set_password(password)
            user._skip_profile_signal = True
            user.save()
            obj.user = user
        else:
            obj.user.first_name = obj.store_name
            obj.user.email = obj.user.email.strip().lower()
            obj.user.save(update_fields=["first_name", "email"])
        super().save_model(request, obj, form, change)

    @admin.display(description="Customers")
    def customers_count(self, obj):
        return obj.user.customers.count()

    @admin.display(description="Debts")
    def debts_count(self, obj):
        return obj.user.debts.count()

    @admin.display(description="Overdue")
    def overdue_installments(self, obj):
        return obj.user.installments.filter(status="late").count()

    @admin.display(description="Billing")
    def billing_state(self, obj):
        return obj.billing_state

    @admin.display(description="Days left")
    def days_left(self, obj):
        days = obj.days_until_expiry
        return "-" if days is None else days


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "price",
        "currency",
        "billing_cycle",
        "is_active",
        "merchant_count",
        "paid_payments_count",
    )
    list_filter = ("is_active", "billing_cycle")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}

    @admin.display(description="Merchants")
    def merchant_count(self, obj):
        return obj.merchants.count()

    @admin.display(description="Paid payments")
    def paid_payments_count(self, obj):
        return obj.payments.filter(status=SubscriptionPayment.Status.PAID).count()


@admin.register(SubscriptionPayment)
class SubscriptionPaymentAdmin(admin.ModelAdmin):
    list_display = (
        "merchant",
        "plan",
        "amount",
        "currency",
        "status",
        "paid_on",
        "period_start",
        "period_end",
        "payment_method",
    )
    list_filter = ("status", "plan", "payment_method", "paid_on", "period_end")
    search_fields = (
        "merchant__store_name",
        "merchant__user__email",
        "reference",
        "notes",
    )
    autocomplete_fields = ("merchant", "plan")
    date_hierarchy = "paid_on"


def platform_dashboard(request):
    today = timezone.localdate()
    month_start = today.replace(day=1)
    next_week = today + timedelta(days=7)

    profiles = MerchantProfile.objects.select_related("user", "plan")
    payments = SubscriptionPayment.objects.select_related("merchant", "plan")
    paid_payments = payments.filter(status=SubscriptionPayment.Status.PAID)

    paid_merchants = profiles.filter(
        subscription_status=MerchantProfile.SubscriptionStatus.ACTIVE,
        subscription_expires_at__gte=today,
        user__is_active=True,
    ).count()
    trial_merchants = profiles.filter(
        subscription_status=MerchantProfile.SubscriptionStatus.TRIAL,
        user__is_active=True,
    ).count()
    overdue_merchants = (
        profiles.filter(
            Q(subscription_status=MerchantProfile.SubscriptionStatus.PAST_DUE)
            | Q(subscription_expires_at__lt=today),
            user__is_active=True,
        )
        .exclude(subscription_status=MerchantProfile.SubscriptionStatus.SUSPENDED)
        .count()
    )
    suspended_merchants = profiles.filter(
        Q(subscription_status=MerchantProfile.SubscriptionStatus.SUSPENDED)
        | Q(user__is_active=False)
    ).count()
    revenue_this_month = (
        paid_payments.filter(paid_on__gte=month_start).aggregate(total=Sum("amount"))["total"] or 0
    )

    plan_rows = (
        SubscriptionPlan.objects.annotate(
            merchants_count=Count("merchants", distinct=True),
            paid_count=Count(
                "payments",
                filter=Q(payments__status=SubscriptionPayment.Status.PAID),
                distinct=True,
            ),
        )
        .order_by("price", "name")
    )
    recent_payments = paid_payments.order_by("-paid_on", "-created_at")[:8]
    needs_payment = (
        profiles.filter(
            Q(subscription_status=MerchantProfile.SubscriptionStatus.PAST_DUE)
            | Q(subscription_expires_at__lt=today)
            | Q(subscription_expires_at__isnull=True)
        )
        .exclude(subscription_status=MerchantProfile.SubscriptionStatus.SUSPENDED)
        .order_by("subscription_expires_at", "store_name")[:12]
    )
    renewals_soon = (
        profiles.filter(
            subscription_status=MerchantProfile.SubscriptionStatus.ACTIVE,
            subscription_expires_at__gte=today,
            subscription_expires_at__lte=next_week,
        )
        .order_by("subscription_expires_at", "store_name")[:8]
    )

    context = {
        **admin.site.each_context(request),
        "title": "Daftar dashboard",
        "today": today,
        "stats": {
            "total_merchants": profiles.count(),
            "paid_merchants": paid_merchants,
            "trial_merchants": trial_merchants,
            "overdue_merchants": overdue_merchants,
            "suspended_merchants": suspended_merchants,
            "revenue_this_month": revenue_this_month,
        },
        "plan_rows": plan_rows,
        "recent_payments": recent_payments,
        "needs_payment": needs_payment,
        "renewals_soon": renewals_soon,
    }
    return TemplateResponse(request, "admin/platform_dashboard.html", context)


original_get_urls = admin.site.get_urls


def get_admin_urls():
    custom_urls = [
        path("dashboard/", admin.site.admin_view(platform_dashboard), name="platform_dashboard"),
    ]
    return custom_urls + original_get_urls()


admin.site.get_urls = get_admin_urls
admin.site.site_header = "Daftar Admin"
admin.site.site_title = "Daftar Admin"
admin.site.index_title = "Merchant management"
