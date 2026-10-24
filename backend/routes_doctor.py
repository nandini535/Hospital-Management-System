"""Everything a logged-in DOCTOR can do. DoctorID always comes from the login token."""
from datetime import date

from flask import Blueprint, g, jsonify, request

import db
import services
from auth import require_role
from errors import ApiError

bp = Blueprint("doctor", __name__, url_prefix="/api/doctor")


def me():
    return g.user["DoctorID"]


def _must_treat(patient_id):
    if not patient_id or not services.doctor_treats(me(), patient_id):
        raise ApiError("This patient has no appointment or prescription with you", 403)


@bp.get("/profile")
@require_role("Doctor")
def profile():
    return jsonify(db.query(
        """SELECT d.*, dep.DeptName FROM Doctor d JOIN Department dep ON dep.DeptID=d.DeptID
           WHERE d.DoctorID=%s""", (me(),), one=True))


@bp.get("/schedule")
@require_role("Doctor")
def get_schedule():
    return jsonify(db.query("SELECT DayOfWeek, StartTime, EndTime, SlotMinutes FROM DoctorSchedule WHERE DoctorID=%s ORDER BY DayOfWeek, StartTime", (me(),)))


@bp.put("/schedule")
@require_role("Doctor")
def set_schedule():
    """Body: [{DayOfWeek:0-6 (0=Mon), StartTime:'09:00', EndTime:'13:00', SlotMinutes:30}, ...]  (replaces the old timetable)"""
    rows = request.get_json(silent=True)
    if not isinstance(rows, list):
        raise ApiError("Send a list of schedule rows")
    clean = []
    for r in rows:
        try:
            dow, slot = int(r["DayOfWeek"]), int(r.get("SlotMinutes", 30))
            start, end = services.to_seconds(r["StartTime"]), services.to_seconds(r["EndTime"])
        except (KeyError, ValueError, TypeError):
            raise ApiError("Each row needs DayOfWeek, StartTime, EndTime")
        if not 0 <= dow <= 6 or not 5 <= slot <= 120 or end <= start:
            raise ApiError("Invalid day, slot length or time range")
        clean.append((me(), dow, services.fmt(start), services.fmt(end), slot))
    with db.transaction() as cur:
        cur.execute("DELETE FROM DoctorSchedule WHERE DoctorID=%s", (me(),))
        for c in clean:
            cur.execute("INSERT INTO DoctorSchedule (DoctorID, DayOfWeek, StartTime, EndTime, SlotMinutes) VALUES (%s,%s,%s,%s,%s)", c)
    return jsonify(message="Schedule saved", rows=len(clean))


@bp.get("/appointments")
@require_role("Doctor")
def appointments():
    """?date=YYYY-MM-DD  ?status=Scheduled|Completed|Cancelled  ?upcoming=1"""
    where, params = ["a.DoctorID=%s"], [me()]
    if request.args.get("date"):
        where.append("a.`Date`=%s"); params.append(request.args["date"])
    if request.args.get("status"):
        where.append("a.Status=%s"); params.append(request.args["status"])
    if request.args.get("upcoming"):
        where.append("a.`Date`>=%s"); params.append(date.today())
    return jsonify(db.query(
        f"""SELECT a.AppointmentID, a.`Date`, a.`Time`, a.Status, a.Reason,
                   p.PatientID, p.Name AS PatientName, p.Gender, p.DOB, p.BloodGroup, p.Phone
            FROM Appointment a JOIN Patient p ON p.PatientID=a.PatientID
            WHERE {' AND '.join(where)} ORDER BY a.`Date`, a.`Time`""", params))


def _set_status(aid, status):
    _, n = db.execute("UPDATE Appointment SET Status=%s WHERE AppointmentID=%s AND DoctorID=%s AND Status='Scheduled'",
                      (status, aid, me()))
    if not n:
        raise ApiError("Appointment not found or already closed", 404)
    return jsonify(message=f"Appointment marked {status}")


@bp.post("/appointments/<int:aid>/complete")
@require_role("Doctor")
def complete(aid):
    return _set_status(aid, "Completed")


@bp.post("/appointments/<int:aid>/cancel")
@require_role("Doctor")
def cancel(aid):
    return _set_status(aid, "Cancelled")


@bp.get("/patients")
@require_role("Doctor")
def my_patients():
    return jsonify(db.query(
        """SELECT p.PatientID, p.Name, p.Gender, p.DOB, p.BloodGroup, p.Phone,
                  COUNT(a.AppointmentID) AS visits, MAX(a.`Date`) AS last_visit
           FROM Patient p JOIN Appointment a ON a.PatientID=p.PatientID
           WHERE a.DoctorID=%s AND a.Status<>'Cancelled'
           GROUP BY p.PatientID, p.Name, p.Gender, p.DOB, p.BloodGroup, p.Phone
           ORDER BY last_visit DESC""", (me(),)))


@bp.get("/patients/<int:pid>/history")
@require_role("Doctor")
def patient_history(pid):
    _must_treat(pid)
    return jsonify(services.patient_history(pid))


@bp.get("/prescriptions")
@require_role("Doctor")
def my_prescriptions():
    return jsonify(services.prescriptions_for(doctor_id=me()))


@bp.post("/prescriptions")
@require_role("Doctor")
def write_prescription():
    """Body: {PatientID, Notes?, items:[{MedicineID, Dosage, Quantity}]}"""
    d = request.get_json(silent=True) or {}
    _must_treat(d.get("PatientID"))
    pid = services.create_prescription(d, doctor_id=me())
    return jsonify(PrescriptionID=pid), 201


@bp.post("/lab-tests")
@require_role("Doctor")
def order_lab_test():
    d = request.get_json(silent=True) or {}
    _must_treat(d.get("PatientID"))
    if not d.get("TestName"):
        raise ApiError("TestName is required")
    new_id, _ = db.execute("INSERT INTO LabTest (PatientID, TestName, Result, TestDate) VALUES (%s,%s,%s,%s)",
                           (d["PatientID"], d["TestName"], d.get("Result"), d.get("TestDate") or date.today()))
    return jsonify(TestID=new_id), 201


@bp.put("/lab-tests/<int:tid>")
@require_role("Doctor")
def enter_result(tid):
    d = request.get_json(silent=True) or {}
    test = db.query("SELECT PatientID FROM LabTest WHERE TestID=%s", (tid,), one=True)
    if not test:
        raise ApiError("Test not found", 404)
    _must_treat(test["PatientID"])
    db.execute("UPDATE LabTest SET Result=%s WHERE TestID=%s", (d.get("Result"), tid))
    return jsonify(message="Result saved")
