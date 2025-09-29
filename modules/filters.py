import pandas as pd

def filter_data(df: pd.DataFrame) -> pd.DataFrame:

    # Spaltennamen vereinheitlichen
    df.columns = df.columns.str.strip().str.replace('\ufeff', '', regex=False)

    # Pflichtspalten prüfen
    required = ["Company Name", "GovernancePillarScore", "Close Price (USD)", "Date"]
    for col in required:
        if col not in df.columns:
            raise KeyError(f"Pflichtspalte fehlt: {col}")

    # Datumsformat umwandeln
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df.dropna(subset=["Date"], inplace=True)
    df["Year"] = df["Date"].dt.year

    # Aktienkurs und Governance-Scores konvertieren
    df["Close Price (USD)"] = pd.to_numeric(df["Close Price (USD)"], errors="coerce")
    df["GovernancePillarScore"] = pd.to_numeric(df["GovernancePillarScore"], errors="coerce")

    if "Sector" in df.columns:
        df["Sector"] = df["Sector"].astype(str).str.strip()

    # Check auf fehlende Werte
    df = df.dropna(subset=["Company Name", "GovernancePillarScore", "Close Price (USD)", "Year"])

    return df

