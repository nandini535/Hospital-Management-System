"""Hospital Management System - backend (Flask + MySQL)
Roles: Admin (reception/staff), Doctor, Patient. All data endpoints need  Authorization: Bearer <token>."""
from datetime import date, time, timedelta, datetime
from decimal import Decimal

import mysql.connector
from flask import Flask, g, jsonify, request
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

import db
import routes_auth, routes_doctor, routes_patient
import services
from auth import authenticate, require_role
from errors import ApiError
from tables import TABLES


class JSONProvider(DefaultJSONProvider):
    def default(self, o):
        if isinstance(o, timedelta):
            s = int(o.total_seconds())
            return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"
        if isinstance(o, Decimal):
            return float(o)
        if isinstance(o, (date, time, datetime)):
            return o.isoformat()
        return super().default(o)


app = Flask(__name__)
app.json = JSONProvider(app)
CORS(app)
app.register_blueprint(routes_auth.bp)
app.register_blueprint(routes_patient.bp)
app.register_blueprint(routes_doctor.bp)


# ---------- errors ----------
@app.errorhandler(ApiError)
def api_error(e):
    return jsonify(error=e.message), e.code


@app.errorhandler(mysql.connector.IntegrityError)
def integrity_error(e):
    return jsonify(error="Constraint violation", detail=e.msg), 409


@app.errorhandler(mysql.connector.Error)
def db_error(e):
    return jsonify(error="Database error", detail=e.msg), 400


@app.errorhandler(HTTPException)
def http_error(e):
    return jsonify(error=e.description or e.name), e.code


@app.errorhandler(Exception)
def unexpected_error(e):
    app.logger.exception(e)
    return jsonify(error="Internal server error"), 500


@app.get("/api/health")
def health():
    return jsonify(status="ok")


# ---------- shared (any logged-in user) ----------
@app.get("/api/doctors")
def list_doctors():
    """Public doctor directory for booking. ?DeptID=  ?q=name or specialization. Admins also get phone/email."""
    user = authenticate()
    cols = "d.DoctorID, d.Name, d.Specialization, d.ConsultationFee, d.DeptID, dep.DeptName"
    if user["Role"] == "Admin":
        cols += ", d.Phone, d.Email"
    where, params = [], []
    if request.args.get("DeptID"):
        where.append("d.DeptID=%s"); params.append(request.args["DeptID"])
    if request.args.get("q"):
        where.append("(d.Name LIKE %s OR d.Specialization LIKE %s)")
        params += [f"%{request.args['q']}%"] * 2
    sql = f"SELECT {cols} FROM Doctor d JOIN Department dep ON dep.DeptID=d.DeptID"
    if where:
        sql += " WHERE " + " AND ".join(where)
    # doctors whose account is still pending approval are hidden from patients
    sql += (" AND" if where else " WHERE") + " NOT EXISTS (SELECT 1 FROM UserAccount u WHERE u.DoctorID=d.DoctorID AND u.Status='Pending')"
    return jsonify(db.query(sql + " ORDER BY d.Name", params))


@app.get("/api/doctors/<int:did>/slots")
@require_role()
def doctor_slots(did):
    """?date=YYYY-MM-DD -> [{time, available}]"""
    if not request.args.get("date"):
        raise ApiError("date is required")
    return jsonify(services.get_slots(did, request.args["date"]))


# ---------- admin: user management ----------
@app.get("/api/admin/pending-doctors")
@require_role("Admin")
def pending_doctors():
    return jsonify(db.query(
        """SELECT u.UserID, u.Username, d.DoctorID, d.Name, d.Specialization, d.Email, d.Phone, dep.DeptName
           FROM UserAccount u JOIN Doctor d ON d.DoctorID=u.DoctorID JOIN Department dep ON dep.DeptID=d.DeptID
           WHERE u.Status='Pending' ORDER BY u.UserID"""))


@app.post("/api/admin/users/<int:uid>/approve")
@require_role("Admin")
def approve_user(uid):
    _, n = db.execute("UPDATE UserAccount SET Status='Active' WHERE UserID=%s AND Status='Pending'", (uid,))
    if not n:
        raise ApiError("No pending account with that id", 404)
    return jsonify(message="Account approved")


@app.post("/api/admin/users/<int:uid>/reject")
@require_role("Admin")
def reject_user(uid):
    with db.transaction() as cur:
        cur.execute("SELECT DoctorID FROM UserAccount WHERE UserID=%s AND Status='Pending' AND Role='Doctor'", (uid,))
        row = cur.fetchone()
        if not row:
            raise ApiError("No pending doctor account with that id", 404)
        cur.execute("DELETE FROM UserAccount WHERE UserID=%s", (uid,))
        cur.execute("DELETE FROM Doctor WHERE DoctorID=%s", (row["DoctorID"],))
    return jsonify(message="Registration rejected and removed")


@app.get("/api/admin/users")
@require_role("Admin")
def list_users():
    return jsonify(db.query("SELECT UserID, Username, Role, Status, DoctorID, PatientID FROM UserAccount ORDER BY UserID"))


@app.post("/api/admin/users/<int:uid>/<action>")
@require_role("Admin")
def set_user_status(uid, action):
    if action not in ("disable", "enable"):
        raise ApiError("Unknown action", 404)
    if uid == g.user["UserID"]:
        raise ApiError("You cannot change your own account status")
    status = "Disabled" if action == "disable" else "Active"
    _, n = db.execute("UPDATE UserAccount SET Status=%s WHERE UserID=%s AND Status<>'Pending'", (status, uid))
    if not n:
        raise ApiError("User not found (or still pending approval)", 404)
    return jsonify(message=f"Account {action}d")


# ---------- admin: hospital operations ----------
@app.get("/api/appointments-detail")
@require_role("Admin")
def appointments_detail():
    day = request.args.get("date")
    return jsonify(db.query(
        """SELECT a.AppointmentID, a.`Date`, a.`Time`, a.Status, a.Reason,
                  p.PatientID, p.Name AS PatientName, d.DoctorID, d.Name AS DoctorName, d.Specialization, dep.DeptName
           FROM Appointment a JOIN Patient p ON p.PatientID=a.PatientID
           JOIN Doctor d ON d.DoctorID=a.DoctorID JOIN Department dep ON dep.DeptID=d.DeptID
           WHERE (%s IS NULL OR a.`Date`=%s) ORDER BY a.`Date`, a.`Time`""", (day, day)))


@app.post("/api/admin/appointments")
@require_role("Admin")
def admin_book():
    """Reception books on behalf of a patient. Body: {PatientID, DoctorID, Date, Time, Reason?}"""
    d = request.get_json(silent=True) or {}
    if not d.get("PatientID") or not d.get("DoctorID") or not d.get("Date"):
        raise ApiError("PatientID, DoctorID, Date and Time are required")
    return jsonify(AppointmentID=services.book_appointment(
        d["PatientID"], d["DoctorID"], d["Date"], d.get("Time"), d.get("Reason"))), 201


@app.get("/api/patients/search")
@require_role("Admin")
def search_patients():
    term = request.args.get("q", "")
    return jsonify(db.query("SELECT * FROM Patient WHERE Name LIKE %s OR Phone LIKE %s ORDER BY Name LIMIT 50",
                            (f"%{term}%", f"%{term}%")))


@app.get("/api/patients/<int:pid>/history")
@require_role("Admin")
def patient_history(pid):
    return jsonify(services.patient_history(pid))


@app.post("/api/admit")
@require_role("Admin")
def admit_patient():
    return jsonify(AdmissionID=services.admit_patient(request.get_json(silent=True) or {})), 201


@app.post("/api/admissions/<int:aid>/discharge")
@require_role("Admin")
def discharge(aid):
    services.discharge_patient(aid)
    return jsonify(message="Discharged", AdmissionID=aid)


@app.post("/api/prescriptions/full")
@require_role("Admin")
def create_full_prescription():
    return jsonify(PrescriptionID=services.create_prescription(request.get_json(silent=True) or {})), 201


@app.post("/api/admissions/<int:aid>/generate-bill")
@require_role("Admin")
def generate_bill(aid):
    mode = (request.get_json(silent=True) or {}).get("PaymentMode", "Cash")
    return jsonify(services.generate_admission_bill(aid, mode)), 201


@app.post("/api/appointments/<int:aid>/generate-bill")
@require_role("Admin")
def appointment_bill(aid):
    mode = (request.get_json(silent=True) or {}).get("PaymentMode", "Cash")
    return jsonify(services.generate_appointment_bill(aid, mode)), 201


@app.post("/api/bills/<int:bid>/pay")
@require_role("Admin")
def pay_bill(bid):
    _, n = db.execute("UPDATE Bill SET Status='Paid' WHERE BillID=%s AND Status='Pending'", (bid,))
    if not n:
        raise ApiError("Bill not found or already paid", 404)
    return jsonify(message="Marked as paid")


@app.get("/api/rooms/available")
@require_role("Admin")
def available_rooms():
    return jsonify(db.query("""SELECT r.*, w.WardName FROM Room r JOIN Ward w ON w.WardID=r.WardID
                               WHERE r.Status='Available' ORDER BY w.WardName, r.RoomID"""))


@app.get("/api/medicines/low-stock")
@require_role("Admin")
def low_stock():
    return jsonify(db.query("SELECT * FROM Medicine WHERE Stock <= %s ORDER BY Stock",
                            (int(request.args.get("threshold", 20)),)))


@app.get("/api/stats")
@require_role("Admin")
def stats():
    return jsonify(db.query(
        """SELECT (SELECT COUNT(*) FROM Patient) AS patients,
                  (SELECT COUNT(*) FROM Doctor) AS doctors,
                  (SELECT COUNT(*) FROM Appointment WHERE `Date`=CURDATE() AND Status<>'Cancelled') AS appointments_today,
                  (SELECT COUNT(*) FROM Admission WHERE DischargeDate IS NULL) AS currently_admitted,
                  (SELECT COUNT(*) FROM Room WHERE Status='Available') AS rooms_available,
                  (SELECT COUNT(*) FROM UserAccount WHERE Status='Pending') AS pending_doctor_approvals,
                  (SELECT COALESCE(SUM(Amount),0) FROM Bill WHERE Status='Paid') AS revenue_collected,
                  (SELECT COALESCE(SUM(Amount),0) FROM Bill WHERE Status='Pending') AS revenue_pending""", one=True))


# ---------- generic CRUD (admin; a few read-only lists open to others) ----------
PUBLIC_READ = {"departments"}        # needed by the registration form
AUTH_READ = {"medicines"}            # doctors need it for prescriptions


def guard(slug):
    if request.method == "GET" and slug in PUBLIC_READ:
        return
    user = authenticate()
    if request.method == "GET" and slug in AUTH_READ:
        return
    if user["Role"] != "Admin":
        raise ApiError("Admin access required", 403)


def write_cols(meta, data):
    return {k: data[k] for k in meta["cols"] if k in data}


def q(col):
    return f"`{col}`"


@app.get("/api/<slug>")
def list_rows(slug):
    meta = TABLES.get(slug)
    if not meta:
        raise ApiError("Unknown resource", 404)
    guard(slug)
    allowed = [meta["pk"]] + meta["cols"]
    where, params = [], []
    for k, v in request.args.items():
        if k in allowed:
            where.append(f"{q(k)}=%s"); params.append(v)
    sql = f"SELECT * FROM {meta['name']}" + (" WHERE " + " AND ".join(where) if where else "") + f" ORDER BY {q(meta['pk'])}"
    return jsonify(db.query(sql, params))


@app.get("/api/<slug>/<int:rid>")
def get_row(slug, rid):
    meta = TABLES.get(slug)
    if not meta:
        raise ApiError("Unknown resource", 404)
    guard(slug)
    row = db.query(f"SELECT * FROM {meta['name']} WHERE {q(meta['pk'])}=%s", (rid,), one=True)
    if not row:
        raise ApiError("Not found", 404)
    return jsonify(row)


@app.post("/api/<slug>")
def create_row(slug):
    meta = TABLES.get(slug)
    if not meta:
        raise ApiError("Unknown resource", 404)
    guard(slug)
    data = write_cols(meta, request.get_json(silent=True) or {})
    if not data:
        raise ApiError("No valid fields supplied")
    new_id, _ = db.execute(
        f"INSERT INTO {meta['name']} ({', '.join(q(c) for c in data)}) VALUES ({', '.join(['%s'] * len(data))})",
        list(data.values()))
    return jsonify({meta["pk"]: new_id}), 201


@app.put("/api/<slug>/<int:rid>")
def update_row(slug, rid):
    meta = TABLES.get(slug)
    if not meta:
        raise ApiError("Unknown resource", 404)
    guard(slug)
    data = write_cols(meta, request.get_json(silent=True) or {})
    if not data:
        raise ApiError("No valid fields supplied")
    sets = ", ".join(f"{q(c)}=%s" for c in data)
    _, n = db.execute(f"UPDATE {meta['name']} SET {sets} WHERE {q(meta['pk'])}=%s", list(data.values()) + [rid])
    return jsonify(updated=n)


@app.delete("/api/<slug>/<int:rid>")
def delete_row(slug, rid):
    meta = TABLES.get(slug)
    if not meta:
        raise ApiError("Unknown resource", 404)
    guard(slug)
    _, n = db.execute(f"DELETE FROM {meta['name']} WHERE {q(meta['pk'])}=%s", (rid,))
    if not n:
        raise ApiError("Not found", 404)
    return jsonify(deleted=n)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
