"""Flask application factory for the Mechanic Shop API."""

from pathlib import Path

from flask import Flask, jsonify
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from config import DevelopmentConfig

from .extensions import cache, db, limiter, ma


def create_app(config_object=DevelopmentConfig) -> Flask:
    """Create and configure a Flask application instance."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)
    validate_configuration(app)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    ma.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)

    from .swagger import init_swagger

    init_swagger(app)
    register_blueprints(app)
    register_routes(app)
    register_error_handlers(app)
    register_commands(app)

    if app.config.get("AUTO_CREATE_DB", False):
        with app.app_context():
            db.create_all()

    return app


def validate_configuration(app: Flask) -> None:
    """Fail fast when required production environment variables are missing."""
    if app.config.get("ENVIRONMENT_NAME") != "production":
        return

    required = {
        "DATABASE_URL": app.config.get("DATABASE_URL"),
        "SECRET_KEY": app.config.get("SECRET_KEY"),
        "JWT_SECRET_KEY": app.config.get("JWT_SECRET_KEY"),
        "SWAGGER_HOST": app.config.get("SWAGGER_HOST"),
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        names = ", ".join(missing)
        raise RuntimeError(f"Missing required production environment variables: {names}")


def register_blueprints(app: Flask) -> None:
    """Register all API blueprints and URL prefixes."""
    from .blueprints.customers import customer_bp
    from .blueprints.inventory import inventory_bp
    from .blueprints.mechanics import mechanic_bp
    from .blueprints.service_tickets import service_ticket_bp

    app.register_blueprint(customer_bp, url_prefix="/customers")
    app.register_blueprint(mechanic_bp, url_prefix="/mechanics")
    app.register_blueprint(service_ticket_bp, url_prefix="/service-tickets")
    app.register_blueprint(inventory_bp, url_prefix="/inventory")


def register_routes(app: Flask) -> None:
    """Register project-level health and index routes."""

    @app.get("/")
    @limiter.exempt
    def index():
        return jsonify(
            {
                "name": "Mechanic Shop Advanced API",
                "status": "running",
                "documentation": "/apidocs/",
            }
        )

    @app.get("/health")
    @limiter.exempt
    def health():
        return jsonify({"status": "healthy"})


def register_error_handlers(app: Flask) -> None:
    """Return consistent JSON responses for common API errors."""

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        return jsonify(
            {"message": "Validation failed", "errors": error.messages}
        ), 400

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(error):
        db.session.rollback()
        return jsonify({"message": "Database integrity error"}), 409

    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify({"message": "Route not found"}), 404

    @app.errorhandler(429)
    def handle_rate_limit(error):
        return jsonify(
            {
                "message": "Rate limit exceeded",
                "detail": str(error.description),
            }
        ), 429


def register_commands(app: Flask) -> None:
    """Register database commands for use with the Flask CLI."""

    @app.cli.command("init-db")
    def init_db():
        """Create all database tables."""
        db.create_all()
        print("Database tables created.")

    @app.cli.command("reset-db")
    def reset_db():
        """Delete and recreate all database tables."""
        db.drop_all()
        db.create_all()
        cache.clear()
        print("Database reset complete.")

    @app.cli.command("seed-db")
    def seed_db():
        """Insert demonstration records."""
        from .seed import seed_database

        results = seed_database()
        created_count = sum(results.values())
        print(f"Seed complete. Created {created_count} new record(s).")
        print("Customer: customer@example.com / password123")
        print("Mechanic: mechanic@example.com / wrench123")
