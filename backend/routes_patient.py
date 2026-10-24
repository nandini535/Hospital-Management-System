"""Everything a logged-in PATIENT can do. A patient only ever sees their own records:
the PatientID always comes from the login token, never from the request."""
from datetime import date

from flask import Blueprint, g, jsonify, request

import db
import services
from auth import require_role
from errors import ApiError

bp = Blueprint("patient", __name__, url_prefix="/api/patient")
PAY_MODES = ("Cash", "Card", "UPI", "Insurance")


def me():
    return g.user["PatientID"]


@bp.get("/profile")
@require_role("Patient")
def profile():
    return jsonify(db.query("SELECT * FROM Patient WHERE PatientID=%s", (me(),), one=True))


@bp.put("/profile")
@require_role("Patient")
def update_profile():
    d = request.get_json(silent=True) or {}
    data = {k: d[k] for k in ("Name", "Phone", "Address", "BloodGroup") if k in d}
    if not data:
        raise ApiError("Nothing to update")
    sets = ", ".join(f"{k}=%s" for k in data)
    db.execute(f"UPDATE Patient SET {sets} WHERE PatientID=%s", list(data.values()) + [me()])
    return jsonify(message="Profile updated")


@bp.get("/history")
@require_role("Patient")
def history():
    return jsonify(services.patient_history(me()))


@bp.get("/appointments")
@require_role("Patient")
def appointments():
    return jsonify(db.query(
        """SELECT a.AppointmentID, a.`Date`, a.`Time`, a.Status, a.Reason,
                  d.DoctorID, d.Name AS Doctor, d.Specialization, dep.DeptName, dep.Location
           FROM Appointment a JOIN Doctor d ON d.DoctorID=a.DoctorID
           JOIN Department dep ON dep.DeptID=d.DeptID
           WHERE a.PatientID=%s ORDER BY a.`Date` DESC, a.`Time` DESC""", (me(),)))


@bp.post("/appointments")
@require_role("Patient")
def book():
    d = request.get_json(silent=True) or {}
    if not d.get("DoctorID") or not d.get("Date"):
        raise ApiError("DoctorID, Date and Time are required")
    new_id = services.book_appointment(me(), d["DoctorID"], d["Date"], d.get("Time"), d.get("Reason"))
    return jsonify(AppointmentID=new_id), 201


@bp.post("/appointments/<int:aid>/cancel")
@require_role("Patient")
def cancel(aid):
    _, n = db.execute(
        "UPDATE Appointment SET Status='Cancelled' WHERE AppointmentID=%s AND PatientID=%s AND Status='Scheduled'",
        (aid, me()))
    if not n:
        raise ApiError("Appointment not found or cannot be cancelled", 404)
    return jsonify(message="Appointment cancelled")


@bp.get("/prescriptions")
@require_role("Patient")
def prescriptions():
    return jsonify(services.prescriptions_for(pid=me()))


@bp.get("/lab-tests")
@require_role("Patient")
def lab_tests():
    return jsonify(db.query("SELECT * FROM LabTest WHERE PatientID=%s ORDER BY TestDate DESC", (me(),)))


@bp.get("/admissions")
@require_role("Patient")
def admissions():
    return jsonify(db.query(
        """SELECT ad.*, r.Type AS RoomType, r.Charge AS RoomCharge, w.WardName
           FROM Admission ad JOIN Room r ON r.RoomID=ad.RoomID JOIN Ward w ON w.WardID=r.WardID
           WHERE ad.PatientID=%s ORDER BY ad.AdmitDate DESC""", (me(),)))


@bp.get("/bills")
@require_role("Patient")
def bills():
    return jsonify(db.query(
        """SELECT b.*, CASE WHEN b.AdmissionID IS NOT NULL THEN 'Hospital stay'
                            WHEN b.AppointmentID IS NOT NULL THEN 'Consultation' ELSE 'Other' END AS BillType
           FROM Bill b WHERE b.PatientID=%s ORDER BY b.`Date` DESC, b.BillID DESC""", (me(),)))


@bp.post("/bills/<int:bid>/pay")
@require_role("Patient")
def pay(bid):
    """Simulated payment (no real payment gateway)."""
    mode = (request.get_json(silent=True) or {}).get("PaymentMode", "UPI")
    if mode not in PAY_MODES:
        raise ApiError("PaymentMode must be one of: " + ", ".join(PAY_MODES))
    _, n = db.execute("UPDATE Bill SET Status='Paid', PaymentMode=%s, `Date`=%s WHERE BillID=%s AND PatientID=%s AND Status='Pending'",
                      (mode, date.today(), bid, me()))
    if not n:
        raise ApiError("Bill not found or already paid", 404)
    return jsonify(message="Payment successful")
