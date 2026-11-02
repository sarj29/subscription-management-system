# API Contracts — Brightloop Subscription Management System

> **Base URL**: `http://localhost:8000`  
> **API prefix**: `/api/v1`  
> **Auth**: Bearer JWT in `Authorization` header (except `/auth/register` and `/auth/token`)  
> **Content-Type**: `application/json` for all request bodies

---

## 1. Authentication & Registration

### `POST /api/v1/auth/register`
Register a new user account.

**Request**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "Jane Doe"
}
```

**Response `201`**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "Jane Doe",
  "role": "staff",
  "status": "active"
}
```

**Errors**: `409` email already registered.

---

### `POST /api/v1/auth/token`
OAuth2 password login — returns access + refresh tokens.

**Request** (`application/x-www-form-urlencoded`)
```
username=user@example.com&password=SecurePass123!
```

**Response `200`**
```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "bearer"
}
```

**Errors**: `401` invalid credentials, `403` account inactive.

---

### `POST /api/v1/auth/refresh`
Issue new tokens using a valid refresh token.

**Request**
```json
{ "refresh_token": "<jwt>" }
```

**Response `200`** — same shape as `/auth/token`.

---

### `GET /api/v1/auth/me`
Return authenticated user's profile.

**Response `200`**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "Jane Doe",
  "role": "staff",
  "status": "active"
}
```

---

## 2. Customers

| Method   | Path                          | Description          |
|----------|-------------------------------|----------------------|
| `GET`    | `/api/v1/customers`           | List customers       |
| `POST`   | `/api/v1/customers`           | Create customer      |
| `GET`    | `/api/v1/customers/{id}`      | Get customer         |
| `PATCH`  | `/api/v1/customers/{id}`      | Partial update       |
| `DELETE` | `/api/v1/customers/{id}`      | Delete customer      |

### Customer object
```json
{
  "id": "uuid",
  "user_id": "uuid | null",
  "company_name": "Acme Corp",
  "contact_name": "John Smith",
  "email": "john@acme.com",
  "phone": "+1-555-0100",
  "address": "123 Main St",
  "city": "San Francisco",
  "country": "US",
  "tax_id": "US123456789",
  "notes": "VIP customer"
}
```

### `POST /api/v1/customers` — Request fields
```json
{
  "company_name": "string (required)",
  "contact_name": "string (required)",
  "email": "string (required)",
  "phone": "string | null",
  "address": "string | null",
  "city": "string | null",
  "country": "string | null",
  "tax_id": "string | null",
  "notes": "string | null"
}
```

**Query params** (list endpoint): `skip=0`, `limit=50`

---

## 3. Products & Variants

| Method   | Path                                            | Description           |
|----------|-------------------------------------------------|-----------------------|
| `GET`    | `/api/v1/products`                              | List products         |
| `POST`   | `/api/v1/products`                              | Create product        |
| `GET`    | `/api/v1/products/{id}`                         | Get product           |
| `PATCH`  | `/api/v1/products/{id}`                         | Update product        |
| `DELETE` | `/api/v1/products/{id}`                         | Delete product        |
| `POST`   | `/api/v1/products/{id}/variants`                | Add variant           |
| `PATCH`  | `/api/v1/products/{id}/variants/{variant_id}`   | Update variant        |
| `DELETE` | `/api/v1/products/{id}/variants/{variant_id}`   | Delete variant        |

### Product create request
```json
{
  "name": "Cloud Storage",
  "description": "Scalable cloud storage service",
  "sku": "CS-001",
  "is_active": true,
  "variants": [
    {
      "name": "100 GB",
      "sku": "CS-001-100GB",
      "unit_price": "9.9900",
      "currency": "USD",
      "is_active": true
    }
  ]
}
```

### Product response
```json
{
  "id": "uuid",
  "name": "Cloud Storage",
  "description": "...",
  "sku": "CS-001",
  "is_active": true,
  "variants": [{ "id": "uuid", "product_id": "uuid", "name": "100 GB", "unit_price": "9.9900", "currency": "USD", "is_active": true }]
}
```

---

## 4. Plans

| Method   | Path                  | Description    |
|----------|-----------------------|----------------|
| `GET`    | `/api/v1/plans`       | List plans     |
| `POST`   | `/api/v1/plans`       | Create plan    |
| `GET`    | `/api/v1/plans/{id}`  | Get plan       |
| `PATCH`  | `/api/v1/plans/{id}`  | Update plan    |
| `DELETE` | `/api/v1/plans/{id}`  | Delete plan    |

### Plan create request
```json
{
  "name": "Pro Monthly",
  "description": "Professional tier billed monthly",
  "billing_interval": "monthly",
  "interval_count": 1,
  "base_price": "49.0000",
  "currency": "USD",
  "trial_days": 14,
  "is_active": true
}
```

**`billing_interval` values**: `daily`, `weekly`, `monthly`, `quarterly`, `yearly`

---

## 5. Quotations

| Method   | Path                               | Description                         |
|----------|------------------------------------|-------------------------------------|
| `GET`    | `/api/v1/quotations`               | List quotations                     |
| `POST`   | `/api/v1/quotations`               | Create quotation                    |
| `GET`    | `/api/v1/quotations/{id}`          | Get quotation                       |
| `PATCH`  | `/api/v1/quotations/{id}`          | Update quotation metadata           |
| `POST`   | `/api/v1/quotations/{id}/status`   | Transition quotation status         |
| `DELETE` | `/api/v1/quotations/{id}`          | Delete (draft/cancelled only)       |

### Quotation create request
```json
{
  "customer_id": "uuid",
  "template_id": "uuid | null",
  "reference": "Q-2024-001",
  "valid_until": "2024-12-31",
  "notes": "Net 30 terms",
  "currency": "USD",
  "lines": [
    {
      "description": "Cloud Storage 100GB",
      "quantity": "1.0000",
      "unit_price": "9.9900",
      "discount_percent": "0.00",
      "tax_percent": "18.00",
      "position": 0,
      "product_variant_id": "uuid | null"
    }
  ]
}
```

### Status transition request
```json
{ "status": "quotation" }
```

**Quotation status machine**:
```
draft → quotation → confirmed
      ↘ cancelled   ↓        ↘ expired
                  cancelled
```

---

## 6. Subscriptions

| Method   | Path                                   | Description                          |
|----------|----------------------------------------|--------------------------------------|
| `GET`    | `/api/v1/subscriptions`                | List subscriptions                   |
| `POST`   | `/api/v1/subscriptions`                | Create subscription                  |
| `GET`    | `/api/v1/subscriptions/{id}`           | Get subscription                     |
| `PATCH`  | `/api/v1/subscriptions/{id}`           | Update subscription metadata         |
| `POST`   | `/api/v1/subscriptions/{id}/status`    | Transition subscription status       |
| `DELETE` | `/api/v1/subscriptions/{id}`           | Delete (draft/closed only)           |

### Subscription create request
```json
{
  "customer_id": "uuid",
  "plan_id": "uuid",
  "quotation_id": "uuid | null",
  "reference": "SUB-2024-001",
  "start_date": "2024-01-01",
  "end_date": null,
  "notes": "",
  "currency": "USD",
  "lines": [
    {
      "description": "Cloud Storage 100GB",
      "quantity": "1.0000",
      "unit_price": "9.9900",
      "discount_percent": "10.00",
      "tax_percent": "18.00",
      "position": 0,
      "product_variant_id": "uuid | null"
    }
  ]
}
```

### Status transition request
```json
{ "status": "active" }
```

**Subscription status machine**:
```
draft → quotation → confirmed → active → paused → active
      ↘ closed      ↘ closed    ↘ closed  ↘ closed
```

---

## 7. Common Response Codes

| Code | Meaning                          |
|------|----------------------------------|
| 200  | OK                               |
| 201  | Created                          |
| 204  | No Content (successful delete)   |
| 400  | Bad Request                      |
| 401  | Unauthorized / token expired     |
| 403  | Forbidden (inactive / wrong role)|
| 404  | Not Found                        |
| 409  | Conflict (duplicate / wrong state)|
| 422  | Validation / invalid transition  |
| 500  | Internal Server Error            |

---

## 8. Planned Phase 2 Endpoints (not yet implemented)

- `GET|POST /api/v1/invoices` — Invoice management
- `POST /api/v1/invoices/{id}/status` — Invoice status transitions (draft → confirmed → paid → cancelled)
- `GET|POST /api/v1/payments` — Payment recording and reversal
- `GET|POST /api/v1/discounts` — Discount codes and rules
- `GET|POST /api/v1/taxes` — Tax rate management
- `GET /api/v1/dashboard` — Analytics and KPI summary
