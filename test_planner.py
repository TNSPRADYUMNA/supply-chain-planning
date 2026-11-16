from planner import ITEMS, SCENARIOS, inputs, solve


def test_capacity_and_flow_conservation():
    for case in SCENARIOS:
        frame, metrics = solve(case)
        _, caps, start = inputs(case)
        assert all(frame.groupby("week").hours_used.sum().to_numpy() <= caps)
        for item, opening in zip(ITEMS, start):
            stock, backlog = opening, 0
            for row in frame[frame.item==item].itertuples():
                stock += row.production - row.ship
                backlog += row.demand - row.ship
                assert stock == row.inventory >= 0
                assert backlog == row.backlog >= 0
        assert metrics["objective"] >= metrics["bound"]
