backup-main
# Hospital Management System - Frontend

A clean, functional, plain HTML, CSS, and vanilla JavaScript frontend for the Hospital Management System DBMS course project.

## Tech Stack
- **Languages**: HTML5, CSS3, Vanilla JavaScript (ES6+).
- **Communication**: Native `fetch()` API with JSON payloads (`http://localhost:5000`).
- **Dependencies**: None (no Node.js, npm, React, or bundler required).
- **Architecture**: Plain tables, clean cards, modal dialogs, status badges, and inline alert feedback.

---

## How to Run the Frontend

### Option 1: Using Python Static Server (Recommended)
From the project root directory, run:
```bash
python -m http.server 8000
```
Then open your browser and navigate to:
[http://localhost:8000/index.html](http://localhost:8000/index.html)

### Option 2: Direct File Opening
You can open `index.html` directly in any web browser (Chrome, Firefox, Edge). All links and assets use relative paths and support the `file:///` protocol.

---

## Demo Accounts

| Role | Username | Password | Access Portal |
|---|---|---|---|
| **Admin** | `admin` | `Admin@123` | Hospital stats, doctor approvals, bed allocation, master CRUD |
| **Doctor** | `doctor1` | `Doctor@123` | Consultations calendar, timetable, patient history, prescriptions |
| **Patient** | `patient1` | `Patient@123` | Consultation slot booking, prescriptions, admissions, bills |

*(Quick-fill buttons on the login page automatically populate these credentials).*

---

## Complete Page & API Endpoint Reference Table

| Portal | File Path | Purpose / Features | Backend Endpoints Used |
|---|---|---|---|
| **Public** | `index.html` | User login & role redirect | `POST /api/auth/login` |
| **Public** | `register.html` | Patient self-registration & Doctor approval request | `POST /api/auth/register/patient`<br>`POST /api/auth/register/doctor`<br>`GET /api/departments` |
| **Patient** | `patient/index.html` | Patient dashboard & summary metrics | `GET /api/patient/appointments`<br>`GET /api/patient/bills`<br>`GET /api/patient/prescriptions`<br>`GET /api/patient/admissions` |
| **Patient** | `patient/book.html` | Specialist search & timetable slot reservation | `GET /api/departments`<br>`GET /api/doctors?DeptID=&q=`<br>`GET /api/doctors/<id>/slots?date=`<br>`POST /api/patient/appointments` |
| **Patient** | `patient/appointments.html` | Past & scheduled consultations with cancel action | `GET /api/patient/appointments`<br>`POST /api/patient/appointments/<id>/cancel` |
| **Patient** | `patient/prescriptions.html` | Medication list, dosages, & clinical advice | `GET /api/patient/prescriptions` |
| **Patient** | `patient/lab-tests.html` | Diagnostic lab investigation reports | `GET /api/patient/lab-tests` |
| **Patient** | `patient/admissions.html` | Room allocation, ward details, & stay dates | `GET /api/patient/admissions` |
| **Patient** | `patient/bills.html` | Invoices and payment simulation (UPI, Card, Cash) | `GET /api/patient/bills`<br>`POST /api/patient/bills/<id>/pay` |
| **Patient** | `patient/profile.html` | Profile management & password change | `GET /api/patient/profile`<br>`PUT /api/patient/profile`<br>`POST /api/auth/change-password` |
| **Doctor** | `doctor/index.html` | Appointments management (complete & cancel) | `GET /api/doctor/appointments`<br>`POST /api/doctor/appointments/<id>/complete`<br>`POST /api/doctor/appointments/<id>/cancel`<br>`GET /api/doctor/patients` |
| **Doctor** | `doctor/schedule.html` | Weekly consultation timetable builder | `GET /api/doctor/schedule`<br>`PUT /api/doctor/schedule` |
| **Doctor** | `doctor/patients.html` | Treated patients & full clinical history modal | `GET /api/doctor/patients`<br>`GET /api/doctor/patients/<id>/history` |
| **Doctor** | `doctor/prescribe.html` | Prescription formulation with stock check | `GET /api/doctor/patients`<br>`GET /api/medicines`<br>`POST /api/doctor/prescriptions`<br>`GET /api/doctor/prescriptions` |
| **Doctor** | `doctor/lab-tests.html` | Order investigations & enter pathology results | `GET /api/doctor/patients`<br>`GET /api/doctor/patients/<id>/history`<br>`POST /api/doctor/lab-tests`<br>`PUT /api/doctor/lab-tests/<id>` |
| **Admin** | `admin/index.html` | 8 operational metrics & low-stock monitor | `GET /api/stats`<br>`GET /api/medicines/low-stock?threshold=20` |
| **Admin** | `admin/approvals.html` | Approve or reject pending doctor registrations | `GET /api/admin/pending-doctors`<br>`POST /api/admin/users/<id>/approve`<br>`POST /api/admin/users/<id>/reject` |
| **Admin** | `admin/users.html` | Manage login access (Enable / Disable) | `GET /api/admin/users`<br>`POST /api/admin/users/<id>/enable`<br>`POST /api/admin/users/<id>/disable` |
| **Admin** | `admin/patients.html` | Fast name/phone search & complete medical history | `GET /api/patients`<br>`GET /api/patients/search?q=`<br>`GET /api/patients/<id>/history` |
| **Admin** | `admin/appointments.html` | Master schedule & walk-in booking slot picker | `GET /api/appointments-detail?date=`<br>`GET /api/patients`<br>`GET /api/doctors`<br>`GET /api/doctors/<id>/slots?date=`<br>`POST /api/admin/appointments`<br>`POST /api/appointments/<id>/generate-bill` |
| **Admin** | `admin/admissions.html` | Room allocation, bed census, discharge & billing | `GET /api/rooms/available`<br>`POST /api/admit`<br>`GET /api/admissions`<br>`POST /api/admissions/<id>/discharge`<br>`POST /api/admissions/<id>/generate-bill` |
| **Admin** | `admin/billing.html` | Billing ledger & cashier settlement | `GET /api/bills`<br>`POST /api/bills/<id>/pay` |
| **Admin** | `admin/medicines.html` | Medicine catalog stock & pricing CRUD | `GET /api/medicines`<br>`POST /api/medicines`<br>`PUT /api/medicines/<id>` |
| **Admin** | `admin/master.html` | Unified CRUD for Departments, Doctors, Wards, Rooms, Nurses | `GET/POST /api/<resource>`<br>`PUT/DELETE /api/<resource>/<id>` |

