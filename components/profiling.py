import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from scripts.data_profiling import DataProfiler

def display_profiling_tab(profiler):
    st.header("👥 Profil Démographique Complet")

    with st.spinner("Génération du profil complet..."):
        profile = profiler.generate_full_profile()

    # Main KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Patients", f"{profile['total_patients']:,}")
    with col2:
        st.metric("Hôpitaux", len(profile['hospital_performance']))
    with col3:
        st.metric("Médecins", len(profile['doctor_workload']))
    with col4:
        st.metric("Diagnostics", len(profile['diagnosis_distribution']))

    # Demographics
    st.subheader("Distribution par Genre")
    demographics = profile['demographics']
    fig_gender = px.pie(demographics, values='patient_count', names='gender',
                       title='Répartition par Genre',
                       color_discrete_sequence=px.colors.qualitative.Set3)
    st.plotly_chart(fig_gender, use_container_width=True)

    # Age Groups
    st.subheader("Analyse par Groupes d'Âge")
    age_groups = profile['age_groups']
    fig_age_groups = go.Figure()
    fig_age_groups.add_trace(go.Bar(
        x=age_groups['age_group'],
        y=age_groups['patient_count'],
        name='Nombre de Patients',
        marker_color='lightblue'
    ))
    fig_age_groups.add_trace(go.Scatter(
        x=age_groups['age_group'],
        y=age_groups['avg_blood_pressure'],
        name='Tension Moyenne',
        yaxis='y2',
        mode='lines+markers',
        line=dict(color='red')
    ))
    fig_age_groups.update_layout(
        title='Patients et Tension par Groupe d\'Âge',
        yaxis=dict(title='Nombre de Patients'),
        yaxis2=dict(title='Tension Artérielle', overlaying='y', side='right'),
        xaxis=dict(title='Groupe d\'Âge')
    )
    st.plotly_chart(fig_age_groups, use_container_width=True)

    # Hospital Performance
    st.subheader("Performance des Hôpitaux")
    hospital_perf = profile['hospital_performance']
    fig_hospitals = px.scatter(hospital_perf,
                              x='avg_satisfaction',
                              y='patient_count',
                              size='doctor_count',
                              color='diagnosis_types',
                              hover_name='hospital_name',
                              title='Performance des Hôpitaux',
                              labels={'avg_satisfaction': 'Satisfaction Moyenne',
                                     'patient_count': 'Nombre de Patients',
                                     'doctor_count': 'Nombre de Médecins',
                                     'diagnosis_types': 'Types de Diagnostics'})
    st.plotly_chart(fig_hospitals, use_container_width=True)

    # Doctor Workload
    st.subheader("Charge de Travail des Médecins")
    doctor_workload = profile['doctor_workload']
    fig_doctors = px.bar(doctor_workload.head(15),
                        x='doctor_name',
                        y='patient_count',
                        title='Top 15 Médecins par Nombre de Patients',
                        color='avg_satisfaction',
                        color_continuous_scale='Viridis')
    fig_doctors.update_xaxes(tickangle=45)
    st.plotly_chart(fig_doctors, use_container_width=True)

    # Diagnosis Distribution
    st.subheader("Distribution des Diagnostics")
    diagnosis_dist = profile['diagnosis_distribution']
    fig_diagnosis = px.treemap(diagnosis_dist.head(20),
                              path=['diagnosis_name'],
                              values='patient_count',
                              title='Distribution des Diagnostics (Top 20)',
                              color='percentage',
                              color_continuous_scale='Blues')
    st.plotly_chart(fig_diagnosis, use_container_width=True)

    # Correlations
    st.subheader("Matrice de Corrélations")
    correlations = profile['correlations']
    corr_dict = correlations.iloc[0].to_dict()
    significant_corrs = {k: v for k, v in corr_dict.items() if abs(v) > 0.1}

    if significant_corrs:
        corr_df = pd.DataFrame(list(significant_corrs.items()),
                              columns=['Relation', 'Coefficient'])
        corr_df['Coefficient'] = corr_df['Coefficient'].round(3)
        fig_corr = px.bar(corr_df.sort_values('Coefficient', key=abs),
                         x='Relation',
                         y='Coefficient',
                         title='Corrélations Significatives (|r| > 0.1)',
                         color='Coefficient',
                         color_continuous_scale='RdBu')
        fig_corr.update_xaxes(tickangle=45)
        st.plotly_chart(fig_corr, use_container_width=True)
    else:
        st.write("Aucune corrélation significative détectée.")

    # Medication Effectiveness
    st.subheader("Efficacité des Médicaments")
    medications = profile['medication_effectiveness']
    fig_meds = px.scatter(medications,
                         x='avg_recovery_time',
                         y='avg_satisfaction',
                         size='prescriptions',
                         color='prescriptions',
                         hover_name='medication_name',
                         title='Efficacité des Médicaments',
                         labels={'avg_recovery_time': 'Temps de Récupération Moyen',
                                'avg_satisfaction': 'Satisfaction Moyenne',
                                'prescriptions': 'Nombre de Prescriptions'})
    st.plotly_chart(fig_meds, use_container_width=True)
