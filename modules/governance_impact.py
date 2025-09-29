import math
import pandas as pd
import streamlit as st
import plotly.express as px
from scipy.stats import linregress

def governance_vs_rendite(df: pd.DataFrame, clip_mode: str = "quantile"):
    """
    Visualisiert den Zusammenhang von GovernancePillarScore und AnnualReturnPct.
    """

    st.subheader("Governance-Score im Vergleich zur Rendite")

    # Spaltenname vereinheitlichen
    if "Sektor" in df.columns and "Sector" not in df.columns:
        df = df.rename(columns={"Sektor": "Sector"})

    required = ["Company Name", "GovernancePillarScore", "AnnualReturnPct", "Year", "Sector"]
    if not all(col in df.columns for col in required):
        st.error("Für diese Analyse fehlen eine oder mehrere Spalten (erwartet: Company Name, GovernancePillarScore, AnnualReturnPct, Year, Sector).")
        return

    # Säubern & Typisieren
    df = df.dropna(subset=required).copy()
    df["AnnualReturnPct"] = pd.to_numeric(df["AnnualReturnPct"], errors="coerce")
    df["GovernancePillarScore"] = pd.to_numeric(df["GovernancePillarScore"], errors="coerce")
    df = df.dropna(subset=["AnnualReturnPct", "GovernancePillarScore"])

    if clip_mode == "hard":
        df = df[df["AnnualReturnPct"].between(-100, 100)]
    elif clip_mode == "quantile":
        q01, q99 = df["AnnualReturnPct"].quantile([0.01, 0.99])
        df = df[df["AnnualReturnPct"].between(q01, q99)]

    # Auswahl der Sektoren
    sektoren = sorted(df["Sector"].dropna().unique())
    selected_sektoren = st.multiselect("Sektoren auswählen", sektoren, default=sektoren)
    if not selected_sektoren:
        st.warning("Bitte mindestens einen Sektor auswählen.")
        return
    df = df[df["Sector"].isin(selected_sektoren)]

    modus = st.radio("Darstellungsmodus", ["Alle Unternehmen", "Sektordurchschnitte", "Einzelunternehmen"], horizontal=True)
    show_points = st.checkbox("Datenpunkte anzeigen", value=True)

    if modus == "Einzelunternehmen":
        companies = df["Company Name"].dropna().unique().tolist()
        all_selected = st.checkbox("Alle Unternehmen anzeigen", value=True)
        selected = companies if all_selected else st.multiselect("Unternehmen auswählen", companies, default=companies[:10])
        if not selected:
            st.warning("Bitte mindestens ein Unternehmen auswählen.")
            return
        df_filtered = df[df["Company Name"].isin(selected)].copy()
        color_col = "Company Name"
        multi_trend = True
    elif modus == "Sektordurchschnitte":
        df_filtered = (
            df.groupby(["Year", "Sector"], as_index=False)
              .agg({"GovernancePillarScore": "mean", "AnnualReturnPct": "mean"})
        )
        color_col = "Sector"
        multi_trend = True
    else:
        df_filtered = df.copy()
        color_col = None
        multi_trend = False

    if df_filtered.empty:
        st.warning("Keine Daten für die aktuelle Auswahl.")
        return

    # Y-Achsenbereich
    scale_all = st.checkbox("Alle Werte anzeigen", value=False)
    ret = pd.to_numeric(df_filtered["AnnualReturnPct"], errors="coerce").dropna()
    if ret.empty:
        y_min, y_max = -20.0, 20.0
    elif scale_all:
        y_min = math.floor(ret.min() / 5.0) * 5.0
        y_max = math.ceil(ret.max() / 5.0) * 5.0
        if y_max - y_min < 10.0:
            y_min -= 5.0
            y_max += 5.0
    else:
        q05 = float(ret.quantile(0.05))
        q95 = float(ret.quantile(0.95))
        R = max(10.0, 1.15 * max(abs(q05), abs(q95)))
        R = math.ceil(R / 5.0) * 5.0
        y_min, y_max = -R, R

    # Regressionskennzahlen
    x = pd.to_numeric(df_filtered["GovernancePillarScore"], errors="coerce")
    y = pd.to_numeric(df_filtered["AnnualReturnPct"], errors="coerce")
    mask = x.notna() & y.notna()
    if mask.sum() >= 2:
        slope, intercept, r_value, p_value, std_err = linregress(x[mask], y[mask])
        title_r = f"{r_value:.2f}"
        title_slope = f"{slope:.3f}"
        title_p = f"{p_value:.3g}"
    else:
        title_r = title_slope = title_p = "-"

    fig = px.scatter(
        df_filtered,
        x="GovernancePillarScore",
        y="AnnualReturnPct",
        color=color_col if multi_trend else None,
        trendline="ols",
        hover_data=df_filtered.columns,
        opacity=0.6 if show_points else 0.0,
        title=f"Governance-Score vs. Jahresrendite (global: r = {title_r}, Steigung {title_slope} %-Pkt/Scorepunkt, p = {title_p})"
    )
    fig.add_hline(y=0, line_dash="dot", line_width=1)

    fig.update_layout(
        width=1000, height=600,
        xaxis_title="Governance-Score",
        yaxis_title="Rendite (%)",
        title_font=dict(size=20),
        xaxis=dict(title_font=dict(size=16), tickfont=dict(size=14)),
        yaxis=dict(title_font=dict(size=16), tickfont=dict(size=14),
                   range=[y_min, y_max], zeroline=True, ticksuffix=" %"),
        font=dict(family="Arial", size=14),
        margin=dict(l=60, r=30, t=60, b=60),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Kennzahlen
    stats = df_filtered["AnnualReturnPct"].agg(
        Mittelwert="mean", Median="median", StdAbw="std",
        Minimum="min", Maximum="max", N="count"
    ).round(2).to_frame().T
    stats.index = ["Jahresrendite (%)"]
    st.markdown("### Statistische Kennzahlen")
    st.dataframe(stats)

    st.markdown(f"**Globaler Korrelationskoeffizient:** {title_r}  **Steigung:** {title_slope} %-Pkt je Scorepunkt  **p:** {title_p}")
    if isinstance(r_value, float) and isinstance(p_value, float) and (mask.sum() >= 2):
        if r_value > 0.2 and p_value < 0.05:
            st.info("Signifikanter positiver Zusammenhang (global).")
        elif r_value < -0.2 and p_value < 0.05:
            st.info("Signifikanter negativer Zusammenhang (global).")
        else:
            st.info("Kein statistisch signifikanter Zusammenhang (global).")

    # Verteilungen
    with st.expander("Histogramme einblenden", expanded=False):
        col1, col2 = st.columns(2)

        # Histogramm Jahresrendite
        with col1:
            ret_series = pd.to_numeric(df_filtered["AnnualReturnPct"], errors="coerce").dropna()
            if not ret_series.empty:
                fig_hist_ret = px.histogram(
                    ret_series.to_frame(name="AnnualReturnPct"),
                    x="AnnualReturnPct",
                    nbins=40,
                    title="Verteilung: Jahresrendite"
                )
                fig_hist_ret.update_layout(
                    height=350,
                    xaxis_title="Rendite (%)",
                    yaxis_title="Häufigkeit",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)"
                )
                fig_hist_ret.update_xaxes(ticksuffix=" %")
                st.plotly_chart(fig_hist_ret, use_container_width=True)
            else:
                st.info("Keine Daten für die Jahresrendite-Histogramm-Anzeige.")

        # Histogramm Governance-Score
        with col2:
            gov_series = pd.to_numeric(df_filtered["GovernancePillarScore"], errors="coerce").dropna()
            if not gov_series.empty:
                fig_hist_gov = px.histogram(
                    gov_series.to_frame(name="GovernancePillarScore"),
                    x="GovernancePillarScore",
                    nbins=40,
                    title="Verteilung: Governance-Score"
                )
                fig_hist_gov.update_layout(
                    height=350,
                    xaxis_title="Governance-Score",
                    yaxis_title="Häufigkeit",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(fig_hist_gov, use_container_width=True)
            else:
                st.info("Keine Daten für die Governance-Score-Histogramm-Anzeige.")

    # Gruppenspezifische Kennzahlen
    if multi_trend and st.checkbox("Gruppenspezifische Regressionsstatistik anzeigen", value=False):
        group_col = color_col
        out_rows = []
        for key, g in df_filtered.groupby(group_col):
            xx = pd.to_numeric(g["GovernancePillarScore"], errors="coerce")
            yy = pd.to_numeric(g["AnnualReturnPct"], errors="coerce")
            m = xx.notna() & yy.notna()
            if m.sum() >= 2:
                sl, itc, r, p, se = linregress(xx[m], yy[m])
                out_rows.append({"Gruppe": key, "r": round(r, 3), "Steigung": round(sl, 4), "p": f"{p:.3g}", "N": int(m.sum())})
        if out_rows:
            st.markdown("### Regressionsstatistik je Gruppe")
            st.dataframe(pd.DataFrame(out_rows))