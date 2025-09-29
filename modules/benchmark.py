import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

def benchmark_governance(df: pd.DataFrame) -> None:
    """
    Zeigt, wie stark einzelne Unternehmen im Hinblick auf ihren Governance-Score vom Median ihrer Branche abweichen.
    """

    st.header("Governance-Benchmarking nach Branche")

    # Jahresauswahl
    jahre = df["Year"].dropna().unique()
    jahre.sort()
    selected_year = st.selectbox("Analysejahr auswählen", jahre)

    # Datenfilterung nach Jahr
    df_filtered = df[df["Year"] == selected_year].copy()

    # Prüfen auf notwendige Spalten
    notwendige_spalten = ["Company Name", "Sektor", "GovernancePillarScore"]
    if not all(spalte in df_filtered.columns for spalte in notwendige_spalten):
        st.error("Es fehlen eine oder mehrere erforderliche Spalten im Datensatz.")
        return

    # Median-Score je Branche
    mediane = df_filtered.groupby("Sektor")["GovernancePillarScore"].median()

    # Abweichung zum Median
    df_filtered["GovernanceDeltaToMedian"] = df_filtered.apply(
        lambda row: row["GovernancePillarScore"] - mediane.get(row["Sektor"], np.nan),
        axis=1
    )

    # Boxplot
    fig = px.box(
        df_filtered,
        x="Sektor",
        y="GovernancePillarScore",
        points="all",
        title=f"Verteilung der Governance-Scores nach Branche ({selected_year})",
        labels={"GovernancePillarScore": "Governance Score"},
        color="Sektor"
    )

    st.plotly_chart(fig, use_container_width=True)

    # Tabelle mit Abweichungen
    with st.expander("Tabelle mit Score-Abweichungen einblenden"):
        # Grundtabelle
        base_cols = [
            "Company Name", "Sektor", "GovernancePillarScore", "GovernanceDeltaToMedian"
        ]
        table_df = df_filtered[base_cols].copy()

        # Bereinigung jeses Unternehmen nur ein Eintrag (Mittelwert)
        only_once = st.checkbox("Je Unternehmen nur eine Zeile (Mittelwert)", value=True)
        if only_once:
            grouped = (table_df
                       .groupby(["Company Name", "Sektor"], as_index=False)
                       .agg({
                           "GovernancePillarScore": "mean",
                           "GovernanceDeltaToMedian": "mean"
                       }))
            grouped["Anzahl_Einträge"] = table_df.groupby(["Company Name", "Sektor"]).size().values
            table_df = grouped

        # Suche nach Unternehmen oder Sektor
        q = st.text_input("Suche (Unternehmen/Sektor)", value="")
        if q:
            mask = (
                table_df["Company Name"].str.contains(q, case=False, na=False)
                | table_df["Sektor"].str.contains(q, case=False, na=False)
            )
            table_df = table_df[mask]

        # Sortierung nach Abweichung vor der Formatierung
        if "GovernanceDeltaToMedian" in table_df.columns:
            table_df = table_df.sort_values("GovernanceDeltaToMedian", ascending=False)

        # Nachkommastellen ausblenden
        for c in ["GovernancePillarScore", "GovernanceDeltaToMedian"]:
            if c in table_df.columns:
                table_df[c] = table_df[c].apply(lambda x: "" if pd.isna(x) else f"{x:.0f}")

        # Spaltennamen für die Darstellung
        display_df = table_df.rename(columns={
            "Company Name": "Unternehmen",
            "GovernancePillarScore": "Governance Score",
            "GovernanceDeltaToMedian": "Abweichung"
        })

        # Index ausblenden
        display_df = display_df.reset_index(drop=True)
        st.dataframe(display_df, use_container_width=True)
