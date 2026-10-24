# Hospital Management System - Frontend

A clean, functional, plain HTML, CSS, and vanilla JavaScript frontend for the Hospital Management System DBMS course project.

## Tech Stack
- **Languages**: HTML5, CSS3, Vanilla JavaScript (ES6+).
- **Communication**: Native `fetch()` API with JSON payloads.
- **Dependencies**: None (no Node.js, npm, React, or bundler required).
- **Backend API**: Flask REST API at `http://localhost:5000`.

---

## How to Run the Frontend

### Option 1: Using Python Static Server (Recommended)
From the project root directory, run:
```bash
python -m http.server 8000
```
Then open your browser and navigate to:
[http://localhost:8000/index.html](http://localhost:8000/index.html)

### Option 2: Opening Files Directly
You can open `index.html` directly in any modern web browser (e.g. Chrome, Firefox, Edge). All assets and links use relative paths.

---

## Demo Accounts

| Role | Username | Password | Notes |
|---|---|---|---|
| **Admin** | `admin` | `Admin@123` | Full administrative access |
| **Doctor** | `doctor1` | `Doctor@123` | Timetable, patients, prescriptions |
| **Patient** | `patient1` | `Patient@123` | Appointment booking, bills, history |

> On the login page (`index.html`), quick-fill buttons are provided to instantly populate demo credentials.

---

## Project Structure

```text
├── index.html            # Login page (role-based redirect & demo credentials)
├── register.html         # Self-registration (Patient & Doctor approval tabs)
├── css/
│   └── style.css         # Shared neutral styling, tables, alerts, badges, forms
├── js/
│   ├── api.js            # Central API client (apiFetch), localStorage, & UI helpers
│   └── auth.js           # Role guards (requireAuth) & shared navbar renderer
├── patient/              # Patient portal pages (Step 2)
├── doctor/               # Doctor portal pages (Step 3)
└── admin/                # Admin portal pages (Step 4)
```

---

## API Endpoints Used by Page

### 1. Authentication & Public
- `POST /api/auth/login`: Authenticates username & password, returns JWT token and role metadata.
- `POST /api/auth/register/patient`: Self-registers patient and returns active session.
- `POST /api/auth/register/doctor`: Self-registers doctor (enters `Pending` state waiting for admin approval).
- `GET /api/departments`: Public endpoint populating department dropdown during doctor registration.
- `GET /api/auth/me`: Verifies active session token.
- `POST /api/auth/change-password`: Updates password with `OldPassword` & `NewPassword`.

### 2. Patient Portal (`/patient/`)
- `GET /api/patient/profile`, `PUT /api/patient/profile`: View and update patient profile.
- `GET /api/doctors?DeptID=&q=`: Search doctors and filter by department.
- `GET /api/doctors/<id>/slots?date=YYYY-MM-DD`: Fetch available and taken appointment slots.
- `POST /api/patient/appointments`: Book consultation slot.
- `GET /api/patient/appointments`: List appointments.
- `POST /api/patient/appointments/<id>/cancel`: Cancel scheduled appointment.
- `GET /api/patient/prescriptions`: View prescriptions and medicine dosages.
- `GET /api/patient/lab-tests`: View lab test results.
- `GET /api/patient/admissions`: View room admissions and ward details.
- `GET /api/patient/bills`: View billing history.
- `POST /api/patient/bills/<id>/pay`: Simulate payment for pending bill.

### 3. Doctor Portal (`/doctor/`)
- `GET /api/doctor/appointments?date=&status=&upcoming=1`: Doctor's consultations.
- `POST /api/doctor/appointments/<id>/complete`: Mark appointment completed.
- `POST /api/doctor/appointments/<id>/cancel`: Cancel appointment.
- `GET /api/doctor/schedule`, `PUT /api/doctor/schedule`: Manage weekly timetable.
- `GET /api/doctor/patients`: Patients treated by the doctor.
- `GET /api/doctor/patients/<id>/history`: Patient's clinical history.
- `GET /api/medicines`: Medicine catalog for prescriptions.
- `POST /api/doctor/prescriptions`: Write prescription with items.
- `POST /api/doctor/lab-tests`: Order lab test.
- `PUT /api/doctor/lab-tests/<id>`: Enter lab test result.

### 4. Admin Portal (`/admin/`)
- `GET /api/stats`: Dashboard statistics.
- `GET /api/admin/pending-doctors`: Doctors waiting for approval.
- `POST /api/admin/users/<id>/approve` | `reject`: Review doctor registrations.
- `GET /api/admin/users`: User account list.
- `POST /api/admin/users/<id>/enable` | `disable`: Account toggle.
- `GET /api/patients/search?q=`: Patient search.
- `GET /api/patients/<id>/history`: Full patient history view.
- `GET /api/appointments-detail?date=`: Master appointment calendar.
- `POST /api/admin/appointments`: Walk-in appointment booking.
- `GET /api/rooms/available`: Available rooms.
- `POST /api/admit`: Admit patient to room.
- `GET /api/admissions`: Current admissions.
- `POST /api/admissions/<id>/discharge`: Discharge patient from room.
- `POST /api/admissions/<id>/generate-bill`: Generate inpatient bill.
- `POST /api/appointments/<id>/generate-bill`: Generate consultation bill.
- `GET /api/bills`, `POST /api/bills/<id>/pay`: Mark bills paid.
- `GET /api/medicines`, `GET /api/medicines/low-stock?threshold=20`: Inventory monitor.
- Generic CRUD (`GET/POST /api/<resource>`, `PUT/DELETE /api/<resource>/<id>`): Departments, Doctors, Wards, Rooms, Nurses.