import pandas as pd
import streamlit as st
from utils.loader import load_workbook_data, load_progress, save_progress

st.set_page_config(
    page_title="Collectibles & Checklists • DSCSCE Companion",
    page_icon="🏅",
    layout="wide",
)

data = load_workbook_data()
progress = load_progress()

# Ensure checklist keys exist in progress dict
progress.setdefault("obtained_medals", [])
progress.setdefault("obtained_mem_ups", [])
progress.setdefault("obtained_hm_memories", [])
progress.setdefault("obtained_uchida", [])
progress.setdefault("obtained_navit", [])
progress.setdefault("completed_cases", [])

st.title("Collectibles & Completion Checklists")
st.caption("Separated CS & HM subtabs for Memory UPs and Medals, plus Cases & NPC collectibles")

mem_ups = data["Memory UP"].copy()
mem_ups.columns = [str(c).strip() for c in mem_ups.columns]
if "Verison" in mem_ups.columns and "Game" not in mem_ups.columns:
    mem_ups = mem_ups.rename(columns={"Verison": "Game"})
mem_ups["Chapter_Clean"] = mem_ups["Chapter"].astype(str).str.strip()
mem_ups["Game_Clean"] = mem_ups["Game"].astype(str).str.strip()

medals = data["Medals"].copy()
medals.columns = [str(c).strip() for c in medals.columns]
medals["Game_Clean"] = medals["Game"].astype(str).str.strip()


def render_mem_up_list(df: pd.DataFrame, prefix: str) -> None:
    c1, c2 = st.columns([1, 1.5])
    chap_opts = ["All"] + sorted(df["Chapter_Clean"].dropna().unique().tolist())
    sel_chap = c1.selectbox("Chapter", chap_opts, key=f"{prefix}_chap")
    search_q = c2.text_input(
        "Search Location / Method",
        placeholder="e.g., Kowloon, chest, boss",
        key=f"{prefix}_q",
    )

    view = df.copy()
    if sel_chap != "All":
        view = view[view["Chapter_Clean"] == sel_chap]
    if search_q.strip():
        q = search_q.strip().lower()
        view = view[view.apply(lambda r: q in str(r.to_dict()).lower(), axis=1)]

    view = view.reset_index().rename(columns={"index": "_mem_id"})
    obtained_set = set(progress["obtained_mem_ups"])
    view["Obtained"] = view["_mem_id"].isin(obtained_set)

    cols = [c for c in ["Obtained", "Game", "Chapter", "Location", "How to Obtain"] if c in view.columns]
    edited = st.data_editor(
        view[["_mem_id"] + cols],
        column_config={
            "_mem_id": None,
            "Obtained": st.column_config.CheckboxColumn("Obtained"),
        },
        disabled=[c for c in cols if c != "Obtained"],
        hide_index=True,
        use_container_width=True,
        key=f"{prefix}_editor",
    )

    updated = set(obtained_set)
    for _, r in edited.iterrows():
        mid = int(r["_mem_id"])
        if r["Obtained"]:
            updated.add(mid)
        else:
            updated.discard(mid)
    if updated != obtained_set:
        progress["obtained_mem_ups"] = sorted(updated)
        save_progress(progress)

    sub_obtained = len([i for i in view["_mem_id"] if int(i) in progress["obtained_mem_ups"]])
    st.progress(min(sub_obtained / max(len(view), 1), 1.0))
    st.caption(f"Checked in this view: {sub_obtained} / {len(view)}  •  Total Memory UPs: {len(progress['obtained_mem_ups'])} / {len(mem_ups)}")


def render_medal_list(df: pd.DataFrame, prefix: str) -> None:
    c1, c2 = st.columns([2, 1])
    search_q = c1.text_input(
        "Search Medal Name or Location",
        placeholder="e.g., Omegamon, Nakano, Gacha",
        key=f"{prefix}_q",
    )
    hide_obtained = c2.checkbox("Hide Obtained", value=False, key=f"{prefix}_hide")

    view = df.copy()
    if search_q.strip():
        q = search_q.strip().lower()
        view = view[view.apply(lambda r: q in str(r.to_dict()).lower(), axis=1)]

    obtained_set = set(progress["obtained_medals"])
    view["Obtained"] = view["Number"].isin(obtained_set)
    if hide_obtained:
        view = view[~view["Obtained"]]

    cols = [
        c
        for c in [
            "Obtained",
            "Number",
            "Medal Name",
            "Game",
            "Medal Location 1",
            "Medal Location 2",
            "Medal Location 3",
        ]
        if c in view.columns
    ]
    edited = st.data_editor(
        view[cols],
        column_config={"Obtained": st.column_config.CheckboxColumn("Obtained")},
        disabled=[c for c in cols if c != "Obtained"],
        hide_index=True,
        use_container_width=True,
        key=f"{prefix}_editor",
    )

    updated = set(obtained_set)
    for _, r in edited.iterrows():
        num = int(r["Number"])
        if r["Obtained"]:
            updated.add(num)
        else:
            updated.discard(num)
    if updated != obtained_set:
        progress["obtained_medals"] = sorted(updated)
        save_progress(progress)

    st.progress(min(len(progress["obtained_medals"]) / max(len(medals), 1), 1.0))
    st.caption(f"Total Medals Collected: {len(progress['obtained_medals'])} / {len(medals)}")


tab_mem, tab_medals, tab_hm_mem, tab_npcs, tab_cases = st.tabs(
    [
        f"Memory UPs ({len(mem_ups)})",
        f"Medals ({len(medals)})",
        f"HM Memories ({len(data['Hackers Memory'])})",
        "Uchida & Mr. Navit",
        f"Cases ({len(data['Cases'])})",
    ]
)

with tab_mem:
    cs_mem = mem_ups[mem_ups["Game_Clean"] == "CS"]
    hm_mem = mem_ups[mem_ups["Game_Clean"] == "HM"]
    sub_all, sub_cs, sub_hm = st.tabs(
        [f"All ({len(mem_ups)})", f"CS ({len(cs_mem)})", f"HM ({len(hm_mem)})"]
    )
    with sub_all:
        render_mem_up_list(mem_ups, "mem_all")
    with sub_cs:
        render_mem_up_list(cs_mem, "mem_cs")
    with sub_hm:
        render_mem_up_list(hm_mem, "mem_hm")

with tab_medals:
    cs_med = medals[medals["Game_Clean"] == "CS"]
    hm_med = medals[medals["Game_Clean"] == "HM"]
    msub_all, msub_cs, msub_hm = st.tabs(
        [f"All ({len(medals)})", f"CS ({len(cs_med)})", f"HM ({len(hm_med)})"]
    )
    with msub_all:
        render_medal_list(medals, "med_all")
    with msub_cs:
        render_medal_list(cs_med, "med_cs")
    with msub_hm:
        render_medal_list(hm_med, "med_hm")

with tab_hm_mem:
    hm_df = data["Hackers Memory"].copy()
    hm_df.columns = [str(c).strip() for c in hm_df.columns]
    hm_q = st.text_input("Search HM Memory Name or Location", key="hm_mem_search")
    if hm_q.strip():
        q = hm_q.strip().lower()
        hm_df = hm_df[hm_df.apply(lambda r: q in str(r.to_dict()).lower(), axis=1)]
    st.dataframe(hm_df, use_container_width=True, hide_index=True)

with tab_npcs:
    st.subheader("Victory Uchida")
    uchida_df = data["Victory Uchida"].copy()
    uchida_df.columns = [str(c).strip() for c in uchida_df.columns]
    st.dataframe(uchida_df, use_container_width=True, hide_index=True)

    st.divider()

    st.subheader("Broken Mr. Navit")
    navit_df = data["Broken Mr Navit"].copy()
    navit_df.columns = [str(c).strip() for c in navit_df.columns]
    st.dataframe(navit_df, use_container_width=True, hide_index=True)

with tab_cases:
    cases_df = data["Cases"].copy()
    cases_df.columns = [str(c).strip() for c in cases_df.columns]
    case_q = st.text_input("Search Case Name, Client, Place, or Chapter", key="case_search")
    if case_q.strip():
        q = case_q.strip().lower()
        cases_df = cases_df[cases_df.apply(lambda r: q in str(r.to_dict()).lower(), axis=1)]
    st.dataframe(cases_df, use_container_width=True, hide_index=True)