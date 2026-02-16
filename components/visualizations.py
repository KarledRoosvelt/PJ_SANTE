import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from scripts.data_profiling import DataProfiler

def display_visualizations_tab(profiler):
    st.header("📈 Visualisations Interactives")

    with st.spinner("Chargement des données de visualisation..."):
        profile = profiler.generate_full_profile()

    # Age Distribution
    st.subheader("Distribution par Âge")
    with profiler.engine.connect() as conn:
        age_data = pd.read_sql("SELECT age FROM patients", conn)

    fig_age = px.histogram(age_data, x='age',
                          title='Distribution des Âges des Patients',
                          nbins=30,
                          color_discrete_sequence=['skyblue'])
    fig_age.update_layout(xaxis_title='Âge', yaxis_title='Fréquence')
    st.plotly_chart(fig_age, use_container_width=True)

    # Diagnosis Analysis
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top Diagnostics")
        top_diagnoses = profile['diagnosis_distribution'].head(10)
        fig_diag_bar = px.bar(top_diagnoses,
                             x='patient_count',
                             y='diagnosis_name',
                             orientation='h',
                             title='Top 10 Diagnostics',
                             color='patient_count',
                             color_continuous_scale='Viridis')
        fig_diag_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_diag_bar, use_container_width=True)

    with col2:
        st.subheader("Répartition Diagnostics")
        fig_diag_pie = px.pie(top_diagnoses,
                             values='patient_count',
                             names='diagnosis_name',
                             title='Répartition des Top Diagnostics')
        st.plotly_chart(fig_diag_pie, use_container_width=True)

    # Hospital Performance
    st.subheader("Performance Hospitalière")
    hospital_perf = profile['hospital_performance'].head(10)
    fig_hospital = go.Figure()

    fig_hospital.add_trace(go.Bar(
        x=hospital_perf['hospital_name'],
        y=hospital_perf['avg_satisfaction'],
        name='Satisfaction Moyenne',
        marker_color='lightgreen'
    ))

    fig_hospital.add_trace(go.Scatter(
        x=hospital_perf['hospital_name'],
        y=hospital_perf['patient_count'],
        name='Nombre de Patients',
        yaxis='y2',
        mode='lines+markers',
        line=dict(color='red')
    ))

    fig_hospital.update_layout(
        title='Satisfaction et Volume par Hôpital',
        xaxis=dict(tickangle=45),
        yaxis=dict(title='Satisfaction (1-5)'),
        yaxis2=dict(title='Nombre de Patients', overlaying='y', side='right')
    )
    st.plotly_chart(fig_hospital, use_container_width=True)

    # Vital Signs Analysis
    st.subheader("Analyse des Signes Vitaux")

    col1, col2 = st.columns(2)

    with col1:
        # Blood Pressure
        bp_data = pd.read_sql("SELECT blood_pressure FROM patients WHERE blood_pressure IS NOT NULL", profiler.engine)
        fig_bp = px.histogram(bp_data, x='blood_pressure',
                             title='Distribution Tension Artérielle',
                             nbins=30,
                             color_discrete_sequence=['salmon'])
        fig_bp.update_layout(xaxis_title='Tension Artérielle', yaxis_title='Fréquence')
        st.plotly_chart(fig_bp, use_container_width=True)

    with col2:
        # Heart Rate
        hr_data = pd.read_sql("SELECT heart_rate FROM patients WHERE heart_rate IS NOT NULL", profiler.engine)
        fig_hr = px.histogram(hr_data, x='heart_rate',
                             title='Distribution Rythme Cardiaque',
                             nbins=30,
                             color_discrete_sequence=['orange'])
        fig_hr.update_layout(xaxis_title='Rythme Cardiaque', yaxis_title='Fréquence')
        st.plotly_chart(fig_hr, use_container_width=True)

    # Recovery Time Analysis
    st.subheader("Analyse des Temps de Récupération")
    recovery_data = pd.read_sql("""
        SELECT d.diagnosis_name, AVG(p.recovery_time) as avg_recovery
        FROM patients p
        JOIN diagnoses d ON p.diagnosis_id = d.diagnosis_id
        GROUP BY d.diagnosis_name
        ORDER BY avg_recovery DESC
        LIMIT 15
    """, profiler.engine)

    fig_recovery = px.bar(recovery_data,
                         x='diagnosis_name',
                         y='avg_recovery',
                         title='Temps de Récupération Moyen par Diagnostic',
                         color='avg_recovery',
                         color_continuous_scale='Reds')
    fig_recovery.update_layout(xaxis_title='Diagnostic', yaxis_title='Jours de Récupération')
    fig_recovery.update_xaxes(tickangle=45)
    st.plotly_chart(fig_recovery, use_container_width=True)

    # AI Confidence vs Satisfaction
    st.subheader("Confiance IA vs Satisfaction Patient")
    ai_data = pd.read_sql("""
        SELECT ai_diagnosis_confidence, patient_satisfaction
        FROM patients
        WHERE ai_diagnosis_confidence IS NOT NULL
        AND patient_satisfaction IS NOT NULL
        LIMIT 1000
    """, profiler.engine)

    fig_ai = px.scatter(ai_data,
                       x='ai_diagnosis_confidence',
                       y='patient_satisfaction',
                       title='Relation Confiance IA - Satisfaction Patient',
                       trendline="ols",
                       color='patient_satisfaction',
                       color_continuous_scale='Blues')
    fig_ai.update_layout(xaxis_title='Confiance IA', yaxis_title='Satisfaction Patient')
    st.plotly_chart(fig_ai, use_container_width=True)
