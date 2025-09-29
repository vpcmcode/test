import pandas as pd
import streamlit as st
import plotly.express as px
from scipy.stats import pearsonr

def correlation_analysis_view(df: pd.DataFrame):
    """
    Analysefunktion zur unternehmensspezifischen Korrelation von ESG-Governance-Score
    und jährlicher Aktienrendite.
    """

    st.subheader("Governance-Score vs. Aktienrendite (Korrelation pro Unternehmen)")

    # Datenbereinigung
    cols_required = ["Company Name", "GovernancePillarScore", "AnnualReturnPct"]
    df = df.dropna(subset=cols_required)
    df["GovernancePillarScore"] = pd.to_numeric(df["GovernancePillarScore"], errors="coerce")
    df["AnnualReturnPct"] = pd.to_numeric(df["AnnualReturnPct"], errors="coerce")
    df = df.dropna(subset=["GovernancePillarScore", "AnnualReturnPct"])

    # Korrelationen je Unternehmen
    result = []
    for name, group in df.groupby("Company Name"):
        if len(group) >= 30:
            r, p = pearsonr(group["GovernancePillarScore"], group["AnnualReturnPct"])
            result.append({
                "Unternehmen": name,
                "Korrelationskoeffizient": round(r, 3),
                "p-Wert": round(p, 4),
                "Anzahl Beobachtungen": len(group)
            })

    if not result:
        st.warning("Nicht genügend Daten zur Berechnung von Korrelationen.")
        return

    df_corr = pd.DataFrame(result).sort_values(by="Korrelationskoeffizient", ascending=False)

    # Filterung
    st.markdown("### Korrelationsbereich auswählen")
    corr_range = st.slider("Korrelation (r)", -1.0, 1.0, (-1.0, 1.0), step=0.05)
    df_corr_filtered = df_corr[
        (df_corr["Korrelationskoeffizient"] >= corr_range[0]) &
        (df_corr["Korrelationskoeffizient"] <= corr_range[1])
    ]

    st.markdown("### Gefilterte Unternehmen (Tabelle)")
    df_show = df_corr_filtered.reset_index(drop=True)
    df_show.index = df_show.index + 1
    df_show.index.name = "Rang"
    st.dataframe(df_show)

    # Top/Flop Korrelationen
    st.markdown("### Top- und Flop-Korrelationen")
    top_n = st.slider("Wie viele anzeigen?", 1, 20, 5)

    top = df_corr.nlargest(top_n, "Korrelationskoeffizient").reset_index(drop=True)
    top.index += 1
    flop = df_corr.nsmallest(top_n, "Korrelationskoeffizient").reset_index(drop=True)
    flop.index += 1

    st.markdown("#### Höchste positive Korrelationen")
    st.dataframe(top)

    st.markdown("#### Stärkste negative Korrelationen")
    st.dataframe(flop)

    # Scatterplots
    st.markdown("### Scatterplots ausgewählter Unternehmen")
    selection = st.multiselect("Unternehmen auswählen", df_corr_filtered["Unternehmen"].tolist())

    for name in selection:
        subset = df[df["Company Name"] == name]
        fig = px.scatter(
            subset,
            x="GovernancePillarScore",
            y="AnnualReturnPct",
            trendline="ols",
            title=f"{name}: Governance-Score vs. Rendite",
            labels={
                "GovernancePillarScore": "Governance-Score",
                "AnnualReturnPct": "Rendite (%)"
            }
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

        # Interpretation
        row = df_corr[df_corr["Unternehmen"] == name].iloc[0]
        r = row["Korrelationskoeffizient"]
        p = row["p-Wert"]

        st.markdown("**Interpretation:**")
        if p < 0.05:
            if r > 0.2:
                st.success("Es liegt ein signifikanter positiver Zusammenhang zwischen Governance-Score und Rendite vor.")
            elif r < -0.2:
                st.success("Es liegt ein signifikanter negativer Zusammenhang zwischen Governance-Score und Rendite vor.")
            else:
                st.info("Der Zusammenhang ist statistisch signifikant, aber inhaltlich schwach ausgeprägt.")
        else:
            st.info("Für dieses Unternehmen besteht kein statistisch signifikanter Zusammenhang zwischen Governance-Score und Rendite.")

    # Aggregierte Auswertung
    st.markdown("### Aggregierte Auswertung")
    total = len(df_corr)
    pos = (df_corr["Korrelationskoeffizient"] > 0.2).sum()
    neg = (df_corr["Korrelationskoeffizient"] < -0.2).sum()
    neutral = total - pos - neg

    st.markdown(f"Es wurden **{total} Unternehmen** ausgewertet.")
    st.markdown(f"* **{pos} Unternehmen** zeigen eine **positive Korrelation** (r > 0.2)")
    st.markdown(f"* **{neg} Unternehmen** zeigen eine **negative Korrelation** (r < -0.2)")
    st.markdown(f"* **{neutral} Unternehmen** ohne signifikanten Zusammenhang")

    # Zusammenfassung
    st.markdown("### Interpretation der Ergebnisse")
    if pos > neg and pos > neutral:
        st.info("Die Mehrheit der Unternehmen weist einen positiven Zusammenhang zwischen Governance-Score und Rendite auf.")
    elif neg > pos and neg > neutral:
        st.info("Die Mehrheit der Unternehmen weist einen negativen Zusammenhang zwischen Governance-Score und Rendite auf.")
    elif neutral > pos and neutral > neg:
        st.info("Bei den meisten Unternehmen lässt sich kein signifikanter Zusammenhang zwischen Governance-Score und Rendite feststellen.")
    else:
        st.info("Die Verteilung der Korrelationen ist ausgewogen und lässt keinen eindeutigen Trend erkennen.")
