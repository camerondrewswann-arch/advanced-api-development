from flask import Blueprint

mechanic_bp = Blueprint("mechanics", __name__)

from . import routes  # noqa: E402, F401
