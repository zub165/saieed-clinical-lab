from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    TECHNICIAN = "technician"
    PATIENT = "patient"

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    COLLECTED = "collected"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255))
    role = Column(String(20), default=UserRole.PATIENT)
    full_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    patients = relationship("Patient", back_populates="user")
    orders = relationship("Order", back_populates="user")

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    mrn = Column(String(20), unique=True, index=True)  # Medical Record Number
    full_name = Column(String(100))
    date_of_birth = Column(DateTime)
    gender = Column(String(10))
    phone = Column(String(20))
    address = Column(String(200))
    insurance_provider = Column(String(100))
    insurance_id = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="patients")
    orders = relationship("Order", back_populates="patient")
    medical_history = relationship("MedicalHistory", back_populates="patient")

class MedicalHistory(Base):
    __tablename__ = "medical_history"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    condition = Column(String(100))
    diagnosis_date = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="medical_history")

class LabTest(Base):
    __tablename__ = "lab_tests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    code = Column(String(20), unique=True)
    category = Column(String(50))
    description = Column(Text)
    price = Column(Float)
    normal_range = Column(String(100))
    unit = Column(String(20))
    preparation = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    results = relationship("Result", back_populates="test")
    order_items = relationship("OrderItem", back_populates="test")

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    patient_id = Column(Integer, ForeignKey("patients.id"))
    order_number = Column(String(20), unique=True)
    status = Column(String(20), default=OrderStatus.PENDING)
    appointment_date = Column(DateTime)
    collection_date = Column(DateTime)
    total_amount = Column(Float)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="orders")
    patient = relationship("Patient", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")
    results = relationship("Result", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    test_id = Column(Integer, ForeignKey("lab_tests.id"))
    price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    order = relationship("Order", back_populates="items")
    test = relationship("LabTest", back_populates="order_items")

class Result(Base):
    __tablename__ = "results"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    test_id = Column(Integer, ForeignKey("lab_tests.id"))
    value = Column(String(100))
    unit = Column(String(20))
    reference_range = Column(String(100))
    is_abnormal = Column(Boolean, default=False)
    notes = Column(Text)
    verified_by = Column(Integer, ForeignKey("users.id"))
    verified_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    order = relationship("Order", back_populates="results")
    test = relationship("LabTest", back_populates="results")
    verifier = relationship("User") 