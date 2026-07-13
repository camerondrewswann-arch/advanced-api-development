"""Swagger 2.0 documentation configuration."""

from __future__ import annotations

from flask import Flask
from flasgger import Swagger

SWAGGER_CONFIG = {
    "headers": [],
    "specs": [
        {
            "endpoint": "mechanic_shop_spec",
            "route": "/swagger.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/",
}


def _json_body(schema_ref: str) -> list[dict]:
    return [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {"$ref": f"#/definitions/{schema_ref}"},
        }
    ]


def build_template(app: Flask) -> dict:
    """Build a Swagger 2.0 template with the production host and HTTPS scheme."""
    return {
        "swagger": "2.0",
        "info": {
            "title": "Mechanic Shop API",
            "description": (
                "Customer, mechanic, service-ticket, inventory, authentication, "
                "rate-limiting, caching, and advanced-query endpoints."
            ),
            "version": "1.0.0",
        },
        "host": app.config["SWAGGER_HOST"],
        "basePath": "/",
        "schemes": app.config["SWAGGER_SCHEMES"],
        "consumes": ["application/json"],
        "produces": ["application/json"],
        "securityDefinitions": {
            "BearerAuth": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "Enter: Bearer <token>",
            }
        },
        "tags": [
            {"name": "Health"},
            {"name": "Customers"},
            {"name": "Mechanics"},
            {"name": "Service Tickets"},
            {"name": "Inventory"},
        ],
        "definitions": {
            "CustomerCreate": {
                "type": "object",
                "required": ["name", "email", "password"],
                "properties": {
                    "name": {"type": "string", "example": "Cameron Swann"},
                    "email": {"type": "string", "example": "cameron@example.com"},
                    "phone": {"type": "string", "example": "555-0100"},
                    "password": {"type": "string", "example": "password123"},
                },
            },
            "Login": {
                "type": "object",
                "required": ["email", "password"],
                "properties": {
                    "email": {"type": "string", "example": "customer@example.com"},
                    "password": {"type": "string", "example": "password123"},
                },
            },
            "MechanicCreate": {
                "type": "object",
                "required": ["name", "email", "password"],
                "properties": {
                    "name": {"type": "string", "example": "Demo Mechanic"},
                    "email": {"type": "string", "example": "mechanic@example.com"},
                    "specialty": {"type": "string", "example": "Diagnostics"},
                    "password": {"type": "string", "example": "wrench123"},
                },
            },
            "TicketCreate": {
                "type": "object",
                "required": ["description"],
                "properties": {
                    "description": {"type": "string", "example": "Replace front brakes"},
                    "status": {
                        "type": "string",
                        "enum": ["Open", "In Progress", "Closed"],
                        "example": "Open",
                    },
                },
            },
            "TicketMechanicEdit": {
                "type": "object",
                "properties": {
                    "add_ids": {"type": "array", "items": {"type": "integer"}},
                    "remove_ids": {"type": "array", "items": {"type": "integer"}},
                },
                "example": {"add_ids": [1], "remove_ids": []},
            },
            "InventoryCreate": {
                "type": "object",
                "required": ["name", "price"],
                "properties": {
                    "name": {"type": "string", "example": "Oil Filter"},
                    "price": {"type": "number", "format": "float", "example": 14.99},
                },
            },
        },
        "paths": {
            "/health": {
                "get": {
                    "tags": ["Health"],
                    "summary": "Render health check",
                    "responses": {"200": {"description": "API is healthy"}},
                }
            },
            "/customers/": {
                "get": {
                    "tags": ["Customers"],
                    "summary": "List customers with pagination",
                    "parameters": [
                        {"name": "page", "in": "query", "type": "integer", "default": 1},
                        {"name": "per_page", "in": "query", "type": "integer", "default": 5},
                    ],
                    "responses": {"200": {"description": "Paginated customers"}},
                },
                "post": {
                    "tags": ["Customers"],
                    "summary": "Create a customer",
                    "parameters": _json_body("CustomerCreate"),
                    "responses": {"201": {"description": "Customer created"}},
                },
            },
            "/customers/login": {
                "post": {
                    "tags": ["Customers"],
                    "summary": "Customer login",
                    "parameters": _json_body("Login"),
                    "responses": {"200": {"description": "JWT returned"}},
                }
            },
            "/customers/my-tickets": {
                "get": {
                    "tags": ["Customers"],
                    "summary": "Get tickets for the authenticated customer",
                    "security": [{"BearerAuth": []}],
                    "responses": {"200": {"description": "Customer tickets"}},
                }
            },
            "/mechanics/": {
                "get": {
                    "tags": ["Mechanics"],
                    "summary": "List mechanics",
                    "responses": {"200": {"description": "Mechanic list"}},
                },
                "post": {
                    "tags": ["Mechanics"],
                    "summary": "Create a mechanic",
                    "parameters": _json_body("MechanicCreate"),
                    "responses": {"201": {"description": "Mechanic created"}},
                },
            },
            "/mechanics/login": {
                "post": {
                    "tags": ["Mechanics"],
                    "summary": "Mechanic login",
                    "parameters": _json_body("Login"),
                    "responses": {"200": {"description": "JWT returned"}},
                }
            },
            "/mechanics/ranked": {
                "get": {
                    "tags": ["Mechanics"],
                    "summary": "Rank mechanics by ticket count",
                    "responses": {"200": {"description": "Ranked mechanics"}},
                }
            },
            "/service-tickets/": {
                "get": {
                    "tags": ["Service Tickets"],
                    "summary": "List service tickets",
                    "parameters": [{"name": "status", "in": "query", "type": "string"}],
                    "responses": {"200": {"description": "Service-ticket list"}},
                },
                "post": {
                    "tags": ["Service Tickets"],
                    "summary": "Create a service ticket as a customer",
                    "security": [{"BearerAuth": []}],
                    "parameters": _json_body("TicketCreate"),
                    "responses": {"201": {"description": "Ticket created"}},
                },
            },
            "/service-tickets/{ticket_id}/edit": {
                "put": {
                    "tags": ["Service Tickets"],
                    "summary": "Add or remove mechanics from a ticket",
                    "security": [{"BearerAuth": []}],
                    "parameters": [
                        {"name": "ticket_id", "in": "path", "required": True, "type": "integer"},
                        *_json_body("TicketMechanicEdit"),
                    ],
                    "responses": {"200": {"description": "Mechanics updated"}},
                }
            },
            "/service-tickets/{ticket_id}/add-part/{part_id}": {
                "put": {
                    "tags": ["Service Tickets"],
                    "summary": "Attach an inventory part to a service ticket",
                    "security": [{"BearerAuth": []}],
                    "parameters": [
                        {"name": "ticket_id", "in": "path", "required": True, "type": "integer"},
                        {"name": "part_id", "in": "path", "required": True, "type": "integer"},
                    ],
                    "responses": {"200": {"description": "Part attached"}},
                }
            },
            "/inventory/": {
                "get": {
                    "tags": ["Inventory"],
                    "summary": "List inventory parts",
                    "responses": {"200": {"description": "Inventory list"}},
                },
                "post": {
                    "tags": ["Inventory"],
                    "summary": "Create an inventory part as a mechanic",
                    "security": [{"BearerAuth": []}],
                    "parameters": _json_body("InventoryCreate"),
                    "responses": {"201": {"description": "Part created"}},
                },
            },
        },
    }


def init_swagger(app: Flask) -> Swagger:
    """Attach Swagger JSON and Swagger UI routes to the Flask application."""
    return Swagger(app, config=SWAGGER_CONFIG, template=build_template(app))
