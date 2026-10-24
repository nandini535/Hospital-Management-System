-- Hospital Management System - database schema (matches the Flask backend)
-- MySQL 8.0.16+ (CHECK constraints need this version). Run from the project root:
--     mysql -u root -p < sql/schema_v2.sql
--     mysql -u root -p < sql/sample_data.sql
-- WARNING: this script DROPS and recreates hospital_db.

DROP DATABASE IF EXISTS hospital_db;
CREATE DATABASE hospital_db CHARACTER SET utf8mb4;
USE hospital_db;

-- 1. DEPARTMENT
CREATE TABLE Department (
    DeptID   INT AUTO_INCREMENT PRIMARY KEY,
    DeptName VARCHAR(100) NOT NULL UNIQUE,
    Location VARCHAR(100) NOT NULL
) ENGINE=InnoDB;

-- 2. DOCTOR
CREATE TABLE Doctor (
    DoctorID        INT AUTO_INCREMENT PRIMARY KEY,
    DeptID          INT NOT NULL,
    Name            VARCHAR(100) NOT NULL,
    Specialization  VARCHAR(100) NOT NULL,
    Phone           VARCHAR(20) UNIQUE,
    Email           VARCHAR(120) NOT NULL UNIQUE,
    ConsultationFee DECIMAL(10,2) NOT NULL DEFAULT 500.00,
    CONSTRAINT chk_doctor_fee CHECK (ConsultationFee >= 0),
    CONSTRAINT fk_doctor_department FOREIGN KEY (DeptID)
        REFERENCES Department(DeptID) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 3. DOCTOR SCHEDULE (weekly timetable; DayOfWeek 0 = Monday ... 6 = Sunday)
CREATE TABLE DoctorSchedule (
    ScheduleID  INT AUTO_INCREMENT PRIMARY KEY,
    DoctorID    INT NOT NULL,
    DayOfWeek   TINYINT NOT NULL,
    StartTime   TIME NOT NULL,
    EndTime     TIME NOT NULL,
    SlotMinutes INT NOT NULL DEFAULT 30,
    CONSTRAINT chk_sched_day  CHECK (DayOfWeek BETWEEN 0 AND 6),
    CONSTRAINT chk_sched_time CHECK (EndTime > StartTime),
    CONSTRAINT chk_sched_slot CHECK (SlotMinutes BETWEEN 5 AND 120),
    CONSTRAINT fk_sched_doctor FOREIGN KEY (DoctorID)
        REFERENCES Doctor(DoctorID) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;

-- 4. PATIENT (Phone is not unique: family members often share a number)
CREATE TABLE Patient (
    PatientID  INT AUTO_INCREMENT PRIMARY KEY,
    Name       VARCHAR(100) NOT NULL,
    Gender     ENUM('Female','Male','Other','Prefer not to say') NOT NULL,
    DOB        DATE NOT NULL,
    Phone      VARCHAR(20) NULL,
    Address    VARCHAR(255) NULL,
    BloodGroup ENUM('A+','A-','B+','B-','AB+','AB-','O+','O-','Unknown') NULL DEFAULT 'Unknown',
    CreatedAt  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 5. USER ACCOUNT (login for Admin / Doctor / Patient)
CREATE TABLE UserAccount (
    UserID       INT AUTO_INCREMENT PRIMARY KEY,
    Username     VARCHAR(50) NOT NULL UNIQUE,
    PasswordHash VARCHAR(255) NOT NULL,
    Role         ENUM('Admin','Doctor','Patient') NOT NULL,
    Status       ENUM('Active','Pending','Disabled') NOT NULL DEFAULT 'Active',
    DoctorID     INT NULL UNIQUE,
    PatientID    INT NULL UNIQUE,
    CONSTRAINT fk_user_doctor  FOREIGN KEY (DoctorID)
        REFERENCES Doctor(DoctorID)   ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_user_patient FOREIGN KEY (PatientID)
        REFERENCES Patient(PatientID) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;

-- 6. WARD
CREATE TABLE Ward (
    WardID   INT AUTO_INCREMENT PRIMARY KEY,
    DeptID   INT NOT NULL,
    WardName VARCHAR(100) NOT NULL,
    Capacity INT NOT NULL,
    Status   ENUM('Open','Closed','Maintenance') NOT NULL DEFAULT 'Open',
    CONSTRAINT chk_ward_capacity CHECK (Capacity > 0),
    CONSTRAINT uq_ward_name_department UNIQUE (DeptID, WardName),
    CONSTRAINT fk_ward_department FOREIGN KEY (DeptID)
        REFERENCES Department(DeptID) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 7. ROOM
CREATE TABLE Room (
    RoomID     INT AUTO_INCREMENT PRIMARY KEY,
    WardID     INT NOT NULL,
    RoomNumber VARCHAR(20) NOT NULL,
    Type       ENUM('General','Semi-Private','Private','ICU','Emergency') NOT NULL,
    Charge     DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    Status     ENUM('Available','Occupied','Maintenance') NOT NULL DEFAULT 'Available',
    CONSTRAINT chk_room_charge CHECK (Charge >= 0),
    CONSTRAINT uq_room_ward_number UNIQUE (WardID, RoomNumber),
    CONSTRAINT fk_room_ward FOREIGN KEY (WardID)
        REFERENCES Ward(WardID) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 8. NURSE
CREATE TABLE Nurse (
    NurseID INT AUTO_INCREMENT PRIMARY KEY,
    DeptID  INT NOT NULL,
    WardID  INT NOT NULL,
    Name    VARCHAR(100) NOT NULL,
    Phone   VARCHAR(20) NOT NULL UNIQUE,
    Shift   ENUM('Morning','Evening','Night','Rotational') NOT NULL,
    CONSTRAINT fk_nurse_department FOREIGN KEY (DeptID)
        REFERENCES Department(DeptID) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_nurse_ward FOREIGN KEY (WardID)
        REFERENCES Ward(WardID) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 9. APPOINTMENT
-- SlotLock is NULL for cancelled rows, so a cancelled slot can be booked again,
-- while two ACTIVE appointments can never share a doctor/date/time (no double booking).
CREATE TABLE Appointment (
    AppointmentID INT AUTO_INCREMENT PRIMARY KEY,
    PatientID     INT NOT NULL,
    DoctorID      INT NOT NULL,
    `Date`        DATE NOT NULL,
    `Time`        TIME NOT NULL,
    Reason        VARCHAR(255) NULL,
    Status        ENUM('Scheduled','Completed','Cancelled') NOT NULL DEFAULT 'Scheduled',
    SlotLock      TINYINT GENERATED ALWAYS AS (IF(Status = 'Cancelled', NULL, 1)) STORED,
    CreatedAt     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_doctor_active_slot UNIQUE (DoctorID, `Date`, `Time`, SlotLock),
    CONSTRAINT fk_appointment_patient FOREIGN KEY (PatientID)
        REFERENCES Patient(PatientID) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_appointment_doctor FOREIGN KEY (DoctorID)
        REFERENCES Doctor(DoctorID) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 10. MEDICINE
CREATE TABLE Medicine (
    MedicineID INT AUTO_INCREMENT PRIMARY KEY,
    Name       VARCHAR(120) NOT NULL UNIQUE,
    Price      DECIMAL(10,2) NOT NULL,
    Stock      INT NOT NULL DEFAULT 0,
    CONSTRAINT chk_medicine_price CHECK (Price >= 0),
    CONSTRAINT chk_medicine_stock CHECK (Stock >= 0)
) ENGINE=InnoDB;

-- 11. PRESCRIPTION (written by a doctor for a patient)
CREATE TABLE Prescription (
    PrescriptionID INT AUTO_INCREMENT PRIMARY KEY,
    `Date`         DATE NOT NULL,
    Notes          TEXT NULL,
    PatientID      INT NOT NULL,
    DoctorID       INT NOT NULL,
    CONSTRAINT fk_prescription_patient FOREIGN KEY (PatientID)
        REFERENCES Patient(PatientID) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_prescription_doctor FOREIGN KEY (DoctorID)
        REFERENCES Doctor(DoctorID) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 12. PRESCRIPTION ITEM (many-to-many Prescription <-> Medicine)
CREATE TABLE PrescriptionItem (
    ItemID         INT AUTO_INCREMENT PRIMARY KEY,
    PrescriptionID INT NOT NULL,
    MedicineID     INT NOT NULL,
    Dosage         VARCHAR(100) NULL,
    Quantity       INT NOT NULL,
    CONSTRAINT chk_item_quantity CHECK (Quantity > 0),
    CONSTRAINT uq_prescription_medicine UNIQUE (PrescriptionID, MedicineID),
    CONSTRAINT fk_item_prescription FOREIGN KEY (PrescriptionID)
        REFERENCES Prescription(PrescriptionID) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_item_medicine FOREIGN KEY (MedicineID)
        REFERENCES Medicine(MedicineID) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 13. ADMISSION (DischargeDate IS NULL = still admitted)
CREATE TABLE Admission (
    AdmissionID   INT AUTO_INCREMENT PRIMARY KEY,
    PatientID     INT NOT NULL,
    RoomID        INT NOT NULL,
    AdmitDate     DATE NOT NULL,
    DischargeDate DATE NULL,
    CONSTRAINT chk_admission_dates CHECK (DischargeDate IS NULL OR DischargeDate >= AdmitDate),
    CONSTRAINT fk_admission_patient FOREIGN KEY (PatientID)
        REFERENCES Patient(PatientID) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_admission_room FOREIGN KEY (RoomID)
        REFERENCES Room(RoomID) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 14. LAB TEST
CREATE TABLE LabTest (
    TestID    INT AUTO_INCREMENT PRIMARY KEY,
    PatientID INT NOT NULL,
    TestName  VARCHAR(120) NOT NULL,
    Result    TEXT NULL,
    TestDate  DATE NOT NULL,
    CONSTRAINT fk_lab_patient FOREIGN KEY (PatientID)
        REFERENCES Patient(PatientID) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 15. BILL (at most one bill per admission and one per appointment)
CREATE TABLE Bill (
    BillID        INT AUTO_INCREMENT PRIMARY KEY,
    PatientID     INT NOT NULL,
    AdmissionID   INT NULL UNIQUE,
    AppointmentID INT NULL UNIQUE,
    Amount        DECIMAL(12,2) NOT NULL,
    `Date`        DATE NOT NULL,
    PaymentMode   ENUM('Cash','Card','UPI','Insurance') NOT NULL DEFAULT 'Cash',
    Status        ENUM('Pending','Paid') NOT NULL DEFAULT 'Pending',
    CONSTRAINT chk_bill_amount CHECK (Amount >= 0),
    CONSTRAINT fk_bill_patient FOREIGN KEY (PatientID)
        REFERENCES Patient(PatientID) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_bill_appointment FOREIGN KEY (AppointmentID)
        REFERENCES Appointment(AppointmentID) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_bill_admission FOREIGN KEY (AdmissionID)
        REFERENCES Admission(AdmissionID) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Indexes for frequent searches and joins
CREATE INDEX idx_doctor_specialization   ON Doctor(Specialization);
CREATE INDEX idx_patient_name            ON Patient(Name);
CREATE INDEX idx_appointment_date_status ON Appointment(`Date`, Status);
CREATE INDEX idx_appointment_patient     ON Appointment(PatientID, `Date`);
CREATE INDEX idx_prescription_patient    ON Prescription(PatientID, `Date`);
CREATE INDEX idx_admission_patient       ON Admission(PatientID, DischargeDate);
CREATE INDEX idx_lab_patient_date        ON LabTest(PatientID, TestDate);
CREATE INDEX idx_bill_patient_date       ON Bill(PatientID, `Date`);

-- Views (handy for reports and the frontend)
CREATE VIEW vw_appointment_details AS
SELECT a.AppointmentID, a.`Date`, a.`Time`, a.Status, a.Reason,
       p.PatientID, p.Name AS PatientName,
       d.DoctorID, d.Name AS DoctorName, d.Specialization, dep.DeptName
FROM Appointment a
JOIN Patient p ON p.PatientID = a.PatientID
JOIN Doctor d ON d.DoctorID = a.DoctorID
JOIN Department dep ON dep.DeptID = d.DeptID;

CREATE VIEW vw_current_admissions AS
SELECT ad.AdmissionID, p.PatientID, p.Name AS PatientName, r.RoomNumber, r.Type AS RoomType,
       w.WardName, ad.AdmitDate, DATEDIFF(CURRENT_DATE, ad.AdmitDate) AS DaysAdmitted
FROM Admission ad
JOIN Patient p ON p.PatientID = ad.PatientID
JOIN Room r ON r.RoomID = ad.RoomID
JOIN Ward w ON w.WardID = r.WardID
WHERE ad.DischargeDate IS NULL;

-- Trigger: a prescription item can never ask for more than the stock on hand.
DELIMITER //
CREATE TRIGGER trg_check_medicine_stock
BEFORE INSERT ON PrescriptionItem
FOR EACH ROW
BEGIN
    DECLARE v_stock INT;
    SELECT Stock INTO v_stock FROM Medicine WHERE MedicineID = NEW.MedicineID;
    IF v_stock IS NOT NULL AND NEW.Quantity > v_stock THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Prescription quantity exceeds available medicine stock';
    END IF;
END//
DELIMITER ;
