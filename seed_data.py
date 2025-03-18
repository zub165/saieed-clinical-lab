"""
This script adds sample data to the database for testing purposes.
Run it with: python seed_data.py
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from main import Base, User, Patient, LabTest, Order, Result
from passlib.context import CryptContext
from datetime import datetime, timedelta
import random

# Load environment variables
load_dotenv()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+mysqlconnector://username:password@localhost/saieed_lab")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def seed_data():
    db = SessionLocal()
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Add admin user if none exists
    admin_count = db.query(User).filter(User.role == "admin").count()
    if admin_count == 0:
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "password123")
        
        print(f"Creating admin user: {admin_username}")
        admin_user = User(
            username=admin_username,
            hashed_password=get_password_hash(admin_password),
            role="admin"
        )
        db.add(admin_user)
        db.commit()
        print("Admin user created successfully")
    
    # Define lab tests by category
    lab_tests_by_category = {
        "Chemistry": [
            {"name": "Glucose", "normal_range": "65-99", "unit": "mg/dL"},
            {"name": "Hemoglobin A1c", "normal_range": "4.0-5.6", "unit": "%"},
            {"name": "Total Cholesterol", "normal_range": "125-200", "unit": "mg/dL"},
            {"name": "HDL Cholesterol", "normal_range": "40-60", "unit": "mg/dL"},
            {"name": "LDL Cholesterol", "normal_range": "0-99", "unit": "mg/dL"},
            {"name": "Triglycerides", "normal_range": "0-149", "unit": "mg/dL"},
            {"name": "Sodium", "normal_range": "136-145", "unit": "mmol/L"},
            {"name": "Potassium", "normal_range": "3.5-5.1", "unit": "mmol/L"},
            {"name": "Chloride", "normal_range": "98-107", "unit": "mmol/L"},
            {"name": "CO2", "normal_range": "21-30", "unit": "mmol/L"},
            {"name": "Calcium", "normal_range": "8.5-10.2", "unit": "mg/dL"},
            {"name": "Blood Urea Nitrogen", "normal_range": "7-20", "unit": "mg/dL"},
            {"name": "Creatinine", "normal_range": "0.6-1.2", "unit": "mg/dL"},
            {"name": "Estimated GFR", "normal_range": ">60", "unit": "mL/min/1.73m²"},
            {"name": "ALT", "normal_range": "7-56", "unit": "U/L"},
            {"name": "AST", "normal_range": "10-40", "unit": "U/L"},
            {"name": "Alkaline Phosphatase", "normal_range": "44-147", "unit": "U/L"},
            {"name": "Total Bilirubin", "normal_range": "0.1-1.2", "unit": "mg/dL"},
            {"name": "Albumin", "normal_range": "3.5-5.0", "unit": "g/dL"},
            {"name": "Total Protein", "normal_range": "6.0-8.3", "unit": "g/dL"}
        ],
        "Hematology": [
            {"name": "White Blood Cell Count", "normal_range": "4.5-11.0", "unit": "10³/µL"},
            {"name": "Red Blood Cell Count", "normal_range": "4.2-5.8", "unit": "10⁶/µL"},
            {"name": "Hemoglobin", "normal_range": "13.5-17.5", "unit": "g/dL"},
            {"name": "Hematocrit", "normal_range": "38.8-50.0", "unit": "%"},
            {"name": "Mean Corpuscular Volume", "normal_range": "80-96", "unit": "fL"},
            {"name": "Mean Corpuscular Hemoglobin", "normal_range": "27-33", "unit": "pg"},
            {"name": "MCHC", "normal_range": "32-36", "unit": "g/dL"},
            {"name": "Red Cell Distribution Width", "normal_range": "11.5-14.5", "unit": "%"},
            {"name": "Platelet Count", "normal_range": "150-450", "unit": "10³/µL"},
            {"name": "Mean Platelet Volume", "normal_range": "7.5-11.5", "unit": "fL"},
            {"name": "Neutrophils", "normal_range": "40-60", "unit": "%"},
            {"name": "Lymphocytes", "normal_range": "20-40", "unit": "%"},
            {"name": "Monocytes", "normal_range": "2-8", "unit": "%"},
            {"name": "Eosinophils", "normal_range": "1-4", "unit": "%"},
            {"name": "Basophils", "normal_range": "0.5-1", "unit": "%"}
        ],
        "Endocrinology": [
            {"name": "TSH", "normal_range": "0.4-4.0", "unit": "mIU/L"},
            {"name": "Free T4", "normal_range": "0.8-1.8", "unit": "ng/dL"},
            {"name": "Free T3", "normal_range": "2.3-4.2", "unit": "pg/mL"},
            {"name": "Insulin", "normal_range": "2.6-24.9", "unit": "μIU/mL"},
            {"name": "Cortisol", "normal_range": "6.2-19.4", "unit": "μg/dL"},
            {"name": "Prolactin", "normal_range": "4.0-15.2", "unit": "ng/mL"},
            {"name": "Testosterone", "normal_range": "280-1100", "unit": "ng/dL"},
            {"name": "Estradiol", "normal_range": "10-50", "unit": "pg/mL"}
        ],
        "Urinalysis": [
            {"name": "Urine Color", "normal_range": "Yellow", "unit": ""},
            {"name": "Urine Clarity", "normal_range": "Clear", "unit": ""},
            {"name": "Urine Specific Gravity", "normal_range": "1.002-1.030", "unit": ""},
            {"name": "Urine pH", "normal_range": "4.5-8.0", "unit": ""},
            {"name": "Urine Protein", "normal_range": "Negative", "unit": ""},
            {"name": "Urine Glucose", "normal_range": "Negative", "unit": ""},
            {"name": "Urine Ketones", "normal_range": "Negative", "unit": ""},
            {"name": "Urine Blood", "normal_range": "Negative", "unit": ""},
            {"name": "Urine Bilirubin", "normal_range": "Negative", "unit": ""},
            {"name": "Urine Nitrite", "normal_range": "Negative", "unit": ""}
        ],
        "Immunology": [
            {"name": "C-Reactive Protein", "normal_range": "0-3.0", "unit": "mg/L"},
            {"name": "Rheumatoid Factor", "normal_range": "0-14", "unit": "IU/mL"},
            {"name": "ANA", "normal_range": "Negative", "unit": ""},
            {"name": "Immunoglobulin A", "normal_range": "70-400", "unit": "mg/dL"},
            {"name": "Immunoglobulin G", "normal_range": "700-1600", "unit": "mg/dL"},
            {"name": "Immunoglobulin M", "normal_range": "40-230", "unit": "mg/dL"}
        ]
    }
    
    # Flatten the list of lab tests
    all_lab_tests = []
    for category, tests in lab_tests_by_category.items():
        for test in tests:
            test["category"] = category
            all_lab_tests.append(test)
    
    print("Adding lab tests...")
    for test_data in all_lab_tests:
        # Check if test already exists
        existing_test = db.query(LabTest).filter(LabTest.name == test_data["name"]).first()
        if not existing_test:
            # Remove category from test_data before creating LabTest
            category = test_data.pop("category", None)
            test = LabTest(**test_data)
            db.add(test)
    
    # Commit the changes
    db.commit()
    print(f"Added {len(all_lab_tests)} lab tests")
    
    # Add sample patient if none exists
    patient_count = db.query(Patient).count()
    if patient_count == 0:
        print("Adding sample patient...")
        patient = Patient(
            name="John Smith",
            dob="1980-05-15",
            gender="male",
            contact="555-123-4567"
        )
        db.add(patient)
        db.commit()
        
        # Add a sample order and results for the comprehensive panel
        doctor = db.query(User).filter(User.role == "admin").first()
        if doctor:
            print("Adding sample order and results...")
            # Create order
            order = Order(
                patient_id=patient.id,
                ordered_by=doctor.id,
                date_ordered=datetime.utcnow() - timedelta(days=2),
                status="completed"
            )
            db.add(order)
            db.commit()
            
            # Define the tests to include in our sample panel
            chemistry_tests = ["Glucose", "Hemoglobin A1c", "Total Cholesterol", "HDL Cholesterol", "LDL Cholesterol", "Triglycerides"]
            hematology_tests = ["White Blood Cell Count", "Red Blood Cell Count", "Hemoglobin", "Platelet Count"]
            endocrinology_tests = ["TSH"]
            
            # Add results for the selected tests
            for test_name in chemistry_tests + hematology_tests + endocrinology_tests:
                test = db.query(LabTest).filter(LabTest.name == test_name).first()
                if not test:
                    continue
                
                # Set appropriate result values - some normal, some abnormal
                result_value = None
                if test_name == "Glucose":
                    result_value = 87  # normal
                elif test_name == "Hemoglobin A1c":
                    result_value = 5.2  # normal
                elif test_name == "Total Cholesterol":
                    result_value = 220  # high
                elif test_name == "HDL Cholesterol":
                    result_value = 35  # low
                elif test_name == "LDL Cholesterol":
                    result_value = 130  # high
                elif test_name == "Triglycerides":
                    result_value = 180  # high
                elif test_name == "White Blood Cell Count":
                    result_value = 9.5  # normal
                elif test_name == "Red Blood Cell Count":
                    result_value = 5.1  # normal
                elif test_name == "Hemoglobin":
                    result_value = 14.5  # normal
                elif test_name == "Platelet Count":
                    result_value = 320  # normal
                elif test_name == "TSH":
                    result_value = 3.2  # normal
                
                if result_value is not None:
                    result = Result(
                        order_id=order.id,
                        test_id=test.id,
                        result_value=result_value,
                        unit=test.unit,
                        reference_range=test.normal_range
                    )
                    db.add(result)
            
            db.commit()
            
            # Add previous order (from 6 months ago) for trending
            previous_order = Order(
                patient_id=patient.id,
                ordered_by=doctor.id,
                date_ordered=datetime.utcnow() - timedelta(days=180),
                status="completed"
            )
            db.add(previous_order)
            db.commit()
            
            # Add previous results with slightly different values
            prev_tests = ["Glucose", "Hemoglobin A1c"]
            prev_values = [81, 5.0]
            
            for i, test_name in enumerate(prev_tests):
                test = db.query(LabTest).filter(LabTest.name == test_name).first()
                if test:
                    prev_result = Result(
                        order_id=previous_order.id,
                        test_id=test.id,
                        result_value=prev_values[i],
                        unit=test.unit,
                        reference_range=test.normal_range
                    )
                    db.add(prev_result)
            
            db.commit()
            results_count = db.query(Result).filter(Result.order_id == order.id).count()
            print(f"Added sample order with {results_count} results")
    
    db.close()
    print("Database seeding complete!")

if __name__ == "__main__":
    seed_data() 