# Supply Chain Scenario Planning

A Python and Streamlit decision-support app for production, inventory and backlog planning. Model three products over eight weeks with shared capacity. Compare a reoptimized plan against a baseline whose product-level production ceilings were frozen from the original forecast and capped by available capacity. Scenarios change demand, production capacity, initial inventory, or a combination.

| Planning approach | Mean modeled cost | Mean final backlog | Mean backlog unit-weeks |
| --- | ---: | ---: | ---: |
| Frozen production ceilings | 3,507.80 | 36.13 | 205.60 |
| Reoptimized | 922.13 | 0.00 | 0.00 |

Results average 15 scenario/seed pairs. The cost function includes production, weekly holding stock, waiting demand and a final backlog penalty. The optimizer knows the entire scenario and the baseline remains constrained by its original plan. The comparison measures value under those assumptions and does not estimate forecast accuracy. Solver status and bounds are in the [report](results.json). Test assertions verify stock and demand balance and capacity feasibility.

```sh
python -m pip install -r requirements.txt
python planner.py
python -m pytest -q
streamlit run dashboard.py
```

The dashboard compares weekly backlog, cost and solver status, lists the recommended production and shipment plan, and can save selected plans to a local SQLite database.
