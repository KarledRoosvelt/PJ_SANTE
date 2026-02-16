import streamlit as st
import pandas as pd
import plotly.express as px
from scripts.quality_analysis import DataQualityAnalyzer

def display_duplicates_tab(quality_analyzer):
    st.header("🔍 Analyse des Doublons")

    with st.spinner("Recherche de doublons potentiels..."):
        quality_analyzer.connect()

        # Get potential duplicates
        duplicates_query = """
        SELECT age, gender, diagnosis_id, hospital_id,
               COUNT(*) as occurrence_count,
               ARRAY_AGG(patient_id) as patient_ids
        FROM patients
        GROUP BY age, gender, diagnosis_id, hospital_id
        HAVING COUNT(*) > 1
        ORDER BY COUNT(*) DESC
        LIMIT 50;
        """
        duplicates = pd.read_sql(duplicates_query, quality_analyzer.conn)

        # Get duplicate patient IDs (true duplicates on patient_id)
        true_duplicates_query = """
        SELECT patient_id, COUNT(*) as occurrence_count
        FROM patients
        GROUP BY patient_id
        HAVING COUNT(*) > 1
        ORDER BY COUNT(*) DESC;
        """
        true_duplicates = pd.read_sql(true_duplicates_query, quality_analyzer.conn)

        quality_analyzer.close()

    # KPIs
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Doublons Vrais (ID)", len(true_duplicates))
    with col2:
        st.metric("Doublons Potentiels", len(duplicates))
    with col3:
        if len(duplicates) > 0:
            avg_occurrences = duplicates['occurrence_count'].mean()
            st.metric("Occurrences Moyennes", f"{avg_occurrences:.1f}")
        else:
            st.metric("Occurrences Moyennes", "0")

    # True Duplicates Analysis
    st.subheader("Doublons Vrais (même ID patient)")

    if len(true_duplicates) > 0:
        st.error(f"⚠️ {len(true_duplicates)} doublons vrais détectés sur l'ID patient. Cela indique des problèmes d'intégrité des données.")

        fig_true_dup = px.bar(true_duplicates,
                             x='patient_id',
                             y='occurrence_count',
                             title='Doublons sur ID Patient',
                             color='occurrence_count',
                             color_continuous_scale='Reds')
        fig_true_dup.update_layout(xaxis_title='ID Patient', yaxis_title='Nombre d\'Occurrences')
        fig_true_dup.update_xaxes(type='category')
        st.plotly_chart(fig_true_dup, use_container_width=True)

        with st.expander("Voir les doublons vrais détaillés"):
            st.dataframe(true_duplicates)
    else:
        st.success("✅ Aucun doublon vrai détecté sur les IDs patients.")

    # Potential Duplicates Analysis
    st.subheader("Doublons Potentiels (mêmes caractéristiques)")

    if len(duplicates) > 0:
        st.warning(f"⚠️ {len(duplicates)} groupes de doublons potentiels détectés. Ces patients ont les mêmes âge, genre, diagnostic et hôpital.")

        # Occurrence distribution
        fig_occurrences = px.histogram(duplicates,
                                      x='occurrence_count',
                                      title='Distribution des Occurrences de Doublons Potentiels',
                                      nbins=int(max(duplicates['occurrence_count'].max(), 5)),
                                      color_discrete_sequence=['orange'])
        fig_occurrences.update_layout(xaxis_title='Nombre d\'Occurrences', yaxis_title='Nombre de Groupes')
        st.plotly_chart(fig_occurrences, use_container_width=True)

        # Top potential duplicates
        st.subheader("Top Doublons Potentiels")
        top_duplicates = duplicates.head(10)

        # Create readable format
        readable_duplicates = top_duplicates.copy()
        readable_duplicates['patient_ids'] = readable_duplicates['patient_ids'].apply(lambda x: ', '.join(map(str, x)) if x else '')

        st.dataframe(readable_duplicates[['age', 'gender', 'diagnosis_id', 'hospital_id', 'occurrence_count', 'patient_ids']])

        # Analysis by gender
        gender_duplicates = duplicates.groupby('gender').agg({
            'occurrence_count': ['count', 'sum', 'mean']
        }).round(2)
        gender_duplicates.columns = ['Nombre_Groupes', 'Total_Occurrences', 'Moyenne_Occurrences']

        st.subheader("Analyse par Genre")
        fig_gender_dup = px.pie(duplicates,
                               names='gender',
                               values='occurrence_count',
                               title='Répartition des Doublons Potentiels par Genre')
        st.plotly_chart(fig_gender_dup, use_container_width=True)

        with st.expander("Analyse détaillée par genre"):
            st.dataframe(gender_duplicates)

        # Age distribution of duplicates
        st.subheader("Distribution par Âge des Doublons")
        fig_age_dup = px.histogram(duplicates,
                                  x='age',
                                  title='Âges des Patients en Doublon Potentiel',
                                  nbins=20,
                                  color_discrete_sequence=['purple'])
        fig_age_dup.update_layout(xaxis_title='Âge', yaxis_title='Nombre de Groupes de Doublons')
        st.plotly_chart(fig_age_dup, use_container_width=True)

    else:
        st.success("✅ Aucun doublon potentiel détecté dans les données.")

    # Recommendations
    st.subheader("Recommandations")

    if len(true_duplicates) > 0:
        st.error("**Action Requise:** Les doublons vrais sur ID patient doivent être résolus immédiatement. Vérifiez la logique d'importation des données.")
    elif len(duplicates) > 0:
        st.warning("**Action Recommandée:** Les doublons potentiels devraient être examinés manuellement. Ils peuvent indiquer des erreurs de saisie ou des patients similaires.")
        st.info("**Suggestion:** Implémenter une validation plus stricte lors de l'importation pour éviter les doublons.")
    else:
        st.success("**Excellent:** Aucune duplication détectée dans les données.")

    # Summary
    st.subheader("Résumé de l'Analyse")
    summary_col1, summary_col2 = st.columns(2)

    with summary_col1:
        st.metric("Taux de Doublon Vrai", f"{len(true_duplicates)} / {len(duplicates) + len(true_duplicates)}" if (len(duplicates) + len(true_duplicates)) > 0 else "0%")
        st.metric("Groupes Potentiels", len(duplicates))

    with summary_col2:
        if len(duplicates) > 0:
            max_occurrences = duplicates['occurrence_count'].max()
            st.metric("Occurrences Max", max_occurrences)
        else:
            st.metric("Occurrences Max", "0")
        st.metric("Doublons Totaux", len(true_duplicates) + duplicates['occurrence_count'].sum() if len(duplicates) > 0 else 0)
