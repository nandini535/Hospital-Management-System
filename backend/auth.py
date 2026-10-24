from functools import wraps

from flask import g, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

import db
from config import SECRET_KEY, TOKEN_MAX_AGE
from errors import ApiError

_ser = URLSafeTimedSerializer(SECRET_KEY, salt="hms-auth")


def make_token(user_id):
    return _ser.dumps({"uid": user_id})


def authenticate():
    """Read 'Authorization: Bearer <token>', load the user from the DB, store in g.user."""
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise ApiError("Login required", 401)
    try:
        data = _ser.loads(header[7:], max_age=TOKEN_MAX_AGE)
    except SignatureExpired:
        raise ApiError("Session expired, please log in again", 401)
    except BadSignature:
        raise ApiError("Invalid token", 401)
    user = db.query(
        "SELECT UserID, Username, Role, Status, DoctorID, PatientID FROM UserAccount WHERE UserID=%s",
        (data["uid"],), one=True)
    if not user or user["Status"] != "Active":
        raise ApiError("Account is not active", 401)
    g.user = user
    return user


def require_role(*roles):
    """@require_role('Admin') or @require_role() for any logged-in user."""
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = authenticate()
            if roles and user["Role"] not in roles:
                raise ApiError("You do not have permission for this action", 403)
            return fn(*args, **kwargs)
        return wrapper
    return deco
