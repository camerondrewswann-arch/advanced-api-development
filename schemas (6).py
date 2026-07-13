from flask import jsonify, request
from sqlalchemy.exc import IntegrityError

from ...auth import encode_token, token_required
from ...extensions import cache, db, limiter
from ...models import Customer, ServiceTicket
from ..service_tickets.schemas import service_tickets_schema
from . import customer_bp
from .schemas import (
    customer_schema,
    customer_update_schema,
    customers_schema,
    login_schema,
)


@customer_bp.post("/")
@limiter.limit("5 per minute")
def create_customer():
    data = customer_schema.load(request.get_json(silent=True) or {})
    customer = Customer(name=data["name"], email=data["email"].lower(), phone=data.get("phone"))
    customer.set_password(data["password"])
    db.session.add(customer)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "A customer with that email already exists"}), 409
    cache.clear()
    return customer_schema.jsonify(customer), 201


@customer_bp.get("/")
@cache.cached(timeout=30, query_string=True)
def get_customers():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 5, type=int)
    per_page = min(max(per_page, 1), 100)
    pagination = db.paginate(
        db.select(Customer).order_by(Customer.id),
        page=max(page, 1),
        per_page=per_page,
        error_out=False,
    )
    return jsonify(
        {
            "items": customers_schema.dump(pagination.items),
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        }
    )


@customer_bp.get("/<int:customer_id>")
def get_customer(customer_id):
    customer = db.session.get(Customer, customer_id)
    if not customer:
        return jsonify({"message": "Customer not found"}), 404
    return customer_schema.jsonify(customer)


@customer_bp.post("/login")
@limiter.limit("5 per minute")
def login():
    data = login_schema.load(request.get_json(silent=True) or {})
    customer = db.session.scalar(
        db.select(Customer).where(Customer.email == data["email"].lower())
    )
    if not customer or not customer.check_password(data["password"]):
        return jsonify({"message": "Invalid email or password"}), 401
    return jsonify({"token": encode_token(customer.id), "customer": customer_schema.dump(customer)})


@customer_bp.get("/my-tickets")
@token_required
def my_tickets(auth_customer_id):
    tickets = db.session.scalars(
        db.select(ServiceTicket)
        .where(ServiceTicket.customer_id == auth_customer_id)
        .order_by(ServiceTicket.id.desc())
    ).all()
    return jsonify(service_tickets_schema.dump(tickets))


@customer_bp.put("/<int:customer_id>")
@token_required
def update_customer(auth_customer_id, customer_id):
    if auth_customer_id != customer_id:
        return jsonify({"message": "You may only update your own customer account"}), 403
    customer = db.session.get(Customer, customer_id)
    if not customer:
        return jsonify({"message": "Customer not found"}), 404
    data = customer_update_schema.load(request.get_json(silent=True) or {})
    for field in ("name", "email", "phone"):
        if field in data:
            setattr(customer, field, data[field].lower() if field == "email" else data[field])
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "That email is already in use"}), 409
    cache.clear()
    return customer_schema.jsonify(customer)


@customer_bp.delete("/<int:customer_id>")
@token_required
def delete_customer(auth_customer_id, customer_id):
    if auth_customer_id != customer_id:
        return jsonify({"message": "You may only delete your own customer account"}), 403
    customer = db.session.get(Customer, customer_id)
    if not customer:
        return jsonify({"message": "Customer not found"}), 404
    db.session.delete(customer)
    db.session.commit()
    cache.clear()
    return jsonify({"message": "Customer deleted"})
