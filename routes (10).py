from flask import jsonify, request
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from ...auth import encode_mechanic_token, mechanic_token_required
from ...extensions import cache, db, limiter
from ...models import Mechanic, service_mechanic
from . import mechanic_bp
from .schemas import (
    mechanic_login_schema,
    mechanic_schema,
    mechanic_update_schema,
    mechanics_schema,
)


@mechanic_bp.post("/")
@limiter.limit("5 per minute")
def create_mechanic():
    data = mechanic_schema.load(request.get_json(silent=True) or {})
    mechanic = Mechanic(
        name=data["name"],
        email=data["email"].lower(),
        specialty=data.get("specialty"),
    )
    mechanic.set_password(data["password"])
    db.session.add(mechanic)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "A mechanic with that email already exists"}), 409
    cache.clear()
    return mechanic_schema.jsonify(mechanic), 201


@mechanic_bp.post("/login")
@limiter.limit("5 per minute")
def mechanic_login():
    data = mechanic_login_schema.load(request.get_json(silent=True) or {})
    mechanic = db.session.scalar(
        db.select(Mechanic).where(Mechanic.email == data["email"].lower())
    )
    if not mechanic or not mechanic.check_password(data["password"]):
        return jsonify({"message": "Invalid email or password"}), 401
    return jsonify(
        {
            "token": encode_mechanic_token(mechanic.id),
            "mechanic": mechanic_schema.dump(mechanic),
        }
    )


@mechanic_bp.get("/")
@cache.cached(timeout=30)
def get_mechanics():
    mechanics = db.session.scalars(db.select(Mechanic).order_by(Mechanic.id)).all()
    return jsonify(mechanics_schema.dump(mechanics))


@mechanic_bp.get("/ranked")
@cache.cached(timeout=30)
def ranked_mechanics():
    ticket_count = func.count(service_mechanic.c.service_ticket_id).label("ticket_count")
    rows = db.session.execute(
        db.select(Mechanic, ticket_count)
        .outerjoin(service_mechanic, Mechanic.id == service_mechanic.c.mechanic_id)
        .group_by(Mechanic.id)
        .order_by(ticket_count.desc(), Mechanic.id)
    ).all()
    return jsonify(
        [
            {**mechanic_schema.dump(mechanic), "ticket_count": count}
            for mechanic, count in rows
        ]
    )


@mechanic_bp.get("/<int:mechanic_id>")
def get_mechanic(mechanic_id):
    mechanic = db.session.get(Mechanic, mechanic_id)
    if not mechanic:
        return jsonify({"message": "Mechanic not found"}), 404
    return mechanic_schema.jsonify(mechanic)


@mechanic_bp.put("/<int:mechanic_id>")
@mechanic_token_required
def update_mechanic(auth_mechanic_id, mechanic_id):
    if auth_mechanic_id != mechanic_id:
        return jsonify({"message": "You may only update your own mechanic account"}), 403
    mechanic = db.session.get(Mechanic, mechanic_id)
    if not mechanic:
        return jsonify({"message": "Mechanic not found"}), 404
    data = mechanic_update_schema.load(request.get_json(silent=True) or {})
    for field in ("name", "email", "specialty"):
        if field in data:
            setattr(mechanic, field, data[field].lower() if field == "email" else data[field])
    if "password" in data:
        mechanic.set_password(data["password"])
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "That email is already in use"}), 409
    cache.clear()
    return mechanic_schema.jsonify(mechanic)


@mechanic_bp.delete("/<int:mechanic_id>")
@mechanic_token_required
def delete_mechanic(auth_mechanic_id, mechanic_id):
    if auth_mechanic_id != mechanic_id:
        return jsonify({"message": "You may only delete your own mechanic account"}), 403
    mechanic = db.session.get(Mechanic, mechanic_id)
    if not mechanic:
        return jsonify({"message": "Mechanic not found"}), 404
    db.session.delete(mechanic)
    db.session.commit()
    cache.clear()
    return jsonify({"message": "Mechanic deleted"})
