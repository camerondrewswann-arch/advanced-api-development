from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import current_app, jsonify, request
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError


def _encode_token(identity, role):
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=current_app.config["JWT_EXPIRES_HOURS"])
    payload = {
        "sub": str(identity),
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
    }
    return jwt.encode(
        payload,
        current_app.config["JWT_SECRET_KEY"],
        algorithm=current_app.config["JWT_ALGORITHM"],
    )


def encode_token(customer_id):
    return _encode_token(customer_id, "customer")


def encode_mechanic_token(mechanic_id):
    return _encode_token(mechanic_id, "mechanic")


def _extract_identity(required_role):
    authorization = request.headers.get("Authorization", "")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None, (jsonify({"message": "Bearer token required"}), 401)

    try:
        payload = jwt.decode(
            parts[1],
            current_app.config["JWT_SECRET_KEY"],
            algorithms=[current_app.config["JWT_ALGORITHM"]],
        )
        if payload.get("role") != required_role:
            return None, (jsonify({"message": f"{required_role.title()} token required"}), 403)
        return int(payload["sub"]), None
    except ExpiredSignatureError:
        return None, (jsonify({"message": "Token has expired"}), 401)
    except (JWTError, KeyError, TypeError, ValueError):
        return None, (jsonify({"message": "Invalid token"}), 401)


def token_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        customer_id, error = _extract_identity("customer")
        if error:
            return error
        return view(customer_id, *args, **kwargs)

    return wrapped


def mechanic_token_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        mechanic_id, error = _extract_identity("mechanic")
        if error:
            return error
        return view(mechanic_id, *args, **kwargs)

    return wrapped
