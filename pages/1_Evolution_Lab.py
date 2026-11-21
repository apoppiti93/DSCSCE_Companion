import pandas as pd
import streamlit as st
from utils.loader import load_workbook_data, clean_name

st.set_page_config(
    page_title="Evolution Lab • DSCSCE Companion",
    page_icon="🧬",
    layout="wide",
)

data = load_workbook_data()
dex = data["dex"].copy()
digi = data["Digivolvution"].copy()
digi.columns = [str(c).strip() for c in digi.columns]

digi["Base_Clean"] = digi["BaseDigimon"].apply(clean_name)
digi["Target_Clean"] = digi["Target Digivolution"].apply(clean_name)

st.title("Digivolution & De-Evolution Lab")
st.caption("Explore evolution trees, stat/ABI/CAM requirements, and HM unlock conditions")

all_names = sorted(dex["Name"].dropna().unique().tolist())
default_idx = all_names.index("Sistermon Blanc") if "Sistermon Blanc" in all_names else 0
selected_mon = st.selectbox("Select Digimon", all_names, index=default_idx)

mon_info = dex[dex["Clean_Name"] == clean_name(selected_mon)]
if not mon_info.empty:
    r = mon_info.iloc[0]
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Field ID", int(r["Field ID"]) if pd.notna(r.get("Field ID")) else "—")
    m2.metric("Stage", r.get("Stage", "—"))
    m3.metric("Type / Attr", f"{r.get('Type', '—')} / {r.get('Attribute', '—')}")
    m4.metric("Memory", r.get("Memory Usage", "—"))
    m5.metric("Equip Slots", r.get("Equip Slot", "—"))

    if str(r.get("Need To be unlocked in HM", "No")).strip().lower() == "yes":
        st.warning(
            f"**HM Unlock Required:** {r.get('How to Unlock') or 'Unlock condition applies in Hacker\'s Memory'}"
        )

st.divider()

col_out, col_in = st.columns(2)
target_clean = clean_name(selected_mon)

with col_out:
    st.subheader(f"Can Digivolve Into (from {selected_mon})")
    out_df = digi[digi["Base_Clean"] == target_clean][
        ["Target Digivolution", "Stage", "Requirements", "Earliest Level / Notes"]
    ]
    if out_df.empty:
        st.info("No further digivolutions listed from this Digimon.")
    else:
        st.dataframe(out_df, use_container_width=True, hide_index=True)

with col_in:
    st.subheader(f"Digivolves From (into {selected_mon})")
    in_df = digi[digi["Target_Clean"] == target_clean][
        ["BaseDigimon", "Stage", "Requirements", "Earliest Level / Notes"]
    ]
    if in_df.empty:
        st.info("No pre-evolutions listed into this Digimon.")
    else:
        st.dataframe(in_df, use_container_width=True, hide_index=True)

st.divider()

st.subheader("Full Digivolution Table Search")
f1, f2, f3 = st.columns(3)
stage_opts = ["All"] + sorted(digi["Stage"].dropna().astype(str).unique().tolist())
sel_evo_stage = f1.selectbox("Filter by Target Stage", stage_opts)
req_query = f2.text_input("Filter Requirements / Notes", placeholder="e.g., ABI, CAM, Omnimon")
mon_query = f3.text_input("Filter Base or Target Name", placeholder="e.g., Sistermon, Agumon")

table_view = digi[["Field #", "BaseDigimon", "Target Digivolution", "Stage", "Requirements", "Earliest Level / Notes"]].copy()
if sel_evo_stage != "All":
    table_view = table_view[table_view["Stage"] == sel_evo_stage]
if req_query.strip():
    q = req_query.strip().lower()
    table_view = table_view[
        table_view["Requirements"].fillna("").str.lower().str.contains(q)
        | table_view["Earliest Level / Notes"].fillna("").str.lower().str.contains(q)
    ]
if mon_query.strip():
    mq = mon_query.strip().lower()
    table_view = table_view[
        table_view["BaseDigimon"].fillna("").str.lower().str.contains(mq)
        | table_view["Target Digivolution"].fillna("").str.lower().str.contains(mq)
    ]

st.dataframe(table_view, use_container_width=True, hide_index=True)