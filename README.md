# Health Data Quality Analysis

Ce projet est une plateforme d'analyse de la qualité des données de santé. Il permet d'automatiser l'importation de données cliniques, d'effectuer un profilage statistique et de générer des rapports de qualité des données.

## 📋 Description

L'application permet de :
- Créer une structure de base de données relationnelle pour stocker des informations patients.
- Importer des données depuis un fichier CSV (`AI_in_HealthCare_Dataset.csv`).
- Analyser les distributions démographiques, les diagnostics et les performances hospitalières.
- Évaluer la qualité des données (complétude, cohérence, doublons, anomalies).

## 🛠️ Prérequis

- **Python 3.8+**
- **PostgreSQL** installé et configuré.
- Un environnement virtuel recommandé.

## ⚙️ Installation

1. Clonez ou téléchargez le projet.
2. Créez un environnement virtuel :
   ```bash
   python -m venv env
   source env/bin/scripts/activate  # Sur Windows: env\Scripts\activate
   ```
3. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

## 🗄️ Configuration de la Base de Données

1. Modifiez le fichier `config/database.ini` avec vos identifiants PostgreSQL :
   ```ini
   [postgresql]
   host=localhost
   port=5432
   database=votre_db
   user=votre_user
   password=votre_mot_de_passe
   ```

2. Créez les tables en exécutant le script SQL dans votre client PostgreSQL (pgAdmin, DBeaver, psql) :
   `scripts/create_tables.sql`

## 🚀 Exécution

Les scripts doivent être exécutés dans l'ordre suivant depuis le dossier `scripts/` :

1. **Importation des données :**
   ```bash
   python import_data.py
   ```
2. **Profilage des données :**
   ```bash
   python data_profiling.py
   ```
3. **Analyse de la qualité :**
   ```bash
   python quality_analysis.py
   ```

## 📂 Structure du Projet

- `config/` : Configuration de la base de données.
- `scripts/` :
  - `create_tables.sql` : Schéma de la base de données.
  - `import_data.py` : Importation du CSV vers PostgreSQL.
  - `data_profiling.py` : Analyses statistiques et distributions.
  - `quality_analysis.py` : Rapports sur la qualité des données.
- `notebooks/` : Analyses exploratoires interactives.
- `AI_in_HealthCare_Dataset.csv` : Dataset source.

## 📊 Rapports

Les rapports générés par `quality_analysis.py` sont sauvegardés dans un dossier `reports/` au format CSV.
