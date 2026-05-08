import django.db.models.deletion
import ledger.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Customer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("phone", models.CharField(max_length=32)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "merchant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="customers",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Debt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("total_amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("description", models.CharField(max_length=255)),
                ("start_date", models.DateField()),
                ("installment_count", models.PositiveIntegerField(default=1)),
                (
                    "receipt_image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to=ledger.models.receipt_upload_path,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="debts",
                        to="ledger.customer",
                    ),
                ),
                (
                    "merchant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="debts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Installment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("due_date", models.DateField()),
                (
                    "status",
                    models.CharField(
                        choices=[("paid", "Paid"), ("unpaid", "Unpaid"), ("late", "Late")],
                        default="unpaid",
                        max_length=12,
                    ),
                ),
                ("paid_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "debt",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="installments",
                        to="ledger.debt",
                    ),
                ),
                (
                    "merchant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="installments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["due_date", "id"],
            },
        ),
        migrations.AddIndex(
            model_name="customer",
            index=models.Index(fields=["merchant", "name"], name="ledger_cust_merchan_336fb9_idx"),
        ),
        migrations.AddIndex(
            model_name="customer",
            index=models.Index(fields=["merchant", "phone"], name="ledger_cust_merchan_2250f9_idx"),
        ),
        migrations.AddIndex(
            model_name="debt",
            index=models.Index(fields=["merchant", "created_at"], name="ledger_debt_merchan_a948a1_idx"),
        ),
        migrations.AddIndex(
            model_name="debt",
            index=models.Index(fields=["customer", "created_at"], name="ledger_debt_custome_a3d480_idx"),
        ),
        migrations.AddIndex(
            model_name="installment",
            index=models.Index(fields=["merchant", "status", "due_date"], name="ledger_inst_merchan_4ddde5_idx"),
        ),
        migrations.AddIndex(
            model_name="installment",
            index=models.Index(fields=["debt", "due_date"], name="ledger_inst_debt_id_74e334_idx"),
        ),
    ]
