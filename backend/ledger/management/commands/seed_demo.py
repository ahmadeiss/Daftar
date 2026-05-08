from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import MerchantProfile, SubscriptionPayment, SubscriptionPlan
from ledger.models import Customer, Debt, DebtActivity, Installment
from ledger.services import add_debt_charge, build_installments, flag_overdue_installments, record_debt_payment


class Command(BaseCommand):
    help = "Create demo data for local testing."

    def handle(self, *args, **options):
        User = get_user_model()
        admin_user, admin_created = User.objects.get_or_create(
            username="admin@daftar.local",
            defaults={
                "email": "admin@daftar.local",
                "first_name": "Daftar Admin",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if admin_created:
            admin_user.set_password("admin123456")
            admin_user.save(update_fields=["password"])
        elif not admin_user.is_staff or not admin_user.is_superuser:
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.save(update_fields=["is_staff", "is_superuser"])

        starter_plan, _ = SubscriptionPlan.objects.update_or_create(
            slug="starter",
            defaults={
                "name": "Starter",
                "price": Decimal("49.00"),
                "currency": "ILS",
                "billing_cycle": SubscriptionPlan.BillingCycle.MONTHLY,
                "max_customers": 150,
                "is_active": True,
                "description": "Small store monthly plan",
            },
        )
        pro_plan, _ = SubscriptionPlan.objects.update_or_create(
            slug="pro",
            defaults={
                "name": "Pro",
                "price": Decimal("99.00"),
                "currency": "ILS",
                "billing_cycle": SubscriptionPlan.BillingCycle.MONTHLY,
                "max_customers": None,
                "is_active": True,
                "description": "Growing merchant monthly plan",
            },
        )

        user, created = User.objects.get_or_create(
            username="demo@daftar.local",
            defaults={
                "email": "demo@daftar.local",
                "first_name": "Daftar Demo",
            },
        )
        if created:
            user.set_password("demo123456")
            user.save(update_fields=["password"])

        MerchantProfile.objects.update_or_create(
            user=user,
            defaults={
                "store_name": "Daftar Demo Store",
                "owner_name": "Demo Merchant",
                "phone": "0599000000",
                "business_type": MerchantProfile.BusinessType.GROCERY,
                "plan": starter_plan,
                "city": "Ramallah",
                "subscription_status": MerchantProfile.SubscriptionStatus.ACTIVE,
                "subscription_started_at": timezone.localdate(),
                "subscription_expires_at": timezone.localdate() + timedelta(days=30),
            },
        )
        demo_profile = user.merchant_profile
        SubscriptionPayment.objects.get_or_create(
            merchant=demo_profile,
            reference="DEMO-PAID-001",
            defaults={
                "plan": starter_plan,
                "amount": starter_plan.price,
                "currency": starter_plan.currency,
                "status": SubscriptionPayment.Status.PAID,
                "paid_on": timezone.localdate(),
                "period_start": timezone.localdate(),
                "period_end": timezone.localdate() + timedelta(days=30),
                "payment_method": SubscriptionPayment.Method.CASH,
                "notes": "Demo paid subscription",
            },
        )

        sample_merchants = [
            {
                "email": "pharmacy@daftar.local",
                "store_name": "Al Quds Pharmacy",
                "owner_name": "Pharmacy Owner",
                "phone": "0599111001",
                "business_type": MerchantProfile.BusinessType.PHARMACY,
                "plan": pro_plan,
                "status": MerchantProfile.SubscriptionStatus.TRIAL,
                "expires": None,
            },
            {
                "email": "electronics@daftar.local",
                "store_name": "Nablus Electronics",
                "owner_name": "Electronics Owner",
                "phone": "0599222002",
                "business_type": MerchantProfile.BusinessType.ELECTRONICS,
                "plan": pro_plan,
                "status": MerchantProfile.SubscriptionStatus.PAST_DUE,
                "expires": timezone.localdate() - timedelta(days=6),
            },
            {
                "email": "market@daftar.local",
                "store_name": "Hebron Mini Market",
                "owner_name": "Market Owner",
                "phone": "0599333003",
                "business_type": MerchantProfile.BusinessType.GROCERY,
                "plan": starter_plan,
                "status": MerchantProfile.SubscriptionStatus.ACTIVE,
                "expires": timezone.localdate() + timedelta(days=5),
            },
        ]
        for merchant in sample_merchants:
            merchant_user, merchant_created = User.objects.get_or_create(
                username=merchant["email"],
                defaults={
                    "email": merchant["email"],
                    "first_name": merchant["store_name"],
                },
            )
            if merchant_created:
                merchant_user.set_password("merchant123456")
                merchant_user.save(update_fields=["password"])
            profile, _ = MerchantProfile.objects.update_or_create(
                user=merchant_user,
                defaults={
                    "store_name": merchant["store_name"],
                    "owner_name": merchant["owner_name"],
                    "phone": merchant["phone"],
                    "business_type": merchant["business_type"],
                    "plan": merchant["plan"],
                    "city": "Palestine",
                    "subscription_status": merchant["status"],
                    "subscription_started_at": timezone.localdate() - timedelta(days=30),
                    "subscription_expires_at": merchant["expires"],
                },
            )
            if merchant["status"] == MerchantProfile.SubscriptionStatus.ACTIVE:
                SubscriptionPayment.objects.get_or_create(
                    merchant=profile,
                    reference=f"DEMO-PAID-{profile.id}",
                    defaults={
                        "plan": merchant["plan"],
                        "amount": merchant["plan"].price,
                        "currency": merchant["plan"].currency,
                        "status": SubscriptionPayment.Status.PAID,
                        "paid_on": timezone.localdate() - timedelta(days=25),
                        "period_start": timezone.localdate() - timedelta(days=25),
                        "period_end": merchant["expires"],
                        "payment_method": SubscriptionPayment.Method.CASH,
                    },
                )

        customers = [
            ("محمد خليل", "0599000001", "بقالة الحارة"),
            ("سارة أحمد", "0599000002", "دفعات شهرية"),
            ("Omar Saleh", "0599000003", ""),
        ]

        customer_objects = []
        for name, phone, notes in customers:
            customer, _ = Customer.objects.get_or_create(
                merchant=user,
                phone=phone,
                defaults={"name": name, "notes": notes},
            )
            customer_objects.append(customer)

        debt_specs = [
            (customer_objects[0], Decimal("450.00"), "مواد تموينية", timezone.localdate() - timedelta(days=95), 3),
            (customer_objects[1], Decimal("1200.00"), "هاتف محمول", timezone.localdate() - timedelta(days=40), 4),
            (customer_objects[2], Decimal("180.00"), "فاتورة صغيرة", timezone.localdate(), 1),
        ]

        for customer, amount, description, start_date, count in debt_specs:
            debt, debt_created = Debt.objects.get_or_create(
                merchant=user,
                customer=customer,
                description=description,
                defaults={
                    "total_amount": amount,
                    "start_date": start_date,
                    "installment_count": count,
                },
            )
            if debt_created:
                build_installments(debt)
                DebtActivity.objects.create(
                    merchant=user,
                    debt=debt,
                    activity_type=DebtActivity.Type.CHARGE,
                    amount=amount,
                    note="Initial demo debt",
                )
            elif not debt.activities.exists():
                DebtActivity.objects.create(
                    merchant=user,
                    debt=debt,
                    activity_type=DebtActivity.Type.CHARGE,
                    amount=debt.total_amount,
                    note="Initial demo debt",
                )

        first_installment = (
            Installment.objects.filter(merchant=user, debt__description="مواد تموينية")
            .order_by("due_date")
            .first()
        )
        if first_installment and first_installment.status != Installment.Status.PAID:
            first_installment.mark_paid()

        phone_debt = Debt.objects.filter(merchant=user, description="هاتف محمول").first()
        if phone_debt and not phone_debt.activities.filter(note="دفعة جزئية للتجربة").exists():
            record_debt_payment(phone_debt, Decimal("150.00"), "دفعة جزئية للتجربة")

        grocery_debt = Debt.objects.filter(merchant=user, description="مواد تموينية").first()
        if grocery_debt and not grocery_debt.activities.filter(note="إضافة مشتريات جديدة").exists():
            add_debt_charge(
                grocery_debt,
                Decimal("75.00"),
                "إضافة مشتريات جديدة",
                timezone.localdate() + timedelta(days=20),
            )

        flag_overdue_installments(user)

        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write("Admin: admin@daftar.local")
        self.stdout.write("Admin password: admin123456")
        self.stdout.write("Email: demo@daftar.local")
        self.stdout.write("Password: demo123456")
