import json
import pandas as pd
import streamlit as st
from utils.loader import load_workbook_data, load_progress, save_progress

st.set_page_config(
    page_title="DSCSCE Companion",
    page_icon="👾",
    layout="wide",
)

data = load_workbook_data()
progress = load_progress()
dex = data["dex"]
digi_hm = data["digi_clean"]

st.title("Digimon Story: Cyber Sleuth Complete Edition — Companion")
st.caption("Powered by DSCSCE.xlsx • Interactive Dex, Evolution Paths & Progression Hub")

# Top summary row from loaded workbook
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Digimon (Field Guide)", len(dex))
c2.metric("Digivolution Links", len(digi_hm))
c3.metric("Medals (Total)", len(data["Medals"]))
c4.metric("Cases", len(data["Cases"]))
c5.metric("Areas", len(data["Area"]))

st.divider()

# Sidebar global filters & progress backup
st.sidebar.header("Dex Filters")
search_q = st.sidebar.text_input("Search Name or Support Skill", placeholder="e.g., Alphamon, Tactician, Piercing")
stages = ["All"] + [s for s in dex["Stage"].dropna().unique().tolist()]
types = ["All"] + [t for t in dex["Type"].dropna().unique().tolist()]
attrs = ["All"] + [a for a in dex["Attribute"].dropna().unique().tolist()]

sel_stage = st.sidebar.selectbox("Stage", stages)
sel_type = st.sidebar.selectbox("Type", types)
sel_attr = st.sidebar.selectbox("Attribute", attrs)
max_mem = st.sidebar.slider(
    "Max Memory Usage",
    min_value=int(dex["Memory Usage"].min()),
    max_value=int(dex["Memory Usage"].max()),
    value=int(dex["Memory Usage"].max()),
)

filtered = dex[dex["Memory Usage"] <= max_mem].copy()
if search_q.strip():
    q = search_q.strip()
    name_match = filtered["Name"].str.contains(q, case=False, na=False)
    skill_match = (
        filtered["Support Skill"].str.contains(q, case=False, na=False)
        if "Support Skill" in filtered.columns
        else False
    )
    filtered = filtered[name_match | skill_match]
if sel_stage != "All":
    filtered = filtered[filtered["Stage"] == sel_stage]
if sel_type != "All":
    filtered = filtered[filtered["Type"] == sel_type]
if sel_attr != "All":
    filtered = filtered[filtered["Attribute"] == sel_attr]

st.sidebar.divider()
st.sidebar.subheader("Progress Backup (Mobile / Cloud)")
st.sidebar.download_button(
    label="Export Progress (JSON)",
    data=json.dumps(progress, indent=2),
    file_name="dscsce_progress.json",
    mime="application/json",
)
uploaded = st.sidebar.file_uploader("Import Progress (JSON)", type=["json"])
if uploaded is not None:
    imported = json.load(uploaded)
    progress.update(imported)
    save_progress(progress)
    st.sidebar.success("Progress loaded!")

st.subheader(f"Digimon Browser ({len(filtered)} matches)")
display_cols = [
    c
    for c in [
        "Field ID",
        "Name",
        "Stage",
        "Type",
        "Attribute",
        "Support Skill",
        "Type Eff - Str",
        "Type Eff - Weak",
        "Memory Usage",
        "Equip Slot",
        "HP",
        "SP",
        "ATK",
        "INT",
        "DEF",
        "SPD",
        "Need To be unlocked in HM",
    ]
    if c in filtered.columns
]
st.dataframe(filtered[display_cols], use_container_width=True, hide_index=True)

st.divider()

# Single-Digimon Inspector Card
st.subheader("Digimon Inspector")
all_names = dex["Name"].dropna().tolist()
default_idx = all_names.index("Alphamon") if "Alphamon" in all_names else 0
selected_mon = st.selectbox("Select a Digimon to inspect", all_names, index=default_idx)

row = dex[dex["Name"] == selected_mon].iloc[0]
clean_target = row["Clean_Name"]

col_info, col_stats = st.columns([1, 1.4])

with col_info:
    st.markdown(f"### #{int(row['Field ID'])} — {row['Name']}")
    st.write(f"**Stage:** {row['Stage']} | **Type:** {row['Type']} | **Attribute:** {row['Attribute']}")
    st.write(f"**Memory Usage:** {row['Memory Usage']} | **Equip Slots:** {row['Equip Slot']}")

    # Support Skill + Description pulled from Support Skills sheet
    if "Support Skill" in dex.columns and pd.notna(row.get("Support Skill")):
        skill_name = str(row["Support Skill"]).strip()
        skill_desc = row.get("Support Skill Description")
        if pd.notna(skill_desc) and str(skill_desc).strip():
            st.info(f"**Support Skill — {skill_name}:** {skill_desc}")
        else:
            st.info(f"**Support Skill:** {skill_name}")

    # Type Effectiveness (Strong / Weak)
    eff_str = row.get("Type Eff - Str") if "Type Eff - Str" in dex.columns else None
    eff_weak = row.get("Type Eff - Weak") if "Type Eff - Weak" in dex.columns else None
    if pd.notna(eff_str) or pd.notna(eff_weak):
        e1, e2 = st.columns(2)
        e1.success(f"**Strong Against:** {eff_str if pd.notna(eff_str) else '—'}")
        e2.error(f"**Weak Against:** {eff_weak if pd.notna(eff_weak) else '—'}")

    if str(row.get("Need To be unlocked in HM", "No")).strip().lower() == "yes":
        st.warning(f"HM Unlock Required: {row.get('How to Unlock') or 'Check story/condition'}")

    is_obtained = selected_mon in progress["obtained_dex"]
    toggled = st.checkbox("Mark as Obtained in Field Guide", value=is_obtained, key="dex_chk")
    if toggled != is_obtained:
        if toggled:
            progress["obtained_dex"].append(selected_mon)
        else:
            progress["obtained_dex"].remove(selected_mon)
        save_progress(progress)

with col_stats:
    stat_cols = [c for c in ["HP", "SP", "ATK", "INT", "DEF", "SPD", "Weighted Total", "Total"] if c in dex.columns]
    if stat_cols:
        st.markdown("**Base Stats**")
        st.dataframe(row[stat_cols].to_frame().T, use_container_width=True, hide_index=True)

evo_col, pre_col = st.columns(2)
with evo_col:
    st.markdown("**Digivolves Into**")
    evos = digi_hm[digi_hm["Base_Clean"] == clean_target][
        ["Target Digivolution", "Stage", "Requirements", "Earliest Level / Notes"]
    ]
    st.dataframe(evos, use_container_width=True, hide_index=True)

with pre_col:
    st.markdown("**Digivolves From (Pre-Evolutions)**")
    pres = digi_hm[digi_hm["Target_Clean"] == clean_target][
        ["BaseDigimon", "Stage", "Requirements", "Earliest Level / Notes"]
    ]
    st.dataframe(pres, use_container_width=True, hide_index=True)