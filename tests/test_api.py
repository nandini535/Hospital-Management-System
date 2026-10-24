"""End-to-end test of the API (uses Flask's test client).  Run from the project root:
    python tests/test_api.py
Needs: database loaded, and `python backend/seed_users.py --admin-only` done. Safe to re-run."""
import os, random, sys
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))
from app import app

c = app.test_client()
passed = failed = 0


def check(name, cond, extra=""):
    global passed, failed
    if cond:
        passed += 1; print(f"  PASS  {name}")
    else:
        failed += 1; print(f"  FAIL  {name}  {extra}")


def call(method, url, token=None, **kw):
    h = {"Authorization": f"Bearer {token}"} if token else {}
    r = getattr(c, method)(url, headers=h, **kw)
    return r.status_code, (r.get_json(silent=True) if r.get_json(silent=True) is not None else {})


def login(u, p):
    s, j = call("post", "/api/auth/login", json={"Username": u, "Password": p})
    return s, j.get("token"), j


tag = str(random.randint(10000, 99999))
d = date.today() + timedelta(days=1)
while d.weekday() > 4:
    d += timedelta(days=1)                       # next weekday (default timetable is Mon-Fri)
day = d.isoformat()

print("== security basics")
check("health is open", call("get", "/api/health")[0] == 200)
check("patients list needs login", call("get", "/api/patients")[0] == 401)
check("fake token rejected", call("get", "/api/auth/me", token="abc")[0] == 401)
check("departments list is public", call("get", "/api/departments")[0] == 200)
s, tok_admin, _ = login("admin", "Admin@123")
check("admin login", s == 200 and tok_admin)
check("wrong password -> 401", login("admin", "nope")[0] == 401)

print("== patient registration + portal")
reg = {"Username": f"pat{tag}", "Password": "Passw0rd!", "Name": "Test Patient", "Gender": "Female", "DOB": "1995-04-12", "Phone": "9000000001"}
s, j = call("post", "/api/auth/register/patient", json=reg)
check("register patient", s == 201 and j.get("token"), j); tok_p1, pid1 = j.get("token"), j.get("PatientID")
check("duplicate username -> 409", call("post", "/api/auth/register/patient", json=reg)[0] == 409)
check("weak password -> 400", call("post", "/api/auth/register/patient", json={**reg, "Username": "x" + tag, "Password": "123"})[0] == 400)
s, j = call("post", "/api/auth/register/patient", json={**reg, "Username": f"pat2{tag}", "Name": "Other Patient"})
tok_p2, pid2 = j.get("token"), j.get("PatientID")
check("patient cannot use admin CRUD", call("get", "/api/patients", tok_p1)[0] == 403)
check("patient cannot see stats", call("get", "/api/stats", tok_p1)[0] == 403)
check("patient cannot use doctor portal", call("get", "/api/doctor/appointments", tok_p1)[0] == 403)
check("patient can read own profile", call("get", "/api/patient/profile", tok_p1)[1].get("Name") == "Test Patient")
check("password hash never exposed", "PasswordHash" not in str(call("get", "/api/auth/me", tok_p1)[1]))

print("== doctor registration + approval")
dreg = {"Username": f"doc{tag}", "Password": "Passw0rd!", "Name": "Dr. Test", "Specialization": "Dermatologist",
        "Email": f"doc{tag}@hms.in", "DeptID": 3, "ConsultationFee": 650}
s, j = call("post", "/api/auth/register/doctor", json=dreg)
check("register doctor", s == 201, j); did = j.get("DoctorID")
s, _, j = login(dreg["Username"], dreg["Password"])
check("pending doctor cannot log in", s == 403, j)
s, pend = call("get", "/api/admin/pending-doctors", tok_admin)
uid = next((x["UserID"] for x in pend if x["DoctorID"] == did), None) if isinstance(pend, list) else None
check("admin sees pending doctor", uid is not None)
s, docs = call("get", "/api/doctors", tok_p1)
check("pending doctor hidden from patients", not any(x["DoctorID"] == did for x in docs))
check("patient cannot approve", call("post", f"/api/admin/users/{uid}/approve", tok_p1)[0] == 403)
check("admin approves", call("post", f"/api/admin/users/{uid}/approve", tok_admin)[0] == 200)
s, tok_d, j = login(dreg["Username"], dreg["Password"])
check("doctor logs in after approval", s == 200 and j["role"] == "Doctor")
check("doctor portal works", call("get", "/api/doctor/profile", tok_d)[1].get("Name") == "Dr. Test")

print("== schedule, slots, booking")
sched = [{"DayOfWeek": x, "StartTime": "09:00", "EndTime": "11:00", "SlotMinutes": 30} for x in range(5)]
check("doctor sets schedule", call("put", "/api/doctor/schedule", tok_d, json=sched)[0] == 200)
s, slots = call("get", f"/api/doctors/{did}/slots?date={day}", tok_p1)
check("4 slots from 09:00 to 11:00", s == 200 and len(slots) == 4 and all(x["available"] for x in slots), slots)
s, docs = call("get", "/api/doctors?q=Dermatologist", tok_p1)
check("doctor directory lists approved doctor", any(x["DoctorID"] == did for x in docs))
b = {"DoctorID": did, "Date": day, "Time": "09:00", "Reason": "Skin rash"}
s, j = call("post", "/api/patient/appointments", tok_p1, json=b)
check("patient books slot", s == 201, j); aid = j.get("AppointmentID")
check("same slot by other patient -> 409", call("post", "/api/patient/appointments", tok_p2, json=b)[0] == 409)
check("off-schedule time rejected", call("post", "/api/patient/appointments", tok_p2, json={**b, "Time": "15:00"})[0] == 400)
check("past date rejected", call("post", "/api/patient/appointments", tok_p2, json={**b, "Date": "2020-01-06"})[0] == 400)
s, slots = call("get", f"/api/doctors/{did}/slots?date={day}", tok_p2)
check("booked slot shows unavailable", slots[0]["available"] is False and slots[1]["available"] is True)
check("patient cancels", call("post", f"/api/patient/appointments/{aid}/cancel", tok_p1)[0] == 200)
s, j = call("post", "/api/patient/appointments", tok_p2, json=b)
check("cancelled slot can be re-booked", s == 201, j); aid2 = j.get("AppointmentID")
check("other patient cannot cancel mine", call("post", f"/api/patient/appointments/{aid2}/cancel", tok_p1)[0] == 404)

print("== doctor workflow")
s, ap = call("get", f"/api/doctor/appointments?date={day}", tok_d)
live = [a for a in ap if a["Status"] == "Scheduled"] if isinstance(ap, list) else []
check("doctor sees list with patient details", s == 200 and len(live) == 1 and live[0]["PatientName"] == "Other Patient" and live[0]["Reason"] == "Skin rash", ap)
check("doctor cannot see unrelated patient", call("get", f"/api/doctor/patients/{pid1}/history", tok_d)[0] == 403)
check("doctor can see own patient history", call("get", f"/api/doctor/patients/{pid2}/history", tok_d)[0] == 200)
s, meds = call("get", "/api/medicines", tok_d)
check("doctor can read medicine list", s == 200 and len(meds) > 0)
check("doctor cannot edit medicines", call("post", "/api/medicines", tok_d, json={"Name": "X", "Price": 1, "Stock": 1})[0] == 403)
stock_before = meds[0]["Stock"]
rx = {"PatientID": pid2, "Notes": "Apply twice daily", "items": [{"MedicineID": meds[0]["MedicineID"], "Dosage": "1-0-1", "Quantity": 5}]}
s, j = call("post", "/api/doctor/prescriptions", tok_d, json=rx)
check("doctor writes prescription", s == 201, j)
check("prescription for unrelated patient blocked", call("post", "/api/doctor/prescriptions", tok_d, json={**rx, "PatientID": pid1})[0] == 403)
check("stock deducted", call("get", f"/api/medicines/{meds[0]['MedicineID']}", tok_d)[1]["Stock"] == stock_before - 5)
check("too-large quantity -> 409", call("post", "/api/doctor/prescriptions", tok_d, json={**rx, "items": [{"MedicineID": meds[0]["MedicineID"], "Quantity": 10**6}]})[0] == 409)
s, j = call("post", "/api/doctor/lab-tests", tok_d, json={"PatientID": pid2, "TestName": "CBC"}); tid = j.get("TestID")
check("doctor orders lab test", s == 201)
check("doctor enters result", call("put", f"/api/doctor/lab-tests/{tid}", tok_d, json={"Result": "Normal"})[0] == 200)
check("doctor completes appointment", call("post", f"/api/doctor/appointments/{aid2}/complete", tok_d)[0] == 200)
check("cannot complete twice", call("post", f"/api/doctor/appointments/{aid2}/complete", tok_d)[0] == 404)

print("== patient sees everything")
check("patient sees prescription with items", (lambda r: len(r) == 1 and len(r[0]["items"]) == 1)(call("get", "/api/patient/prescriptions", tok_p2)[1]))
check("patient sees lab result", call("get", "/api/patient/lab-tests", tok_p2)[1][0]["Result"] == "Normal")
check("patient1 cannot see patient2 data", call("get", "/api/patient/prescriptions", tok_p1)[1] == [])
h = call("get", "/api/patient/history", tok_p2)[1]
check("full history has all sections", all(k in h for k in ("patient", "appointments", "prescriptions", "lab_tests", "admissions", "bills")))

print("== billing")
check("cannot bill an uncompleted appointment", call("post", f"/api/appointments/{aid}/generate-bill", tok_admin)[0] == 409)
s, j = call("post", f"/api/appointments/{aid2}/generate-bill", tok_admin)
check("admin bills completed visit (fee 650)", s == 201 and j["total"] == 650, j); bid = j.get("BillID")
check("duplicate bill -> 409", call("post", f"/api/appointments/{aid2}/generate-bill", tok_admin)[0] == 409)
check("patient sees pending bill", call("get", "/api/patient/bills", tok_p2)[1][0]["Status"] == "Pending")
check("other patient cannot pay it", call("post", f"/api/patient/bills/{bid}/pay", tok_p1, json={"PaymentMode": "UPI"})[0] == 404)
check("patient pays", call("post", f"/api/patient/bills/{bid}/pay", tok_p2, json={"PaymentMode": "UPI"})[0] == 200)
check("cannot pay twice", call("post", f"/api/patient/bills/{bid}/pay", tok_p2, json={"PaymentMode": "UPI"})[0] == 404)

print("== admin operations")
s, rooms = call("get", "/api/rooms/available", tok_admin)
s, j = call("post", "/api/admit", tok_admin, json={"PatientID": pid2, "RoomID": rooms[0]["RoomID"]})
check("admit patient", s == 201, j); adm = j.get("AdmissionID")
check("patient sees admission", len(call("get", "/api/patient/admissions", tok_p2)[1]) == 1)
check("discharge", call("post", f"/api/admissions/{adm}/discharge", tok_admin)[0] == 200)
check("admission bill", call("post", f"/api/admissions/{adm}/generate-bill", tok_admin)[0] == 201)
check("stats", "pending_doctor_approvals" in call("get", "/api/stats", tok_admin)[1])
check("change password", call("post", "/api/auth/change-password", tok_p1, json={"OldPassword": "Passw0rd!", "NewPassword": "NewPassw0rd!"})[0] == 200)
check("old password no longer works", login(reg["Username"], "Passw0rd!")[0] == 401)
check("disable account", call("post", f"/api/admin/users/{uid}/disable", tok_admin)[0] == 200)
check("disabled doctor's token stops working", call("get", "/api/doctor/profile", tok_d)[0] == 401)

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
