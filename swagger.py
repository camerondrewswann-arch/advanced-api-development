from marshmallow import fields, validate

from ...extensions import ma
from ...models import ServiceTicket


class ServiceTicketSchema(ma.SQLAlchemyAutoSchema):
    mechanics = fields.Method("serialize_mechanics", dump_only=True)
    parts = fields.Method("serialize_parts", dump_only=True)

    class Meta:
        model = ServiceTicket
        load_instance = False
        include_fk = True
        exclude = ("customer",)

    def serialize_mechanics(self, obj):
        return [
            {"id": mechanic.id, "name": mechanic.name, "specialty": mechanic.specialty}
            for mechanic in obj.mechanics
        ]

    def serialize_parts(self, obj):
        return [
            {"id": part.id, "name": part.name, "price": part.price}
            for part in obj.parts
        ]


class ServiceTicketCreateSchema(ma.Schema):
    description = fields.String(required=True, validate=validate.Length(min=3, max=500))
    status = fields.String(load_default="Open", validate=validate.OneOf(["Open", "In Progress", "Closed"]))


class ServiceTicketUpdateSchema(ma.Schema):
    description = fields.String(validate=validate.Length(min=3, max=500))
    status = fields.String(validate=validate.OneOf(["Open", "In Progress", "Closed"]))


class TicketMechanicEditSchema(ma.Schema):
    add_ids = fields.List(fields.Integer(strict=True), load_default=list)
    remove_ids = fields.List(fields.Integer(strict=True), load_default=list)


service_ticket_schema = ServiceTicketSchema()
service_tickets_schema = ServiceTicketSchema(many=True)
service_ticket_create_schema = ServiceTicketCreateSchema()
service_ticket_update_schema = ServiceTicketUpdateSchema()
ticket_mechanic_edit_schema = TicketMechanicEditSchema()
