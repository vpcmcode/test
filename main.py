import streamlit as st
import pandas as pd

# Gecachte Ladefunktion
DATA_PATH = "data/esg_dataset.xlsx"

@st.cache_data(show_spinner=False)
def load_excel(path: str) -> pd.DataFrame:
    """Laden und cachen der Datei."""
    return pd.read_excel(path, engine="openpyxl")

# Grundlayout
st.set_page_config(
    page_title="ESG-Governance Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

with st.sidebar:
    st.markdown("## ESG-Daten (Excel-Datei)")
    st.info("Die Datei ist bereits im Hintergrund geladen. Optionaler Bereich.")

# Datenvorbereitung
from modules.filters import filter_data
from modules.calculations import calculate_returns

# Analysefunktionen
from modules.governance_impact import governance_vs_rendite
from modules.governance_analysis import governance_analysis_view
from modules.correlation import correlation_analysis_view
from modules.benchmark import benchmark_governance
from modules.timeseries import governance_timeseries

# Fehlermeldung bei nicht vorhandenem Dataset
try:
    df_raw = load_excel(DATA_PATH)
except FileNotFoundError:
    st.error(f"Die Datenquelle '{DATA_PATH}' ist nicht verfügbar. Bitte stellen Sie sicher, dass die Datei im Repository vorhanden ist.")
    st.stop()

# Vorverarbeitung und Aggregation
df_filtered = filter_data(df_raw)
df = calculate_returns(df_filtered)

# Tabstruktur
tabs = st.tabs([
    "Governance-Scores und Renditeentwicklung im Vergleich",
    "Governance-Quintile",
    "Korrelation",
    "Branchen-Benchmarking",
    "Renditeentwicklung im Zeitverlauf"
])

with tabs[0]:
    governance_vs_rendite(df)

with tabs[1]:
    governance_analysis_view(df)

with tabs[2]:
    correlation_analysis_view(df)

with tabs[3]:
    benchmark_governance(df)

with tabs[4]:
    governance_timeseries(df)