import pandas as pd
import streamlit as st
import plotly.express as px

def governance_analysis_view(df: pd.DataFrame):
    """
    Vergleich der durchschnittlichen Jahresrenditen nach ESG-Governance-Score-Quintilen.
    Ziel: Erkennen von Renditeunterschieden zwischen Gruppen mit verschiedenen Governance-Niveaus.
    """

    st.subheader("Governance-Score vs. Rendite (Gruppiert nach Quintilen)")

    # Jahresauswahl
    years = sorted(df["Year"].dropna().unique())
    selected_years = st.multiselect("Analysejahre", options=years, default=years)

    # Datenfilterung
    df_filtered = df[df["Year"].isin(selected_years)].copy()

    # Prüfung auf notewendige Spalten
    cols_needed = ["GovernancePillarScore", "AnnualReturnPct", "Company Name"]
    if not all(col in df_filtered.columns for col in cols_needed):
        st.error("Mindestens eine der benötigten Spalten fehlt.")
        return

    # Bereinigung auf valide numerische Werte
    df_filtered["GovernancePillarScore"] = pd.to_numeric(df_filtered["GovernancePillarScore"], errors="coerce")
    df_filtered["AnnualReturnPct"] = pd.to_numeric(df_filtered["AnnualReturnPct"], errors="coerce")
    df_filtered.dropna(subset=["GovernancePillarScore", "AnnualReturnPct"], inplace=True)

    if df_filtered.empty:
        st.warning("Keine verwertbaren Daten für die aktuelle Auswahl.")
        return

    # Governance-Quintile
    try:
        df_filtered["Governance Group"] = pd.qcut(
            df_filtered["GovernancePillarScore"],
            q=5,
            labels=["Sehr niedrig", "Niedrig", "Mittel", "Hoch", "Sehr hoch"]
        )
    except ValueError:
        st.warning("Nicht genügend Datenpunkte zur Bildung von Quintilen.")
        return

    # Durchschnittsrendite je Gruppe
    stats = (
        df_filtered.groupby("Governance Group", observed=True)["AnnualReturnPct"]
        .agg(["mean", "std", "count"])
        .rename(columns={
            "mean": "Durchschnitt",
            "std": "Standardabweichung",
            "count": "Unternehmensanzahl"
        })
        .reset_index()
    )
    stats["Governance Group"] = stats["Governance Group"].astype(str)

    # Rundung
    stats["Durchschnitt"] = stats["Durchschnitt"].round(2)
    stats["Standardabweichung"] = stats["Standardabweichung"].round(4)

    # Visualisierung
    title = f"Durchschnittliche Renditen pro Governance-Gruppe ({min(selected_years)}–{max(selected_years)})"
    fig = px.bar(
        stats,
        x="Governance Group",
        y="Durchschnitt",
        text="Durchschnitt",
        color="Governance Group",
        title=title,
        labels={
            "Governance Group": "Governance-Score (Quintil)",
            "Durchschnitt": "Ø Rendite (%)"
        },
        height=500
    )

    fig.update_layout(
        xaxis=dict(tickfont=dict(size=14)),
        yaxis=dict(tickfont=dict(size=14))
    )

    st.plotly_chart(fig, use_container_width=True)

    # Tabelle anzeigen
    st.markdown("### Statistische Kennzahlen je Gruppe")
    st.dataframe(stats.set_index("Governance Group"))
