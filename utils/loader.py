from __future__ import annotations

import json
from pathlib import Path
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_XLSX = BASE_DIR / "data" / "DSCSCE.xlsx"
DEFAULT_PROGRESS = BASE_DIR / "data" / "user_progress.json"

NAME_FIXES = {
    "Brakedramon": "Breakdramon",
    "Hippogryphonmon": "HippoGryphonmon",
    "Angewoman": "Angewomon",
    "Raptormon": "Raptordramon",
}


def clean_name(val: object) -> str:
    if pd.isna(val):
        return ""
    s = str(val).strip()
    parts = s.split(" ", 1)
    if len(parts) == 2 and parts[0].isdigit():
        s = parts[1].strip()
    return NAME_FIXES.get(s, s)


@st.cache_data(show_spinner="Loading Digimon Cyber Sleuth Complete Edition data...")
def load_workbook_data(xlsx_path: str | Path = DEFAULT_XLSX) -> dict[str, pd.DataFrame]:
    path = Path(xlsx_path)
    xl = pd.ExcelFile(path)
    data: dict[str, pd.DataFrame] = {}

    for sheet in xl.sheet_names:
        df = xl.parse(sheet)
        df.columns = [str(c).strip() for c in df.columns]
        data[sheet] = df

    # Build unified Digimon master table (Field Guide + Stats)
    fg = data["Field Guide"].copy()
    stats = data["Stats"].copy()

    fg["Clean_Name"] = fg["Name"].apply(clean_name)
    stats["Clean_Name"] = stats["Name"].apply(clean_name)

    stats_cols = [
        c for c in stats.columns if c not in {"Name", "Stage", "Field Number", "Clean_Name"}
    ]
    dex = fg.merge(
        stats[["Clean_Name"] + stats_cols],
        on="Clean_Name",
        how="left",
    )
    data["dex"] = dex

    # Normalize unified Digivolvution sheet
    digi = data["Digivolvution"].copy()
    digi["Base_Clean"] = digi["BaseDigimon"].apply(clean_name)
    digi["Target_Clean"] = digi["Target Digivolution"].apply(clean_name)
    data["digi_clean"] = digi

    # Normalize Memory UP column header in case of lingering typo
    mem = data["Memory UP"].copy()
    if "Verison" in mem.columns and "Game" not in mem.columns:
        mem = mem.rename(columns={"Verison": "Game"})
    data["Memory UP"] = mem

    return data


def load_progress(progress_path: Path = DEFAULT_PROGRESS) -> dict:
    if progress_path.exists():
        try:
            return json.loads(progress_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {
        "memory_cap": 150,
        "team": [None] * 11,
        "obtained_dex": [],
        "completed_cases": [],
        "obtained_medals": [],
        "obtained_mem_ups": [],
        "obtained_uchida": [],
        "obtained_navit": [],
        "obtained_hm_memories": [],
    }


def save_progress(progress: dict, progress_path: Path = DEFAULT_PROGRESS) -> None:
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    progress_path.write_text(json.dumps(progress, indent=2), encoding="utf-8")