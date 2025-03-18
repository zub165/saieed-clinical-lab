from main import User, Patient, LabTest, Order, Result, get_password_hash, engine, Base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import random

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def init_database():
    # Drop all tables and recreate them
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    print("Tables recreated")
    
    # Create admin user
    admin_password = get_password_hash("admin123")
    admin = User(username="admin", hashed_password=admin_password, role="admin")
    db.add(admin)
    db.commit()
    print("Admin user created")
    
    # Create technician user
    tech_password = get_password_hash("tech123")
    tech = User(username="technician", hashed_password=tech_password, role="technician")
    db.add(tech)
    db.commit()
    print("Technician user created")
    
    # Create doctor user
    doctor_password = get_password_hash("doctor123")
    doctor = User(username="doctor", hashed_password=doctor_password, role="doctor")
    db.add(doctor)
    db.commit()
    print("Doctor user created")
    
    # Create sample patients
    patients = [
        {"name": "John Smith", "dob": "1980-05-15", "gender": "Male", "contact": "123-456-7890"},
        {"name": "Sarah Johnson", "dob": "1992-09-23", "gender": "Female", "contact": "234-567-8901"},
        {"name": "Michael Brown", "dob": "1975-11-30", "gender": "Male", "contact": "345-678-9012"},
        {"name": "Emily Davis", "dob": "1988-02-14", "gender": "Female", "contact": "456-789-0123"},
        {"name": "David Wilson", "dob": "1965-07-10", "gender": "Male", "contact": "567-890-1234"}
    ]
    
    for patient_data in patients:
        patient = Patient(**patient_data)
        db.add(patient)
    
    db.commit()
    print("Sample patients created")
    
    # Create sample lab tests
    lab_tests = [
        {"name": "Complete Blood Count", "normal_range": "4.5-11", "unit": "10^9/L"},
        {"name": "Glucose", "normal_range": "70-99", "unit": "mg/dL"},
        {"name": "Hemoglobin A1C", "normal_range": "4.0-5.6", "unit": "%"},
        {"name": "Cholesterol", "normal_range": "125-200", "unit": "mg/dL"},
        {"name": "HDL Cholesterol", "normal_range": "40-60", "unit": "mg/dL"},
        {"name": "LDL Cholesterol", "normal_range": "0-100", "unit": "mg/dL"},
        {"name": "Triglycerides", "normal_range": "0-150", "unit": "mg/dL"},
        {"name": "Thyroid Stimulating Hormone", "normal_range": "0.4-4.0", "unit": "mIU/L"},
        {"name": "Vitamin D", "normal_range": "30-100", "unit": "ng/mL"},
        {"name": "Vitamin B12", "normal_range": "200-900", "unit": "pg/mL"}
    ]
    
    for test_data in lab_tests:
        test = LabTest(**test_data)
        db.add(test)
    
    db.commit()
    print("Sample lab tests created")
    
    # Get all patients and lab tests
    patients = db.query(Patient).all()
    lab_tests = db.query(LabTest).all()
    doctor = db.query(User).filter(User.role == "doctor").first()
    
    # Create 10 orders with varying dates
    for i in range(10):
        # Randomly select a patient
        patient = random.choice(patients)
        
        # Create order with a date within the last 30 days
        days_ago = random.randint(0, 30)
        order_date = datetime.utcnow() - timedelta(days=days_ago)
        
        order = Order(
            patient_id=patient.id,
            ordered_by=doctor.id,
            date_ordered=order_date,
            status="completed" if days_ago > 5 else "pending"
        )
        db.add(order)
        db.flush()  # Flush to get the order ID
        
        # Create 3-5 test results for this order
        num_tests = random.randint(3, 5)
        selected_tests = random.sample(lab_tests, num_tests)
        
        for test in selected_tests:
            # Generate a random result value within or slightly outside normal range
            normal_range = test.normal_range
            result_value = None
            
            if "-" in normal_range:
                min_val, max_val = map(float, normal_range.split("-"))
                # 80% chance of normal value, 20% chance of abnormal
                if random.random() < 0.8:
                    result_value = round(random.uniform(min_val, max_val), 1)
                else:
                    # Create abnormal value (either below min or above max)
                    if random.random() < 0.5:
                        result_value = round(random.uniform(min_val - 10, min_val), 1)
                    else:
                        result_value = round(random.uniform(max_val, max_val + 10), 1)
            else:
                # Default value if range format is not recognized
                result_value = round(random.uniform(50, 150), 1)
            
            result = Result(
                order_id=order.id,
                test_id=test.id,
                result_value=result_value,
                unit=test.unit,
                reference_range=test.normal_range,
                status="final"
            )
            db.add(result)
    
    db.commit()
    print("Sample orders and results created")
    
    print("Database initialization complete")

if __name__ == "__main__":
    init_database() 