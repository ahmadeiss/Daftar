from calendar import monthrange
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.db.models import F, Sum
from django.utils import timezone

from .models import Customer, DebtActivity, Installment


ZERO = Decimal("0.00")


def money_value(value):
    return (Decimal(value).quantize(Decimal("0.01")) if value is not None else ZERO)


def add_months(date_value, months):
    month = date_value.month - 1 + months
    year = date_value.year + month // 12
    month = month % 12 + 1
    day = min(date_value.day, monthrange(year, month)[1])
    return date_value.replace(year=year, month=month, day=day)


def split_amount(total_amount, count):
    cents = int((total_amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    base = cents // count
    remainder = cents % count

    amounts = []
    for index in range(count):
        item_cents = base + (1 if index < remainder else 0)
        amounts.append((Decimal(item_cents) / Decimal("100")).quantize(Decimal("0.01")))
    return amounts


def build_installments(debt):
    amounts = split_amount(debt.total_amount, debt.installment_count)
    installments = []
    for index, amount in enumerate(amounts, start=1):
        installments.append(
            Installment(
                merchant=debt.merchant,
                debt=debt,
                amount=amount,
                due_date=add_months(debt.start_date, index),
            )
        )
    return Installment.objects.bulk_create(installments)


def flag_overdue_installments(user):
    return (
        Installment.objects.filter(
            merchant=user,
            status__in=[Installment.Status.UNPAID, Installment.Status.LATE],
            paid_amount__lt=F("amount"),
            due_date__lt=timezone.localdate(),
        ).update(status=Installment.Status.LATE)
    )


def _installments_remaining(queryset):
    return sum((item.remaining_amount for item in queryset), ZERO)


@transaction.atomic
def record_debt_payment(debt, amount, note=""):
    amount = money_value(amount)
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")
    if amount > debt.remaining_amount:
        raise ValueError("Payment cannot be greater than remaining debt.")

    remaining_payment = amount
    installments = debt.installments.exclude(status=Installment.Status.PAID).order_by(
        "due_date", "id"
    )
    for installment in installments:
        if remaining_payment <= 0:
            break
        applied = installment.apply_payment(remaining_payment)
        remaining_payment -= applied

    DebtActivity.objects.create(
        merchant=debt.merchant,
        debt=debt,
        activity_type=DebtActivity.Type.PAYMENT,
        amount=amount,
        note=note.strip(),
    )
    return debt


@transaction.atomic
def mark_installment_paid(installment, note=""):
    amount = installment.remaining_amount
    if amount <= 0:
        return installment
    installment.mark_paid()
    DebtActivity.objects.create(
        merchant=installment.merchant,
        debt=installment.debt,
        activity_type=DebtActivity.Type.PAYMENT,
        amount=amount,
        note=note.strip(),
    )
    return installment


@transaction.atomic
def add_debt_charge(debt, amount, note="", due_date=None):
    amount = money_value(amount)
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")

    due_date = due_date or add_months(timezone.localdate(), 1)
    debt.total_amount += amount
    debt.installment_count += 1
    debt.save(update_fields=["total_amount", "installment_count", "updated_at"])

    Installment.objects.create(
        merchant=debt.merchant,
        debt=debt,
        amount=amount,
        due_date=due_date,
    )
    DebtActivity.objects.create(
        merchant=debt.merchant,
        debt=debt,
        activity_type=DebtActivity.Type.CHARGE,
        amount=amount,
        note=note.strip(),
    )
    return debt


def customer_reputation(customer):
    installments = Installment.objects.filter(debt__customer=customer)
    total_installments = installments.count()
    paid_count = installments.filter(status=Installment.Status.PAID).count()
    late_count = installments.filter(status=Installment.Status.LATE).count()
    overdue_amount = _installments_remaining(installments.filter(status=Installment.Status.LATE))
    outstanding_amount = _installments_remaining(installments.exclude(status=Installment.Status.PAID))
    total_debt_amount = customer.debts.aggregate(total=Sum("total_amount"))["total"] or ZERO
    paid_amount = installments.aggregate(total=Sum("paid_amount"))["total"] or ZERO

    if total_installments == 0 or (paid_count == 0 and late_count == 0):
        score = 70
        risk_level = "new"
    else:
        paid_ratio = paid_count / total_installments
        late_ratio = late_count / total_installments
        score = round((paid_ratio * 100) - (late_ratio * 45))
        if late_count == 0 and paid_count > 0:
            score += 10
        score = max(0, min(100, score))

        if late_count >= 2 or score < 45:
            risk_level = "risky"
        elif late_count == 1 or score < 75:
            risk_level = "watch"
        else:
            risk_level = "trusted"

    active_debts = sum(1 for debt in customer.debts.all() if debt.remaining_amount > 0)

    return {
        "commitment_score": score,
        "risk_level": risk_level,
        "total_installments": total_installments,
        "paid_installments": paid_count,
        "late_installments": late_count,
        "total_debt_amount": total_debt_amount,
        "paid_amount": paid_amount,
        "outstanding_amount": outstanding_amount,
        "overdue_amount": overdue_amount,
        "active_debts": active_debts,
    }


def customer_reputation_lists(user):
    flag_overdue_installments(user)
    customers = Customer.objects.filter(merchant=user).prefetch_related("debts__installments")
    summaries = []
    for customer in customers:
        summary = customer_reputation(customer)
        summaries.append(
            {
                "id": customer.id,
                "name": customer.name,
                "phone": customer.phone,
                **summary,
            }
        )

    committed = sorted(
        [item for item in summaries if item["risk_level"] in ["trusted", "new"]],
        key=lambda item: (item["commitment_score"], item["paid_installments"]),
        reverse=True,
    )[:5]
    risky = sorted(
        [item for item in summaries if item["risk_level"] in ["risky", "watch"]],
        key=lambda item: (item["risk_level"] != "risky", -item["overdue_amount"]),
    )[:5]
    return committed, risky


def dashboard_summary(user):
    flag_overdue_installments(user)
    installments = Installment.objects.filter(merchant=user)
    today = timezone.localdate()
    next_week = today + timedelta(days=7)

    total_debts = user.debts.aggregate(total=Sum("total_amount"))["total"] or ZERO
    paid_amount = installments.aggregate(total=Sum("paid_amount"))["total"] or ZERO
    unpaid_amount = _installments_remaining(installments.exclude(status=Installment.Status.PAID))
    overdue_amount = _installments_remaining(installments.filter(status=Installment.Status.LATE))

    upcoming = installments.filter(
        status=Installment.Status.UNPAID,
        due_date__gte=today,
        due_date__lte=next_week,
    ).select_related("debt", "debt__customer")[:10]

    overdue = installments.filter(status=Installment.Status.LATE).select_related(
        "debt", "debt__customer"
    )[:10]
    committed_customers, risky_customers = customer_reputation_lists(user)

    return {
        "total_debts": total_debts,
        "paid_amount": paid_amount,
        "unpaid_amount": unpaid_amount,
        "overdue_amount": overdue_amount,
        "customers_count": user.customers.count(),
        "debts_count": user.debts.count(),
        "upcoming_count": installments.filter(
            status=Installment.Status.UNPAID,
            due_date__gte=today,
            due_date__lte=next_week,
        ).count(),
        "overdue_count": installments.filter(status=Installment.Status.LATE).count(),
        "upcoming_installments": upcoming,
        "overdue_installments": overdue,
        "committed_customers": committed_customers,
        "risky_customers": risky_customers,
    }
