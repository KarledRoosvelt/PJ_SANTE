import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scripts.data_profiling import DataProfiler

def display_doctors_tab(profiler):
    st.header("👨‍⚕️ Charge de Travail des Médecins")

    with st.spinner("Analyse de la charge de travail médicale..."):
        profile = profiler.generate_full_profile()
        doctor_workload = profile['doctor_workload']

    # KPIs
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Médecins", len(doctor_workload))
    with col2:
        avg_patients = doctor_workload['patient_count'].mean()
        st.metric("Patients Moyens par Médecin", f"{avg_patients:.1f}")
    with col3:
        busiest_doctor = doctor_workload.iloc[0]['doctor_name']
        st.metric("Médecin le Plus Occupé", busiest_doctor)

    # Doctor Workload Distribution
    st.subheader("Distribution de la Charge de Travail")

    fig_workload = px.histogram(doctor_workload,
                               x='patient_count',
                               title='Distribution du Nombre de Patients par Médecin',
                               nbins=20,
                               color_discrete_sequence=['lightcoral'])
    fig_workload.update_layout(xaxis_title='Nombre de Patients', yaxis_title='Nombre de Médecins')
    st.plotly_chart(fig_workload, use_container_width=True)

    # Top Doctors by Patient Count
    st.subheader("Top Médecins par Nombre de Patients")
    top_doctors = doctor_workload.head(15)

    fig_top_doctors = px.bar(top_doctors,
                            x='doctor_name',
                            y='patient_count',
                            title='Top 15 Médecins par Volume de Patients',
                            color='avg_satisfaction',
                            color_continuous_scale='RdYlGn')
    fig_top_doctors.update_layout(xaxis_title='Médecin', yaxis_title='Nombre de Patients')
    fig_top_doctors.update_xaxes(tickangle=45)
    st.plotly_chart(fig_top_doctors, use_container_width=True)

    # Doctor Performance Scatter
    st.subheader("Performance des Médecins")
    fig_performance = px.scatter(doctor_workload,
                                x='patient_count',
                                y='avg_satisfaction',
                                size='specialties_count',
                                color='avg_ai_confidence',
                                hover_name='doctor_name',
                                title='Performance des Médecins',
                                labels={'patient_count': 'Nombre de Patients',
                                       'avg_satisfaction': 'Satisfaction Moyenne',
                                       'specialties_count': 'Nombre de Spécialités',
                                       'avg_ai_confidence': 'Confiance IA Moyenne'},
                                color_continuous_scale='Viridis')
    st.plotly_chart(fig_performance, use_container_width=True)

    # Specialties Analysis
    st.subheader("Analyse des Spécialités")
    specialties_data = doctor_workload.groupby('specialties_count').agg({
        'doctor_name': 'count',
        'patient_count': 'mean',
        'avg_satisfaction': 'mean'
    }).reset_index()

    fig_specialties = go.Figure()
    fig_specialties.add_trace(go.Bar(
        x=specialties_data['specialties_count'],
        y=specialties_data['doctor_name'],
        name='Nombre de Médecins',
        marker_color='skyblue'
    ))
    fig_specialties.add_trace(go.Scatter(
        x=specialties_data['specialties_count'],
        y=specialties_data['avg_satisfaction'],
        name='Satisfaction Moyenne',
        yaxis='y2',
        mode='lines+markers',
        line=dict(color='red')
    ))
    fig_specialties.update_layout(
        title='Spécialités et Performance',
        xaxis=dict(title='Nombre de Spécialités'),
        yaxis=dict(title='Nombre de Médecins'),
        yaxis2=dict(title='Satisfaction Moyenne', overlaying='y', side='right')
    )
    st.plotly_chart(fig_specialties, use_container_width=True)

    # Detailed Table
    with st.expander("Voir tous les médecins"):
        st.dataframe(doctor_workload)

    # Summary Insights
    st.subheader("Insights Clés")
    workload_stats = doctor_workload['patient_count'].describe()

    insights_col1, insights_col2 = st.columns(2)
    with insights_col1:
        st.info(f"**Charge moyenne:** {workload_stats['mean']:.1f} patients par médecin")
        st.info(f"**Écart-type:** {workload_stats['std']:.1f} patients")
    with insights_col2:
        st.info(f"**Médecin le moins occupé:** {workload_stats['min']:.0f} patients")
        st.info(f"**Médecin le plus occupé:** {workload_stats['max']:.0f} patients")
