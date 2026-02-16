import psycopg2
import pandas as pd
import configparser
import logging
from sqlalchemy import create_engine
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataProfiler:
    def __init__(self, config_file='../config/database.ini'):
        self.config_file = config_file
        self.config = None
        self.engine = self.create_engine()

    def load_config(self, filename):
        path = Path(filename).resolve()
        if not path.exists():
            raise FileNotFoundError(f"database.ini introuvable: {path}")

        config = configparser.ConfigParser()
        config.read(path)

        if 'postgresql' not in config:
            raise KeyError(
                f"Section [postgresql] introuvable dans {path}. "
                f"Sections disponibles: {config.sections()}"
            )
        return config['postgresql']

    def create_engine(self):
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            return create_engine(db_url, connect_args={"sslmode": "require"})

        self.config = self.load_config(self.config_file)
        connection_string = (
            f"postgresql://{self.config['user']}:{self.config['password']}"
            f"@{self.config['host']}:{self.config['port']}/{self.config['database']}"
        )
        return create_engine(connection_string)
    
    def profile_patients_demographics(self): ##statistiques selon le sexe
        """Profil démographique des patients"""
        query = """
        SELECT 
            gender,
            COUNT(*) as patient_count,
            ROUND(AVG(age), 1) as avg_age,
            MIN(age) as min_age,
            MAX(age) as max_age,
            ROUND(AVG(patient_satisfaction), 2) as avg_satisfaction,
            ROUND(AVG(ai_diagnosis_confidence), 3) as avg_ai_confidence
        FROM patients
        GROUP BY gender
        ORDER BY patient_count DESC;
        """
        return pd.read_sql(query, self.engine)
    
    def profile_diagnosis_distribution(self): ##statistique selon la maladie
        """Distribution des diagnostics"""
        query = """
        SELECT 
            d.diagnosis_name,
            COUNT(*) as patient_count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage,
            ROUND(AVG(p.age), 1) as avg_age,
            ROUND(AVG(p.patient_satisfaction), 2) as avg_satisfaction,
            ROUND(AVG(p.ai_diagnosis_confidence), 3) as avg_ai_confidence
        FROM patients p
        JOIN diagnoses d ON p.diagnosis_id = d.diagnosis_id
        GROUP BY d.diagnosis_name
        ORDER BY patient_count DESC;
        """
        return pd.read_sql(query, self.engine)
    
    def profile_hospital_performance(self): ##statistique selon les hopitaux
        """Performance par hôpital"""
        query = """
        SELECT 
            h.hospital_name,
            COUNT(*) as patient_count,
            ROUND(AVG(p.patient_satisfaction), 2) as avg_satisfaction,
            ROUND(AVG(p.recovery_time), 1) as avg_recovery_time,
            COUNT(DISTINCT p.doctor_id) as doctor_count,
            COUNT(DISTINCT p.diagnosis_id) as diagnosis_types
        FROM patients p
        JOIN hospitals h ON p.hospital_id = h.hospital_id
        GROUP BY h.hospital_name
        ORDER BY patient_count DESC;
        """
        return pd.read_sql(query, self.engine)
    
    def profile_medication_effectiveness(self): ##statistique selon les medicament
        """Efficacité des médicaments"""
        query = """
        SELECT 
            m.medication_name,
            COUNT(*) as prescriptions,
            ROUND(AVG(p.recovery_time), 1) as avg_recovery_time,
            ROUND(AVG(p.patient_satisfaction), 2) as avg_satisfaction,
            ROUND(AVG(p.treatment_duration), 1) as avg_treatment_duration
        FROM patients p
        JOIN medications m ON p.medication_id = m.medication_id
        GROUP BY m.medication_name
        ORDER BY prescriptions DESC;
        """
        return pd.read_sql(query, self.engine)
    
    def profile_doctor_workload(self):  ##statistique des docteur
        """Charge de travail des médecins"""
        query = """
        SELECT 
            d.doctor_name,
            COUNT(*) as patient_count,
            ROUND(AVG(p.patient_satisfaction), 2) as avg_satisfaction,
            ROUND(AVG(p.ai_diagnosis_confidence), 3) as avg_ai_confidence,
            COUNT(DISTINCT p.diagnosis_id) as specialties_count,
            STRING_AGG(DISTINCT diag.diagnosis_name, ', ') as diagnoses
        FROM patients p
        JOIN doctors d ON p.doctor_id = d.doctor_id
        JOIN diagnoses diag ON p.diagnosis_id = diag.diagnosis_id
        GROUP BY d.doctor_name
        ORDER BY patient_count DESC;
        """
        return pd.read_sql(query, self.engine)
    
    def profile_age_groups(self):   ## statistique selon age
        """Analyse par groupes d'âge"""
        query = """
        SELECT 
            CASE 
                WHEN age < 30 THEN '18-29'
                WHEN age BETWEEN 30 AND 44 THEN '30-44'
                WHEN age BETWEEN 45 AND 59 THEN '45-59'
                WHEN age BETWEEN 60 AND 74 THEN '60-74'
                ELSE '75+'
            END as age_group,
            COUNT(*) as patient_count,
            ROUND(AVG(blood_pressure), 1) as avg_blood_pressure,
            ROUND(AVG(heart_rate), 1) as avg_heart_rate,
            ROUND(AVG(recovery_time), 1) as avg_recovery_time,
            ROUND(AVG(patient_satisfaction), 2) as avg_satisfaction
        FROM patients
        GROUP BY age_group
        ORDER BY age_group;
        """
        return pd.read_sql(query, self.engine)
    
    def profile_correlations(self):
        """Corrélations entre variables"""
        query = """
        SELECT 
            CORR(age, blood_pressure) as age_bp_correlation,
            CORR(age, heart_rate) as age_hr_correlation,
            CORR(age, recovery_time) as age_recovery_correlation,
            CORR(blood_pressure, heart_rate) as bp_hr_correlation,
            CORR(patient_satisfaction, recovery_time) as satisfaction_recovery_correlation,
            CORR(ai_diagnosis_confidence, patient_satisfaction) as ai_satisfaction_correlation
        FROM patients;
        """
        return pd.read_sql(query, self.engine)
    
    def generate_full_profile(self):
        """Génère un profil complet"""
        logger.info("Génération du profil complet des données...")
        
        profile = {
            'demographics': self.profile_patients_demographics(),
            'diagnosis_distribution': self.profile_diagnosis_distribution(),
            'hospital_performance': self.profile_hospital_performance(),
            'medication_effectiveness': self.profile_medication_effectiveness(),
            'doctor_workload': self.profile_doctor_workload(),
            'age_groups': self.profile_age_groups(),
            'correlations': self.profile_correlations()
        }
        
        # Statistiques générales
        with self.engine.connect() as conn:
            total_patients = pd.read_sql("SELECT COUNT(*) FROM patients", conn).iloc[0,0]
            profile['total_patients'] = total_patients
        
        logger.info("Profil généré avec succès")
        return profile

if __name__ == "__main__":
    profiler = DataProfiler()
    profile = profiler.generate_full_profile()
    
    print("\n=== PROFIL DÉMOGRAPHIQUE ===")
    print(profile['demographics'])
    
    print("\n=== DISTRIBUTION DES DIAGNOSTICS ===")
    print(profile['diagnosis_distribution'].head(10))
    
    print("\n=== PERFORMANCE DES HÔPITAUX ===")
    print(profile['hospital_performance'])
    
    print("\n=== CORRÉLATIONS ===")
    print(profile['correlations'])