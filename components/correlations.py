import streamlit as st
import pandas as pd
import plotly.figure_factory as ff
import plotly.express as px
import numpy as np
from scripts.data_profiling import DataProfiler

def display_correlations_tab(profiler):
    st.header("🔗 Analyses de Corrélations")

    with st.spinner("Calcul des corrélations..."):
        profile = profiler.generate_full_profile()
        correlations = profile['correlations']

    # Correlation Matrix Display
    st.subheader("Matrice de Corrélations")

    corr_dict = correlations.iloc[0].to_dict()
    correlation_data = {
        'Variables': list(corr_dict.keys()),
        'Coefficient': list(corr_dict.values())
    }
    corr_df = pd.DataFrame(correlation_data)

    # Color coding for correlation strength
    def get_correlation_color(corr):
        abs_corr = abs(corr)
        if abs_corr >= 0.8:
            return '🔴 Forte' if corr > 0 else '🔵 Forte Négative'
        elif abs_corr >= 0.6:
            return '🟠 Modérée' if corr > 0 else '🔵 Modérée Négative'
        elif abs_corr >= 0.3:
            return '🟡 Faible' if corr > 0 else '🔵 Faible Négative'
        else:
            return '⚪ Très Faible'

    corr_df['Force'] = corr_df['Coefficient'].apply(get_correlation_color)
    corr_df['Coefficient'] = corr_df['Coefficient'].round(4)

    # Sort by absolute correlation strength
    corr_df['Abs_Corr'] = corr_df['Coefficient'].abs()
    corr_df = corr_df.sort_values('Abs_Corr', ascending=False).drop('Abs_Corr', axis=1)

    st.dataframe(corr_df.style.background_gradient(cmap='RdYlBu', subset=['Coefficient']))

    # Significant Correlations
    st.subheader("Corrélations Significatives")

    significant_corrs = {k: v for k, v in corr_dict.items() if abs(v) > 0.1}

    if significant_corrs:
        sig_corr_df = pd.DataFrame(list(significant_corrs.items()),
                                  columns=['Relation', 'Coefficient'])
        sig_corr_df['Coefficient'] = sig_corr_df['Coefficient'].round(4)
        sig_corr_df = sig_corr_df.sort_values('Coefficient', key=abs, ascending=False)

        fig_sig_corr = px.bar(sig_corr_df,
                             x='Relation',
                             y='Coefficient',
                             title='Corrélations Statistiquement Significatives (|r| > 0.1)',
                             color='Coefficient',
                             color_continuous_scale='RdBu')
        fig_sig_corr.update_layout(xaxis_title='Variables', yaxis_title='Coefficient de Corrélation')
        fig_sig_corr.update_xaxes(tickangle=45)
        st.plotly_chart(fig_sig_corr, use_container_width=True)

        # Interpretation
        st.subheader("Interprétation des Corrélations Clés")

        interpretations = []
        for relation, coeff in significant_corrs.items():
            var1, var2 = relation.replace('_correlation', '').replace('_corr', '').split('_', 1)
            var1_name = var1.replace('age', 'Âge').replace('bp', 'Tension').replace('hr', 'Rythme').replace('recovery', 'Récupération').replace('satisfaction', 'Satisfaction').replace('ai', 'IA')
            var2_name = var2.replace('bp', 'Tension').replace('hr', 'Rythme').replace('recovery', 'Récupération').replace('satisfaction', 'Satisfaction').replace('ai', 'IA')

            strength = "forte" if abs(coeff) > 0.7 else "modérée" if abs(coeff) > 0.5 else "faible"
            direction = "positive" if coeff > 0 else "négative"

            interp = f"**{var1_name} - {var2_name}**: Corrélation {strength} {direction} (r = {coeff:.3f})"
            interpretations.append(interp)

        for interp in interpretations:
            st.write(interp)

    else:
        st.warning("Aucune corrélation significative détectée dans les données.")

    # Correlation Heatmap
    st.subheader("Carte de Chaleur des Corrélations")

    # Get actual correlation matrix from database
    with profiler.engine.connect() as conn:
        corr_query = """
        SELECT
            CORR(age, blood_pressure) as age_bp,
            CORR(age, heart_rate) as age_hr,
            CORR(age, recovery_time) as age_recovery,
            CORR(blood_pressure, heart_rate) as bp_hr,
            CORR(blood_pressure, recovery_time) as bp_recovery,
            CORR(heart_rate, recovery_time) as hr_recovery,
            CORR(age, patient_satisfaction) as age_satisfaction,
            CORR(blood_pressure, patient_satisfaction) as bp_satisfaction,
            CORR(recovery_time, patient_satisfaction) as recovery_satisfaction,
            CORR(ai_diagnosis_confidence, patient_satisfaction) as ai_satisfaction
        FROM patients
        WHERE age IS NOT NULL AND blood_pressure IS NOT NULL AND heart_rate IS NOT NULL
            AND recovery_time IS NOT NULL AND patient_satisfaction IS NOT NULL
            AND ai_diagnosis_confidence IS NOT NULL
        """
        full_corr = pd.read_sql(corr_query, conn)

    if not full_corr.empty:
        corr_matrix = full_corr.iloc[0].values.reshape(1, -1)
        corr_labels = ['Âge-Tension', 'Âge-Rythme', 'Âge-Récupération', 'Tension-Rythme',
                      'Tension-Récupération', 'Rythme-Récupération', 'Âge-Satisfaction',
                      'Tension-Satisfaction', 'Récupération-Satisfaction', 'IA-Satisfaction']

        fig_heatmap = ff.create_annotated_heatmap(
            [corr_matrix[0]],
            x=corr_labels,
            y=['Corrélations'],
            annotation_text=[[f"{val:.3f}" for val in corr_matrix[0]]],
            colorscale='RdBu',
            showscale=True
        )
        fig_heatmap.update_layout(title='Carte de Chaleur des Corrélations Inter-Variables')
        st.plotly_chart(fig_heatmap, use_container_width=True)
    else:
        st.info("Données insuffisantes pour générer la carte de chaleur complète.")

    # Scatter Plots for Key Correlations
    st.subheader("Nuages de Points pour Corrélations Clés")

    with profiler.engine.connect() as conn:
        scatter_data = pd.read_sql("""
        SELECT age, blood_pressure, heart_rate, recovery_time, patient_satisfaction, ai_diagnosis_confidence
        FROM patients
        WHERE age IS NOT NULL AND blood_pressure IS NOT NULL AND heart_rate IS NOT NULL
            AND recovery_time IS NOT NULL AND patient_satisfaction IS NOT NULL
            AND ai_diagnosis_confidence IS NOT NULL
        LIMIT 1000
        """, conn)

    if not scatter_data.empty:
        # Key scatter plots
        col1, col2 = st.columns(2)

        with col1:
            fig_scatter1 = px.scatter(scatter_data,
                                     x='age',
                                     y='blood_pressure',
                                     title='Âge vs Tension Artérielle',
                                     trendline="ols",
                                     color='patient_satisfaction',
                                     color_continuous_scale='Viridis')
            st.plotly_chart(fig_scatter1, use_container_width=True)

        with col2:
            fig_scatter2 = px.scatter(scatter_data,
                                     x='ai_diagnosis_confidence',
                                     y='patient_satisfaction',
                                     title='Confiance IA vs Satisfaction Patient',
                                     trendline="ols",
                                     color='recovery_time',
                                     color_continuous_scale='Plasma')
            st.plotly_chart(fig_scatter2, use_container_width=True)

    # Summary Statistics
    st.subheader("Résumé Statistique")
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Corrélations Calculées", len(corr_dict))
        significant_count = sum(1 for v in corr_dict.values() if abs(v) > 0.1)
        st.metric("Corrélations Significatives", significant_count)

    with col2:
        if significant_corrs:
            strongest_corr = max(significant_corrs.items(), key=lambda x: abs(x[1]))
            st.metric("Corrélation la Plus Forte", f"{strongest_corr[0]}: {strongest_corr[1]:.3f}")
        else:
            st.metric("Corrélation la Plus Forte", "N/A")
