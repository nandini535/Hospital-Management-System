-- Hospital Management System DBMS Project
-- MySQL 8.0+ | Run this entire script in MySQL Workbench.
-- Test database: hospital_db
-- IMPORTANT: This script drops hospital_db if it already exists.

--DROP DATABASE IF EXISTS hospital_db;
CREATE DATABASE hospital_db CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE hospital_db;

-- 1. DEPARTMENT
CREATE TABLE Department (
    DeptID INT AUTO_INCREMENT PRIMARY KEY,
    DeptName VARCHAR(100) NOT NULL UNIQUE,
    Location VARCHAR(100) NOT NULL
) ENGINE=InnoDB;

-- 2. DOCTOR
CREATE TABLE Doctor (
    DoctorID INT AUTO_INCREMENT PRIMARY KEY,
    DeptID INT NOT NULL,
    Name VARCHAR(100) NOT NULL,
    Specialization VARCHAR(100) NOT NULL,
    Phone VARCHAR(20) UNIQUE,
    Email VARCHAR(120) NOT NULL UNIQUE,
    CONSTRAINT fk_doctor_department FOREIGN KEY (DeptID)
        REFERENCES Department(DeptID)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 3. PATIENT
CREATE TABLE Patient (
    PatientID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Gender ENUM('Female','Male','Other','Prefer not to say') NOT NULL,
    DOB DATE NOT NULL,
    Phone VARCHAR(20) NOT NULL UNIQUE,
    Address VARCHAR(255) NOT NULL,
    BloodGroup ENUM('A+','A-','B+','B-','AB+','AB-','O+','O-','Unknown') DEFAULT 'Unknown',
    CreatedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 4. WARD
CREATE TABLE Ward (
    WardID INT AUTO_INCREMENT PRIMARY KEY,
    DeptID INT NOT NULL,
    WardName VARCHAR(100) NOT NULL,
    Capacity INT NOT NULL,
    Status ENUM('Open','Closed','Maintenance') NOT NULL DEFAULT 'Open',
    CONSTRAINT chk_ward_capacity CHECK (Capacity > 0),
    CONSTRAINT uq_ward_name_department UNIQUE (DeptID, WardName),
    CONSTRAINT fk_ward_department FOREIGN KEY (DeptID)
        REFERENCES Department(DeptID)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 5. ROOM
CREATE TABLE Room (
    RoomID INT AUTO_INCREMENT PRIMARY KEY,
    WardID INT NOT NULL,
    RoomNumber VARCHAR(20) NOT NULL,
    Type ENUM('General','Semi-Private','Private','ICU','Emergency') NOT NULL,
    Charge DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    Status ENUM('Available','Occupied','Maintenance') NOT NULL DEFAULT 'Available',
    CONSTRAINT chk_room_charge CHECK (Charge >= 0),
    CONSTRAINT uq_room_ward_number UNIQUE (WardID, RoomNumber),
    CONSTRAINT fk_room_ward FOREIGN KEY (WardID)
        REFERENCES Ward(WardID)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 6. NURSE
CREATE TABLE Nurse (
    NurseID INT AUTO_INCREMENT PRIMARY KEY,
    DeptID INT NOT NULL,
    WardID INT NOT NULL,
    Name VARCHAR(100) NOT NULL,
    Phone VARCHAR(20) NOT NULL UNIQUE,
    Shift ENUM('Morning','Evening','Night','Rotational') NOT NULL,
    CONSTRAINT fk_nurse_department FOREIGN KEY (DeptID)
        REFERENCES Department(DeptID)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_nurse_ward FOREIGN KEY (WardID)
        REFERENCES Ward(WardID)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 7. APPOINTMENT
CREATE TABLE Appointment (
    AppointmentID INT AUTO_INCREMENT PRIMARY KEY,
    PatientID INT NOT NULL,
    DoctorID INT NOT NULL,
    AppointmentDate DATE NOT NULL,
    AppointmentTime TIME NOT NULL,
    Reason VARCHAR(255),
    Status ENUM('Booked','Confirmed','Completed','Cancelled','No-show') NOT NULL DEFAULT 'Booked',
    CreatedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_appointment_patient FOREIGN KEY (PatientID)
        REFERENCES Patient(PatientID)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_appointment_doctor FOREIGN KEY (DoctorID)
        REFERENCES Doctor(DoctorID)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT uq_doctor_slot UNIQUE (DoctorID, AppointmentDate, AppointmentTime)
) ENGINE=InnoDB;

-- 8. PRESCRIPTION
-- One prescription can be linked to an appointment; an appointment can have zero or one prescription.
CREATE TABLE Prescription (
    PrescriptionID INT AUTO_INCREMENT PRIMARY KEY,
    AppointmentID INT NOT NULL UNIQUE,
    PrescriptionDate DATE NOT NULL,
    Notes TEXT,
    CONSTRAINT fk_prescription_appointment FOREIGN KEY (AppointmentID)
        REFERENCES Appointment(AppointmentID)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 9. MEDICINE
CREATE TABLE Medicine (
    MedicineID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(120) NOT NULL UNIQUE,
    Price DECIMAL(10,2) NOT NULL,
    Stock INT NOT NULL DEFAULT 0,
    CONSTRAINT chk_medicine_price CHECK (Price >= 0),
    CONSTRAINT chk_medicine_stock CHECK (Stock >= 0)
) ENGINE=InnoDB;

-- 10. PRESCRIPTION ITEM (resolves many-to-many Prescription <-> Medicine)
CREATE TABLE PrescriptionItem (
    ItemID INT AUTO_INCREMENT PRIMARY KEY,
    PrescriptionID INT NOT NULL,
    MedicineID INT NOT NULL,
    Dosage VARCHAR(100) NOT NULL,
    Quantity INT NOT NULL,
    Instructions VARCHAR(255),
    CONSTRAINT chk_prescription_quantity CHECK (Quantity > 0),
    CONSTRAINT uq_prescription_medicine UNIQUE (PrescriptionID, MedicineID),
    CONSTRAINT fk_item_prescription FOREIGN KEY (PrescriptionID)
        REFERENCES Prescription(PrescriptionID)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_item_medicine FOREIGN KEY (MedicineID)
        REFERENCES Medicine(MedicineID)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 11. ADMISSION
CREATE TABLE Admission (
    AdmissionID INT AUTO_INCREMENT PRIMARY KEY,
    PatientID INT NOT NULL,
    RoomID INT NOT NULL,
    AdmitDate DATE NOT NULL,
    DischargeDate DATE NULL,
    Status ENUM('Admitted','Discharged','Transferred') NOT NULL DEFAULT 'Admitted',
    CONSTRAINT chk_admission_dates CHECK (DischargeDate IS NULL OR DischargeDate >= AdmitDate),
    CONSTRAINT fk_admission_patient FOREIGN KEY (PatientID)
        REFERENCES Patient(PatientID)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_admission_room FOREIGN KEY (RoomID)
        REFERENCES Room(RoomID)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 12. LAB TEST
CREATE TABLE LabTest (
    TestID INT AUTO_INCREMENT PRIMARY KEY,
    PatientID INT NOT NULL,
    AppointmentID INT NULL,
    TestName VARCHAR(120) NOT NULL,
    Result TEXT,
    TestDate DATE NOT NULL,
    Status ENUM('Ordered','In Progress','Completed','Cancelled') NOT NULL DEFAULT 'Ordered',
    CONSTRAINT fk_lab_patient FOREIGN KEY (PatientID)
        REFERENCES Patient(PatientID)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_lab_appointment FOREIGN KEY (AppointmentID)
        REFERENCES Appointment(AppointmentID)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

-- 13. BILL
CREATE TABLE Bill (
    BillID INT AUTO_INCREMENT PRIMARY KEY,
    PatientID INT NOT NULL,
    AppointmentID INT NULL,
    AdmissionID INT NULL,
    Amount DECIMAL(12,2) NOT NULL,
    BillDate DATE NOT NULL,
    Status ENUM('Unpaid','Partially Paid','Paid','Cancelled') NOT NULL DEFAULT 'Unpaid',
    CONSTRAINT chk_bill_amount CHECK (Amount >= 0),
    CONSTRAINT fk_bill_patient FOREIGN KEY (PatientID)
        REFERENCES Patient(PatientID)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_bill_appointment FOREIGN KEY (AppointmentID)
        REFERENCES Appointment(AppointmentID)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_bill_admission FOREIGN KEY (AdmissionID)
        REFERENCES Admission(AdmissionID)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 14. PAYMENT (a bill can have multiple partial payments)
CREATE TABLE Payment (
    PaymentID INT AUTO_INCREMENT PRIMARY KEY,
    BillID INT NOT NULL,
    PaymentDate DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    Amount DECIMAL(12,2) NOT NULL,
    PaymentMode ENUM('Cash','Card','UPI','Net Banking','Insurance') NOT NULL,
    ReferenceNo VARCHAR(100) UNIQUE,
    CONSTRAINT chk_payment_amount CHECK (Amount > 0),
    CONSTRAINT fk_payment_bill FOREIGN KEY (BillID)
        REFERENCES Bill(BillID)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Indexes for frequent searching and joining
CREATE INDEX idx_doctor_specialization ON Doctor(Specialization);
CREATE INDEX idx_patient_name ON Patient(Name);
CREATE INDEX idx_appointment_date_status ON Appointment(AppointmentDate, Status);
CREATE INDEX idx_appointment_patient_date ON Appointment(PatientID, AppointmentDate);
CREATE INDEX idx_admission_patient_status ON Admission(PatientID, Status);
CREATE INDEX idx_lab_patient_date ON LabTest(PatientID, TestDate);
CREATE INDEX idx_bill_patient_date ON Bill(PatientID, BillDate);
CREATE INDEX idx_payment_bill_date ON Payment(BillID, PaymentDate);

-- Sample data
INSERT INTO Department (DeptName, Location) VALUES
('Cardiology','Block A'), ('Neurology','Block B'), ('General Medicine','Block A'),
('Laboratory','Block C');

INSERT INTO Doctor (DeptID, Name, Specialization, Phone, Email) VALUES
(1,'Dr Asha Kulkarni','Cardiology','9000000001','asha.kulkarni@example.com'),
(2,'Dr Rahul Deshmukh','Neurology','9000000002','rahul.deshmukh@example.com'),
(3,'Dr Meera Shah','General Medicine','9000000003','meera.shah@example.com');

INSERT INTO Patient (Name, Gender, DOB, Phone, Address, BloodGroup) VALUES
('Ananya Patil','Female','2003-04-12','9100000001','Pune, Maharashtra','O+'),
('Rohan Joshi','Male','1998-09-23','9100000002','Pimpri, Maharashtra','B+'),
('Sana Khan','Female','1987-01-05','9100000003','Pune, Maharashtra','AB+');

INSERT INTO Ward (DeptID, WardName, Capacity, Status) VALUES
(1,'Cardiology Ward',20,'Open'), (2,'Neurology Ward',15,'Open'),
(3,'General Ward',30,'Open');

INSERT INTO Room (WardID, RoomNumber, Type, Charge, Status) VALUES
(1,'A-101','Private',2500.00,'Available'),
(1,'A-102','General',900.00,'Available'),
(2,'B-201','ICU',5000.00,'Available'),
(3,'C-101','Semi-Private',1500.00,'Available');

INSERT INTO Nurse (DeptID, WardID, Name, Phone, Shift) VALUES
(1,1,'Kavita More','9200000001','Morning'),
(2,2,'Priya Nair','9200000002','Night'),
(3,3,'Sneha Pawar','9200000003','Evening');

INSERT INTO Appointment (PatientID, DoctorID, AppointmentDate, AppointmentTime, Reason, Status) VALUES
(1,1,'2026-11-02','10:00:00','Routine heart check-up','Confirmed'),
(2,2,'2026-11-02','11:00:00','Recurring headache','Booked'),
(3,3,'2026-11-03','09:30:00','General consultation','Completed');

INSERT INTO Prescription (AppointmentID, PrescriptionDate, Notes) VALUES
(3,'2026-11-03','Take medicines after food and follow up in one week');

INSERT INTO Medicine (Name, Price, Stock) VALUES
('Paracetamol 500mg',2.50,500),
('Vitamin D3',15.00,120),
('Amlodipine 5mg',8.00,200),
('Antacid tablets',4.00,300);

INSERT INTO PrescriptionItem (PrescriptionID, MedicineID, Dosage, Quantity, Instructions) VALUES
(1,1,'1 tablet','10','After food when needed'),
(1,2,'1 capsule weekly','4','Take after a meal');

INSERT INTO Admission (PatientID, RoomID, AdmitDate, DischargeDate, Status) VALUES
(2,3,'2026-10-20',NULL,'Admitted'),
(3,4,'2026-10-10','2026-10-12','Discharged');

INSERT INTO LabTest (PatientID, AppointmentID, TestName, Result, TestDate, Status) VALUES
(1,1,'Lipid Profile',NULL,'2026-11-02','Ordered'),
(2,2,'Complete Blood Count','Within expected range','2026-10-15','Completed'),
(3,3,'Blood Glucose','92 mg/dL','2026-11-03','Completed');

INSERT INTO Bill (PatientID, AppointmentID, AdmissionID, Amount, BillDate, Status) VALUES
(1,1,NULL,800.00,'2026-11-02','Partially Paid'),
(2,NULL,1,12000.00,'2026-10-20','Unpaid'),
(3,3,2,2200.00,'2026-10-12','Paid');

INSERT INTO Payment (BillID, Amount, PaymentMode, ReferenceNo) VALUES
(1,300.00,'UPI','UPI-DEMO-001'),
(3,2200.00,'Card','CARD-DEMO-001');

-- Views: reusable summaries for reports and the future frontend
CREATE VIEW vw_appointment_details AS
SELECT a.AppointmentID, a.AppointmentDate, a.AppointmentTime, a.Status,
       p.PatientID, p.Name AS PatientName,
       d.DoctorID, d.Name AS DoctorName, d.Specialization,
       dep.DeptName
FROM Appointment a
JOIN Patient p ON p.PatientID = a.PatientID
JOIN Doctor d ON d.DoctorID = a.DoctorID
JOIN Department dep ON dep.DeptID = d.DeptID;

CREATE VIEW vw_bill_balance AS
SELECT b.BillID, b.PatientID, p.Name AS PatientName, b.Amount AS BillAmount,
       COALESCE(SUM(pay.Amount), 0) AS AmountPaid,
       b.Amount - COALESCE(SUM(pay.Amount), 0) AS Balance,
       b.Status
FROM Bill b
JOIN Patient p ON p.PatientID = b.PatientID
LEFT JOIN Payment pay ON pay.BillID = b.BillID
GROUP BY b.BillID, b.PatientID, p.Name, b.Amount, b.Status;

CREATE VIEW vw_current_admissions AS
SELECT ad.AdmissionID, p.Name AS PatientName, r.RoomNumber, r.Type AS RoomType,
       w.WardName, ad.AdmitDate, DATEDIFF(COALESCE(ad.DischargeDate, CURRENT_DATE), ad.AdmitDate) AS DaysAdmitted
FROM Admission ad
JOIN Patient p ON p.PatientID = ad.PatientID
JOIN Room r ON r.RoomID = ad.RoomID
JOIN Ward w ON w.WardID = r.WardID
WHERE ad.Status = 'Admitted';

-- Example stored procedure: safely record a payment and update bill status.
DELIMITER //
CREATE PROCEDURE RecordPayment(
    IN p_BillID INT,
    IN p_Amount DECIMAL(12,2),
    IN p_Mode VARCHAR(30),
    IN p_ReferenceNo VARCHAR(100)
)
BEGIN
    DECLARE v_BillAmount DECIMAL(12,2);
    DECLARE v_Paid DECIMAL(12,2);
    DECLARE v_NewPaid DECIMAL(12,2);

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    SELECT Amount INTO v_BillAmount
    FROM Bill WHERE BillID = p_BillID FOR UPDATE;

    IF v_BillAmount IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Bill does not exist';
    END IF;

    SELECT COALESCE(SUM(Amount), 0) INTO v_Paid
    FROM Payment WHERE BillID = p_BillID;

    IF p_Amount <= 0 OR (v_Paid + p_Amount) > v_BillAmount THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid payment amount';
    END IF;

    INSERT INTO Payment (BillID, Amount, PaymentMode, ReferenceNo)
    VALUES (p_BillID, p_Amount, p_Mode, p_ReferenceNo);

    SET v_NewPaid = v_Paid + p_Amount;

    UPDATE Bill
    SET Status = CASE
        WHEN v_NewPaid = v_BillAmount THEN 'Paid'
        WHEN v_NewPaid > 0 THEN 'Partially Paid'
        ELSE 'Unpaid'
    END
    WHERE BillID = p_BillID;

    COMMIT;
END//
DELIMITER ;

-- Example trigger: prevent a medicine item quantity exceeding current stock.
DELIMITER //
CREATE TRIGGER trg_check_medicine_stock
BEFORE INSERT ON PrescriptionItem
FOR EACH ROW
BEGIN
    DECLARE v_Stock INT;
    SELECT Stock INTO v_Stock FROM Medicine WHERE MedicineID = NEW.MedicineID;
    IF NEW.Quantity > v_Stock THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Prescription quantity exceeds available medicine stock';
    END IF;
END//
DELIMITER ;

-- Useful test queries (run individually after the script finishes):
-- 1. Appointments with doctor, patient and department
-- SELECT * FROM vw_appointment_details ORDER BY AppointmentDate, AppointmentTime;
-- 2. Patients with outstanding balances
-- SELECT * FROM vw_bill_balance WHERE Balance > 0;
-- 3. Current inpatients
-- SELECT * FROM vw_current_admissions;
-- 4. Doctors and their appointment counts (including doctors with no appointments)
-- SELECT d.DoctorID, d.Name, COUNT(a.AppointmentID) AS AppointmentCount
-- FROM Doctor d LEFT JOIN Appointment a ON a.DoctorID=d.DoctorID
-- GROUP BY d.DoctorID, d.Name ORDER BY AppointmentCount DESC;
-- 5. Medicine stock below 100
-- SELECT * FROM Medicine WHERE Stock < 100 ORDER BY Stock;
-- 6. Monthly revenue
-- SELECT DATE_FORMAT(PaymentDate, '%Y-%m') AS Month, SUM(Amount) AS Revenue
-- FROM Payment GROUP BY DATE_FORMAT(PaymentDate, '%Y-%m') ORDER BY Month;
-- 7. Patients who have had more than one appointment (HAVING)
-- SELECT p.PatientID, p.Name, COUNT(*) AS Visits
-- FROM Patient p JOIN Appointment a ON a.PatientID=p.PatientID
-- GROUP BY p.PatientID, p.Name HAVING COUNT(*) > 1;
