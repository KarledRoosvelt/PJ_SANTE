import psycopg2
import pandas as pd
from psycopg2 import sql
from psycopg2.extras import execute_values
import configparser
from pathlib import Path
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HealthDataImporter:
    def __init__(self, config_file='../config/database.ini'):
        self.config = self.load_config(config_file)
        self.conn = None
        self.cursor = None
        
    def load_config(self, filename):
        """Charge la configuration de la base de données"""
        config = configparser.ConfigParser()
        config.read(filename)
        return config['postgresql']
    
    def connect(self):
        """Établit la connexion à la base de données"""
        try:
            self.conn = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password']
            )
            self.cursor = self.conn.cursor()
            logger.info("Connexion à la base de données établie")
        except Exception as e:
            logger.error(f"Erreur de connexion: {e}")
            raise
    
    def close(self):
        """Ferme la connexion"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            logger.info("Connexion fermée")
    
    def load_csv_data(self, csv_path):
        """Charge les données CSV"""
        df = pd.read_csv(csv_path,encoding='latin1')
        logger.info(f"Fichier CSV chargé: {len(df)} lignes")
        return df
    
    def import_reference_data(self, df):
        """Importe les données de référence (hôpitaux, médecins, etc.)"""
        
        # Import des hôpitaux
        hospitals = df['Hospital_Name'].unique()
        hospital_data = [(h,) for h in hospitals]
        execute_values(self.cursor, 
                      "INSERT INTO hospitals (hospital_name) VALUES %s ON CONFLICT (hospital_name) DO NOTHING",
                      hospital_data)
        
        # Import des médecins
        doctors = df['Doctor_Name'].unique()
        doctor_data = [(d,) for d in doctors]
        execute_values(self.cursor,
                      "INSERT INTO doctors (doctor_name) VALUES %s ON CONFLICT (doctor_name) DO NOTHING",
                      doctor_data)
        
        # Import des diagnostics
        diagnoses = df['Diagnosis'].unique()
        diagnosis_data = [(d,) for d in diagnoses]
        execute_values(self.cursor,
                      "INSERT INTO diagnoses (diagnosis_name) VALUES %s ON CONFLICT (diagnosis_name) DO NOTHING",
                      diagnosis_data)
        
        # Import des médicaments
        medications = df['Medication'].unique()
        medication_data = [(m,) for m in medications]
        execute_values(self.cursor,
                      "INSERT INTO medications (medication_name) VALUES %s ON CONFLICT (medication_name) DO NOTHING",
                      medication_data)
        
        # Import des chirurgies
        surgeries = df['Surgery_Type'].unique()
        surgery_data = [(s,) for s in surgeries]
        execute_values(self.cursor,
                      "INSERT INTO surgeries (surgery_type) VALUES %s ON CONFLICT (surgery_type) DO NOTHING",
                      surgery_data)
        
        self.conn.commit()
        logger.info("Données de référence importées")
    
    def get_reference_ids(self):
        """Récupère les IDs des tables de référence"""
        self.cursor.execute("SELECT hospital_name, hospital_id FROM hospitals")
        hospital_dict = dict(self.cursor.fetchall())
        
        self.cursor.execute("SELECT doctor_name, doctor_id FROM doctors")
        doctor_dict = dict(self.cursor.fetchall())
        
        self.cursor.execute("SELECT diagnosis_name, diagnosis_id FROM diagnoses")
        diagnosis_dict = dict(self.cursor.fetchall())
        
        self.cursor.execute("SELECT medication_name, medication_id FROM medications")
        medication_dict = dict(self.cursor.fetchall())
        
        self.cursor.execute("SELECT surgery_type, surgery_id FROM surgeries")
        surgery_dict = dict(self.cursor.fetchall())
        
        return hospital_dict, doctor_dict, diagnosis_dict, medication_dict, surgery_dict
    
    def import_patients(self, df):
        """Importe les données des patients"""
        
        # Récupérer les IDs de référence
        hospital_dict, doctor_dict, diagnosis_dict, medication_dict, surgery_dict = self.get_reference_ids()
        
        # Préparer les données des patients
        patient_data = []
        for _, row in df.iterrows():
            patient_data.append((
                row['Patient_ID'],
                row['Age'],
                row['Gender'],
                row['Blood_Pressure'],
                row['Heart_Rate'],
                row['Temperature'],
                diagnosis_dict.get(row['Diagnosis']),
                medication_dict.get(row['Medication']),
                row['Treatment_Duration'],
                row['Insurance_Type'],
                doctor_dict.get(row['Doctor_Name']),
                hospital_dict.get(row['Hospital_Name']),
                row['Lab_Test_Results'],
                row['X-ray_Results'],
                surgery_dict.get(row['Surgery_Type']),
                row['Recovery_Time'],
                row['Allergies'],
                row['Family_History'],
                row['Patient_Satisfaction'],
                row['AI_Diagnosis_Confidence']
            ))
        
        # Insertion par lots
        execute_values(self.cursor, """
            INSERT INTO patients (
                patient_id, age, gender, blood_pressure, heart_rate, temperature,
                diagnosis_id, medication_id, treatment_duration, insurance_type,
                doctor_id, hospital_id, lab_test_results, xray_results,
                surgery_id, recovery_time, allergies, family_history,
                patient_satisfaction, ai_diagnosis_confidence
            ) VALUES %s
            ON CONFLICT (patient_id) DO UPDATE SET
                age = EXCLUDED.age,
                blood_pressure = EXCLUDED.blood_pressure,
                patient_satisfaction = EXCLUDED.patient_satisfaction
        """, patient_data)
        
        self.conn.commit()
        logger.info(f"{len(patient_data)} patients importés/mis à jour")
    
    def run(self, csv_path):
        """Exécute le processus complet d'importation"""
        try:
            self.connect()
            df = self.load_csv_data(csv_path)
            self.import_reference_data(df)
            self.import_patients(df)
            logger.info("Importation terminée avec succès")
        except Exception as e:
            print("ERREUR COMPLET:",e)
            raise
        finally:
            self.close()

if __name__ == "__main__":
    importer = HealthDataImporter()
    importer.run('../AI_in_HealthCare_Dataset.csv')