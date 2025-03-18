from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Float, DateTime, func
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
import openpyxl
from fastapi.responses import FileResponse
from typing import Optional, List, Union
from dotenv import load_dotenv
import logging
from pathlib import Path
import uuid
import io
from starlette.background import BackgroundTask

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///saieed_lab.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# JWT Secret Key
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# Dependency for getting DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# OAuth2 Setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Database Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255))
    role = Column(String(50), default="patient")  # admin, technician, doctor, patient

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    dob = Column(String(20))
    gender = Column(String(10))
    contact = Column(String(20))

class TestCategory(Base):
    __tablename__ = "test_categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True)
    description = Column(String(500))
    tests = relationship("LabTest", back_populates="category")

class LabTest(Base):
    __tablename__ = "lab_tests"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    code = Column(String(20), unique=True)
    price = Column(Float)
    normal_range = Column(String(100))
    unit = Column(String(20))
    description = Column(String(500))
    category_id = Column(Integer, ForeignKey("test_categories.id"))
    category = relationship("TestCategory", back_populates="tests")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    ordered_by = Column(Integer, ForeignKey("users.id"))
    date_ordered = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="pending")  # pending, completed

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.order_number:
            self.order_number = f"ORD{uuid.uuid4().hex[:8].upper()}"

class Result(Base):
    __tablename__ = "results"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    test_id = Column(Integer, ForeignKey("lab_tests.id"))
    result_value = Column(Float)
    unit = Column(String(20))
    reference_range = Column(String(100))
    status = Column(String(20), default="final")  # preliminary, final
    date_created = Column(DateTime, default=datetime.utcnow)

# FastAPI App
app = FastAPI(title="Saieed Clinical Lab")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Test categories and their descriptions
TEST_CATEGORIES = {
    "routine": {
        "name": "Routine Health Screening",
        "tests": [
            {"name": "Complete Blood Count (CBC)", "code": "CBC001", "price": 500.00},
            {"name": "Comprehensive Metabolic Panel", "code": "CMP001", "price": 650.00},
            {"name": "Lipid Panel", "code": "LIP001", "price": 400.00},
            {"name": "Thyroid Function Tests", "code": "THY001", "price": 850.00}
        ]
    },
    "cardiac": {
        "name": "Cardiac Health",
        "tests": [
            {"name": "Lipid Profile", "code": "LIP002", "price": 450.00},
            {"name": "Cardiac Risk Assessment", "code": "CRA001", "price": 1200.00},
            {"name": "High-Sensitivity CRP", "code": "CRP001", "price": 550.00},
            {"name": "Homocysteine", "code": "HCY001", "price": 750.00}
        ]
    },
    "diabetes": {
        "name": "Diabetes Management",
        "tests": [
            {"name": "Hemoglobin A1C", "code": "A1C001", "price": 450.00},
            {"name": "Glucose Testing", "code": "GLU001", "price": 250.00},
            {"name": "Insulin Level", "code": "INS001", "price": 650.00},
            {"name": "Microalbumin", "code": "MAL001", "price": 350.00}
        ]
    },
    "hormones": {
        "name": "Hormone Tests",
        "tests": [
            {"name": "Thyroid Panel", "code": "THY002", "price": 950.00},
            {"name": "Testosterone", "code": "TES001", "price": 750.00},
            {"name": "Estrogen", "code": "EST001", "price": 850.00},
            {"name": "Cortisol", "code": "COR001", "price": 650.00}
        ]
    },
    "allergy": {
        "name": "Allergy & Immunology",
        "tests": [
            {"name": "Food Allergy Panel", "code": "ALL001", "price": 2250.00},
            {"name": "Environmental Allergens", "code": "ALL002", "price": 1950.00},
            {"name": "Immunoglobulins", "code": "IMG001", "price": 1450.00},
            {"name": "Autoimmune Markers", "code": "AIM001", "price": 1650.00}
        ]
    },
    "nutrition": {
        "name": "Vitamin & Nutrition",
        "tests": [
            {"name": "Vitamin D", "code": "VTD001", "price": 450.00},
            {"name": "Vitamin B12", "code": "VTB001", "price": 350.00},
            {"name": "Iron Studies", "code": "IRN001", "price": 750.00},
            {"name": "Nutritional Panel", "code": "NUT001", "price": 1650.00}
        ]
    }
}

# User Authentication & Token Generation
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

# Routes for HTML pages
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/home", response_class=HTMLResponse)
async def home(request: Request, token: str = None, db: Session = Depends(get_db)):
    if not token:
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "error": "Please log in to access the home page"
        })
    
    try:
        # Validate token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        
        # Get dashboard statistics
        total_patients = db.query(Patient).count()
        today_orders = db.query(Order).filter(
            Order.date_ordered >= datetime.now().date()
        ).count()
        pending_orders = db.query(Order).filter(Order.status == "pending").count()
        completed_orders = db.query(Order).filter(Order.status == "completed").count()
        
        stats = {
            "total_patients": total_patients,
            "today_orders": today_orders,
            "pending_orders": pending_orders,
            "completed_orders": completed_orders
        }
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "token": token,
            "username": username,
            "stats": stats,
            "active_page": "home"
        })
    except JWTError:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Session expired. Please log in again"
        })

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, token: str = None, db: Session = Depends(get_db)):
    if not token:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Please log in to access the dashboard"
        })
    
    try:
        # Validate token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        
        # Get dashboard statistics
        total_patients = db.query(Patient).count()
        pending_orders = db.query(Order).filter(Order.status == "pending").count()
        todays_tests = db.query(Result).filter(
            Result.date_created >= datetime.now().date()
        ).count()
        
        # Get recent patients
        recent_patients = db.query(Patient).order_by(Patient.id.desc()).limit(5).all()
        recent_patients_data = []
        for patient in recent_patients:
            last_order = db.query(Order).filter(Order.patient_id == patient.id).order_by(Order.date_ordered.desc()).first()
            recent_patients_data.append({
                "id": patient.id,
                "name": patient.name,
                "last_visit": last_order.date_ordered.strftime("%Y-%m-%d") if last_order else "No visits",
                "status": "active" if last_order and last_order.status == "pending" else "completed"
            })
        
        # Get recent orders
        recent_orders = db.query(Order).order_by(Order.date_ordered.desc()).limit(5).all()
        recent_orders_data = []
        for order in recent_orders:
            patient = db.query(Patient).filter(Patient.id == order.patient_id).first()
            test_count = db.query(Result).filter(Result.order_id == order.id).count()
            recent_orders_data.append({
                "id": order.id,
                "patient_name": patient.name if patient else "Unknown",
                "test_count": test_count,
                "status": order.status
            })
        
        # Get recent reports
        recent_reports = []
        for order in recent_orders:
            if order.status == "completed":
                patient = db.query(Patient).filter(Patient.id == order.patient_id).first()
                recent_reports.append({
                    "id": f"R{order.id}",
                    "patient_name": patient.name if patient else "Unknown",
                    "date": order.date_ordered.strftime("%Y-%m-%d"),
                    "type": "Lab Report"
                })
        
        # Get recent activities
        recent_activities = []
        # Combine recent orders and results for activity feed
        for order in recent_orders:
            patient = db.query(Patient).filter(Patient.id == order.patient_id).first()
            recent_activities.append({
                "time": order.date_ordered.strftime("%Y-%m-%d %H:%M"),
                "description": f"New order created for {patient.name if patient else 'Unknown'}",
                "status": order.status
            })
        
        # Return dashboard with all data
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "username": username,
            "token": token,
            "total_patients": total_patients,
            "pending_orders": pending_orders,
            "todays_tests": todays_tests,
            "recent_patients": recent_patients_data,
            "recent_orders": recent_orders_data,
            "recent_reports": recent_reports,
            "recent_activities": recent_activities,
            "active_page": "dashboard"
        })
    except JWTError:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Session expired. Please log in again"
        })

# Patient Registration Form
@app.get("/patient_form", response_class=HTMLResponse)
async def patient_form(request: Request, token: str = None, success: str = None, error: str = None):
    # Get token from query parameter
    if token is None:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Please login to access patient registration"
        })
    
    # Try to validate token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role", "")
        
        # Check if user has permission to register patients
        if role not in ["admin", "technician", "doctor"]:
            return templates.TemplateResponse("login.html", {
                "request": request,
                "error": "You don't have permission to register patients"
            })
        
        # Return patient form if token is valid
        return templates.TemplateResponse("patient_form.html", {
            "request": request,
            "username": username,
            "token": token,
            "success": success,
            "error": error
        })
    except JWTError:
        # Return to login page if token is invalid
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Session expired or invalid. Please login again."
        })

# Lab Report Template
@app.get("/report/{order_id}", response_class=HTMLResponse)
async def view_report(request: Request, order_id: int, token: str = None, db: Session = Depends(get_db)):
    if not token:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Please log in to view reports"
        })
    
    try:
        # Validate token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        
        # Retrieve order and results
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            # For demo purposes, if order doesn't exist but order_id is 1, 
            # find any completed order to show sample report
            if order_id == 1:
                order = db.query(Order).filter(Order.status == "completed").first()
                if order:
                    order_id = order.id
                else:
                    return HTMLResponse(content="No completed orders found for sample report", status_code=404)
            else:
                return HTMLResponse(content="Order not found", status_code=404)
        
        # Get ordered by user (doctor)
        doctor = db.query(User).filter(User.id == order.ordered_by).first()
        doctor_name = doctor.username if doctor else "Unknown Doctor"
        
        # Get patient information
        patient = db.query(Patient).filter(Patient.id == order.patient_id).first()
        if not patient:
            return HTMLResponse(content="Patient not found", status_code=404)
        
        # Get results for the order
        results = db.query(Result).filter(Result.order_id == order.id).all()
        if not results:
            return HTMLResponse(content="No results found for this order", status_code=404)
        
        # Prepare results data for template
        results_data = []
        abnormal_count = 0
        normal_count = 0
        test_type = "Comprehensive Lab Panel"
        range_low = None
        range_high = None
        previous_result = None
        
        for result in results:
            # Get test information
            test = db.query(LabTest).filter(LabTest.id == result.test_id).first()
            if not test:
                continue
            
            # Determine if result is abnormal
            is_abnormal = False
            flag = ""
            
            # Parse reference range
            ref_range = test.normal_range
            if '-' in ref_range:
                low, high = ref_range.split('-')
                try:
                    range_low = float(low)
                    range_high = float(high)
                    if result.result_value < range_low:
                        is_abnormal = True
                        flag = "L"
                    elif result.result_value > range_high:
                        is_abnormal = True
                        flag = "H"
                except ValueError:
                    # Handle case where range might not be simple numbers
                    pass
            elif '>' in ref_range:
                try:
                    threshold = float(ref_range.replace('>', '').strip())
                    if result.result_value <= threshold:
                        is_abnormal = True
                        flag = "L"
                except ValueError:
                    pass
            elif '<' in ref_range:
                try:
                    threshold = float(ref_range.replace('<', '').strip())
                    if result.result_value >= threshold:
                        is_abnormal = True
                        flag = "H"
                except ValueError:
                    pass
            
            if is_abnormal:
                abnormal_count += 1
            else:
                normal_count += 1
            
            # Add result to data
            results_data.append({
                'test_name': test.name,
                'value': result.result_value,
                'unit': result.unit,
                'reference_range': result.reference_range,
                'is_abnormal': is_abnormal,
                'flag': flag
            })
            
            # For first test, get previous result if available
            if test.name == "Glucose" and previous_result is None:
                # Find previous order for this patient
                prev_order = db.query(Order).filter(
                    Order.patient_id == patient.id,
                    Order.id != order.id
                ).order_by(Order.date_ordered.desc()).first()
                
                if prev_order:
                    prev_result = db.query(Result).join(LabTest).filter(
                        Result.order_id == prev_order.id,
                        LabTest.name == "Glucose"
                    ).first()
                    
                    if prev_result:
                        previous_result = prev_result.result_value
        
        # Format dates for the report
        collected_date = order.date_ordered.strftime("%m/%d/%Y")
        received_date = order.date_ordered.strftime("%m/%d/%Y") # Same as collected for simplicity
        reported_date = datetime.utcnow().strftime("%m/%d/%Y")
        signed_date = datetime.utcnow().strftime("%m/%d/%Y %H:%M:%S")
        
        # Additional lab notes for the report
        lab_notes = "Test performed using standard clinical laboratory procedures. Results have been verified and validated according to laboratory quality control standards."
        
        return templates.TemplateResponse("report_template.html", {
            "request": request,
            "token": token,
            "report_id": f"R{order_id}",
            "patient": {
                "id": patient.id,
                "name": patient.name,
                "dob": patient.dob,
                "gender": patient.gender
            },
            "collected_date": collected_date,
            "received_date": received_date,
            "reported_date": reported_date,
            "doctor_name": doctor_name,
            "signed_date": signed_date,
            "provider": doctor_name,
            "account_number": f"ACC{patient.id}",
            "results": results_data,
            "abnormal_count": abnormal_count,
            "normal_count": normal_count,
            "test_type": test_type,
            "range_low": range_low,
            "range_high": range_high,
            "previous_result": previous_result,
            "notes": lab_notes,
            "order_id": order_id
        })
    except JWTError:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Session expired. Please log in again"
        })
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return HTMLResponse(content=f"Error generating report: {str(e)}", status_code=500)

# Generate PDF Report
@app.get("/report/{order_id}/pdf")
async def generate_pdf_report(request: Request, order_id: int, token: str = None, db: Session = Depends(get_db)):
    if not token:
        return HTMLResponse(content="Please log in to download reports", status_code=401)
    
    try:
        # Validate token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        
        # Check if order exists
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            if order_id == 1:
                order = db.query(Order).filter(Order.status == "completed").first()
                if order:
                    order_id = order.id
                else:
                    return HTMLResponse(content="No completed orders found for sample report", status_code=404)
            else:
                return HTMLResponse(content="Order not found", status_code=404)
        
        # Get patient information
        patient = db.query(Patient).filter(Patient.id == order.patient_id).first()
        if not patient:
            return HTMLResponse(content="Patient not found", status_code=404)
        
        # Get test results
        results = db.query(Result).filter(Result.order_id == order.id).all()
        if not results:
            return HTMLResponse(content="No results found for this order", status_code=404)
        
        # Create temp directory if it doesn't exist
        os.makedirs("temp", exist_ok=True)
        
        # Create a unique filename for the PDF
        pdf_filename = f"report_{order.order_number}_{uuid.uuid4().hex[:8]}.pdf"
        pdf_path = os.path.join("temp", pdf_filename)
        
        # Create the PDF
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = styles["Heading1"]
        title_style.alignment = 1  # Center
        
        header_style = styles["Heading2"]
        normal_style = styles["Normal"]
        
        # Create title
        elements.append(Paragraph("Saieed Clinical Laboratory", title_style))
        elements.append(Paragraph("Lab Test Report", header_style))
        elements.append(Paragraph(f"Order Number: {order.order_number}", header_style))
        elements.append(Spacer(1, 12))
        
        # Patient information
        patient_info = [
            ["Patient Name:", patient.name, "Patient ID:", str(patient.id)],
            ["Date of Birth:", patient.dob, "Gender:", patient.gender],
            ["Report Date:", datetime.utcnow().strftime("%m/%d/%Y"), "Order ID:", str(order_id)]
        ]
        
        patient_table = Table(patient_info, colWidths=[100, 150, 100, 150])
        patient_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
        ]))
        
        elements.append(patient_table)
        elements.append(Spacer(1, 20))
        
        # Test Results
        elements.append(Paragraph("Test Results", header_style))
        elements.append(Spacer(1, 10))
        
        # Header row for test results
        result_data = [["Test Name", "Result", "Units", "Reference Range", "Flag"]]
        
        # Add each test result
        for result in results:
            test = db.query(LabTest).filter(LabTest.id == result.test_id).first()
            test_name = test.name if test else f"Test #{result.test_id}"
            
            # Determine if result is abnormal
            flag = ""
            if test and test.normal_range:
                try:
                    # Simple check for numeric ranges in format "X-Y"
                    range_parts = test.normal_range.split("-")
                    if len(range_parts) == 2:
                        min_val = float(range_parts[0])
                        max_val = float(range_parts[1])
                        if result.result_value < min_val:
                            flag = "L"
                        elif result.result_value > max_val:
                            flag = "H"
                except:
                    pass
            
            result_data.append([
                test_name,
                str(result.result_value),
                result.unit,
                result.reference_range or (test.normal_range if test else ""),
                flag
            ])
        
        result_table = Table(result_data, colWidths=[150, 80, 80, 120, 50])
        result_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
        ]))
        
        elements.append(result_table)
        elements.append(Spacer(1, 30))
        
        # Notes
        elements.append(Paragraph("Notes:", styles["Heading3"]))
        elements.append(Paragraph("H = Higher than reference range", normal_style))
        elements.append(Paragraph("L = Lower than reference range", normal_style))
        elements.append(Spacer(1, 20))
        
        # Footer with signature
        elements.append(Paragraph(f"Electronically signed by: Dr. {username}", normal_style))
        elements.append(Paragraph(f"Report generated on {datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S')}", normal_style))
        
        # Build the PDF
        doc.build(elements)
        
        # Return the PDF file and delete it after sending
        return FileResponse(
            path=pdf_path,
            filename=pdf_filename,
            media_type="application/pdf",
            background=BackgroundTask(lambda: os.unlink(pdf_path))
        )
    except JWTError:
        return HTMLResponse(content="Session expired. Please log in again", status_code=401)
    except Exception as e:
        logger.error(f"Error generating PDF report: {str(e)}")
        return HTMLResponse(content=f"Error generating PDF report: {str(e)}", status_code=500)

# Additional API endpoints for dashboard
@app.get("/patients/count")
async def get_patient_count(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    count = db.query(Patient).count()
    return {"count": count}

@app.get("/orders/pending/count")
async def get_pending_orders_count(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    count = db.query(Order).filter(Order.status == "pending").count()
    return {"count": count}

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}

# Patient Management
@app.post("/patients")
def create_patient(
    name: str, 
    dob: str, 
    gender: str, 
    contact: str, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["admin", "technician", "doctor"]:
        raise HTTPException(status_code=403, detail="Not authorized to create patients")
    
    new_patient = Patient(name=name, dob=dob, gender=gender, contact=contact)
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    return new_patient

@app.get("/patients/{id}")
def get_patient(id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Patients can only view their own records
    if current_user.role == "patient" and id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this patient")
    
    patient = db.query(Patient).filter(Patient.id == id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

# Lab Order Management
@app.get("/order", response_class=HTMLResponse)
async def order_page(request: Request, token: str = None, tests: str = None, db: Session = Depends(get_db)):
    if not token:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Please log in to create orders"
        })
    
    try:
        # Validate token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        
        # Get all patients for the dropdown
        patients = db.query(Patient).all()
        
        return templates.TemplateResponse("order.html", {
            "request": request,
            "token": token,
            "username": username,
            "patients": patients,
            "active_page": "orders"
        })
    except JWTError:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Session expired. Please log in again"
        })

@app.post("/orders")
async def create_order(request: Request, token: str, db: Session = Depends(get_db)):
    try:
        # Verify token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Get request data
        data = await request.json()
        patient_id = data.get('patient_id')
        test_ids = data.get('tests', [])
        
        # Create new order
        new_order = Order(
            patient_id=patient_id,
            ordered_by=user.id,
            status="pending"
        )
        db.add(new_order)
        db.flush()  # Get the report ID
        
        # Create results entries for each test
        for test_id in test_ids:
            test = db.query(LabTest).filter(LabTest.id == test_id).first()
            if test:
                new_result = Result(
                    order_id=new_order.id,
                    test_id=test_id,
                    unit=test.unit,
                    reference_range=test.normal_range
                )
                db.add(new_result)
        
        db.commit()
        return {"success": True, "order_id": new_order.id}
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/orders/{id}")
def get_order(id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == id).first()
    
    # Check authorization
    if current_user.role == "patient" and order.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this order")
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

# Result Management
@app.post("/results")
def add_result(
    order_id: int, 
    test_id: int, 
    result_value: float, 
    unit: str, 
    reference_range: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["admin", "technician"]:
        raise HTTPException(status_code=403, detail="Not authorized to add results")
    
    # Check if order exists
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    new_result = Result(
        order_id=order_id, 
        test_id=test_id, 
        result_value=result_value, 
        unit=unit, 
        reference_range=reference_range
    )
    db.add(new_result)
    db.commit()
    db.refresh(new_result)
    
    # Update order status
    order.status = "completed"
    db.commit()
    
    return new_result

@app.get("/results", response_class=HTMLResponse)
async def get_results(request: Request, token: str = None, db: Session = Depends(get_db)):
    if not token:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Please log in to view results"
        })
    
    try:
        # Verify token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        
        # Get all results with related data
        results_query = (
            db.query(
                Result,
                Order.date_ordered,
                Patient.name.label("patient_name"),
                LabTest.name.label("test_name"),
                LabTest.unit,
                LabTest.normal_range.label("reference_range")
            )
            .join(Order, Result.order_id == Order.id)
            .join(Patient, Order.patient_id == Patient.id)
            .join(LabTest, Result.test_id == LabTest.id)
            .order_by(Order.date_ordered.desc())
        )
        
        results = []
        for r, date, patient, test, unit, ref_range in results_query.all():
            result = {
                "order_id": r.order_id,
                "patient_name": patient,
                "test_name": test,
                "value": r.result_value,
                "unit": unit,
                "reference_range": ref_range,
                "is_abnormal": is_result_abnormal(r.result_value, ref_range),
                "date": date.strftime("%Y-%m-%d"),
                "status": r.status
            }
            results.append(result)
        
        return templates.TemplateResponse("results.html", {
            "request": request,
            "token": token,
            "username": username,
            "results": results,
            "active_page": "results"
        })
        
    except JWTError:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Session expired. Please log in again"
        })

def is_result_abnormal(value: float, reference_range: str) -> bool:
    """Check if a result value is outside the normal range"""
    try:
        if not reference_range or not value:
            return False
            
        # Parse range (format: "min-max")
        min_val, max_val = map(float, reference_range.split("-"))
        return value < min_val or value > max_val
    except:
        return False

# User Management
@app.post("/users")
def create_user(
    username: str, 
    password: str, 
    role: str, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only admins can create users
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to create users")
    
    # Check if username already exists
    db_user = db.query(User).filter(User.username == username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Validate role
    if role not in ["admin", "technician", "doctor", "patient"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    hashed_password = get_password_hash(password)
    new_user = User(username=username, hashed_password=hashed_password, role=role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"id": new_user.id, "username": new_user.username, "role": new_user.role}

def init_admin():
    """Create admin user if no admin exists"""
    db = SessionLocal()
    admin_user = db.query(User).filter(User.role == "admin").first()
    if not admin_user:
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "password123")
        hashed_password = get_password_hash(admin_password)
        
        new_admin = User(username=admin_username, hashed_password=hashed_password, role="admin")
        db.add(new_admin)
        try:
            db.commit()
            logger.info(f"Admin user '{admin_username}' created successfully")
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating admin user: {e}")
    db.close()

def init_test_data():
    """Initialize test data in the database"""
    db = SessionLocal()
    try:
        # Only add test data if database is empty
        if db.query(Patient).count() == 0:
            # Add some test patients
            test_patients = [
                Patient(name="John Doe", dob="1980-01-01", gender="Male", contact="123-456-7890"),
                Patient(name="Jane Smith", dob="1990-05-15", gender="Female", contact="234-567-8901"),
                Patient(name="Bob Johnson", dob="1975-12-25", gender="Male", contact="345-678-9012")
            ]
            db.add_all(test_patients)
            db.commit()

            # Add some lab tests
            test_lab_tests = [
                LabTest(name="Complete Blood Count", normal_range="4.5-5.5", unit="M/uL"),
                LabTest(name="Blood Glucose", normal_range="70-100", unit="mg/dL"),
                LabTest(name="Cholesterol", normal_range="125-200", unit="mg/dL")
            ]
            db.add_all(test_lab_tests)
            db.commit()

            # Add some test orders
            test_orders = [
                Order(
                    patient_id=1,
                    ordered_by=1,
                    status="completed",
                    date_ordered=datetime.now() - timedelta(days=5)
                ),
                Order(
                    patient_id=2,
                    ordered_by=1,
                    status="pending",
                    date_ordered=datetime.now() - timedelta(days=2)
                ),
                Order(
                    patient_id=3,
                    ordered_by=1,
                    status="completed",
                    date_ordered=datetime.now() - timedelta(days=1)
                )
            ]
            db.add_all(test_orders)
            db.commit()

            # Add some test results
            test_results = [
                Result(
                    order_id=1,
                    test_id=1,
                    result_value=4.8,
                    unit="M/uL",
                    reference_range="4.5-5.5",
                    status="final"
                ),
                Result(
                    order_id=1,
                    test_id=2,
                    result_value=95,
                    unit="mg/dL",
                    reference_range="70-100",
                    status="final"
                ),
                Result(
                    order_id=3,
                    test_id=3,
                    result_value=180,
                    unit="mg/dL",
                    reference_range="125-200",
                    status="final"
                )
            ]
            db.add_all(test_results)
            db.commit()

        logger.info("Test data initialized successfully")
    except Exception as e:
        db.rollback()
        logger.error(f"Error initializing test data: {e}")
    finally:
        db.close()
    
@app.on_event("startup")
def startup_event():
    """Initialize database and create admin user on startup"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create admin user
    init_admin()
    
    # Initialize test data
    init_test_data()
    
    logger.info("Application startup complete")

@app.get("/tests", response_class=HTMLResponse)
async def test_catalog(request: Request, token: str = None):
    if not token:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Please log in to view our test catalog"
        })
    
    try:
        # Validate token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        
        return templates.TemplateResponse("test_catalog.html", {
            "request": request,
            "token": token,
            "username": username,
            "categories": TEST_CATEGORIES,
            "active_page": "tests"
        })
    except JWTError:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Session expired. Please log in again"
        })

@app.get("/tests/details/{test_id}", response_class=HTMLResponse)
async def test_detail(request: Request, test_id: str, token: str = None):
    if not token:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Please log in to view test details"
        })
    
    try:
        # Validate token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        
        # For now, we only have the comprehensive-standard test detail page
        # In a real app, we would fetch test details from the database based on test_id
        
        return templates.TemplateResponse("test_detail.html", {
            "request": request,
            "token": token,
            "username": username,
            "test_id": test_id,
            "active_page": "tests"
        })
    except JWTError:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Session expired. Please log in again"
        })

@app.get("/tests/category/{category}", response_class=HTMLResponse)
async def get_test_category(request: Request, category: str, token: str):
    try:
        # Verify token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        
        if category not in TEST_CATEGORIES:
            raise HTTPException(status_code=404, detail="Category not found")
            
        category_data = TEST_CATEGORIES[category]
        return templates.TemplateResponse(
            "test_category.html",
            {
                "request": request,
                "category": category_data["name"],
                "tests": category_data["tests"],
                "token": token,
                "username": username,
                "active_page": "tests"
            }
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/orders", response_class=HTMLResponse)
async def get_orders_page(request: Request, token: str = None):
    if not token:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Please log in to view orders"
        })
    
    try:
        # Verify token
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        
        # Get orders from database
        db = SessionLocal()
        try:
            orders = db.query(Order).order_by(Order.date_ordered.desc()).all()
            
            orders_data = []
            for order in orders:
                # Get patient information
                patient = db.query(Patient).filter(Patient.id == order.patient_id).first()
                
                # Get test count
                test_count = db.query(Result).filter(Result.order_id == order.id).count()
                
                orders_data.append({
                    "id": order.id,
                    "order_number": order.order_number,
                    "patient_name": patient.name if patient else "Unknown",
                    "date": order.date_ordered.strftime("%Y-%m-%d"),
                    "test_count": test_count,
                    "status": order.status
                })
            
            return templates.TemplateResponse(
                "orders.html",
                {
                    "request": request,
                    "token": token,
                    "orders": orders_data,
                    "username": username,
                    "active_page": "orders"
                }
            )
        finally:
            db.close()
            
    except jwt.ExpiredSignatureError:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Session expired. Please log in again."}
        )
    except jwt.InvalidTokenError:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid token. Please log in again."}
        )

# Error Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "status_code": exc.status_code,
            "detail": exc.detail
        }
    )

@app.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request, token: str = None, db: Session = Depends(get_db)):
    if not token:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Please log in to view reports"
        })
    
    try:
        # Verify token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        
        # Get all completed orders with their results
        orders_query = (
            db.query(
                Order,
                Patient.name.label("patient_name"),
                func.count(Result.id).label("test_count")
            )
            .join(Patient, Order.patient_id == Patient.id)
            .join(Result, Order.id == Result.order_id)
            .filter(Order.status == "completed")
            .group_by(Order.id, Patient.name)
            .order_by(Order.date_ordered.desc())
        )
        
        reports = []
        for order, patient_name, test_count in orders_query.all():
            report = {
                "id": order.id,
                "patient_name": patient_name,
                "test_count": test_count,
                "date": order.date_ordered.strftime("%Y-%m-%d"),
                "status": "Ready"
            }
            reports.append(report)
        
        return templates.TemplateResponse("reports.html", {
            "request": request,
            "token": token,
            "username": username,
            "reports": reports,
            "active_page": "reports"
        })
        
    except JWTError:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Session expired. Please log in again"
        })

@app.get("/reports/{order_id}", response_class=HTMLResponse)
async def view_report(request: Request, order_id: int, token: str = None, db: Session = Depends(get_db)):
    if not token:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Please log in to view report"
        })
    
    try:
        # Verify token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        
        # Get order details with patient info
        order = (
            db.query(Order, Patient)
            .join(Patient, Order.patient_id == Patient.id)
            .filter(Order.id == order_id)
            .first()
        )
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Get all results for this order
        results = (
            db.query(Result, LabTest)
            .join(LabTest, Result.test_id == LabTest.id)
            .filter(Result.order_id == order_id)
            .all()
        )
        
        report_data = {
            "order_id": order_id,
            "patient": {
                "name": order.Patient.name,
                "dob": order.Patient.dob,
                "gender": order.Patient.gender,
                "contact": order.Patient.contact
            },
            "date": order.Order.date_ordered.strftime("%Y-%m-%d"),
            "results": [{
                "test_name": test.name,
                "result": result.result_value,
                "unit": test.unit,
                "reference_range": test.normal_range,
                "is_abnormal": is_result_abnormal(result.result_value, test.normal_range),
                "status": result.status
            } for result, test in results]
        }
        
        return templates.TemplateResponse("report_template.html", {
            "request": request,
            "token": token,
            "username": username,
            "report": report_data,
            "active_page": "reports"
        })
        
    except JWTError:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Session expired. Please log in again"
        })
    except Exception as e:
        logger.error(f"Error viewing report: {str(e)}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "status_code": 500,
            "detail": "Internal server error"
        })

@app.get("/appointments", response_class=HTMLResponse)
async def appointments_page(request: Request, token: str = None, db: Session = Depends(get_db)):
    if not token:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Please log in to view appointments"
        })
    
    try:
        # Validate token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        
        # For now, return empty appointments list
        # In a real application, you would fetch appointments from the database
        appointments = []
        
        return templates.TemplateResponse("appointments.html", {
            "request": request,
            "token": token,
            "username": username,
            "appointments": appointments,
            "active_page": "appointments"
        })
    except JWTError:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Session expired. Please log in again"
        })

@app.post("/appointments")
async def create_appointment(
    request: Request,
    token: str,
    db: Session = Depends(get_db)
):
    try:
        # Validate token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        
        # Get request body
        data = await request.json()
        
        # In a real application, you would save the appointment to the database
        # For now, just return success
        return {"success": True}
    except JWTError:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/appointments/{appointment_id}")
async def delete_appointment(
    appointment_id: str,
    token: str,
    db: Session = Depends(get_db)
):
    try:
        # Validate token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        
        # In a real application, you would delete the appointment from the database
        # For now, just return success
        return {"success": True}
    except JWTError:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/report/new", response_class=HTMLResponse)
async def new_report(
    request: Request,
    token: str = None,
    template: str = None,
    db: Session = Depends(get_db)
):
    if not token:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Please log in to create reports"
        })
    
    try:
        # Validate token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        
        # Get all patients and tests for the form
        patients = db.query(Patient).all()
        tests = db.query(LabTest).all()
        
        return templates.TemplateResponse("new_report.html", {
            "request": request,
            "token": token,
            "username": username,
            "patients": patients,
            "tests": tests,
            "template": template,
            "active_page": "reports"
        })
    except JWTError:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Session expired. Please log in again"
        })
    except Exception as e:
        logger.error(f"Error creating new report form: {str(e)}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "status_code": 500,
            "detail": "Internal server error"
        })

@app.get("/report/sample/{template}", response_class=HTMLResponse)
async def view_sample_report(request: Request, template: str, token: str = None):
    if not token:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Please log in to view sample reports"
        })
    
    try:
        # Validate token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        
        # Sample data for preview
        sample_data = {
            "request": request,
            "token": token,
            "username": username,
            "patient": {
                "name": "John Doe",
                "id": "SAMPLE-001",
                "gender": "Male",
                "dob": "1980-01-01"
            },
            "order": {
                "order_number": "SAMPLE-ORDER",
                "date_ordered": datetime.utcnow()
            },
            "results": [
                {
                    "test_id": 1,
                    "result_value": 120,
                    "unit": "mg/dL",
                    "reference_range": "70-110"
                },
                {
                    "test_id": 2,
                    "result_value": 14.5,
                    "unit": "g/dL",
                    "reference_range": "13.5-17.5"
                }
            ],
            "tests": {
                1: {"name": "Glucose"},
                2: {"name": "Hemoglobin"}
            },
            "reported_by": username,
            "is_abnormal": is_result_abnormal,
            "datetime": datetime
        }
        
        return templates.TemplateResponse(f"report_{template}.html", sample_data)
    except JWTError:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Session expired. Please log in again"
        })
    except Exception as e:
        logger.error(f"Error generating sample report: {str(e)}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "status_code": 500,
            "detail": "Internal server error"
        })

@app.post("/reports/settings")
async def save_report_settings(
    request: Request,
    token: str,
    db: Session = Depends(get_db)
):
    try:
        # Validate token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        
        # Get settings from request body
        settings = await request.json()
        
        # In a real application, you would save these settings to the database
        # For now, just return success
        return {"success": True}
    except JWTError:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patients", response_class=HTMLResponse)
async def get_patients_page(request: Request, token: str = None):
    if not token:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Please log in to view patients"
        })
    
    try:
        # Verify token
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        
        # Get patients from database
        db = SessionLocal()
        patients = db.query(Patient).all()
        
        patients_data = []
        for patient in patients:
            # Get last visit date from orders
            last_order = db.query(Order).filter(Order.patient_id == patient.id).order_by(Order.date_ordered.desc()).first()
            last_visit = last_order.date_ordered.strftime("%Y-%m-%d") if last_order else "No visits"
            
            patients_data.append({
                "id": patient.id,
                "name": patient.name,
                "age": calculate_age(patient.dob) if patient.dob else "",
                "gender": patient.gender,
                "contact": patient.contact,
                "last_visit": last_visit
            })
        
        return templates.TemplateResponse(
            "patients.html",
            {
                "request": request, 
                "token": token, 
                "patients": patients_data,
                "username": username,
                "active_page": "patients"
            }
        )
    except jwt.ExpiredSignatureError:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Session expired. Please log in again."}
        )
    except jwt.InvalidTokenError:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid token. Please log in again."}
        )
    finally:
        db.close()

def calculate_age(dob):
    try:
        birth_date = datetime.strptime(dob, "%Y-%m-%d")
        today = datetime.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age
    except:
        return None

@app.post("/api/patients")
async def create_patient(patient: dict):
    # TODO: Add database integration
    return {"success": True, "message": "Patient created successfully"}

@app.get("/api/patients/{patient_id}")
async def get_patient(patient_id: str):
    # TODO: Add database integration
    return {
        "id": patient_id,
        "name": "John Doe",
        "age": 35,
        "gender": "Male",
        "contact": "+92 300 1234567",
        "email": "john@example.com",
        "address": "123 Main St"
    }

@app.put("/api/patients/{patient_id}")
async def update_patient(patient_id: str, patient: dict):
    # TODO: Add database integration
    return {"success": True, "message": "Patient updated successfully"}

@app.delete("/api/patients/{patient_id}")
async def delete_patient(patient_id: str):
    # TODO: Add database integration
    return {"success": True, "message": "Patient deleted successfully"}

@app.get("/admin/tests", response_class=HTMLResponse)
async def manage_tests(request: Request, token: str = None, db: Session = Depends(get_db)):
    if not token:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Please log in to manage tests"
        })
    
    try:
        # Validate token and check admin role
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        user = db.query(User).filter(User.username == username).first()
        
        if not user or user.role != "admin":
            return HTMLResponse(content="Unauthorized access", status_code=403)
        
        # Get all tests with their categories
        tests = db.query(LabTest).all()
        categories = db.query(TestCategory).all()
        
        return templates.TemplateResponse("manage_tests.html", {
            "request": request,
            "token": token,
            "username": username,
            "tests": tests,
            "categories": categories,
            "active_page": "tests"
        })
    except JWTError:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Session expired. Please log in again"
        })

@app.post("/api/tests")
async def create_test(
    request: Request,
    token: str,
    db: Session = Depends(get_db)
):
    try:
        # Validate token and check admin role
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        user = db.query(User).filter(User.username == username).first()
        
        if not user or user.role != "admin":
            raise HTTPException(status_code=403, detail="Unauthorized access")
        
        # Get request data
        data = await request.json()
        
        # Create new test
        new_test = LabTest(
            name=data["name"],
            code=data["code"],
            price=float(data["price"]),
            normal_range=data["normal_range"],
            unit=data["unit"],
            description=data.get("description", ""),
            category_id=data.get("category_id")
        )
        
        db.add(new_test)
        db.commit()
        db.refresh(new_test)
        
        return {"success": True, "test_id": new_test.id}
    except JWTError:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/tests/{test_id}")
async def update_test(
    test_id: int,
    request: Request,
    token: str,
    db: Session = Depends(get_db)
):
    try:
        # Validate token and check admin role
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        user = db.query(User).filter(User.username == username).first()
        
        if not user or user.role != "admin":
            raise HTTPException(status_code=403, detail="Unauthorized access")
        
        # Get request data
        data = await request.json()
        
        # Update test
        test = db.query(LabTest).filter(LabTest.id == test_id).first()
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        
        test.name = data.get("name", test.name)
        test.code = data.get("code", test.code)
        test.price = float(data.get("price", test.price))
        test.normal_range = data.get("normal_range", test.normal_range)
        test.unit = data.get("unit", test.unit)
        test.description = data.get("description", test.description)
        test.category_id = data.get("category_id", test.category_id)
        
        db.commit()
        return {"success": True}
    except JWTError:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/tests/{test_id}")
async def delete_test(
    test_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    try:
        # Validate token and check admin role
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        user = db.query(User).filter(User.username == username).first()
        
        if not user or user.role != "admin":
            raise HTTPException(status_code=403, detail="Unauthorized access")
        
        # Delete test
        test = db.query(LabTest).filter(LabTest.id == test_id).first()
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        
        db.delete(test)
        db.commit()
        return {"success": True}
    except JWTError:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/results/{order_id}")
async def update_result(
    order_id: int,
    request: Request,
    token: str,
    db: Session = Depends(get_db)
):
    try:
        # Validate token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        user = db.query(User).filter(User.username == username).first()
        
        if not user or user.role not in ["admin", "technician"]:
            raise HTTPException(status_code=403, detail="Unauthorized access")
        
        # Get request data
        data = await request.json()
        result_id = data.get("result_id")
        result_value = data.get("result_value")
        
        # Update result
        result = db.query(Result).filter(
            Result.id == result_id,
            Result.order_id == order_id
        ).first()
        
        if not result:
            raise HTTPException(status_code=404, detail="Result not found")
        
        result.result_value = float(result_value)
        result.status = "final"
        
        # Check if all results are entered
        all_results = db.query(Result).filter(Result.order_id == order_id).all()
        all_completed = all(r.result_value is not None for r in all_results)
        
        if all_completed:
            # Update order status
            order = db.query(Order).filter(Order.id == order_id).first()
            if order:
                order.status = "completed"
        
        db.commit()
        return {"success": True}
    except JWTError:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reports")
async def create_report(request: Request, token: str):
    if not verify_token(token):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    data = await request.json()
    
    # Validate required fields
    required_fields = ["template", "patient_id", "tests"]
    for field in required_fields:
        if field not in data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    # Get patient information
    patient = db.query(Patient).filter(Patient.id == data["patient_id"]).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Create new report
    report = Report(
        patient_id=patient.id,
        template=data["template"],
        comments=data.get("comments", ""),
        created_at=datetime.now(),
        status="completed"
    )
    db.add(report)
    db.flush()  # Get the report ID
    
    # Add test results
    for test_data in data["tests"]:
        test_result = TestResult(
            report_id=report.id,
            test_id=test_data["test_id"],
            result_value=test_data["result_value"],
            unit=test_data["unit"],
            reference_range=test_data["reference_range"]
        )
        db.add(test_result)
    
    try:
        db.commit()
        return {"report_id": report.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/order/{order_id}/results", response_class=HTMLResponse)
async def enter_results(
    request: Request,
    order_id: int,
    token: str = None,
    db: Session = Depends(get_db)
):
    if not token:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Please log in to enter results"
        })
    
    try:
        # Validate token and check role
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        user = db.query(User).filter(User.username == username).first()
        
        if not user or user.role not in ["admin", "technician"]:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "status_code": 403,
                "detail": "You don't have permission to enter results"
            })
        
        # Get order details
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "status_code": 404,
                "detail": "Order not found"
            })
        
        # Get patient information
        patient = db.query(Patient).filter(Patient.id == order.patient_id).first()
        
        # Get all results for this order with test information
        results = []
        for result in db.query(Result).filter(Result.order_id == order_id).all():
            test = db.query(LabTest).filter(LabTest.id == result.test_id).first()
            if test:
                results.append({
                    "id": result.id,
                    "test_name": test.name,
                    "result_value": result.result_value,
                    "unit": test.unit,
                    "reference_range": test.normal_range
                })
        
        return templates.TemplateResponse("new_result.html", {
            "request": request,
            "token": token,
            "username": username,
            "order": order,
            "patient": patient,
            "results": results,
            "active_page": "orders"
        })
        
    except JWTError:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Session expired. Please log in again"
        })
    except Exception as e:
        logger.error(f"Error loading result entry form: {str(e)}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "status_code": 500,
            "detail": "Internal server error"
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8081)
