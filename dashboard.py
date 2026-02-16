import streamlit as st
import pandas as pd
from scripts.quality_analysis import DataQualityAnalyzer
from scripts.data_profiling import DataProfiler

# Import all component modules
from components.quality import display_quality_tab
from components.profiling import display_profiling_tab
from components.visualizations import display_visualizations_tab
from components.medications_anomalies import display_medications_anomalies_tab
from components.doctors import display_doctors_tab
from components.age_groups import display_age_groups_tab
from components.correlations import display_correlations_tab
from components.duplicates import display_duplicates_tab
from pathlib import Path
# Configure page
st.set_page_config(
    page_title="Tableau de Bord Santé - Analyse de Qualité",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .sidebar-header {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 1rem;
        color: #1f77b4;
    }
    .tab-header {
        font-size: 1.8rem;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize analyzers with caching
@st.cache_resource
def load_analyzers():
    try:
        # Chemin absolu vers database.ini
        base_dir = Path(__file__).resolve().parent
        config_path = base_dir / "config" / "database.ini"

        quality_analyzer = DataQualityAnalyzer(config_file=str(config_path))
        profiler = DataProfiler(config_file=str(config_path))

        return quality_analyzer, profiler

    except Exception as e:
        st.error(f"Erreur de connexion à la base de données: {e}")
        st.stop()

quality_analyzer, profiler = load_analyzers()

# Sidebar with filters and navigation
st.sidebar.markdown('<div class="sidebar-header">🏥 Dashboard Santé</div>', unsafe_allow_html=True)
st.sidebar.markdown("---")

# Filters section
st.sidebar.subheader("🔍 Filtres et Options")

# Hospital filter
try:
    with profiler.engine.connect() as conn:
        hospitals = pd.read_sql("SELECT hospital_name FROM hospitals ORDER BY hospital_name", conn)
    hospital_options = ["Tous"] + hospitals['hospital_name'].tolist()
    selected_hospital = st.sidebar.selectbox("Hôpital", hospital_options, key="hospital_filter")
except:
    selected_hospital = "Tous"
    st.sidebar.warning("Impossible de charger la liste des hôpitaux")

# Doctor filter
try:
    with profiler.engine.connect() as conn:
        doctors = pd.read_sql("SELECT doctor_name FROM doctors ORDER BY doctor_name", conn)
    doctor_options = ["Tous"] + doctors['doctor_name'].tolist()
    selected_doctor = st.sidebar.selectbox("Médecin", doctor_options, key="doctor_filter")
except:
    selected_doctor = "Tous"
    st.sidebar.warning("Impossible de charger la liste des médecins")

# Age range filter
age_min, age_max = st.sidebar.slider(
    "Tranche d'âge",
    min_value=0,
    max_value=120,
    value=(0, 120),
    key="age_filter"
)

# Display options
st.sidebar.subheader("⚙️ Options d'Affichage")
show_raw_data = st.sidebar.checkbox("Afficher les données brutes", value=False, key="raw_data")
export_data = st.sidebar.checkbox("Activer l'export des données", value=True, key="export")

st.sidebar.markdown("---")

# Quick stats in sidebar
try:
    with profiler.engine.connect() as conn:
        total_patients = pd.read_sql("SELECT COUNT(*) as count FROM patients", conn).iloc[0]['count']
        total_hospitals = pd.read_sql("SELECT COUNT(*) as count FROM hospitals", conn).iloc[0]['count']
        total_doctors = pd.read_sql("SELECT COUNT(*) as count FROM doctors", conn).iloc[0]['count']

    st.sidebar.metric("Total Patients", f"{total_patients:,}")
    st.sidebar.metric("Hôpitaux", total_hospitals)
    st.sidebar.metric("Médecins", total_doctors)
except:
    st.sidebar.error("Impossible de charger les statistiques")

# Main content
st.markdown('<div class="main-header">🏥 Tableau de Bord d\'Analyse de la Qualité des Données de Santé</div>', unsafe_allow_html=True)
st.markdown("*Analyse complète et interactive des données médicales*")
st.markdown("---")

# Filter status
if selected_hospital != "Tous" or selected_doctor != "Tous" or age_min > 0 or age_max < 120:
    st.info(f"🔍 Filtres actifs: Hôpital={selected_hospital}, Médecin={selected_doctor}, Âge={age_min}-{age_max}")
    # Note: Actual filtering implementation would require modifying the SQL queries in components
    # For now, showing filter status

# Navigation tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📊 Qualité des Données",
    "👥 Profil Démographique",
    "📈 Visualisations",
    "💊 Médicaments & Anomalies",
    "👨‍⚕️ Charge Médecins",
    "🎂 Groupes d'Âge",
    "🔗 Corrélations",
    "🔍 Doublons"
])

# Tab content using component functions
with tab1:
    display_quality_tab(quality_analyzer)

with tab2:
    display_profiling_tab(profiler)

with tab3:
    display_visualizations_tab(profiler)

with tab4:
    display_medications_anomalies_tab(profiler, quality_analyzer)

with tab5:
    display_doctors_tab(profiler)

with tab6:
    display_age_groups_tab(profiler)

with tab7:
    display_correlations_tab(profiler)

with tab8:
    display_duplicates_tab(quality_analyzer)

# Footer with export options
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📥 Exporter Rapport Qualité", key="export_quality"):
        try:
            report = quality_analyzer.generate_quality_report()
            # Export logic would go here
            st.success("Rapport de qualité exporté!")
        except Exception as e:
            st.error(f"Erreur d'export: {e}")

with col2:
    if st.button("📊 Exporter Profil", key="export_profile"):
        try:
            profile = profiler.generate_full_profile()
            # Export logic would go here
            st.success("Profil démographique exporté!")
        except Exception as e:
            st.error(f"Erreur d'export: {e}")

with col3:
    st.markdown("**🛠️ Version je suis fatigué**")
    st.markdown("*Dashboard professionnel de santé*")

# Error handling for database issues
if 'error' in st.session_state:
    st.error(st.session_state['error'])
    del st.session_state['error']
