# Hospital Management System

A comprehensive Hospital Management System (HMS) database and application designed to manage hospital workflows, patient records, doctor appointments, admissions, pharmacy prescriptions, and billing.

---

## 📋 Database Overview

- **DBMS:** MySQL 8.0+
- **Database Name:** `hospital_db`
- **Character Set / Collation:** `utf8mb4` / `utf8mb4_0900_ai_ci`
- **Schema File:** [`hospital_db_schemas.sql`](hospital_db_schemas.sql)

### Core Modules & Entities

| Module | Entities / Tables | Description |
| :--- | :--- | :--- |
| **Administration** | `Department`, `Ward`, `Room` | Manages hospital departments, hospital wards, room types, capacities, and rates. |
| **Staff** | `Doctor`, `Nurse` | Stores doctor specializations, shift schedules, contact details, and department assignments. |
| **Patients & Clinical** | `Patient`, `Appointment`, `Admission`, `LabTest` | Tracks patient profiles, appointment bookings, inpatient admissions/discharges, and lab tests. |
| **Pharmacy** | `Prescription`, `Medicine`, `PrescriptionItem` | Handles prescriptions, drug inventory, dosage, and stock validation. |
| **Finance** | `Bill`, `Payment` | Generates bills, supports partial/complete payments across modes (Cash, Card, UPI), and tracks balances. |

### Advanced Features

- **Views:**
  - `vw_appointment_details`: Joined view combining appointment, patient, and doctor details.
  - `vw_bill_balance`: Real-time calculation of total bill amount, amount paid, and outstanding balance.
  - `vw_current_admissions`: Active inpatient tracking with length-of-stay calculation.
- **Stored Procedure:**
  - `RecordPayment`: Atomically processes payments, validates amounts against bill totals, and updates payment statuses (`Paid` / `Partially Paid`).
- **Triggers:**
  - `trg_check_medicine_stock`: Prevents prescribing quantities exceeding current medicine inventory.

---

## 🚀 Database Setup for Team Members

Each team member should run their own local instance of the database to test features independently without affecting each other's test data.

### Prerequisites

- [MySQL 8.0+](https://dev.mysql.com/downloads/installer/) installed and running.
- [MySQL Workbench](https://dev.mysql.com/downloads/workbench/) (optional, but recommended) or MySQL Command Line Client.

---

### Setup Instructions

#### Option 1: Using MySQL Workbench (GUI)

1. Open **MySQL Workbench** and connect to your local MySQL instance (e.g., `Local instance MySQL80`).
2. Go to **File** > **Open SQL Script...** (or press `Ctrl + Shift + O`).
3. Select [`hospital_db_schemas.sql`](hospital_db_schemas.sql) from this repository.
4. Click the **Execute** button (the yellow lightning bolt ⚡ icon) to run the full script.
5. In the **Navigator** panel on the left, right-click and click **Refresh All** under the **Schemas** tab. You will see `hospital_db` with all tables, views, stored procedures, and sample data.

---

#### Option 2: Using Command Prompt / Terminal (CLI)

1. Open your terminal or Command Prompt.
2. Navigate to the project root directory:
   ```bash
   cd path/to/Hospital-Management-System
   ```
3. Run the script using the MySQL client:
   ```bash
   mysql -u root -p < hospital_db_schemas.sql
   ```
   *(Enter your local MySQL root password when prompted).*

> [!WARNING]
> **Data Reset Warning:** The script begins with `DROP DATABASE IF EXISTS hospital_db;`. Running the script will drop and recreate the database, resetting all tables to the initial sample seed data.

---

## 🔐 Environment Variables & Configuration

When developing backend services (Node.js, Python, Java, etc.) for this project:

1. **Never commit passwords or credentials to GitHub.**
2. Keep your database credentials in a `.env` file in your project root:
   ```env
   DB_HOST=localhost
   DB_PORT=3306
   DB_NAME=hospital_db
   DB_USER=root
   DB_PASSWORD=your_local_password
   ```
3. Make sure `.env` is listed inside `.gitignore`.

---

## 🧪 Verification Queries

After setting up the database, you can test it by running sample queries provided at the bottom of [`hospital_db_schemas.sql`](hospital_db_schemas.sql), for example:

```sql
USE hospital_db;

-- 1. View all appointments with patient and doctor details
SELECT * FROM vw_appointment_details ORDER BY AppointmentDate, AppointmentTime;

-- 2. View patients with pending bill balances
SELECT * FROM vw_bill_balance WHERE Balance > 0;

-- 3. View currently admitted inpatients
SELECT * FROM vw_current_admissions;
```
# Hospital Management System

A comprehensive Hospital Management System (HMS) database and application designed to manage hospital workflows, patient records, doctor appointments, admissions, pharmacy prescriptions, and billing.

---

## 📋 Database Overview

- **DBMS:** MySQL 8.0+
- **Database Name:** `hospital_db`
- **Character Set / Collation:** `utf8mb4` / `utf8mb4_0900_ai_ci`
- **Schema File:** [`hospital_db_schemas.sql`](hospital_db_schemas.sql)

### Core Modules & Entities

| Module | Entities / Tables | Description |
| :--- | :--- | :--- |
| **Administration** | `Department`, `Ward`, `Room` | Manages hospital departments, hospital wards, room types, capacities, and rates. |
| **Staff** | `Doctor`, `Nurse` | Stores doctor specializations, shift schedules, contact details, and department assignments. |
| **Patients & Clinical** | `Patient`, `Appointment`, `Admission`, `LabTest` | Tracks patient profiles, appointment bookings, inpatient admissions/discharges, and lab tests. |
| **Pharmacy** | `Prescription`, `Medicine`, `PrescriptionItem` | Handles prescriptions, drug inventory, dosage, and stock validation. |
| **Finance** | `Bill`, `Payment` | Generates bills, supports partial/complete payments across modes (Cash, Card, UPI), and tracks balances. |

### Advanced Features

- **Views:**
  - `vw_appointment_details`: Joined view combining appointment, patient, and doctor details.
  - `vw_bill_balance`: Real-time calculation of total bill amount, amount paid, and outstanding balance.
  - `vw_current_admissions`: Active inpatient tracking with length-of-stay calculation.
- **Stored Procedure:**
  - `RecordPayment`: Atomically processes payments, validates amounts against bill totals, and updates payment statuses (`Paid` / `Partially Paid`).
- **Triggers:**
  - `trg_check_medicine_stock`: Prevents prescribing quantities exceeding current medicine inventory.

---

## 🚀 Database Setup for Team Members

Each team member should run their own local instance of the database to test features independently without affecting each other's test data.

### Prerequisites

- [MySQL 8.0+](https://dev.mysql.com/downloads/installer/) installed and running.
- [MySQL Workbench](https://dev.mysql.com/downloads/workbench/) (optional, but recommended) or MySQL Command Line Client.

---

### Setup Instructions

#### Option 1: Using MySQL Workbench (GUI)

1. Open **MySQL Workbench** and connect to your local MySQL instance (e.g., `Local instance MySQL80`).
2. Go to **File** > **Open SQL Script...** (or press `Ctrl + Shift + O`).
3. Select [`hospital_db_schemas.sql`](hospital_db_schemas.sql) from this repository.
4. Click the **Execute** button (the yellow lightning bolt ⚡ icon) to run the full script.
5. In the **Navigator** panel on the left, right-click and click **Refresh All** under the **Schemas** tab. You will see `hospital_db` with all tables, views, stored procedures, and sample data.

---

#### Option 2: Using Command Prompt / Terminal (CLI)

1. Open your terminal or Command Prompt.
2. Navigate to the project root directory:
   ```bash
   cd path/to/Hospital-Management-System
   ```
3. Run the script using the MySQL client:
   ```bash
   mysql -u root -p < hospital_db_schemas.sql
   ```
   *(Enter your local MySQL root password when prompted).*

> [!WARNING]
> **Data Reset Warning:** The script begins with `DROP DATABASE IF EXISTS hospital_db;`. Running the script will drop and recreate the database, resetting all tables to the initial sample seed data.

---

## 🔐 Environment Variables & Configuration

When developing backend services (Node.js, Python, Java, etc.) for this project:

1. **Never commit passwords or credentials to GitHub.**
2. Keep your database credentials in a `.env` file in your project root:
   ```env
   DB_HOST=localhost
   DB_PORT=3306
   DB_NAME=hospital_db
   DB_USER=root
   DB_PASSWORD=your_local_password
   ```
3. Make sure `.env` is listed inside `.gitignore`.

---

## 🧪 Verification Queries

After setting up the database, you can test it by running sample queries provided at the bottom of [`hospital_db_schemas.sql`](hospital_db_schemas.sql), for example:

```sql
USE hospital_db;

-- 1. View all appointments with patient and doctor details
SELECT * FROM vw_appointment_details ORDER BY AppointmentDate, AppointmentTime;

-- 2. View patients with pending bill balances
SELECT * FROM vw_bill_balance WHERE Balance > 0;

-- 3. View currently admitted inpatients
SELECT * FROM vw_current_admissions;
```
