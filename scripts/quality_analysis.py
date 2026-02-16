import psycopg2
import pandas as pd
import configparser
import logging
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataQualityAnalyzer:
    def __init__(self, config_file='../config/database.ini'):
        self.config = self.load_config(config_file)
        self.conn = None
        
    def load_config(self, filename):
        config = configparser.ConfigParser()
        config.read(filename)
        return config['postgresql']
    
    def connect(self):
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            self.conn = psycopg2.connect(db_url, sslmode="require")
        else:
            # fallback local: database.ini
            self.conn = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password']
            )
    
    def close(self):
        if self.conn:
            self.conn.close()
    
    def analyze_completeness(self):
        """Analyse la complétude des données"""
        query = """
        WITH completeness_stats AS (
            SELECT 
                COUNT(*) as total_records,
                COUNT(age) as age_complete,
                COUNT(gender) as gender_complete,
                COUNT(blood_pressure) as bp_complete,
                COUNT(heart_rate) as hr_complete,
                COUNT(temperature) as temp_complete,
                COUNT(patient_satisfaction) as satisfaction_complete,
                COUNT(ai_diagnosis_confidence) as ai_confidence_complete
            FROM patients
        )
        SELECT 
            total_records,
            ROUND(100.0 * age_complete / total_records, 2) as age_completeness_pct,
            ROUND(100.0 * gender_complete / total_records, 2) as gender_completeness_pct,
            ROUND(100.0 * bp_complete / total_records, 2) as bp_completeness_pct,
            ROUND(100.0 * hr_complete / total_records, 2) as hr_completeness_pct,
            ROUND(100.0 * temp_complete / total_records, 2) as temp_completeness_pct,
            ROUND(100.0 * satisfaction_complete / total_records, 2) as satisfaction_completeness_pct,
            ROUND(100.0 * ai_confidence_complete / total_records, 2) as ai_confidence_completeness_pct
        FROM completeness_stats
        """
        return pd.read_sql(query, self.conn)
    
    def analyze_duplicates(self):
        """Analyse les doublons potentiels"""
        query = """
        -- Doublons sur patient_id (ne devrait pas exister)
        SELECT patient_id, COUNT(*) as occurrence_count
        FROM patients
        GROUP BY patient_id
        HAVING COUNT(*) > 1;
        
        -- Patients avec mêmes caractéristiques (doublons potentiels)
        SELECT age, gender, diagnosis_id, hospital_id, 
               COUNT(*) as occurrence_count,
               ARRAY_AGG(patient_id) as patient_ids
        FROM patients
        GROUP BY age, gender, diagnosis_id, hospital_id
        HAVING COUNT(*) > 1
        ORDER BY COUNT(*) DESC
        LIMIT 10;
        """
        # Note: Cette requête retourne deux résultats, à adapter selon les besoins
        return pd.read_sql(query, self.conn)
    
    def analyze_freshness(self):
        """Analyse la fraîcheur des données"""
        query = """
        SELECT 
            MIN(created_at) as oldest_record,
            MAX(created_at) as newest_record,
            EXTRACT(day FROM (MAX(created_at) - MIN(created_at))) as data_span_days,
            COUNT(*) as total_records
        FROM patients;
        """
        return pd.read_sql(query, self.conn)
    
    def analyze_consistency(self):
        """Analyse la cohérence des données"""
        query = """
        WITH consistency_checks AS (
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN age BETWEEN 0 AND 120 THEN 1 ELSE 0 END) as valid_age,
                SUM(CASE WHEN gender IN ('Male', 'Female') THEN 1 ELSE 0 END) as valid_gender,
                SUM(CASE WHEN blood_pressure BETWEEN 60 AND 200 THEN 1 ELSE 0 END) as valid_bp,
                SUM(CASE WHEN heart_rate BETWEEN 40 AND 200 THEN 1 ELSE 0 END) as valid_hr,
                SUM(CASE WHEN temperature BETWEEN 35 AND 42 THEN 1 ELSE 0 END) as valid_temp,
                SUM(CASE WHEN patient_satisfaction BETWEEN 1 AND 5 THEN 1 ELSE 0 END) as valid_satisfaction,
                SUM(CASE WHEN ai_diagnosis_confidence BETWEEN 0 AND 1 THEN 1 ELSE 0 END) as valid_ai_confidence
            FROM patients
        )
        SELECT 
            total,
            ROUND(100.0 * valid_age / total, 2) as valid_age_pct,
            ROUND(100.0 * valid_gender / total, 2) as valid_gender_pct,
            ROUND(100.0 * valid_bp / total, 2) as valid_bp_pct,
            ROUND(100.0 * valid_hr / total, 2) as valid_hr_pct,
            ROUND(100.0 * valid_temp / total, 2) as valid_temp_pct,
            ROUND(100.0 * valid_satisfaction / total, 2) as valid_satisfaction_pct,
            ROUND(100.0 * valid_ai_confidence / total, 2) as valid_ai_confidence_pct
        FROM consistency_checks;
        """
        return pd.read_sql(query, self.conn)
    
    def analyze_anomalies(self):
        """Détecte les anomalies statistiques"""
        query = """
        -- Valeurs aberrantes (z-score > 3)
        WITH stats AS (
            SELECT 
                AVG(age) as avg_age, STDDEV(age) as stddev_age,
                AVG(blood_pressure) as avg_bp, STDDEV(blood_pressure) as stddev_bp,
                AVG(heart_rate) as avg_hr, STDDEV(heart_rate) as stddev_hr
            FROM patients
        )
        SELECT 
            p.patient_id, p.age, p.blood_pressure, p.heart_rate,
            ABS(p.age - s.avg_age) / NULLIF(s.stddev_age, 0) as age_zscore,
            ABS(p.blood_pressure - s.avg_bp) / NULLIF(s.stddev_bp, 0) as bp_zscore,
            ABS(p.heart_rate - s.avg_hr) / NULLIF(s.stddev_hr, 0) as hr_zscore
        FROM patients p
        CROSS JOIN stats s
        WHERE ABS(p.age - s.avg_age) / NULLIF(s.stddev_age, 0) > 3
           OR ABS(p.blood_pressure - s.avg_bp) / NULLIF(s.stddev_bp, 0) > 3
           OR ABS(p.heart_rate - s.avg_hr) / NULLIF(s.stddev_hr, 0) > 3
        LIMIT 20;
        """
        return pd.read_sql(query, self.conn)
    
    def generate_quality_report(self):
        """Génère un rapport complet de qualité des données"""
        self.connect()
        
        report = {
            'timestamp': datetime.now(),
            'completeness': self.analyze_completeness(),
            'freshness': self.analyze_freshness(),
            'consistency': self.analyze_consistency(),
            'anomalies': self.analyze_anomalies()
        }
        
        self.close()
        return report
    
    def save_report_to_csv(self, report, output_dir='../reports'):
        """Sauvegarde le rapport au format CSV"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for key, df in report.items():
            if isinstance(df, pd.DataFrame):
                filename = f"{output_dir}/quality_{key}_{timestamp}.csv"
                df.to_csv(filename, index=False)
                logger.info(f"Rapport {key} sauvegardé: {filename}")

if __name__ == "__main__":
    analyzer = DataQualityAnalyzer()
    report = analyzer.generate_quality_report()
    analyzer.save_report_to_csv(report)
    
    print("=== RAPPORT DE QUALITÉ DES DONNÉES ===")
    print("\n--- COMPLÉTUDE ---")
    print(report['completeness'])
    print("\n--- FRAÎCHEUR ---")
    print(report['freshness'])
    print("\n--- COHÉRENCE ---")
    print(report['consistency'])
    print("\n--- ANOMALIES (10 premiers) ---")
    print(report['anomalies'].head(10))