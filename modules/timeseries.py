import math
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from scipy.stats import pearsonr

def governance_timeseries(df: pd.DataFrame):
    """
    Visualisierung der Entwicklung von Governance-Scores und Jahresrenditen im Zeitverlauf.
    """

    st.subheader("Zeitliche Entwicklung von Governance-Score und Rendite")

    modus = st.radio("Darstellungsmodus", ["Einzelunternehmen", "Sektortrends"], horizontal=True)

    if modus == "Einzelunternehmen":
        companies = df["Company Name"].dropna().unique()
        selected = st.multiselect("Unternehmen auswählen", sorted(companies), default=sorted(companies)[:1])

        if not selected:
            st.warning("Bitte mindestens ein Unternehmen auswählen.")
            return

        df_filtered = df[df["Company Name"].isin(selected)]
        cols_needed = ["Year", "GovernancePillarScore", "AnnualReturnPct", "Company Name"]
        if not all(col in df_filtered.columns for col in cols_needed):
            st.error("Fehlende Spalten – erforderlich: Year, GovernancePillarScore, AnnualReturnPct, Company Name")
            return

        df_filtered = df_filtered[cols_needed].dropna().sort_values("Year")
        if df_filtered.empty:
            st.warning("Keine gültigen Daten gefunden.")
            return

        # Anpassung der Renditeachse
        ret_all = pd.to_numeric(df_filtered["AnnualReturnPct"], errors="coerce")
        if ret_all.notna().any():
            q_low = float(ret_all.quantile(0.05))
            q_high = float(ret_all.quantile(0.95))
            pad = max(5.0, 0.1 * (q_high - q_low))

            y2_min = float(min(q_low - pad, 0.0))
            y2_max = float(max(q_high + pad, 0.0))

            real_min = float(ret_all.min())
            real_max = float(ret_all.max())
            y2_min = min(y2_min, real_min)
            y2_max = max(y2_max, real_max)
        else:
            y2_min, y2_max = -10.0, 10.0

        step = 5.0
        y2_min = math.floor(y2_min / step) * step
        y2_max = math.ceil(y2_max / step) * step
        if y2_max - y2_min < step:  # Sicherheitsabstand
            y2_min -= step
            y2_max += step

        x_min = int(df_filtered["Year"].min())
        x_max = int(df_filtered["Year"].max())

        fig = go.Figure()
        for firm in selected:
            data = df_filtered[df_filtered["Company Name"] == firm]
            fig.add_trace(go.Scatter(
                x=data["Year"],
                y=data["GovernancePillarScore"],
                name=f"{firm} – Governance-Score",
                mode="lines+markers",
                yaxis="y1"
            ))
            fig.add_trace(go.Scatter(
                x=data["Year"],
                y=data["AnnualReturnPct"],
                name=f"{firm} – Jahresrendite (%)",
                mode="lines+markers",
                yaxis="y2",
                hovertemplate="Jahr %{x}<br>Rendite %{y:.1f} %<extra></extra>"
            ))

        # Nullreferenz
        fig.add_shape(
            type="line",
            x0=x_min, x1=x_max, y0=0, y1=0,
            xref="x", yref="y2",
            line=dict(width=1, dash="dot")
        )

        fig.update_layout(
            title="Zeitliche Entwicklung: Governance & Rendite (Einzelunternehmen)",
            xaxis_title="Jahr",
            yaxis=dict(title="Governance-Score", side="left"),
            yaxis2=dict(
                title="Rendite (%)",
                side="right",
                overlaying="y",
                showgrid=False,
                range=[y2_min, y2_max],
                zeroline=True,
                ticksuffix=" %"
            ),
            legend=dict(x=0.01, y=0.99),
            height=600
        )
        st.plotly_chart(fig, use_container_width=True)

        # Korrelation und kurze Interpretation
        for firm in selected:
            sub = df_filtered[df_filtered["Company Name"] == firm][["GovernancePillarScore", "AnnualReturnPct"]].copy()
            sub = sub.apply(pd.to_numeric, errors="coerce").dropna()
            n = len(sub)
            if n >= 3:
                r, p = pearsonr(sub["GovernancePillarScore"], sub["AnnualReturnPct"])
                r_val = float(r)
                p_val = float(p)
                if p_val < 0.05 and r_val > 0:
                    interp = "signifikanter positiver Zusammenhang"
                elif p_val < 0.05 and r_val < 0:
                    interp = "signifikanter negativer Zusammenhang"
                else:
                    interp = "kein statistisch signifikanter Zusammenhang"
                st.info(f"{firm}: r = {r_val:.2f}, p = {p_val:.3f}, n = {n} – {interp}.")
            else:
                st.info(f"{firm}: zu wenige Beobachtungen für eine belastbare Korrelation (n = {n}).")
        st.markdown(
            """
            <div style="font-size:1.0rem; line-height:1.6; margin-top:0.25rem;">
            <strong>Legende</strong><br/>
            <strong>r</strong> Pearson Korrelationskoeffizient von −1 bis +1. Gibt Richtung und Stärke eines linearen Zusammenhangs an.<br/>
            <strong>p</strong> Signifikanzniveau der Korrelation. Werte unter 0,05 gelten als statistisch signifikant.<br/>
            <strong>n</strong> Anzahl der berücksichtigten Jahresbeobachtungen.<br/>
            Hinweis: Korrelation impliziert keine Kausalität.
            </div>
            """,
            unsafe_allow_html=True,
        )

    elif modus == "Sektortrends":
        sektoren = df["Sektor"].dropna().unique()
        selected_sectors = st.multiselect("Sektoren auswählen", sorted(sektoren), default=sorted(sektoren)[:3])

        if not selected_sectors:
            st.warning("Bitte mindestens einen Sektor auswählen.")
            return

        df_sector = df[df["Sektor"].isin(selected_sectors)].copy()
        df_sector = df_sector.dropna(subset=["Year", "Sektor", "GovernancePillarScore", "AnnualReturnPct"])

        df_grouped = (
            df_sector.groupby(["Year", "Sektor"])
            .agg({
                "GovernancePillarScore": "mean",
                "AnnualReturnPct": "mean"
            })
            .reset_index()
        )

        fig_score = px.line(
            df_grouped,
            x="Year",
            y="GovernancePillarScore",
            color="Sektor",
            title="Sektorale Entwicklung der Governance-Scores"
        )
        fig_score.update_layout(yaxis_title="Governance-Score", height=400)
        st.plotly_chart(fig_score, use_container_width=True)

        fig_return = px.line(
            df_grouped,
            x="Year",
            y="AnnualReturnPct",
            color="Sektor",
            title="Sektorale Entwicklung der Jahresrenditen"
        )
        fig_return.update_layout(yaxis_title="Rendite (%)", height=400, yaxis=dict(ticksuffix=" %"))
        st.plotly_chart(fig_return, use_container_width=True)