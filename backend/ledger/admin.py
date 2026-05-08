from django.contrib import admin

from .models import Customer, Debt, DebtActivity, Installment


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "merchant", "created_at")
    search_fields = ("name", "phone", "merchant__username")
    list_filter = ("created_at",)


class InstallmentInline(admin.TabularInline):
    model = Installment
    extra = 0
    readonly_fields = ("paid_at", "created_at", "updated_at")


class DebtActivityInline(admin.TabularInline):
    model = DebtActivity
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Debt)
class DebtAdmin(admin.ModelAdmin):
    list_display = ("customer", "total_amount", "installment_count", "status", "created_at")
    search_fields = ("customer__name", "customer__phone", "description")
    list_filter = ("created_at",)
    inlines = (InstallmentInline, DebtActivityInline)


@admin.register(Installment)
class InstallmentAdmin(admin.ModelAdmin):
    list_display = ("debt", "amount", "paid_amount", "due_date", "status", "paid_at")
    search_fields = ("debt__customer__name", "debt__description")
    list_filter = ("status", "due_date")


@admin.register(DebtActivity)
class DebtActivityAdmin(admin.ModelAdmin):
    list_display = ("debt", "activity_type", "amount", "note", "created_at")
    search_fields = ("debt__customer__name", "debt__description", "note")
    list_filter = ("activity_type", "created_at")
