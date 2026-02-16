import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from scripts.data_profiling import DataProfiler

def display_age_groups_tab(profiler):
    st.header("🎂 Analyse par Groupes d'Âge")

    with st.spinner("Analyse démographique par âge..."):
        profile = profiler.generate_full_profile()
        age_groups = profile['age_groups']

    # Age Group KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Groupe le Plus Nombreux", age_groups.loc[age_groups['patient_count'].idxmax()]['age_group'])
    with col2:
        st.metric("Âge Moyen Global", f"{profile['demographics']['avg_age'].mean():.1f} ans")
    with col3:
        highest_bp = age_groups.loc[age_groups['avg_blood_pressure'].idxmax()]['age_group']
        st.metric("Tension la Plus Élevée", highest_bp)
    with col4:
        best_recovery = age_groups.loc[age_groups['avg_recovery_time'].idxmin()]['age_group']
        st.metric("Récupération la Plus Rapide", best_recovery)

    # Patient Distribution by Age Group
    st.subheader("Distribution des Patients par Groupe d'Âge")

    fig_patients = px.bar(age_groups,
                         x='age_group',
                         y='patient_count',
                         title='Nombre de Patients par Groupe d\'Âge',
                         color='patient_count',
                         color_continuous_scale='Blues')
    fig_patients.update_layout(xaxis_title='Groupe d\'Âge', yaxis_title='Nombre de Patients')
    st.plotly_chart(fig_patients, use_container_width=True)

    # Health Metrics by Age Group
    st.subheader("Métriques de Santé par Groupe d'Âge")

    # Create subplots for multiple metrics
    fig_metrics = go.Figure()

    # Blood Pressure
    fig_metrics.add_trace(go.Scatter(
        x=age_groups['age_group'],
        y=age_groups['avg_blood_pressure'],
        mode='lines+markers',
        name='Tension Artérielle Moyenne',
        line=dict(color='red', width=3),
        marker=dict(size=8)
    ))

    # Heart Rate
    fig_metrics.add_trace(go.Scatter(
        x=age_groups['age_group'],
        y=age_groups['avg_heart_rate'],
        mode='lines+markers',
        name='Rythme Cardiaque Moyen',
        line=dict(color='blue', width=3),
        marker=dict(size=8)
    ))

    fig_metrics.update_layout(
        title='Signes Vitaux par Groupe d\'Âge',
        xaxis_title='Groupe d\'Âge',
        yaxis_title='Valeur',
        legend_title='Métrique'
    )
    st.plotly_chart(fig_metrics, use_container_width=True)

    # Recovery Time and Satisfaction
    col1, col2 = st.columns(2)

    with col1:
        fig_recovery = px.bar(age_groups,
                             x='age_group',
                             y='avg_recovery_time',
                             title='Temps de Récupération Moyen',
                             color='avg_recovery_time',
                             color_continuous_scale='Reds')
        fig_recovery.update_layout(xaxis_title='Groupe d\'Âge', yaxis_title='Jours')
        st.plotly_chart(fig_recovery, use_container_width=True)

    with col2:
        fig_satisfaction = px.line(age_groups,
                                  x='age_group',
                                  y='avg_satisfaction',
                                  title='Satisfaction Moyenne par Âge',
                                  markers=True,
                                  line_shape='spline')
        fig_satisfaction.update_layout(xaxis_title='Groupe d\'Âge', yaxis_title='Satisfaction (1-5)')
        fig_satisfaction.update_traces(line=dict(color='green', width=3), marker=dict(size=10))
        st.plotly_chart(fig_satisfaction, use_container_width=True)

    # Comparative Analysis
    st.subheader("Analyse Comparative")

    # Create a comprehensive comparison table
    comparison_data = age_groups.set_index('age_group')[['patient_count', 'avg_blood_pressure', 'avg_heart_rate', 'avg_recovery_time', 'avg_satisfaction']]
    comparison_data.columns = ['Patients', 'Tension Moyenne', 'Rythme Cardiaque Moyen', 'Récupération Moyenne (jours)', 'Satisfaction Moyenne']

    # Normalize for comparison (0-1 scale)
    comparison_normalized = comparison_data.copy()
    for col in comparison_normalized.columns:
        comparison_normalized[col] = (comparison_normalized[col] - comparison_normalized[col].min()) / (comparison_normalized[col].max() - comparison_normalized[col].min())

    fig_comparison = px.imshow(comparison_normalized.T,
                              title='Comparaison Normalisée des Métriques par Groupe d\'Âge',
                              color_continuous_scale='RdYlBu_r',
                              aspect='auto')
    fig_comparison.update_layout(xaxis_title='Groupe d\'Âge', yaxis_title='Métrique')
    st.plotly_chart(fig_comparison, use_container_width=True)

    # Detailed Data Table
    with st.expander("Voir les données détaillées par groupe d'âge"):
        st.dataframe(age_groups)

    # Key Insights
    st.subheader("Insights par Groupe d'Âge")

    insights = []
    for _, row in age_groups.iterrows():
        age_group = row['age_group']
        patients = row['patient_count']
        bp = row['avg_blood_pressure']
        recovery = row['avg_recovery_time']
        satisfaction = row['avg_satisfaction']

        insight = f"**{age_group}**: {patients} patients, tension moyenne {bp:.1f}, récupération {recovery:.1f} jours, satisfaction {satisfaction:.2f}/5"
        insights.append(insight)

    for insight in insights:
        st.info(insight)
