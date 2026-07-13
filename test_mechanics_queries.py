"""Database seeding helpers used by both Flask CLI and seed.py."""

from .extensions import cache, db
from .models import Customer, Inventory, Mechanic, ServiceTicket


def seed_database() -> dict[str, bool]:
    """Create predictable demonstration data without duplicating records."""
    db.create_all()

    customer = db.session.scalar(
        db.select(Customer).where(Customer.email == "customer@example.com")
    )
    customer_created = customer is None
    if customer is None:
        customer = Customer(
            name="Demo Customer",
            email="customer@example.com",
            phone="555-0100",
        )
        customer.set_password("password123")
        db.session.add(customer)

    mechanic = db.session.scalar(
        db.select(Mechanic).where(Mechanic.email == "mechanic@example.com")
    )
    mechanic_created = mechanic is None
    if mechanic is None:
        mechanic = Mechanic(
            name="Demo Mechanic",
            email="mechanic@example.com",
            specialty="Diagnostics",
        )
        mechanic.set_password("wrench123")
        db.session.add(mechanic)

    oil_filter = db.session.scalar(
        db.select(Inventory).where(Inventory.name == "Oil Filter")
    )
    oil_filter_created = oil_filter is None
    if oil_filter is None:
        oil_filter = Inventory(name="Oil Filter", price=14.99)
        db.session.add(oil_filter)

    brake_pad = db.session.scalar(
        db.select(Inventory).where(Inventory.name == "Brake Pad Set")
    )
    brake_pad_created = brake_pad is None
    if brake_pad is None:
        brake_pad = Inventory(name="Brake Pad Set", price=79.99)
        db.session.add(brake_pad)

    # Flush first so the new customer receives an ID before the ticket query.
    db.session.flush()
    ticket = db.session.scalar(
        db.select(ServiceTicket).where(
            ServiceTicket.customer_id == customer.id,
            ServiceTicket.description == "Oil change and brake inspection",
        )
    )
    ticket_created = ticket is None
    if ticket is None:
        ticket = ServiceTicket(
            description="Oil change and brake inspection",
            status="Open",
            customer=customer,
        )
        ticket.mechanics.append(mechanic)
        ticket.parts.append(oil_filter)
        db.session.add(ticket)

    db.session.commit()
    cache.clear()

    return {
        "customer_created": customer_created,
        "mechanic_created": mechanic_created,
        "oil_filter_created": oil_filter_created,
        "brake_pad_created": brake_pad_created,
        "ticket_created": ticket_created,
    }
