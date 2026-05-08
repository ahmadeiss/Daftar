# Database Schema

The backend uses Django's default `auth_user` table for merchants and four MVP tables for the debt ledger.

## `auth_user`

Built-in Django user table.

Important fields used by Daftar:

| Field | Type | Notes |
| --- | --- | --- |
| `id` | bigint | Primary key |
| `username` | varchar | Set to email by default |
| `email` | varchar | Login identifier |
| `first_name` | varchar | Merchant/business display name |
| `password` | varchar | Hashed password |

## `ledger_customer`

| Field | Type | Notes |
| --- | --- | --- |
| `id` | bigint | Primary key |
| `merchant_id` | bigint | FK to merchant user |
| `name` | varchar(120) | Customer name |
| `phone` | varchar(32) | Customer phone number |
| `notes` | text | Optional |
| `created_at` | timestamptz | Created time |
| `updated_at` | timestamptz | Updated time |

Indexes:

- `(merchant_id, name)`
- `(merchant_id, phone)`

## `ledger_debt`

| Field | Type | Notes |
| --- | --- | --- |
| `id` | bigint | Primary key |
| `merchant_id` | bigint | FK to merchant user |
| `customer_id` | bigint | FK to customer |
| `total_amount` | numeric(12,2) | Debt total, including extra charges |
| `description` | varchar(255) | Debt reason/item |
| `start_date` | date | Schedule start |
| `installment_count` | integer | Number of generated installments |
| `receipt_image` | varchar | Optional Cloudinary/local storage path |
| `created_at` | timestamptz | Created time |
| `updated_at` | timestamptz | Updated time |

Computed API fields:

- `paid_amount`
- `remaining_amount`
- `status`: `paid`, `unpaid`, or `late`
- `receipt_url`

## `ledger_installment`

| Field | Type | Notes |
| --- | --- | --- |
| `id` | bigint | Primary key |
| `merchant_id` | bigint | FK to merchant user |
| `debt_id` | bigint | FK to debt |
| `amount` | numeric(12,2) | Installment amount |
| `paid_amount` | numeric(12,2) | Partial/full paid amount |
| `due_date` | date | Due date |
| `status` | varchar(12) | `paid`, `unpaid`, `late` |
| `paid_at` | timestamptz | Set when fully paid |
| `created_at` | timestamptz | Created time |
| `updated_at` | timestamptz | Updated time |

Indexes:

- `(merchant_id, status, due_date)`
- `(debt_id, due_date)`

## `ledger_debtactivity`

Audit trail for merchant actions on a debt.

| Field | Type | Notes |
| --- | --- | --- |
| `id` | bigint | Primary key |
| `merchant_id` | bigint | FK to merchant user |
| `debt_id` | bigint | FK to debt |
| `activity_type` | varchar(12) | `payment`, `charge`, or `note` |
| `amount` | numeric(12,2) | Positive amount for the activity |
| `note` | varchar(255) | Optional merchant note |
| `created_at` | timestamptz | Created time |

Indexes:

- `(merchant_id, activity_type, created_at)`
- `(debt_id, created_at)`

## Customer Reputation

The API computes a simple credit profile from installment behavior:

- `commitment_score`: 0 to 100
- `risk_level`: `trusted`, `watch`, `risky`, or `new`
- `outstanding_amount`
- `overdue_amount`
- paid and late installment counts

This gives the merchant a fast decision aid before offering more credit, without adding accounting or ERP complexity.

## Data Ownership

Every business record includes `merchant_id`. API querysets always filter by the authenticated user, so one merchant cannot read or modify another merchant's data.
