-- Demo data. Run after schema_v2.sql:  mysql -u root -p < sql/sample_data.sql
USE hospital_db;

INSERT INTO Department (DeptName, Location) VALUES
('Cardiology','Block A'), ('Neurology','Block B'), ('General Medicine','Block A'), ('Laboratory','Block C');

INSERT INTO Doctor (DeptID, Name, Specialization, Phone, Email, ConsultationFee) VALUES
(1,'Dr Asha Kulkarni','Cardiology','9000000001','asha.kulkarni@example.com',800.00),
(2,'Dr Rahul Deshmukh','Neurology','9000000002','rahul.deshmukh@example.com',700.00),
(3,'Dr Meera Shah','General Medicine','9000000003','meera.shah@example.com',500.00);

-- Mon-Fri, 09:00-13:00, 30-minute slots for every demo doctor
INSERT INTO DoctorSchedule (DoctorID, DayOfWeek, StartTime, EndTime, SlotMinutes)
SELECT d.DoctorID, n.dow, '09:00:00', '13:00:00', 30
FROM Doctor d JOIN (SELECT 0 AS dow UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4) n;

INSERT INTO Patient (Name, Gender, DOB, Phone, Address, BloodGroup) VALUES
('Ananya Patil','Female','2003-04-12','9100000001','Pune, Maharashtra','O+'),
('Rohan Joshi','Male','1998-09-23','9100000002','Pimpri, Maharashtra','B+'),
('Sana Khan','Female','1987-01-05','9100000003','Pune, Maharashtra','AB+');

INSERT INTO Ward (DeptID, WardName, Capacity, Status) VALUES
(1,'Cardiology Ward',20,'Open'), (2,'Neurology Ward',15,'Open'), (3,'General Ward',30,'Open');

INSERT INTO Room (WardID, RoomNumber, Type, Charge, Status) VALUES
(1,'A-101','Private',2500.00,'Available'),
(1,'A-102','General',900.00,'Available'),
(2,'B-201','ICU',5000.00,'Available'),
(3,'C-101','Semi-Private',1500.00,'Available');

INSERT INTO Nurse (DeptID, WardID, Name, Phone, Shift) VALUES
(1,1,'Kavita More','9200000001','Morning'),
(2,2,'Priya Nair','9200000002','Night'),
(3,3,'Sneha Pawar','9200000003','Evening');

INSERT INTO Medicine (Name, Price, Stock) VALUES
('Paracetamol 500mg',2.50,500), ('Vitamin D3',15.00,120), ('Amlodipine 5mg',8.00,200), ('Antacid tablets',4.00,300);

-- A finished past visit, with a prescription, lab test and paid bill
INSERT INTO Appointment (PatientID, DoctorID, `Date`, `Time`, Reason, Status) VALUES
(3,3,CURDATE() - INTERVAL 10 DAY,'09:30:00','General consultation','Completed');
INSERT INTO Prescription (`Date`, Notes, PatientID, DoctorID) VALUES
(CURDATE() - INTERVAL 10 DAY,'Take medicines after food and follow up in one week',3,3);
INSERT INTO PrescriptionItem (PrescriptionID, MedicineID, Dosage, Quantity) VALUES
(1,1,'1 tablet when needed',10), (1,2,'1 capsule weekly',4);
INSERT INTO LabTest (PatientID, TestName, Result, TestDate) VALUES
(3,'Blood Glucose','92 mg/dL',CURDATE() - INTERVAL 10 DAY);
INSERT INTO Bill (PatientID, AppointmentID, Amount, `Date`, PaymentMode, Status) VALUES
(3,1,500.00,CURDATE() - INTERVAL 10 DAY,'Card','Paid');
