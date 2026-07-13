from marshmallow import fields, validate

from ...extensions import ma
from ...models import Customer


class CustomerSchema(ma.SQLAlchemyAutoSchema):
    password = fields.String(load_only=True, required=True, validate=validate.Length(min=6))
    id = fields.Integer(dump_only=True)
    email = fields.Email(required=True)
    name = fields.String(required=True, validate=validate.Length(min=2, max=120))

    class Meta:
        model = Customer
        load_instance = False
        include_fk = True
        exclude = ("password_hash", "service_tickets")


class CustomerUpdateSchema(ma.Schema):
    name = fields.String(validate=validate.Length(min=2, max=120))
    email = fields.Email()
    phone = fields.String(allow_none=True, validate=validate.Length(max=30))


customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)
login_schema = CustomerSchema(only=("email", "password"))
customer_update_schema = CustomerUpdateSchema()
