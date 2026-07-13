from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


service_mechanic = db.Table(
    "service_mechanic",
    db.Column(
        "service_ticket_id",
        db.Integer,
        db.ForeignKey("service_tickets.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "mechanic_id",
        db.Integer,
        db.ForeignKey("mechanics.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


ticket_inventory = db.Table(
    "ticket_inventory",
    db.Column(
        "service_ticket_id",
        db.Integer,
        db.ForeignKey("service_tickets.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "inventory_id",
        db.Integer,
        db.ForeignKey("inventory.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(30), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)

    service_tickets = db.relationship(
        "ServiceTicket",
        back_populates="customer",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Mechanic(db.Model):
    __tablename__ = "mechanics"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    specialty = db.Column(db.String(120), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)

    service_tickets = db.relationship(
        "ServiceTicket",
        secondary=service_mechanic,
        back_populates="mechanics",
        lazy="selectin",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class ServiceTicket(db.Model):
    __tablename__ = "service_tickets"

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(50), nullable=False, default="Open")
    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    customer = db.relationship("Customer", back_populates="service_tickets")
    mechanics = db.relationship(
        "Mechanic",
        secondary=service_mechanic,
        back_populates="service_tickets",
        lazy="selectin",
    )
    parts = db.relationship(
        "Inventory",
        secondary=ticket_inventory,
        back_populates="service_tickets",
        lazy="selectin",
    )


class Inventory(db.Model):
    __tablename__ = "inventory"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True, index=True)
    price = db.Column(db.Float, nullable=False)

    service_tickets = db.relationship(
        "ServiceTicket",
        secondary=ticket_inventory,
        back_populates="parts",
        lazy="selectin",
    )
