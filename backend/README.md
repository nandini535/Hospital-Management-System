# Hospital Management System: Backend API

REST API for the Hospital Management System, built with **Flask (Python)** and **MySQL**.
It handles login and registration, role-based access (Admin / Doctor / Patient), appointment booking with time slots, prescriptions, lab tests, admissions and billing.

## Tech stack
- Python 3.9+
- Flask, Flask-CORS
- MySQL 8.0.16+ (CHECK constraints need this version)
- mysql-connector-python

## Folder structure
```
backend/
├── app.py              Entry point; admin endpoints and generic table CRUD
├── auth.py             Token check and role guard
├── routes_auth.py      Login, registration, change password
├── routes_patient.py   Patient portal
├── routes_doctor.py    Doctor portal
├── services.py         Business logic (booking, prescriptions, admission, billing)
├── db.py               MySQL connection pool and transaction helper
├── tables.py           Table definitions for the generic CRUD
├── config.py           Settings read from environment variables
├── errors.py           Error type used for clean JSON errors
├── seed_users.py       Creates the admin and demo accounts
└── requirements.txt
```
The database scripts are in `sql/` (`schema_v2.sql`, `sample_data.sql`) and the tests in `tests/`, both at the project root.

## Setup

### 1. Create the database
Run from the project root (MySQL 8.0.16+):

```bash
mysql -u root -p < sql/schema_v2.sql
mysql -u root -p < sql/sample_data.sql
```
`schema_v2.sql` **drops and recreates** the database `hospital_db`, so only run it on a fresh setup. `sample_data.sql` adds demo departments, doctors (with Mon-Fri timetables), patients, rooms and medicines.

### 2. Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Set your configuration
The app reads these environment variables:

| Variable | Default | Meaning |
|---|---|---|
| `DB_HOST` | localhost | MySQL host |
| `DB_PORT` | 3306 | MySQL port |
| `DB_USER` | root | MySQL user |
| `DB_PASSWORD` | (empty) | MySQL password |
| `DB_NAME` | hospital_db | Database name |
| `SECRET_KEY` | dev-only-change-me | Signs login tokens. **Set your own.** |
| `TOKEN_MAX_AGE` | 43200 | Login lifetime in seconds (12 h) |

Windows PowerShell:
```powershell
$env:DB_USER="root"; $env:DB_PASSWORD="yourpassword"; $env:SECRET_KEY="any-long-random-text"
```
Linux / macOS:
```bash
export DB_USER=root DB_PASSWORD=yourpassword SECRET_KEY=any-long-random-text
```
Environment variables last only for the current terminal window, so set them again if you open a new one.

### 4. Create login accounts
```bash
python seed_users.py --admin-only    # only the admin
python seed_users.py                 # admin + a demo login for every doctor and patient in the database
```

| Account | Username | Password |
|---|---|---|
| Admin | `admin` | `Admin@123` |
| Doctor | `doctor<ID>` (e.g. `doctor1`) | `Doctor@123` |
| Patient | `patient<ID>` (e.g. `patient1`) | `Patient@123` |

These are demo passwords. Change them before showing the project to anyone outside your team.

### 5. Run the server
```bash
python app.py
```
The API runs at `http://localhost:5000`. Check it with `http://localhost:5000/api/health`.

### 6. Run the tests (optional)
From the project root:
```bash
python tests/test_api.py
```
It runs 66 end-to-end checks covering registration, login, role restrictions, booking, prescriptions, billing and admissions. It needs the database loaded and the admin account created.

## How authentication works
1. The website sends `POST /api/auth/login` with `{"Username": "...", "Password": "..."}`.
2. The server returns a token, along with `role`, `name`, `DoctorID` and `PatientID`.
3. The website sends the token on every later request:
   ```
   Authorization: Bearer <token>
   ```
4. Tokens expire after 12 hours, and the user must log in again.

Error responses are JSON, for example `{"error": "Slot is already taken"}`.

| Code | Meaning |
|---|---|
| 400 | Invalid or missing input |
| 401 | Not logged in, or the token expired |
| 403 | Logged in but not allowed (wrong role) |
| 404 | Not found |
| 409 | Conflict (double booking, not enough stock, duplicate) |
| 429 | Too many failed login attempts |

## Endpoints

### Public (no login)
| Method | Path | Purpose |
|---|---|---|
| POST | `/api/auth/register/patient` | Register a patient (`Username`, `Password` of 8+ characters, `Name`, `Gender`, `DOB`, optional `Phone`, `Address`, `BloodGroup`). Logs in immediately. |
| POST | `/api/auth/register/doctor` | Register a doctor (`Username`, `Password`, `Name`, `Specialization`, `Email`, `DeptID`, optional `Phone`, `ConsultationFee`). The account is **Pending** until an admin approves it. |
| POST | `/api/auth/login` | Log in |
| GET | `/api/departments` | Department list for the registration form |
| GET | `/api/health` | Server check |

### Any logged-in user
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/auth/me` | Current user |
| POST | `/api/auth/change-password` | `OldPassword`, `NewPassword` |
| GET | `/api/doctors?DeptID=&q=` | Doctor directory (pending doctors are hidden) |
| GET | `/api/doctors/<id>/slots?date=YYYY-MM-DD` | Free and taken slots |
| GET | `/api/medicines` | Medicine list |

### Patient portal (`/api/patient/...`)
A patient only ever sees their own data.

| Method | Path | Purpose |
|---|---|---|
| GET / PUT | `/profile` | View or update profile |
| GET | `/history` | Full record in one call |
| GET | `/appointments` | My appointments |
| POST | `/appointments` | Book: `DoctorID`, `Date`, `Time`, optional `Reason` |
| POST | `/appointments/<id>/cancel` | Cancel |
| GET | `/prescriptions` | My prescriptions with medicines |
| GET | `/lab-tests` | My lab results |
| GET | `/admissions` | My admissions |
| GET | `/bills` | My bills |
| POST | `/bills/<id>/pay` | Pay: `PaymentMode` (Cash, Card, UPI or Insurance). Payment is simulated. |

### Doctor portal (`/api/doctor/...`)
| Method | Path | Purpose |
|---|---|---|
| GET | `/profile` | My profile |
| GET / PUT | `/schedule` | View or replace my weekly timetable |
| GET | `/appointments?date=&status=&upcoming=1` | My appointments with patient details |
| POST | `/appointments/<id>/complete` | Mark completed |
| POST | `/appointments/<id>/cancel` | Cancel |
| GET | `/patients` | Patients who booked with me |
| GET | `/patients/<id>/history` | A patient's full history (only my patients) |
| GET / POST | `/prescriptions` | List mine / write one: `PatientID`, `Notes`, `items[{MedicineID, Dosage, Quantity}]` |
| POST | `/lab-tests` | Order a test: `PatientID`, `TestName` |
| PUT | `/lab-tests/<id>` | Enter a result: `Result` |

Timetable format for `PUT /schedule`:
```json
[{"DayOfWeek": 0, "StartTime": "09:00", "EndTime": "13:00", "SlotMinutes": 30}]
```
`DayOfWeek`: 0 = Monday ... 6 = Sunday.

### Admin
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/admin/pending-doctors` | Doctors waiting for approval |
| POST | `/api/admin/users/<id>/approve` or `reject` | Approve or reject a doctor |
| POST | `/api/admin/users/<id>/disable` or `enable` | Block or unblock an account |
| GET | `/api/admin/users` | All accounts |
| POST | `/api/admin/appointments` | Book for a walk-in patient |
| GET | `/api/appointments-detail?date=` | Appointments with patient and doctor names |
| POST | `/api/admit` | Admit a patient: `PatientID`, `RoomID` |
| POST | `/api/admissions/<id>/discharge` | Discharge |
| POST | `/api/admissions/<id>/generate-bill` | Bill: room charge x days + medicines |
| POST | `/api/appointments/<id>/generate-bill` | Bill a completed consultation (doctor's fee) |
| POST | `/api/bills/<id>/pay` | Mark a bill as paid |
| GET | `/api/stats` | Dashboard numbers |
| GET | `/api/rooms/available` | Free rooms |
| GET | `/api/medicines/low-stock?threshold=20` | Medicines running low |
| GET | `/api/patients/search?q=` | Search patients by name or phone |
| GET | `/api/patients/<id>/history` | Any patient's full history |

Admins also get create, read, update and delete on every table at `/api/<resource>`, where `<resource>` is one of: `departments`, `doctors`, `patients`, `appointments`, `wards`, `rooms`, `nurses`, `admissions`, `prescriptions`, `medicines`, `prescription-items`, `lab-tests`, `bills`. List endpoints accept filters, for example `/api/bills?Status=Pending`.

## Business rules
- **No double booking.** A doctor's slot can be held by one active appointment. Cancelling frees the slot.
- **Slots come from the doctor's timetable.** Off-schedule times and past dates are rejected.
- **Room allocation is transactional.** Admitting locks the room, creates the admission and marks the room Occupied together. Discharge frees it.
- **Prescriptions deduct stock** in the same transaction. If any medicine is short, nothing is saved.
- **One bill per admission** and **one bill per appointment**.
- **New doctors need approval** before they can log in.
- **A doctor can only open records of patients who booked with them.**

## Security
- Passwords are hashed and never stored in plain text.
- Tokens are signed with `SECRET_KEY`.
- All SQL uses parameterized queries, which prevents SQL injection.
- The patient or doctor ID always comes from the login token, never from the request body.
- 5 wrong passwords lock a username for 10 minutes.
- Limitation: payment is simulated and there is no real payment gateway.

## Troubleshooting
| Problem | Fix |
|---|---|
| `Access denied for user` | Check `DB_USER` and `DB_PASSWORD`, and that the variables are set in this terminal. |
| `Can't connect to MySQL server` | Start MySQL and check `DB_HOST` and `DB_PORT`. |
| `Unknown database 'hospital_db'` | Run the SQL setup step first. |
| `401 Login required` | Send the `Authorization: Bearer <token>` header. |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` inside `backend/`. |
| Website can't reach the API | The API must be running on port 5000, and the site should call `http://localhost:5000`. |
