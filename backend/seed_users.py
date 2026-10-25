"""Create login accounts.
  python seed_users.py --admin-only        -> just the admin   (username: admin, password: Admin@123)
  python seed_users.py                     -> admin + a demo login for EVERY existing doctor and patient
Demo passwords:  Doctor@123  /  Patient@123.  Usernames: doctor<ID>, patient<ID>.  CHANGE THEM before any real use."""
import sys

from werkzeug.security import generate_password_hash

import db


def main():
    if not db.query("SELECT 1 FROM UserAccount WHERE Username='admin'", one=True):
        db.execute("INSERT INTO UserAccount (Username, PasswordHash, Role, Status) VALUES ('admin', %s, 'Admin', 'Active')",
                   (generate_password_hash("Admin@123"),))
        print("created admin / Admin@123")
    if "--admin-only" in sys.argv:
        return
    for d in db.query("SELECT DoctorID FROM Doctor WHERE DoctorID NOT IN (SELECT DoctorID FROM UserAccount WHERE DoctorID IS NOT NULL)"):
        db.execute("INSERT INTO UserAccount (Username, PasswordHash, Role, Status, DoctorID) VALUES (%s,%s,'Doctor','Active',%s)",
                   (f"doctor{d['DoctorID']}", generate_password_hash("Doctor@123"), d["DoctorID"]))
        print(f"created doctor{d['DoctorID']} / Doctor@123")
    for p in db.query("SELECT PatientID FROM Patient WHERE PatientID NOT IN (SELECT PatientID FROM UserAccount WHERE PatientID IS NOT NULL)"):
        db.execute("INSERT INTO UserAccount (Username, PasswordHash, Role, Status, PatientID) VALUES (%s,%s,'Patient','Active',%s)",
                   (f"patient{p['PatientID']}", generate_password_hash("Patient@123"), p["PatientID"]))
        print(f"created patient{p['PatientID']} / Patient@123")


if __name__ == "__main__":
    main()
