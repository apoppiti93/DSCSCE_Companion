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


def find_col_fuzzy(
    df: pd.DataFrame,
    exact_candidates: list[str],
    keywords: list[str] | None = None,
) -> str | None:
    norm_map = {str(c).strip().lower(): c for c in df.columns}
    for cand in exact_candidates:
        if cand.strip().lower() in norm_map:
            return norm_map[cand.strip().lower()]
    if keywords:
        for norm_name, orig_col in norm_map.items():
            if any(kw in norm_name for kw in keywords):
                return orig_col
    return None


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
        suffixes=("", "_stats"),
    )

    # Fuzzy-match Support Skill & Type Effectiveness columns regardless of exact header wording
    ss_col = find_col_fuzzy(
        dex,
        ["Support Skill", "Support Skills", "Skill", "Passive"],
        ["support", "skill", "passive"],
    )
    str_col = find_col_fuzzy(
        dex,
        ["Type Eff - Str", "Type Eff - Strong", "Strong"],
        ["str", "strong"],
    )
    weak_col = find_col_fuzzy(
        dex,
        ["Type Eff - Weak", "Weak"],
        ["weak"],
    )

    if ss_col and ss_col != "Support Skill":
        dex = dex.rename(columns={ss_col: "Support Skill"})
    if str_col and str_col != "Type Eff - Str":
        dex = dex.rename(columns={str_col: "Type Eff - Str"})
    if weak_col and weak_col != "Type Eff - Weak":
        dex = dex.rename(columns={weak_col: "Type Eff - Weak"})

    # Merge Support Skill description from the 'Support Skills' sheet
    if "Support Skill" in dex.columns and "Support Skills" in data:
        ss_df = data["Support Skills"].copy()
        skill_key = find_col_fuzzy(ss_df, ["Skill", "Support Skill", "Name"], ["skill", "name"])
        desc_key = find_col_fuzzy(ss_df, ["Description", "Effect"], ["desc", "effect"])
        if skill_key and desc_key:
            ss_lookup = (
                ss_df[[skill_key, desc_key]]
                .dropna(subset=[skill_key])
                .drop_duplicates(subset=[skill_key])
                .copy()
            )
            ss_lookup["_skill_join"] = ss_lookup[skill_key].astype(str).str.strip().str.lower()
            dex["_skill_join"] = dex["Support Skill"].fillna("").astype(str).str.strip().str.lower()

            dex = dex.merge(
                ss_lookup[["_skill_join", desc_key]].rename(
                    columns={desc_key: "Support Skill Description"}
                ),
                on="_skill_join",
                how="left",
            ).drop(columns=["_skill_join"])

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