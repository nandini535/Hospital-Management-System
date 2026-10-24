"""Login + self-registration for patients and doctors."""
import time

import mysql.connector
from flask import Blueprint, g, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

import db
from auth import authenticate, make_token, require_role
from errors import ApiError

bp = Blueprint("auth", __name__, url_prefix="/api/auth")
_FAILS = {}                      # username -> [timestamps]  (simple brute-force guard)
MAX_FAILS, WINDOW = 5, 600


def _need(data, fields):
    missing = [f for f in fields if not str(data.get(f) or "").strip()]
    if missing:
        raise ApiError("Missing required field(s): " + ", ".join(missing))


def _check_password(pw):
    if len(pw) < 8:
        raise ApiError("Password must be at least 8 characters")


def _name_of(user):
    if user["Role"] == "Doctor":
        row = db.query("SELECT Name FROM Doctor WHERE DoctorID=%s", (user["DoctorID"],), one=True)
    elif user["Role"] == "Patient":
        row = db.query("SELECT Name FROM Patient WHERE PatientID=%s", (user["PatientID"],), one=True)
    else:
        row = {"Name": "Administrator"}
    return row["Name"] if row else user["Username"]


def _session(user):
    return dict(token=make_token(user["UserID"]), role=user["Role"], username=user["Username"],
                name=_name_of(user), DoctorID=user["DoctorID"], PatientID=user["PatientID"])


@bp.post("/register/patient")
def register_patient():
    d = request.get_json(silent=True) or {}
    _need(d, ["Username", "Password", "Name", "Gender", "DOB"])
    _check_password(d["Password"])
    try:
        with db.transaction() as cur:
            cur.execute("INSERT INTO Patient (Name, Gender, DOB, Phone, Address, BloodGroup) VALUES (%s,%s,%s,%s,%s,%s)",
                        (d["Name"], d["Gender"], d["DOB"], d.get("Phone"), d.get("Address"), d.get("BloodGroup")))
            pid = cur.lastrowid
            cur.execute("INSERT INTO UserAccount (Username, PasswordHash, Role, Status, PatientID) VALUES (%s,%s,'Patient','Active',%s)",
                        (d["Username"].strip(), generate_password_hash(d["Password"]), pid))
            uid = cur.lastrowid
    except mysql.connector.IntegrityError as e:
        if "Username" in e.msg:
            raise ApiError("Username already taken", 409)
        raise
    user = db.query("SELECT * FROM UserAccount WHERE UserID=%s", (uid,), one=True)
    return jsonify(_session(user)), 201


@bp.post("/register/doctor")
def register_doctor():
    """New doctors cannot log in until an admin approves them (Status = Pending)."""
    d = request.get_json(silent=True) or {}
    _need(d, ["Username", "Password", "Name", "Specialization", "Email", "DeptID"])
    _check_password(d["Password"])
    try:
        with db.transaction() as cur:
            cur.execute("""INSERT INTO Doctor (Name, Specialization, Phone, Email, ConsultationFee, DeptID)
                           VALUES (%s,%s,%s,%s,%s,%s)""",
                        (d["Name"], d["Specialization"], d.get("Phone"), d["Email"],
                         d.get("ConsultationFee", 500), d["DeptID"]))
            did = cur.lastrowid
            cur.execute("INSERT INTO UserAccount (Username, PasswordHash, Role, Status, DoctorID) VALUES (%s,%s,'Doctor','Pending',%s)",
                        (d["Username"].strip(), generate_password_hash(d["Password"]), did))
    except mysql.connector.IntegrityError as e:
        if "Username" in e.msg:
            raise ApiError("Username already taken", 409)
        if "Email" in e.msg:
            raise ApiError("A doctor with this email already exists", 409)
        raise
    return jsonify(message="Registration submitted. You can log in once an administrator approves your account.",
                   DoctorID=did), 201


@bp.post("/login")
def login():
    d = request.get_json(silent=True) or {}
    _need(d, ["Username", "Password"])
    uname, now = d["Username"].strip(), time.time()
    recent = [t for t in _FAILS.get(uname, []) if now - t < WINDOW]
    if len(recent) >= MAX_FAILS:
        raise ApiError("Too many failed attempts. Try again in a few minutes.", 429)
    user = db.query("SELECT * FROM UserAccount WHERE Username=%s", (uname,), one=True)
    if not user or not check_password_hash(user["PasswordHash"], d["Password"]):
        _FAILS[uname] = recent + [now]
        raise ApiError("Invalid username or password", 401)
    if user["Status"] == "Pending":
        raise ApiError("Your registration is waiting for administrator approval", 403)
    if user["Status"] == "Disabled":
        raise ApiError("This account has been disabled", 403)
    _FAILS.pop(uname, None)
    return jsonify(_session(user))


@bp.get("/me")
@require_role()
def me():
    u = g.user
    return jsonify(role=u["Role"], username=u["Username"], name=_name_of(u),
                   DoctorID=u["DoctorID"], PatientID=u["PatientID"])


@bp.post("/change-password")
@require_role()
def change_password():
    d = request.get_json(silent=True) or {}
    _need(d, ["OldPassword", "NewPassword"])
    _check_password(d["NewPassword"])
    row = db.query("SELECT PasswordHash FROM UserAccount WHERE UserID=%s", (g.user["UserID"],), one=True)
    if not check_password_hash(row["PasswordHash"], d["OldPassword"]):
        raise ApiError("Old password is incorrect", 401)
    db.execute("UPDATE UserAccount SET PasswordHash=%s WHERE UserID=%s",
               (generate_password_hash(d["NewPassword"]), g.user["UserID"]))
    return jsonify(message="Password changed")
