# Admin Panel

Daftar includes a Django Admin panel for platform owners.

Local URL:

```text
http://127.0.0.1:8000/admin/
```

Dashboard URL:

```text
http://127.0.0.1:8000/admin/dashboard/
```

Local demo admin:

```text
admin@daftar.local
admin123456
```

## What Admin Can Do

- Monitor platform subscription revenue.
- See paid merchants, trial merchants, overdue merchants, and suspended merchants.
- Track which stores need payment and which renew soon.
- Manage subscription plans.
- Record subscription payments for stores.
- Create merchant/store accounts from `Merchant profiles`.
- Manage store details: store name, owner, phone, city, address, business type, subscription status, notes.
- Activate or suspend login by editing the linked user account.
- View quick store metrics: customer count, debt count, overdue installment count.
- Manage users, customers, debts, installments, and debt activity records.

## Subscription Management

Use these admin sections:

- `Subscription plans`: create plans such as Starter or Pro, with price and billing cycle.
- `Subscription payments`: record payments from merchants.
- `Merchant profiles`: assign a plan, set subscription status, and view expiry date.

When a payment is saved as `Paid`, the system updates the merchant profile automatically:

- sets the active plan
- marks the merchant as `Active`
- updates subscription start and expiry dates
- re-enables merchant login if it was inactive

Dashboard cards show:

- monthly subscription revenue
- paid merchants
- merchants needing payment
- trial stores
- suspended stores

## Creating a Merchant

1. Open `/admin/`.
2. Go to `Merchant profiles`.
3. Click `Add merchant profile`.
4. Enter merchant email, password, and store details.
5. Save.

The system automatically creates the merchant login account and links it to the store profile.

## Production Note

Do not use the local demo admin credentials in production. Create a real superuser with:

```bash
python manage.py createsuperuser
```
