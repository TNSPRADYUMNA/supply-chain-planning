import sqlite3
from contextlib import closing

import streamlit as st

from planner import SCENARIOS, solve

st.set_page_config(page_title="Supply chain scenario planner", layout="wide")
st.title("Supply chain scenario planner")
scenario = st.selectbox("Scenario", SCENARIOS)
seed = st.number_input("Demand seed", min_value=0, max_value=99999, value=17)
rows, result = solve(scenario, int(seed))
base, _ = solve("base", int(seed))
comparison, prior = solve(scenario, int(seed), base.production.to_numpy().reshape(8, 3))
a,b,c = st.columns(3)
a.metric("Planning cost", f'{result["objective"]:,.0f}', f'{result["objective"]-prior["objective"]:,.0f}', delta_color="inverse")
b.metric("Final backlog", result["final_backlog"], result["final_backlog"]-prior["final_backlog"], delta_color="inverse")
c.metric("Solver status", result["status"])
st.line_chart(rows.groupby("week").backlog.sum().rename("Reoptimized").to_frame().join(
    comparison.groupby("week").backlog.sum().rename("Capacity-capped baseline")))
st.dataframe(rows, hide_index=True)
if st.button("Save plan snapshot"):
    with closing(sqlite3.connect("plans.db")) as conn:
        rows.assign(scenario=scenario, seed=int(seed)).to_sql("plans", conn, if_exists="append", index=False)
    st.success("Plan snapshot stored.")
