from __future__ import annotations

import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_PATH = PROJECT_ROOT / "results" / "results.json"

# Validated categorical palette (fixed hue order, colorblind-safe adjacent pairs).
CATEGORY_ORDER = ["direct", "indirect", "payload_splitting", "obfuscation"]
CATEGORY_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]

MITIGATION_ORDER = ["baseline", "sandwich", "delimiting"]
MITIGATION_COLORS = ["#2a78d6", "#eb6834", "#1baf7a"]

WIN_CONDITION_ORDER = ["canary_leak", "instruction_hijack", "persona_switch"]

STATUS_GOOD = "#0ca30c"
STATUS_CRITICAL = "#d03b3b"

st.set_page_config(page_title="Prompt Injection Benchmark", page_icon="\U0001F6E1️", layout="wide")


@st.cache_data
def load_results() -> pd.DataFrame:
    with open(RESULTS_PATH) as f:
        data = json.load(f)
    return pd.DataFrame(data)


df = load_results()

st.title("\U0001F6E1️ Prompt Injection Benchmark")
st.caption(
    "OWASP LLM01:2025 attack taxonomy — Claude Haiku, evaluated against "
    "direct, indirect, payload-splitting, and obfuscation injection techniques, "
    "each tested with no mitigation, sandwich defense, and delimiting."
)

# ---------------------------------------------------------------------------
# Headline numbers
# ---------------------------------------------------------------------------
total_attacks = df["id"].nunique()
total_runs = len(df)
total_successes = int(df["success"].sum())
success_rate = total_successes / total_runs if total_runs else 0.0

col1, col2, col3 = st.columns(3)
col1.metric("Attacks in corpus", total_attacks)
col2.metric("Total runs", total_runs, help="attacks × mitigation conditions")
col3.metric("Overall attack success rate", f"{success_rate:.0%}")

if total_successes == 0:
    st.success(
        f"Claude resisted all {total_runs} runs across every category, "
        "win-condition, and mitigation tested — including several "
        "escalating techniques (prefix-completion, fiction + authority "
        "stacking) tried beyond the base corpus."
    )

st.divider()

# ---------------------------------------------------------------------------
# Corpus composition
# ---------------------------------------------------------------------------
st.subheader("Corpus composition")
composition = (
    df[df["mitigation"] == "baseline"]
    .groupby("category")
    .size()
    .reindex(CATEGORY_ORDER, fill_value=0)
    .reset_index(name="count")
)
composition_chart = (
    alt.Chart(composition)
    .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, size=48)
    .encode(
        x=alt.X("category:N", sort=CATEGORY_ORDER, title=None),
        y=alt.Y("count:Q", title="Number of attacks"),
        color=alt.Color(
            "category:N",
            sort=CATEGORY_ORDER,
            scale=alt.Scale(domain=CATEGORY_ORDER, range=CATEGORY_COLORS),
            legend=None,
        ),
        tooltip=["category", "count"],
    )
    .properties(height=280)
)
st.altair_chart(composition_chart, width="stretch")

st.divider()


def rate_table(group_col: str, order: list[str] | None = None) -> pd.DataFrame:
    grouped = df.groupby(group_col).agg(
        runs=("success", "size"), successes=("success", "sum")
    )
    if order:
        grouped = grouped.reindex(order)
    grouped["success_rate"] = (grouped["successes"] / grouped["runs"] * 100).round(1).astype(str) + "%"
    return grouped


# ---------------------------------------------------------------------------
# Success-rate breakdowns
# ---------------------------------------------------------------------------
st.subheader("Success rate breakdown")
tab1, tab2, tab3 = st.tabs(["By category", "By mitigation", "By win condition"])
with tab1:
    st.dataframe(rate_table("category", CATEGORY_ORDER), width="stretch")
with tab2:
    st.dataframe(rate_table("mitigation", MITIGATION_ORDER), width="stretch")
with tab3:
    st.dataframe(rate_table("win_condition", WIN_CONDITION_ORDER), width="stretch")

st.divider()

# ---------------------------------------------------------------------------
# Full results explorer
# ---------------------------------------------------------------------------
st.subheader("Full results explorer")
fcol1, fcol2, fcol3 = st.columns(3)
category_filter = fcol1.multiselect("Category", CATEGORY_ORDER, default=CATEGORY_ORDER)
mitigation_filter = fcol2.multiselect("Mitigation", MITIGATION_ORDER, default=MITIGATION_ORDER)
win_condition_filter = fcol3.multiselect(
    "Win condition", WIN_CONDITION_ORDER, default=WIN_CONDITION_ORDER
)

filtered = df[
    df["category"].isin(category_filter)
    & df["mitigation"].isin(mitigation_filter)
    & df["win_condition"].isin(win_condition_filter)
].sort_values(["category", "id", "mitigation"])

st.caption(f"{len(filtered)} of {total_runs} runs shown")

for _, row in filtered.iterrows():
    icon = "\U0001F534 SUCCEEDED" if row["success"] else "\U0001F7E2 RESISTED"
    label = f"{icon} — {row['id']} / {row['mitigation']} / {row['win_condition']}"
    with st.expander(label):
        st.text(row["response"])
