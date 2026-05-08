# API Endpoints

Base URL:

```text
/api
```

Authentication uses JWT bearer tokens:

```http
Authorization: Bearer <access_token>
```

## Auth

| Method | Endpoint | Body | Description |
| --- | --- | --- | --- |
| POST | `/auth/register/` | `name`, `email`, `password` | Create merchant account and return tokens |
| POST | `/auth/token/` | `email`, `password` | Login and return tokens |
| POST | `/auth/token/refresh/` | `refresh` | Return a new access token |
| GET | `/auth/me/` | none | Return current merchant |

## Customers

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/customers/` | List customers with reputation fields |
| GET | `/customers/?search=0599` | Search by name or phone |
| POST | `/customers/` | Add customer |
| GET | `/customers/{id}/` | Customer details |
| GET | `/customers/{id}/profile/` | Credit profile, reputation summary, debts, recent installments |
| PATCH | `/customers/{id}/` | Update customer |
| DELETE | `/customers/{id}/` | Delete customer and related debts |

Customer body:

```json
{
  "name": "Customer name",
  "phone": "0599000001",
  "notes": "Optional note"
}
```

Customer list responses include:

```json
{
  "commitment_score": 85,
  "risk_level": "trusted",
  "unpaid_amount": "300.00",
  "late_installments": 0
}
```

Risk levels:

- `trusted`: good payer
- `watch`: lend with caution
- `risky`: avoid new credit until payment is made
- `new`: not enough history yet

## Debts

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/debts/` | List debts with installments and activity history |
| GET | `/debts/?customer=1` | List debts for one customer |
| POST | `/debts/` | Create debt and auto-generate schedule |
| GET | `/debts/{id}/` | Debt details |
| PATCH | `/debts/{id}/` | Update debt metadata or unpaid schedule |
| DELETE | `/debts/{id}/` | Delete debt and installments |
| GET | `/debts/{id}/installments/` | List installments for one debt |
| POST | `/debts/{id}/record-payment/` | Record partial/full payment and reduce balance |
| POST | `/debts/{id}/add-charge/` | Add a new amount to an existing debt |

Debt body can be JSON or `multipart/form-data` when uploading `receipt_image`:

```json
{
  "customer": 1,
  "total_amount": "450.00",
  "description": "Groceries",
  "start_date": "2026-05-08",
  "installment_count": 3
}
```

Installments are generated monthly. The first due date is one month after `start_date`. Amounts are split to cents, with any remainder distributed across the first installments.

Record payment body:

```json
{
  "amount": "100.00",
  "note": "Cash payment"
}
```

The backend allocates the payment to the oldest unpaid installments first.

Add charge body:

```json
{
  "amount": "75.00",
  "note": "New purchase",
  "due_date": "2026-06-08"
}
```

This increases `total_amount`, creates a new unpaid installment, and records a debt activity entry.

## Installments

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/installments/` | List installments |
| GET | `/installments/?status=late` | Filter by `paid`, `unpaid`, or `late` |
| GET | `/installments/{id}/` | Installment details |
| POST | `/installments/{id}/mark-paid/` | Mark installment as paid |

Each installment includes:

- `amount`
- `paid_amount`
- `remaining_amount`
- `due_date`
- `status`
- `paid_at`

The API refreshes overdue unpaid or partially paid installments to `late` before list/dashboard/reminder responses.

## Dashboard

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/dashboard/` | Totals, upcoming/overdue installments, committed customers, risky customers |

Response shape:

```json
{
  "total_debts": "1830.00",
  "paid_amount": "150.00",
  "unpaid_amount": "1680.00",
  "overdue_amount": "300.00",
  "customers_count": 3,
  "debts_count": 3,
  "upcoming_count": 2,
  "overdue_count": 1,
  "upcoming_installments": [],
  "overdue_installments": [],
  "committed_customers": [],
  "risky_customers": []
}
```

## Reminder Logic

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/reminders/` | Return unpaid and late installments ready for reminder processing |

No SMS provider is called in the MVP. This endpoint provides the data needed for a future scheduled reminder worker.

## Health

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/health/` | API health check |
