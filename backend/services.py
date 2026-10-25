"""Business logic shared by admin / doctor / patient routes."""
from datetime import date, datetime, timedelta

import mysql.connector

import db
from errors import ApiError


# ---------- small helpers ----------
def to_seconds(t):
    if isinstance(t, timedelta):
        return int(t.total_seconds())
    if isinstance(t, str):
        parts = [int(x) for x in t.split(":")]
        while len(parts) < 3:
            parts.append(0)
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return t.hour * 3600 + t.minute * 60 + t.second       # datetime.time


def fmt(sec):
    return f"{sec // 3600:02d}:{sec % 3600 // 60:02d}:{sec % 60:02d}"


def parse_date(s):
    try:
        return date.fromisoformat(str(s))
    except ValueError:
        raise ApiError("Date must be in YYYY-MM-DD format")


# ---------- appointment slots ----------
def get_slots(doctor_id, day):
    d = parse_date(day)
    if not db.query("SELECT 1 FROM Doctor WHERE DoctorID=%s", (doctor_id,), one=True):
        raise ApiError("Doctor not found", 404)
    sched = db.query(
        "SELECT StartTime, EndTime, SlotMinutes FROM DoctorSchedule WHERE DoctorID=%s AND DayOfWeek=%s ORDER BY StartTime",
        (doctor_id, d.weekday()))
    booked = {to_seconds(r["Time"]) for r in db.query(
        "SELECT `Time` FROM Appointment WHERE DoctorID=%s AND `Date`=%s AND Status<>'Cancelled'", (doctor_id, d))}
    now = datetime.now()
    now_sec = now.hour * 3600 + now.minute * 60
    slots = []
    for s in sched:
        t, end, step = to_seconds(s["StartTime"]), to_seconds(s["EndTime"]), s["SlotMinutes"] * 60
        while t + step <= end:
            free = t not in booked and not (d == now.date() and t <= now_sec)
            slots.append({"time": fmt(t), "available": free})
            t += step
    return slots


def book_appointment(patient_id, doctor_id, day, time_str, reason=None):
    d = parse_date(day)
    if d < date.today():
        raise ApiError("Cannot book an appointment in the past")
    if time_str is None:
        raise ApiError("Time is required")
    t = to_seconds(time_str)
    slot = next((s for s in get_slots(doctor_id, day) if to_seconds(s["time"]) == t), None)
    if slot is None:
        raise ApiError("The doctor has no slot at that time. Check the available slots first.")
    if not slot["available"]:
        raise ApiError("That slot is already taken", 409)
    clash = db.query(
        "SELECT 1 FROM Appointment WHERE PatientID=%s AND `Date`=%s AND `Time`=%s AND Status<>'Cancelled'",
        (patient_id, d, fmt(t)), one=True)
    if clash:
        raise ApiError("You already have an appointment at that time", 409)
    try:
        new_id, _ = db.execute(
            "INSERT INTO Appointment (`Date`, `Time`, Status, Reason, PatientID, DoctorID) VALUES (%s,%s,'Scheduled',%s,%s,%s)",
            (d, fmt(t), reason, patient_id, doctor_id))
    except mysql.connector.IntegrityError:
        raise ApiError("That slot was just booked by someone else", 409)
    return new_id


# ---------- records ----------
def patient_history(pid):
    patient = db.query("SELECT * FROM Patient WHERE PatientID=%s", (pid,), one=True)
    if not patient:
        raise ApiError("Patient not found", 404)
    return dict(
        patient=patient,
        appointments=db.query(
            """SELECT a.AppointmentID, a.`Date`, a.`Time`, a.Status, a.Reason, d.Name AS Doctor, d.Specialization
               FROM Appointment a JOIN Doctor d ON d.DoctorID=a.DoctorID
               WHERE a.PatientID=%s ORDER BY a.`Date` DESC, a.`Time` DESC""", (pid,)),
        prescriptions=prescriptions_for(pid),
        lab_tests=db.query("SELECT * FROM LabTest WHERE PatientID=%s ORDER BY TestDate DESC", (pid,)),
        admissions=db.query(
            """SELECT ad.*, r.Type AS RoomType, w.WardName
               FROM Admission ad JOIN Room r ON r.RoomID=ad.RoomID JOIN Ward w ON w.WardID=r.WardID
               WHERE ad.PatientID=%s ORDER BY ad.AdmitDate DESC""", (pid,)),
        bills=db.query("SELECT * FROM Bill WHERE PatientID=%s ORDER BY `Date` DESC, BillID DESC", (pid,)),
    )


def prescriptions_for(pid=None, doctor_id=None):
    """Prescriptions grouped with their medicine items."""
    where, params = [], []
    if pid is not None:
        where.append("pr.PatientID=%s"); params.append(pid)
    if doctor_id is not None:
        where.append("pr.DoctorID=%s"); params.append(doctor_id)
    rows = db.query(
        f"""SELECT pr.PrescriptionID, pr.`Date`, pr.Notes, pr.PatientID, p.Name AS PatientName,
                   d.Name AS Doctor, m.Name AS Medicine, pi.Dosage, pi.Quantity
            FROM Prescription pr
            JOIN Doctor d ON d.DoctorID = pr.DoctorID
            JOIN Patient p ON p.PatientID = pr.PatientID
            LEFT JOIN PrescriptionItem pi ON pi.PrescriptionID = pr.PrescriptionID
            LEFT JOIN Medicine m ON m.MedicineID = pi.MedicineID
            WHERE {' AND '.join(where) or '1=1'}
            ORDER BY pr.`Date` DESC, pr.PrescriptionID DESC""", params)
    grouped = {}
    for r in rows:
        g = grouped.setdefault(r["PrescriptionID"], {
            "PrescriptionID": r["PrescriptionID"], "Date": r["Date"], "Notes": r["Notes"],
            "PatientID": r["PatientID"], "PatientName": r["PatientName"], "Doctor": r["Doctor"], "items": []})
        if r["Medicine"]:
            g["items"].append({"Medicine": r["Medicine"], "Dosage": r["Dosage"], "Quantity": r["Quantity"]})
    return list(grouped.values())


def doctor_treats(doctor_id, patient_id):
    return db.query(
        """SELECT 1 FROM Appointment WHERE DoctorID=%s AND PatientID=%s AND Status<>'Cancelled'
           UNION SELECT 1 FROM Prescription WHERE DoctorID=%s AND PatientID=%s LIMIT 1""",
        (doctor_id, patient_id, doctor_id, patient_id), one=True) is not None


# ---------- transactions ----------
def create_prescription(data, doctor_id=None):
    doctor_id = doctor_id or data.get("DoctorID")
    items = data.get("items") or []
    if not data.get("PatientID") or not doctor_id or not items:
        raise ApiError("PatientID, DoctorID and at least one item are required")
    with db.transaction() as cur:
        cur.execute("INSERT INTO Prescription (`Date`, Notes, PatientID, DoctorID) VALUES (%s,%s,%s,%s)",
                    (data.get("Date") or date.today(), data.get("Notes"), data["PatientID"], doctor_id))
        pid = cur.lastrowid
        for it in items:
            try:
                qty = int(it.get("Quantity", 0))
            except (TypeError, ValueError):
                raise ApiError("Quantity must be a number")
            if qty <= 0:
                raise ApiError("Quantity must be greater than 0")
            cur.execute("SELECT Stock FROM Medicine WHERE MedicineID=%s FOR UPDATE", (it.get("MedicineID"),))
            med = cur.fetchone()
            if not med:
                raise ApiError(f"Medicine {it.get('MedicineID')} not found", 404)
            if med["Stock"] < qty:
                raise ApiError(f"Insufficient stock for medicine {it['MedicineID']} (have {med['Stock']})", 409)
            cur.execute("INSERT INTO PrescriptionItem (PrescriptionID, MedicineID, Dosage, Quantity) VALUES (%s,%s,%s,%s)",
                        (pid, it["MedicineID"], it.get("Dosage"), qty))
            cur.execute("UPDATE Medicine SET Stock = Stock - %s WHERE MedicineID=%s", (qty, it["MedicineID"]))
    return pid


def admit_patient(data):
    if not data.get("PatientID") or not data.get("RoomID"):
        raise ApiError("PatientID and RoomID are required")
    with db.transaction() as cur:
        cur.execute("SELECT Status FROM Room WHERE RoomID=%s FOR UPDATE", (data["RoomID"],))
        room = cur.fetchone()
        if not room:
            raise ApiError("Room not found", 404)
        if room["Status"] != "Available":
            raise ApiError(f"Room is {room['Status']}", 409)
        cur.execute("INSERT INTO Admission (PatientID, RoomID, AdmitDate) VALUES (%s,%s,%s)",
                    (data["PatientID"], data["RoomID"], data.get("AdmitDate") or date.today()))
        adm_id = cur.lastrowid
        cur.execute("UPDATE Room SET Status='Occupied' WHERE RoomID=%s", (data["RoomID"],))
    return adm_id


def discharge_patient(aid):
    with db.transaction() as cur:
        cur.execute("SELECT RoomID, DischargeDate FROM Admission WHERE AdmissionID=%s FOR UPDATE", (aid,))
        adm = cur.fetchone()
        if not adm:
            raise ApiError("Admission not found", 404)
        if adm["DischargeDate"]:
            raise ApiError("Already discharged", 409)
        cur.execute("UPDATE Admission SET DischargeDate=%s WHERE AdmissionID=%s", (date.today(), aid))
        cur.execute("UPDATE Room SET Status='Available' WHERE RoomID=%s", (adm["RoomID"],))


def generate_admission_bill(aid, payment_mode="Cash"):
    adm = db.query("""SELECT ad.*, r.Charge FROM Admission ad JOIN Room r ON r.RoomID=ad.RoomID
                      WHERE ad.AdmissionID=%s""", (aid,), one=True)
    if not adm:
        raise ApiError("Admission not found", 404)
    if not adm["DischargeDate"]:
        raise ApiError("Discharge the patient before generating the bill", 409)
    days = max((adm["DischargeDate"] - adm["AdmitDate"]).days, 1)
    room_total = float(adm["Charge"]) * days
    med = db.query(
        """SELECT COALESCE(SUM(m.Price * pi.Quantity), 0) AS total
           FROM Prescription pr JOIN PrescriptionItem pi ON pi.PrescriptionID=pr.PrescriptionID
           JOIN Medicine m ON m.MedicineID=pi.MedicineID
           WHERE pr.PatientID=%s AND pr.`Date` BETWEEN %s AND %s""",
        (adm["PatientID"], adm["AdmitDate"], adm["DischargeDate"]), one=True)
    med_total = float(med["total"])
    bill_id, _ = db.execute(
        "INSERT INTO Bill (PatientID, AdmissionID, Amount, `Date`, PaymentMode, Status) VALUES (%s,%s,%s,%s,%s,'Pending')",
        (adm["PatientID"], aid, room_total + med_total, date.today(), payment_mode))
    return dict(BillID=bill_id, days=days, room_charges=room_total,
                medicine_charges=med_total, total=room_total + med_total)


def generate_appointment_bill(appt_id, payment_mode="Cash"):
    appt = db.query("""SELECT a.*, d.ConsultationFee FROM Appointment a JOIN Doctor d ON d.DoctorID=a.DoctorID
                       WHERE a.AppointmentID=%s""", (appt_id,), one=True)
    if not appt:
        raise ApiError("Appointment not found", 404)
    if appt["Status"] != "Completed":
        raise ApiError("Only completed appointments can be billed", 409)
    bill_id, _ = db.execute(
        "INSERT INTO Bill (PatientID, AppointmentID, Amount, `Date`, PaymentMode, Status) VALUES (%s,%s,%s,%s,%s,'Pending')",
        (appt["PatientID"], appt_id, appt["ConsultationFee"], date.today(), payment_mode))
    return dict(BillID=bill_id, total=float(appt["ConsultationFee"]))
