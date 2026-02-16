import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scripts.quality_analysis import DataQualityAnalyzer
from scripts.data_profiling import DataProfiler

def display_medications_anomalies_tab(profiler, quality_analyzer):
    st.header("💊 Médicaments & Anomalies")

    with st.spinner("Chargement des analyses..."):
        profile = profiler.generate_full_profile()
        report = quality_analyzer.generate_quality_report()

    # Medications Analysis
    st.subheader("Analyse des Médicaments")

    medications = profile['medication_effectiveness']
    col1, col2 = st.columns(2)

    with col1:
        # Top prescribed medications
        top_meds = medications.head(15)
        fig_meds_bar = px.bar(top_meds,
                             x='medication_name',
                             y='prescriptions',
                             title='Top 15 Médicaments les Plus Prescrits',
                             color='prescriptions',
                             color_continuous_scale='Greens')
        fig_meds_bar.update_xaxes(tickangle=45)
        st.plotly_chart(fig_meds_bar, use_container_width=True)

    with col2:
        # Medication effectiveness scatter
        fig_meds_scatter = px.scatter(medications,
                                     x='avg_recovery_time',
                                     y='avg_satisfaction',
                                     size='prescriptions',
                                     color='prescriptions',
                                     hover_name='medication_name',
                                     title='Efficacité des Médicaments',
                                     labels={'avg_recovery_time': 'Récupération Moyenne (jours)',
                                            'avg_satisfaction': 'Satisfaction Moyenne',
                                            'prescriptions': 'Nombre de Prescriptions'})
        st.plotly_chart(fig_meds_scatter, use_container_width=True)

    # Medication details table
    with st.expander("Voir tous les médicaments"):
        st.dataframe(medications)

    # Anomalies Analysis
    st.subheader("Détection d'Anomalies Statistiques")

    anomalies = report['anomalies']
    st.write(f"**Nombre d'anomalies détectées:** {len(anomalies)}")

    if len(anomalies) > 0:
        # Anomalies by type
        anomaly_counts = {
            'Âge': anomalies['age_zscore'].notna().sum(),
            'Tension Artérielle': anomalies['bp_zscore'].notna().sum(),
            'Rythme Cardiaque': anomalies['hr_zscore'].notna().sum()
        }

        fig_anomalies = go.Figure(data=[
            go.Bar(x=list(anomaly_counts.keys()),
                  y=list(anomaly_counts.values()),
                  marker_color=['red', 'blue', 'green'])
        ])
        fig_anomalies.update_layout(
            title='Répartition des Anomalies par Type',
            xaxis_title='Type d\'Anomalie',
            yaxis_title='Nombre d\'Anomalies'
        )
        st.plotly_chart(fig_anomalies, use_container_width=True)

        # Anomalies distribution
        fig_anomalies_dist = go.Figure()
        fig_anomalies_dist.add_trace(go.Histogram(
            x=anomalies['age_zscore'].dropna(),
            name='Âge Z-Score',
            opacity=0.7,
            nbinsx=20
        ))
        fig_anomalies_dist.add_trace(go.Histogram(
            x=anomalies['bp_zscore'].dropna(),
            name='Tension Z-Score',
            opacity=0.7,
            nbinsx=20
        ))
        fig_anomalies_dist.add_trace(go.Histogram(
            x=anomalies['hr_zscore'].dropna(),
            name='Rythme Z-Score',
            opacity=0.7,
            nbinsx=20
        ))
        fig_anomalies_dist.update_layout(
            title='Distribution des Scores Z des Anomalies',
            barmode='overlay',
            xaxis_title='Score Z',
            yaxis_title='Fréquence'
        )
        st.plotly_chart(fig_anomalies_dist, use_container_width=True)

        with st.expander("Voir les anomalies détaillées"):
            st.dataframe(anomalies.head(20))
    else:
        st.success("✅ Aucune anomalie statistique détectée dans les données.")

    # Summary
    st.subheader("Résumé")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Médicaments", len(medications))
        st.metric("Médicament le Plus Prescrit", medications.iloc[0]['medication_name'])
    with col2:
        st.metric("Anomalies Totales", len(anomalies))
        if len(anomalies) > 0:
            most_common_anomaly = max(anomaly_counts, key=anomaly_counts.get)
            st.metric("Type Principal d'Anomalie", most_common_anomaly)
