import os
import psycopg2
import pandas as pd
from psycopg2.extras import execute_values
import configparser
from pathlib import Path
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class HealthDataImporter:
    def __init__(self, config_file="config/database.ini"):
        # ✅ chemin robuste : toujours relatif à la racine du projet
        # si tu lances depuis scripts/, ça marche aussi
        base_dir = Path(__file__).resolve().parent.parent  # .../AI_in_HealthCare_Dataset
        self.config_file = str((base_dir / config_file).resolve())

        self.config = None
        self.conn = None
        self.cursor = None

    def load_config(self, filename):
        """Charge la configuration database.ini (mode local seulement)"""
        path = Path(filename).resolve()
        if not path.exists():
            raise FileNotFoundError(f"database.ini introuvable: {path}")

        config = configparser.ConfigParser()
        config.read(path)

        if "postgresql" not in config:
            raise KeyError(
                f"Section [postgresql] introuvable dans {path}. Sections: {config.sections()}"
            )

        return config["postgresql"]

    def connect(self):
        """Établit la connexion à la base de données (Render ou Local)"""
        try:
            db_url = os.getenv("DATABASE_URL")

            if db_url:
                # ✅ Render / Cloud
                self.conn = psycopg2.connect(db_url, sslmode="require", connect_timeout=10)
            else:
                # ✅ Local via database.ini
                self.config = self.load_config(self.config_file)
                self.conn = psycopg2.connect(
                    host=self.config["host"],
                    port=self.config["port"],
                    database=self.config["database"],
                    user=self.config["user"],
                    password=self.config["password"],
                    connect_timeout=10
                )

            self.cursor = self.conn.cursor()
            logger.info("Connexion à la base de données établie ✅")

        except Exception as e:
            logger.error(f"Erreur de connexion: {e}")
            raise

    def close(self):
        """Ferme la connexion"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
                logger.info("Connexion fermée ✅")
        except Exception:
            pass

    def load_csv_data(self, csv_path):
        """Charge les données CSV"""
        csv_path = Path(csv_path).resolve()
        df = pd.read_csv(csv_path, encoding="latin1")
        logger.info(f"Fichier CSV chargé: {len(df)} lignes ✅ ({csv_path})")
        return df

    def import_reference_data(self, df):
        """Importe les données de référence (hôpitaux, médecins, etc.)"""

        # ✅ petit helper pour nettoyer NaN
        def safe_unique(col):
            return [x for x in df[col].dropna().unique()]

        # Import des hôpitaux
        hospitals = safe_unique("Hospital_Name")
        execute_values(
            self.cursor,
            "INSERT INTO hospitals (hospital_name) VALUES %s ON CONFLICT (hospital_name) DO NOTHING",
            [(h,) for h in hospitals]
        )

        # Import des médecins
        doctors = safe_unique("Doctor_Name")
        execute_values(
            self.cursor,
            "INSERT INTO doctors (doctor_name) VALUES %s ON CONFLICT (doctor_name) DO NOTHING",
            [(d,) for d in doctors]
        )

        # Import des diagnostics
        diagnoses = safe_unique("Diagnosis")
        execute_values(
            self.cursor,
            "INSERT INTO diagnoses (diagnosis_name) VALUES %s ON CONFLICT (diagnosis_name) DO NOTHING",
            [(d,) for d in diagnoses]
        )

        # Import des médicaments
        medications = safe_unique("Medication")
        execute_values(
            self.cursor,
            "INSERT INTO medications (medication_name) VALUES %s ON CONFLICT (medication_name) DO NOTHING",
            [(m,) for m in medications]
        )

        # Import des chirurgies
        surgeries = safe_unique("Surgery_Type")
        execute_values(
            self.cursor,
            "INSERT INTO surgeries (surgery_type) VALUES %s ON CONFLICT (surgery_type) DO NOTHING",
            [(s,) for s in surgeries]
        )

        self.conn.commit()
        logger.info("Données de référence importées ✅")

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

        hospital_dict, doctor_dict, diagnosis_dict, medication_dict, surgery_dict = self.get_reference_ids()

        patient_data = []
        for _, row in df.iterrows():
            patient_data.append((
                row.get("Patient_ID"),
                row.get("Age"),
                row.get("Gender"),
                row.get("Blood_Pressure"),
                row.get("Heart_Rate"),
                row.get("Temperature"),
                diagnosis_dict.get(row.get("Diagnosis")),
                medication_dict.get(row.get("Medication")),
                row.get("Treatment_Duration"),
                row.get("Insurance_Type"),
                doctor_dict.get(row.get("Doctor_Name")),
                hospital_dict.get(row.get("Hospital_Name")),
                row.get("Lab_Test_Results"),
                row.get("X-ray_Results"),
                surgery_dict.get(row.get("Surgery_Type")),
                row.get("Recovery_Time"),
                row.get("Allergies"),
                row.get("Family_History"),
                row.get("Patient_Satisfaction"),
                row.get("AI_Diagnosis_Confidence")
            ))

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
        logger.info(f"{len(patient_data)} patients importés/mis à jour ✅")

    def run(self, csv_path):
        """Exécute le processus complet d'importation"""
        try:
            self.connect()
            df = self.load_csv_data(csv_path)
            self.import_reference_data(df)
            self.import_patients(df)
            logger.info("Importation terminée avec succès ✅")

        except Exception as e:
            if self.conn:
                self.conn.rollback()
            logger.error(f"ERREUR COMPLÈTE: {e}")
            raise

        finally:
            self.close()


if __name__ == "__main__":
    importer = HealthDataImporter()

    # ✅ chemin CSV robuste (relatif à la racine projet)
    base_dir = Path(__file__).resolve().parent.parent
    csv_file = base_dir / "AI_in_HealthCare_Dataset.csv"  # adapte si ton fichier a un autre nom

    importer.run(str(csv_file))
