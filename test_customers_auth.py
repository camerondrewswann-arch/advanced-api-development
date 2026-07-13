from marshmallow import fields, validate

from ...extensions import ma
from ...models import Inventory


class InventorySchema(ma.SQLAlchemyAutoSchema):
    id = fields.Integer(dump_only=True)
    name = fields.String(required=True, validate=validate.Length(min=2, max=150))
    price = fields.Float(required=True, validate=validate.Range(min=0))

    class Meta:
        model = Inventory
        load_instance = False
        exclude = ("service_tickets",)


class InventoryUpdateSchema(ma.Schema):
    name = fields.String(validate=validate.Length(min=2, max=150))
    price = fields.Float(validate=validate.Range(min=0))


inventory_schema = InventorySchema()
inventory_items_schema = InventorySchema(many=True)
inventory_update_schema = InventoryUpdateSchema()
