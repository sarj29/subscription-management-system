"""
Comprehensive integration tests for Brightloop business APIs:
- Customer CRUD, search, and validation
- Product & Variant CRUD and price adjustments
- Plan CRUD, intervals, and settings
- Quotation lifecycle & conversion to subscription
- Subscription lifecycle (active -> pause -> resume -> close -> renew)
- Billing integration: subscription-to-invoice and payment recording
"""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.dependencies import get_current_active_user
from app.main import app
from app.models.user import User, UserRole, UserStatus
from app.models.quotation_template import QuotationTemplate

# Create an in-memory SQLite database for test client
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


# Mock authenticated users
admin_user = User(
    id="admin-uuid",
    email="admin@brightloop.com",
    hashed_password="hash",
    full_name="Admin User",
    role=UserRole.ADMIN.value,
    status=UserStatus.ACTIVE.value,
)

staff_user = User(
    id="staff-uuid",
    email="staff@brightloop.com",
    hashed_password="hash",
    full_name="Staff User",
    role=UserRole.STAFF.value,
    status=UserStatus.ACTIVE.value,
)

customer_user = User(
    id="customer-uuid",
    email="customer@brightloop.com",
    hashed_password="hash",
    full_name="Customer User",
    role=UserRole.CUSTOMER.value,
    status=UserStatus.ACTIVE.value,
)

current_mock_user = admin_user


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_get_current_active_user():
    return current_mock_user


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_active_user] = override_get_current_active_user

client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def setup_database():
    """Reset mock user to admin by default for each test."""
    global current_mock_user
    current_mock_user = admin_user
    yield


# ---------------------------------------------------------------------------
# 1. Customer APIs Tests
# ---------------------------------------------------------------------------

def test_customer_crud_and_validation():
    # Create customer
    payload = {
        "company_name": "Brightloop Partner Ltd",
        "contact_name": "Alice Smith",
        "email": "alice@partner.com",
        "city": "London",
        "country": "UK",
    }
    resp = client.post("/api/v1/customers/", json=payload)
    assert resp.status_code == 201
    customer = resp.json()
    assert customer["company_name"] == "Brightloop Partner Ltd"
    cust_id = customer["id"]

    # Duplicate email should return 409 Conflict
    dup_resp = client.post("/api/v1/customers/", json=payload)
    assert dup_resp.status_code == 409

    # Search customer
    search_resp = client.get("/api/v1/customers/?search=Partner")
    assert search_resp.status_code == 200
    results = search_resp.json()
    assert any(c["id"] == cust_id for c in results)

    # Filter by city
    city_resp = client.get("/api/v1/customers/?city=London")
    assert city_resp.status_code == 200
    assert any(c["id"] == cust_id for c in city_resp.json())

    # Update customer
    patch_resp = client.patch(f"/api/v1/customers/{cust_id}", json={"contact_name": "Alice Johnson"})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["contact_name"] == "Alice Johnson"

    # Get customer
    get_resp = client.get(f"/api/v1/customers/{cust_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == cust_id


# ---------------------------------------------------------------------------
# 2. Product & Variant APIs Tests
# ---------------------------------------------------------------------------

def test_product_and_variant_crud_and_price_adjustment():
    # Create product with variant
    payload = {
        "name": "Cloud Accounting",
        "sku": f"PROD-{uuid.uuid4().hex[:6]}",
        "is_active": True,
        "variants": [
            {
                "name": "Standard Edition",
                "sku": f"VAR-{uuid.uuid4().hex[:6]}",
                "unit_price": "100.0000",
                "currency": "USD",
            }
        ],
    }
    resp = client.post("/api/v1/products/", json=payload)
    assert resp.status_code == 201
    prod = resp.json()
    prod_id = prod["id"]
    var_id = prod["variants"][0]["id"]
    assert Decimal(prod["variants"][0]["unit_price"]) == Decimal("100.0000")

    # Add a second variant (e.g. Odoo brand edition)
    var_payload = {
        "name": "Odoo Brand Edition",
        "sku": f"VAR-{uuid.uuid4().hex[:6]}",
        "unit_price": "150.0000",
        "currency": "USD",
    }
    v_resp = client.post(f"/api/v1/products/{prod_id}/variants", json=var_payload)
    assert v_resp.status_code == 201
    odoo_var_id = v_resp.json()["id"]

    # Price adjustment (+560.00 as in Brightloop story)
    adj_resp = client.post(
        f"/api/v1/products/{prod_id}/variants/{odoo_var_id}/adjust-price",
        json={"adjustment": "560.00"},
    )
    assert adj_resp.status_code == 200
    adjusted_price = Decimal(adj_resp.json()["unit_price"])
    assert adjusted_price == Decimal("710.0000")  # 150 + 560 = 710

    # Negative price validation
    neg_resp = client.post(
        f"/api/v1/products/{prod_id}/variants/{odoo_var_id}/adjust-price",
        json={"adjustment": "-1000.00"},
    )
    assert neg_resp.status_code == 422


# ---------------------------------------------------------------------------
# 3. Plan APIs Tests
# ---------------------------------------------------------------------------

def test_plan_crud_and_settings():
    payload = {
        "name": "Enterprise Yearly Plan",
        "description": "Premium tier billed yearly",
        "billing_interval": "yearly",
        "interval_count": 1,
        "base_price": "1200.0000",
        "currency": "USD",
        "trial_days": 30,
        "is_active": True,
        "min_quantity": 5,
        "allow_pause": True,
        "allow_early_closure": True,
        "allow_renewal": True,
    }
    resp = client.post("/api/v1/plans/", json=payload)
    assert resp.status_code == 201
    plan = resp.json()
    assert plan["billing_interval"] == "yearly"
    assert plan["min_quantity"] == 5
    assert plan["allow_pause"] is True
    plan_id = plan["id"]

    # Get plan
    get_resp = client.get(f"/api/v1/plans/{plan_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Enterprise Yearly Plan"
    assert get_resp.json()["min_quantity"] == 5

    # Filter plans by interval
    filter_resp = client.get("/api/v1/plans/?billing_interval=yearly")
    assert filter_resp.status_code == 200
    assert any(p["id"] == plan_id for p in filter_resp.json())


# ---------------------------------------------------------------------------
# 4. Quotations & Conversion to Subscription Tests
# ---------------------------------------------------------------------------

def test_quotation_lifecycle_and_conversion():
    # Create customer & plan first
    cust_resp = client.post("/api/v1/customers/", json={
        "company_name": "Quote Customer Inc",
        "contact_name": "Bob Vance",
        "email": f"bob-{uuid.uuid4().hex[:6]}@vance.com",
    })
    cust_id = cust_resp.json()["id"]

    plan_resp = client.post("/api/v1/plans/", json={
        "name": "Standard Monthly",
        "billing_interval": "monthly",
        "interval_count": 1,
        "base_price": "50.0000",
        "currency": "USD",
        "min_quantity": 1,
    })
    plan_id = plan_resp.json()["id"]

    # Create quotation with lines, discounts, and taxes
    quote_payload = {
        "customer_id": cust_id,
        "currency": "USD",
        "lines": [
            {
                "description": "Software Seat",
                "quantity": "2.0000",
                "unit_price": "100.0000",
                "discount_percent": "10.00",  # 200 - 10% = 180 subtotal
                "tax_percent": "10.00",       # 180 * 10% = 18 tax
            }
        ],
    }
    resp = client.post("/api/v1/quotations/", json=quote_payload)
    assert resp.status_code == 201
    quote = resp.json()
    quote_id = quote["id"]
    assert quote["status"] == "draft"
    assert Decimal(quote["subtotal"]) == Decimal("180.0000")
    assert Decimal(quote["tax_amount"]) == Decimal("18.0000")
    assert Decimal(quote["total_amount"]) == Decimal("198.0000")

    # Transition: draft -> quotation
    t1_resp = client.post(f"/api/v1/quotations/{quote_id}/status", json={"status": "quotation"})
    assert t1_resp.status_code == 200
    assert t1_resp.json()["status"] == "quotation"

    # Transition: quotation -> confirmed
    t2_resp = client.post(f"/api/v1/quotations/{quote_id}/status", json={"status": "confirmed"})
    assert t2_resp.status_code == 200
    assert t2_resp.json()["status"] == "confirmed"

    # Convert confirmed quotation into a subscription
    convert_resp = client.post(
        f"/api/v1/quotations/{quote_id}/convert-to-subscription",
        json={"plan_id": plan_id},
    )
    assert convert_resp.status_code == 201
    sub = convert_resp.json()
    assert sub["customer_id"] == cust_id
    assert sub["plan_id"] == plan_id
    assert sub["quotation_id"] == quote_id
    assert sub["status"] == "confirmed"
    assert len(sub["lines"]) == 1
    assert Decimal(sub["total_amount"]) == Decimal("198.0000")

    # Duplicate conversion should be rejected with 409 Conflict
    dup_convert = client.post(
        f"/api/v1/quotations/{quote_id}/convert-to-subscription",
        json={"plan_id": plan_id},
    )
    assert dup_convert.status_code == 409


# ---------------------------------------------------------------------------
# 5. Subscription Lifecycle: Active, Pause, Resume, Close, Renew
# ---------------------------------------------------------------------------

def test_subscription_lifecycle_operations():
    # Create customer and plan
    cust_resp = client.post("/api/v1/customers/", json={
        "company_name": "Lifecycle Corp",
        "contact_name": "Charlie Day",
        "email": f"charlie-{uuid.uuid4().hex[:6]}@paddys.com",
    })
    cust_id = cust_resp.json()["id"]

    plan_resp = client.post("/api/v1/plans/", json={
        "name": "Pro Monthly Plan",
        "billing_interval": "monthly",
        "base_price": "75.0000",
        "trial_days": 14,
        "allow_pause": True,
        "allow_early_closure": True,
        "allow_renewal": True,
    })
    plan_id = plan_resp.json()["id"]

    # Create subscription in draft
    sub_payload = {
        "customer_id": cust_id,
        "plan_id": plan_id,
        "start_date": str(date.today()),
        "lines": [
            {
                "description": "Pro Tier Seat",
                "quantity": "1.0000",
                "unit_price": "75.0000",
            }
        ],
    }
    resp = client.post("/api/v1/subscriptions/", json=sub_payload)
    assert resp.status_code == 201
    sub = resp.json()
    sub_id = sub["id"]
    assert sub["status"] == "draft"
    assert sub["trial_end_date"] is not None

    # Step through status flow: draft -> confirmed -> active
    client.post(f"/api/v1/subscriptions/{sub_id}/status", json={"status": "confirmed"})
    active_resp = client.post(f"/api/v1/subscriptions/{sub_id}/status", json={"status": "active"})
    assert active_resp.status_code == 200
    assert active_resp.json()["status"] == "active"

    # Action: Pause
    pause_resp = client.post(f"/api/v1/subscriptions/{sub_id}/pause")
    assert pause_resp.status_code == 200
    assert pause_resp.json()["status"] == "paused"

    # Action: Resume
    resume_resp = client.post(f"/api/v1/subscriptions/{sub_id}/resume")
    assert resume_resp.status_code == 200
    assert resume_resp.json()["status"] == "active"

    # Action: Close
    close_resp = client.post(f"/api/v1/subscriptions/{sub_id}/close", json={"reason": "Completed contract"})
    assert close_resp.status_code == 200
    assert close_resp.json()["status"] == "closed"

    # Action: Renew
    renew_resp = client.post(f"/api/v1/subscriptions/{sub_id}/renew", json={"notes": "Annual renewal"})
    assert renew_resp.status_code == 200
    assert renew_resp.json()["status"] == "active"


# ---------------------------------------------------------------------------
# 6. Billing Integration Tests: Invoice Generation and Payment
# ---------------------------------------------------------------------------

def test_billing_integration_invoice_and_payment():
    # Create customer and plan
    cust_resp = client.post("/api/v1/customers/", json={
        "company_name": "Billing Day Corp",
        "contact_name": "Dennis Reynolds",
        "email": f"dennis-{uuid.uuid4().hex[:6]}@reynolds.com",
    })
    cust_id = cust_resp.json()["id"]

    plan_resp = client.post("/api/v1/plans/", json={
        "name": "Basic Monthly",
        "billing_interval": "monthly",
        "base_price": "100.0000",
    })
    plan_id = plan_resp.json()["id"]

    sub_resp = client.post("/api/v1/subscriptions/", json={
        "customer_id": cust_id,
        "plan_id": plan_id,
        "lines": [
            {
                "description": "Basic Subscription",
                "quantity": "1.0000",
                "unit_price": "100.0000",
                "tax_percent": "10.00",
            }
        ],
    })
    sub_id = sub_resp.json()["id"]

    # Generate draft invoice from subscription
    inv_resp = client.post(f"/api/v1/subscriptions/{sub_id}/invoices?due_days=15")
    assert inv_resp.status_code == 201
    invoice = inv_resp.json()
    inv_id = invoice["id"]
    assert invoice["status"] == "draft"
    assert invoice["customer_id"] == cust_id
    assert invoice["subscription_id"] == sub_id
    assert Decimal(invoice["total_amount"]) == Decimal("110.0000")

    # Confirm invoice
    conf_resp = client.post(f"/api/v1/invoices/{inv_id}/status", json={"status": "confirmed"})
    assert conf_resp.status_code == 200
    assert conf_resp.json()["status"] == "confirmed"

    # Record payment against invoice
    pay_payload = {
        "invoice_id": inv_id,
        "customer_id": cust_id,
        "amount": "110.0000",
        "payment_method": "credit_card",
        "notes": "Paid in full via Stripe",
    }
    pay_resp = client.post("/api/v1/payments/", json=pay_payload)
    assert pay_resp.status_code == 201
    payment = pay_resp.json()
    assert payment["status"] == "recorded"
    assert Decimal(payment["amount"]) == Decimal("110.0000")

    # Verify invoice was automatically transitioned to 'paid'
    inv_check = client.get(f"/api/v1/invoices/{inv_id}")
    assert inv_check.status_code == 200
    assert inv_check.json()["status"] == "paid"
