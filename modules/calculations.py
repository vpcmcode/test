import pandas as pd
import numpy as np

def calculate_returns(df: pd.DataFrame, min_months_per_year: int = 12, partial_policy: str = "strict", min_months_for_partial: int = 6) -> pd.DataFrame:
    """
    Berechnung der prozentualen Jahresrendite aus Monatsdaten.
    """
    df = df.copy()
    df.columns = df.columns.str.strip().str.replace('\ufeff', '', regex=False)

    req = ["Company Name", "Date", "Close Price (USD)"]
    missing = [c for c in req if c not in df.columns]
    if missing:
        raise KeyError(f"Fehlende Spalten: {', '.join(missing)}")

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])
    df["Close Price (USD)"] = pd.to_numeric(df["Close Price (USD)"], errors="coerce")
    df = df[df["Close Price (USD)"] > 0].sort_values(["Company Name", "Date"])

    # Eindeutigkeit je Monat
    df["Month"] = df["Date"].dt.to_period("M")
    df = df.drop_duplicates(subset=["Company Name", "Month"], keep="first")

    # Monatsrenditen je Kalenderjahr
    df["Year"] = df["Date"].dt.year
    df["PeriodReturn"] = (
        df.groupby(["Company Name", "Year"], sort=False)["Close Price (USD)"].pct_change()
    )

    # Jahresaggregation
    def _annual_from_group(g: pd.DataFrame) -> float:
        # Monate und Renditen ermitteln
        months = g["Month"].sort_values().unique()
        n_months = len(months)
        s = g["PeriodReturn"].dropna()
        n_returns = s.size

        # Vollständiges Jahr vorhanden?
        full_year = (n_months >= min_months_per_year) and (n_returns >= max(1, min_months_per_year - 1))
        total_factor = (1.0 + s).prod() if n_returns > 0 else np.nan

        if partial_policy == "strict":
            if not full_year:
                return np.nan
            return total_factor - 1.0

        elif partial_policy == "ytd_partial":

            if full_year:
                return total_factor - 1.0
            if n_months < max(2, min_months_for_partial) or n_returns < 1:
                return np.nan
            return total_factor - 1.0

        elif partial_policy == "annualize_by_span":

            if full_year:
                return total_factor - 1.0
            if n_months < max(2, min_months_for_partial) or n_returns < 1:
                return np.nan
            # Spannweite in Monaten zwischen erstem und letztem Monat
            m0, m1 = months[0], months[-1]
            try:
                months_span = (m1.year - m0.year) * 12 + (m1.month - m0.month)
            except AttributeError:
                # Fallback für PeriodArray mit .ordinal
                months_span = m1.ordinal - m0.ordinal
            if months_span <= 0:
                return np.nan
            monthly_factor = total_factor ** (1.0 / months_span)
            return monthly_factor ** 12 - 1.0

        else:
            raise ValueError("partial_policy must be 'strict', 'ytd_partial', or 'annualize_by_span'")

    annual = (
        df.groupby(["Company Name", "Year"], sort=False)
          .apply(_annual_from_group)
          .reset_index(name="AnnualReturn")
    )
    annual["AnnualReturnPct"] = annual["AnnualReturn"] * 100.0

    out = df.merge(
        annual[["Company Name", "Year", "AnnualReturnPct"]],
        on=["Company Name", "Year"], how="left"
    ).drop(columns=["PeriodReturn", "Month"])

    return out