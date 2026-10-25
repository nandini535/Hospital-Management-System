"""Table metadata for the generic (admin) CRUD endpoints. `cols` = writable columns.
UserAccount is deliberately NOT here so password hashes are never exposed."""

TABLES = {
    "departments":  {"name": "Department",   "pk": "DeptID",         "cols": ["DeptName", "Location"]},
    "doctors":      {"name": "Doctor",       "pk": "DoctorID",       "cols": ["Name", "Specialization", "Phone", "Email", "ConsultationFee", "DeptID"]},
    "patients":     {"name": "Patient",      "pk": "PatientID",      "cols": ["Name", "Gender", "DOB", "Phone", "Address", "BloodGroup"]},
    "appointments": {"name": "Appointment",  "pk": "AppointmentID",  "cols": ["Date", "Time", "Status", "Reason", "PatientID", "DoctorID"]},
    "wards":        {"name": "Ward",         "pk": "WardID",         "cols": ["DeptID", "WardName", "Capacity", "Status"]},
    "rooms":        {"name": "Room",         "pk": "RoomID",         "cols": ["WardID", "RoomNumber", "Type", "Charge", "Status"]},
    "nurses":       {"name": "Nurse",        "pk": "NurseID",        "cols": ["Name", "Phone", "Shift", "DeptID", "WardID"]},
    "admissions":   {"name": "Admission",    "pk": "AdmissionID",    "cols": ["PatientID", "RoomID", "AdmitDate", "DischargeDate"]},
    "prescriptions":{"name": "Prescription", "pk": "PrescriptionID", "cols": ["Date", "Notes", "PatientID", "DoctorID"]},
    "medicines":    {"name": "Medicine",     "pk": "MedicineID",     "cols": ["Name", "Price", "Stock"]},
    "prescription-items": {"name": "PrescriptionItem", "pk": "ItemID", "cols": ["PrescriptionID", "MedicineID", "Dosage", "Quantity"]},
    "lab-tests":    {"name": "LabTest",      "pk": "TestID",         "cols": ["PatientID", "TestName", "Result", "TestDate"]},
    "bills":        {"name": "Bill",         "pk": "BillID",         "cols": ["PatientID", "AdmissionID", "AppointmentID", "Amount", "Date", "PaymentMode", "Status"]},
}
