"""Integer production, stock and backlog planning under demand and capacity shocks."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from ortools.sat.python import cp_model

ITEMS = ("A", "B", "C")
HOURS = (2, 3, 4)
STARTING = (30, 20, 15)
CAPACITY = (190, 190, 195, 195, 200, 200, 200, 205)
SCENARIOS = ("base", "demand_surge", "downtime", "inventory_loss", "compound")


def inputs(scenario, seed=17):
    rng = np.random.default_rng(seed)
    demand = rng.integers([17, 11, 7], [26, 18, 13], size=(8, 3))
    capacity = list(CAPACITY)
    starting = list(STARTING)
    if scenario in ("demand_surge", "compound"):
        demand[2:5, 1] += 16
    if scenario in ("downtime", "compound"):
        capacity[3:5] = [90, 95]
    if scenario in ("inventory_loss", "compound"):
        starting[0] = 4
    return demand, capacity, starting


def solve(scenario, seed=17, fixed=None):
    demand, capacity, starting = inputs(scenario, seed)
    model = cp_model.CpModel()
    bound = int(demand.sum()) + sum(starting)
    p, inv, backlog, shipped = {}, {}, {}, {}
    for t, q in np.ndindex(demand.shape):
        p[t,q] = model.new_int_var(0, min(bound, capacity[t] // HOURS[q]), f"p{t}_{q}")
        inv[t,q] = model.new_int_var(0, bound, f"i{t}_{q}")
        backlog[t,q] = model.new_int_var(0, bound, f"b{t}_{q}")
        shipped[t,q] = model.new_int_var(0, bound, f"s{t}_{q}")
        model.add(inv[t,q] == (inv[t-1,q] if t else starting[q]) + p[t,q] - shipped[t,q])
        model.add(backlog[t,q] == (backlog[t-1,q] if t else 0) + int(demand[t,q]) - shipped[t,q])
        if fixed is not None:
            model.add(p[t,q] <= int(fixed[t,q]))
    for t, cap in enumerate(capacity):
        model.add(sum(HOURS[q] * p[t,q] for q in range(3)) <= cap)
    model.minimize(sum((q+2)*p[t,q] + inv[t,q] + 9*backlog[t,q] + (24*backlog[t,q] if t==7 else 0)
                       for t,q in p))
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.max_time_in_seconds = 5
    status = solver.solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(solver.status_name(status))
    rows = pd.DataFrame([{"week": t+1, "item": ITEMS[q], "demand": int(demand[t,q]),
                          "production": solver.value(p[t,q]), "ship": solver.value(shipped[t,q]),
                          "inventory": solver.value(inv[t,q]), "backlog": solver.value(backlog[t,q]),
                          "hours_used": HOURS[q]*solver.value(p[t,q]), "capacity": capacity[t]}
                         for t,q in p])
    return rows, {"objective": solver.objective_value, "bound": solver.best_objective_bound,
                  "status": solver.status_name(status), "final_backlog": int(rows[rows.week==8].backlog.sum()),
                  "backlog_unit_weeks": int(rows.backlog.sum())}


def benchmark():
    reports = []
    for seed in (7, 17, 41):
        base, _ = solve("base", seed)
        frozen = base.production.to_numpy().reshape(8, 3)
        for scenario in SCENARIOS:
            for method, plan in (("frozen_capacity_capped", frozen), ("reoptimized", None)):
                _, result = solve(scenario, seed, fixed=plan)
                reports.append({"seed": seed, "scenario": scenario, "method": method, **result})
    Path("results.json").write_text(json.dumps(reports, indent=2) + "\n", encoding="utf-8")
    print(pd.DataFrame(reports).groupby("method")[["objective","final_backlog","backlog_unit_weeks"]].mean())


if __name__ == "__main__":
    benchmark()
