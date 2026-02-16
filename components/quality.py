import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from scripts.quality_analysis import DataQualityAnalyzer

def display_quality_tab(quality_analyzer):
    st.header("📊 Analyse de la Qualité des Données")

    with st.spinner("Génération du rapport de qualité..."):
        report = quality_analyzer.generate_quality_report()

    # KPIs Cards
    col1, col2, col3, col4 = st.columns(4)
    completeness = report['completeness'].iloc[0]

    with col1:
        st.metric("Complétude Âge", f"{completeness['age_completeness_pct']:.1f}%")
    with col2:
        st.metric("Complétude Satisfaction", f"{completeness['satisfaction_completeness_pct']:.1f}%")
    with col3:
        st.metric("Cohérence Âge", f"{report['consistency'].iloc[0]['valid_age_pct']:.1f}%")
    with col4:
        st.metric("Anomalies", len(report['anomalies']))

    # Detailed Completeness
    st.subheader("Complétude des Données")
    completeness_data = {
        'Champ': ['Âge', 'Genre', 'Tension', 'Rythme Cardiaque', 'Température', 'Satisfaction', 'Confiance IA'],
        'Pourcentage': [
            completeness['age_completeness_pct'],
            completeness['gender_completeness_pct'],
            completeness['bp_completeness_pct'],
            completeness['hr_completeness_pct'],
            completeness['temp_completeness_pct'],
            completeness['satisfaction_completeness_pct'],
            completeness['ai_confidence_completeness_pct']
        ]
    }
    fig_completeness = px.bar(completeness_data, x='Champ', y='Pourcentage',
                             title='Complétude par Champ',
                             color='Pourcentage',
                             color_continuous_scale='RdYlGn')
    st.plotly_chart(fig_completeness, use_container_width=True)

    # Consistency
    st.subheader("Cohérence des Données")
    consistency = report['consistency'].iloc[0]
    consistency_data = {
        'Champ': ['Âge', 'Genre', 'Tension', 'Rythme Cardiaque', 'Température', 'Satisfaction', 'Confiance IA'],
        'Validité (%)': [
            consistency['valid_age_pct'],
            consistency['valid_gender_pct'],
            consistency['valid_bp_pct'],
            consistency['valid_hr_pct'],
            consistency['valid_temp_pct'],
            consistency['valid_satisfaction_pct'],
            consistency['valid_ai_confidence_pct']
        ]
    }
    fig_consistency = px.bar(consistency_data, x='Champ', y='Validité (%)',
                            title='Validité des Données par Champ',
                            color='Validité (%)',
                            color_continuous_scale='Blues')
    st.plotly_chart(fig_consistency, use_container_width=True)

    # Freshness
    st.subheader("Fraîcheur des Données")
    freshness = report['freshness'].iloc[0]
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Enregistrements", f"{freshness['total_records']:,}")
    with col2:
        st.metric("Plus Ancien", str(freshness['oldest_record'])[:10])
    with col3:
        st.metric("Plus Récent", str(freshness['newest_record'])[:10])

    # Anomalies
    st.subheader("Détection d'Anomalies")
    anomalies = report['anomalies']
    st.write(f"Nombre d'anomalies détectées: {len(anomalies)}")

    if len(anomalies) > 0:
        # Anomalies chart
        anomaly_types = anomalies['age_zscore'].notna().sum(), anomalies['bp_zscore'].notna().sum(), anomalies['hr_zscore'].notna().sum()
        fig_anomalies = go.Figure(data=[
            go.Bar(name='Âge', x=['Anomalies'], y=[anomaly_types[0]]),
            go.Bar(name='Tension', x=['Anomalies'], y=[anomaly_types[1]]),
            go.Bar(name='Rythme Cardiaque', x=['Anomalies'], y=[anomaly_types[2]])
        ])
        fig_anomalies.update_layout(title='Types d\'Anomalies Détectées', barmode='stack')
        st.plotly_chart(fig_anomalies, use_container_width=True)

        with st.expander("Voir les anomalies détaillées"):
            st.dataframe(anomalies.head(20))
    else:
        st.success("Aucune anomalie statistique détectée.")
