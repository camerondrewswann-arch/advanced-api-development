from flask import jsonify, request
from sqlalchemy.exc import IntegrityError

from ...auth import mechanic_token_required
from ...extensions import cache, db
from ...models import Inventory
from . import inventory_bp
from .schemas import inventory_items_schema, inventory_schema, inventory_update_schema


@inventory_bp.post("/")
@mechanic_token_required
def create_inventory(auth_mechanic_id):
    data = inventory_schema.load(request.get_json(silent=True) or {})
    part = Inventory(name=data["name"], price=data["price"])
    db.session.add(part)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "An inventory part with that name already exists"}), 409
    cache.clear()
    return inventory_schema.jsonify(part), 201


@inventory_bp.get("/")
@cache.cached(timeout=30)
def get_inventory():
    parts = db.session.scalars(db.select(Inventory).order_by(Inventory.name)).all()
    return jsonify(inventory_items_schema.dump(parts))


@inventory_bp.get("/<int:part_id>")
def get_inventory_part(part_id):
    part = db.session.get(Inventory, part_id)
    if not part:
        return jsonify({"message": "Inventory part not found"}), 404
    return inventory_schema.jsonify(part)


@inventory_bp.put("/<int:part_id>")
@mechanic_token_required
def update_inventory(auth_mechanic_id, part_id):
    part = db.session.get(Inventory, part_id)
    if not part:
        return jsonify({"message": "Inventory part not found"}), 404
    data = inventory_update_schema.load(request.get_json(silent=True) or {})
    for field in ("name", "price"):
        if field in data:
            setattr(part, field, data[field])
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "An inventory part with that name already exists"}), 409
    cache.clear()
    return inventory_schema.jsonify(part)


@inventory_bp.delete("/<int:part_id>")
@mechanic_token_required
def delete_inventory(auth_mechanic_id, part_id):
    part = db.session.get(Inventory, part_id)
    if not part:
        return jsonify({"message": "Inventory part not found"}), 404
    for ticket in list(part.service_tickets):
        ticket.parts.remove(part)
    db.session.delete(part)
    db.session.commit()
    cache.clear()
    return jsonify({"message": "Inventory part deleted"})
