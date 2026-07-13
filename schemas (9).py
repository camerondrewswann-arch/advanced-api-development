from marshmallow import fields, validate

from ...extensions import ma
from ...models import Mechanic


class MechanicSchema(ma.SQLAlchemyAutoSchema):
    password = fields.String(load_only=True, required=True, validate=validate.Length(min=6))
    id = fields.Integer(dump_only=True)
    email = fields.Email(required=True)
    name = fields.String(required=True, validate=validate.Length(min=2, max=120))

    class Meta:
        model = Mechanic
        load_instance = False
        include_fk = True
        exclude = ("password_hash", "service_tickets")


class MechanicUpdateSchema(ma.Schema):
    name = fields.String(validate=validate.Length(min=2, max=120))
    email = fields.Email()
    specialty = fields.String(allow_none=True, validate=validate.Length(max=120))
    password = fields.String(load_only=True, validate=validate.Length(min=6))


mechanic_schema = MechanicSchema()
mechanics_schema = MechanicSchema(many=True)
mechanic_login_schema = MechanicSchema(only=("email", "password"))
mechanic_update_schema = MechanicUpdateSchema()
