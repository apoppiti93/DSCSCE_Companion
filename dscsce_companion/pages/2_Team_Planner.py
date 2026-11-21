import pandas as pd
import streamlit as st
from utils.loader import load_workbook_data, load_progress, save_progress

st.set_page_config(
    page_title="Team Planner • DSCSCE Companion",
    page_icon="🛡️",
    layout="wide",
)

data = load_workbook_data()
progress = load_progress()
dex = data["dex"].copy()

st.title("11-Slot Party & Memory Planner")
st.caption("Manage party memory limits, ABI bonus stat caps, and dungeon Hacking Skill requirements")

# Top Memory Cap & ABI Calculator Controls
ctrl1, ctrl2 = st.columns([1, 1])

with ctrl1:
    st.subheader("Party Memory Cap")
    mem_cap = st.number_input(
        "Your Current Memory Cap",
        min_value=20,
        max_value=999,
        value=int(progress.get("memory_cap", 150)),
        step=5,
    )
    if mem_cap != progress.get("memory_cap"):
        progress["memory_cap"] = int(mem_cap)
        save_progress(progress)

with ctrl2:
    st.subheader("Quick ABI Bonus Stat Cap Calculator")
    abi_val = st.slider("Digimon ABI (0 – 200)", min_value=0, max_value=200, value=100)
    bonus_pts = 50 + (abi_val // 2)
    st.info(
        f"At **{abi_val} ABI**, you get **{bonus_pts} total bonus training points** "
        f"(1 pt = +1 SP/ATK/DEF/INT/SPD or +10 HP)."
    )

st.divider()

# 11-Slot Party Builder
st.subheader("Active & Reserve Party (11 Slots)")
mon_options = ["(Empty)"] + dex["Name"].dropna().tolist()
saved_team = progress.get("team", [None] * 11)
if len(saved_team) < 11:
    saved_team = saved_team + [None] * (11 - len(saved_team))

selected_team = []
cols = st.columns(3)
for i in range(11):
    col = cols[i % 3]
    role = "Battle" if i < 3 else "Reserve"
    current_val = saved_team[i] if saved_team[i] in mon_options else "(Empty)"
    choice = col.selectbox(
        f"Slot {i + 1} ({role})",
        mon_options,
        index=mon_options.index(current_val),
        key=f"team_slot_{i}",
    )
    selected_team.append(None if choice == "(Empty)" else choice)

if selected_team != saved_team:
    progress["team"] = selected_team
    save_progress(progress)

# Build summary table of chosen Digimon
active_names = [m for m in selected_team if m is not None]
if active_names:
    rows = []
    for idx, name in enumerate(selected_team):
        if name is None:
            continue
        r = dex[dex["Name"] == name].iloc[0]
        rows.append(
            {
                "Slot": f"Slot {idx + 1} ({'Battle' if idx < 3 else 'Reserve'})",
                "Name": r["Name"],
                "Stage": r["Stage"],
                "Type": r["Type"],
                "Attribute": r["Attribute"],
                "Memory": int(r["Memory Usage"]),
                "Slots": int(r["Equip Slot"]),
                "HP": r.get("HP"),
                "SP": r.get("SP"),
                "ATK": r.get("ATK"),
                "INT": r.get("INT"),
                "DEF": r.get("DEF"),
                "SPD": r.get("SPD"),
            }
        )
    team_df = pd.DataFrame(rows)
    total_mem = int(team_df["Memory"].sum())
    remaining_mem = int(mem_cap) - total_mem

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Memory Used", f"{total_mem} / {mem_cap}")
    m2.metric("Remaining Memory", remaining_mem, delta=remaining_mem)
    m3.metric("Party Size", f"{len(team_df)} / 11")

    st.progress(min(total_mem / max(int(mem_cap), 1), 1.0))
    if total_mem > mem_cap:
        st.error(f"Over Memory Cap by {total_mem - mem_cap} MB! Swap out a Mega/Ultra or equip Memory UPs.")

    st.dataframe(team_df, use_container_width=True, hide_index=True)

    st.divider()

    # Hacking Skill Coverage Check
    st.subheader("Hacking Skill & Type Coverage")
    type_counts = team_df["Type"].value_counts().to_dict()
    stage_order = {
        "Training 1": 1,
        "Training 2": 2,
        "Rookie": 3,
        "Champion": 4,
        "Ultimate": 5,
        "Mega": 6,
        "Ultra": 7,
        "Armor": 4,
    }
    team_df["StageRank"] = team_df["Stage"].map(stage_order).fillna(0)
    mega_plus = int((team_df["StageRank"] >= 6).sum())
    ult_plus = int((team_df["StageRank"] >= 5).sum())
    champ_plus = int((team_df["StageRank"] >= 4).sum())

    t1, t2, t3, t4 = st.columns(4)
    t1.metric("Vaccine", type_counts.get("Vaccine", 0))
    t2.metric("Data", type_counts.get("Data", 0))
    t3.metric("Virus", type_counts.get("Virus", 0))
    t4.metric("Free", type_counts.get("Free", 0))

    checks = [
        ("Copy & Paste / Stealth Hide (1+ Virus, 1+ Data)", type_counts.get("Virus", 0) >= 1 and type_counts.get("Data", 0) >= 1),
        ("Wall Crack Lv. 1 (1+ Champion or higher)", champ_plus >= 1),
        ("Wall Crack Lv. 2 (2+ Ultimate or higher)", ult_plus >= 2),
        ("Wall Crack Lv. 3 (3+ Mega or higher)", mega_plus >= 3),
        ("Acceleration / High Security (1+ Free)", type_counts.get("Free", 0) >= 1),
    ]
    for label, passed in checks:
        if passed:
            st.success(f"Ready: {label}")
        else:
            st.warning(f"Missing: {label}")
else:
    st.info("Pick Digimon in Slots 1–11 above to calculate party memory, stats, and Hacking Skills.")