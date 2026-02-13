-- Supprimer les tables si elles existent
DROP TABLE IF EXISTS patients CASCADE;
DROP TABLE IF EXISTS hospitals CASCADE;
DROP TABLE IF EXISTS doctors CASCADE;
DROP TABLE IF EXISTS diagnoses CASCADE;
DROP TABLE IF EXISTS medications CASCADE;
DROP TABLE IF EXISTS surgeries CASCADE;

-- Table des hôpitaux
CREATE TABLE hospitals (
    hospital_id SERIAL PRIMARY KEY,
    hospital_name VARCHAR(100) UNIQUE NOT NULL
);

-- Table des médecins
CREATE TABLE doctors (
    doctor_id SERIAL PRIMARY KEY,
    doctor_name VARCHAR(100) NOT NULL,
    UNIQUE(doctor_name)
);

-- Table des diagnostics
CREATE TABLE diagnoses (
    diagnosis_id SERIAL PRIMARY KEY,
    diagnosis_name VARCHAR(100) UNIQUE NOT NULL
);

-- Table des médicaments
CREATE TABLE medications (
    medication_id SERIAL PRIMARY KEY,
    medication_name VARCHAR(100) UNIQUE NOT NULL
);

-- Table des chirurgies
CREATE TABLE surgeries (
    surgery_id SERIAL PRIMARY KEY,
    surgery_type VARCHAR(100) UNIQUE NOT NULL
);

-- Table principale des patients
CREATE TABLE patients (
    patient_id INTEGER PRIMARY KEY,
    age INTEGER,
    gender VARCHAR(10),
    blood_pressure DECIMAL(10,5),
    heart_rate DECIMAL(10,5),
    temperature DECIMAL(10,5),
    diagnosis_id INTEGER REFERENCES diagnoses(diagnosis_id),
    medication_id INTEGER REFERENCES medications(medication_id),
    treatment_duration INTEGER,
    insurance_type VARCHAR(50),
    doctor_id INTEGER REFERENCES doctors(doctor_id),
    hospital_id INTEGER REFERENCES hospitals(hospital_id),
    lab_test_results DECIMAL(10,5),
    xray_results VARCHAR(20),
    surgery_id INTEGER REFERENCES surgeries(surgery_id),
    recovery_time INTEGER,
    allergies VARCHAR(100),
    family_history VARCHAR(100),
    patient_satisfaction INTEGER,
    ai_diagnosis_confidence DECIMAL(10,5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Créer des index pour optimiser les requêtes
CREATE INDEX idx_patient_age ON patients(age);
CREATE INDEX idx_patient_diagnosis ON patients(diagnosis_id);
CREATE INDEX idx_patient_hospital ON patients(hospital_id);
CREATE INDEX idx_patient_doctor ON patients(doctor_id);
CREATE INDEX idx_patient_satisfaction ON patients(patient_satisfaction);