# core/database/models.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Doctor(Base):
    __tablename__ = 'doctors'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    crm = Column(String(20))
    consultation_price = Column(String(20))
    is_director = Column(Boolean, default=False)
    scheduling_type = Column(String(50))  # doctoralia_human, human_only
    description = Column(Text)
    insurance_note = Column(Text)
    
    # Relacionamentos
    specialties = relationship("DoctorSpecialty", back_populates="doctor")
    insurance_plans = relationship("DoctorInsurance", back_populates="doctor")

class Specialty(Base):
    __tablename__ = 'specialties'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    symptoms = Column(Text)  # JSON array de sintomas
    treatments = Column(Text)  # JSON array de tratamentos
    exams = Column(Text)  # JSON array de exames

class InsurancePlan(Base):
    __tablename__ = 'insurance_plans'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    covers_consultation = Column(Boolean, default=True)
    covers_treatments = Column(Boolean, default=False)
    covers_exams = Column(Text)  # JSON array de exames cobertos
    rules = Column(Text)  # JSON com regras específicas

class DoctorSpecialty(Base):
    __tablename__ = 'doctor_specialties'
    
    doctor_id = Column(Integer, ForeignKey('doctors.id'), primary_key=True)
    specialty_id = Column(Integer, ForeignKey('specialties.id'), primary_key=True)
    doctor = relationship("Doctor", back_populates="specialties")
    specialty = relationship("Specialty")

class DoctorInsurance(Base):
    __tablename__ = 'doctor_insurance'
    
    doctor_id = Column(Integer, ForeignKey('doctors.id'), primary_key=True)
    insurance_id = Column(Integer, ForeignKey('insurance_plans.id'), primary_key=True)
    doctor = relationship("Doctor", back_populates="insurance_plans")
    insurance = relationship("InsurancePlan")

class MedicalExam(Base):
    __tablename__ = 'medical_exams'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    price = Column(String(20))
    coverage = Column(String(100))

class Treatment(Base):
    __tablename__ = 'treatments'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    consultation_price = Column(String(20))
    treatment_full_price = Column(String(20))
    treatment_final_price = Column(String(20))
    price_from = Column(String(20))
    payment_options = Column(Text)
    sessions = Column(String(100))
    discount_rule = Column(Text)
    note = Column(Text)