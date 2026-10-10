"""
Simulation: average travel time BEFORE vs AFTER signal optimisation.

Before : every junction uses a fixed timing (30s, 30s, 25s).
After  : every junction uses the best plan that satisfies the CSP constraints
         (fixed cycle, pedestrian minimum, priority for the busier approach).

Signal delay uses the uniform-delay formula
    d = 0.5 * C * (1 - g/C)^2 / (1 - (g/C) * X),   X = min(0.95, flow / (S * g/C))
Junction delay for a node = demand-weighted average of its phase delays.

Also checks that A* returns the same cost as Dijkstra on every trip, including
trips where an accident has blocked a road (A* stays optimal on the dynamic graph).

Seeded with register number 15152.
"""

import heapq
import itertools
import random

from ai.congestion import build_expected_graph, make_sensitivity
from csp.signal_csp import CYCLE_LENGTH, PHASES, build_csp, group_ok
from rules.incident_rules import (apply_facts_to_graph, astar, build_demo_map,
                                  forward_chain)

SEED = 15152
SATURATION = 1.0 / 1.0            # vehicles per second a green lane can discharge
JUNCTION_NODES = {1: "B", 2: "C", 3: "D"}   # which map node is each junction
FIXED_PLAN = {"NS": 30, "EW": 30, "TURN": 25}


def phase_delay(green, flow_per_min):
    """Average delay (seconds) of one phase."""
    lam = green / CYCLE_LENGTH
    flow = flow_per_min / 60.0
    x = min(0.95, flow / (SATURATION * lam))
    return 0.5 * CYCLE_LENGTH * (1 - lam) ** 2 / (1 - lam * x)


def junction_delay(greens, demands):
    """Demand-weighted average delay in MINUTES for one junction."""
    total = sum(demands.values())
    return sum(demands[p] * phase_delay(greens[p], demands[p]) for p in PHASES) / total / 60.0


def best_csp_plan(group, demand):
    """All plans that satisfy the CSP constraints; return the one with least delay."""
    domain = list(range(15, 61, 5))
    best, best_delay = None, float("inf")
    for combo in itertools.product(domain, repeat=len(group)):
        assignment = dict(zip(group, combo))
        if group_ok(group, assignment, demand):
            d = junction_delay({v.split("_")[1]: assignment[v] for v in group},
                               {v.split("_")[1]: demand[v] for v in group})
            if d < best_delay:
                best, best_delay = assignment, d
    return best, best_delay


def node_delays(demand, groups, plan_type):
    """Delay (min) at each junction node for the 'fixed' or 'csp' plan."""
    delays, plans = {}, {}
    for j, group in groups.items():
        demands = {v.split("_")[1]: demand[v] for v in group}
        if plan_type == "fixed":
            greens = FIXED_PLAN
        else:
            best, _ = best_csp_plan(group, demand)
            greens = {v.split("_")[1]: best[v] for v in group}
            plans[j] = best
        delays[JUNCTION_NODES[j]] = junction_delay(greens, demands)
        if plan_type == "fixed":
            plans[j] = {v: FIXED_PLAN[v.split("_")[1]] for v in group}
    return delays, plans


def graph_with_signals(graph, delays):
    """Signal delay is paid when ENTERING a junction node."""
    g = {u: {} for u in graph}
    for u in graph:
        for v, e in graph[u].items():
            g[u][v] = {"time": e["time"], "delay": delays.get(v, 0.0)}
    return g


def dijkstra_cost(graph, start, goal):
    """Reference answer used to check A* optimality."""
    dist = {start: 0}
    heap = [(0, start)]
    while heap:
        d, n = heapq.heappop(heap)
        if n == goal:
            return d
        if d > dist.get(n, float("inf")):
            continue
        for nxt, e in graph[n].items():
            nd = d + e["time"] + e["delay"]
            if nd < dist.get(nxt, float("inf")):
                dist[nxt] = nd
                heapq.heappush(heap, (nd, nxt))
    return float("inf")


def make_trips(nodes, graph, n_trips, seed=SEED):
    """Random origin, destination, hour, and an accident on 20% of the trips."""
    rng = random.Random(seed)
    roads = sorted({tuple(sorted((u, v))) for u in graph for v in graph[u]})
    trips = []
    for _ in range(n_trips):
        s, g = rng.sample(nodes, 2)
        accident = rng.choice(roads) if rng.random() < 0.2 else None
        trips.append((s, g, rng.randint(0, 23), accident))
    return trips


def run(n_trips=100):
    graph, coords = build_demo_map()
    sens = make_sensitivity(graph)
    _, _, groups, demand = build_csp(3)
    trips = make_trips(sorted(coords), graph, n_trips)

    results = {}
    for plan_type in ("fixed", "csp"):
        delays, plans = node_delays(demand, groups, plan_type)
        base = graph_with_signals(graph, delays)
        total, count, mismatches = 0.0, 0, 0
        for s, g, hour, accident in trips:
            facts_in = [("Accident", accident)] if accident else []
            facts, _ = forward_chain(facts_in)
            dyn = apply_facts_to_graph(base, facts)               # rules change the map
            exp_graph = build_expected_graph(dyn, hour, sens, avoid_sensitive=False)
            path, cost, _ = astar(exp_graph, coords, s, g)
            if path is None:
                continue                                           # blocked completely
            if abs(cost - dijkstra_cost(exp_graph, s, g)) > 1e-9:
                mismatches += 1
            total += cost
            count += 1
        avg_signal = sum(delays.values()) / len(delays) * 60      # seconds per junction
        results[plan_type] = (total / count, count, mismatches, plans, avg_signal)
    return results, demand, groups


def save_plot(before, after, path="docs/travel_time.png"):
    try:
        import os
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("(matplotlib not installed - plot skipped)")
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    plt.bar(["Fixed timing", "CSP timing"], [before, after], color=["#999", "#2a7"])
    plt.ylabel("Average travel time (min)")
    plt.title("Before vs after signal optimisation")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Plot saved to {path}")


if __name__ == "__main__":
    results, demand, groups = run()
    before, n1, mis1, _, sig_before = results["fixed"]
    after, n2, mis2, plans, sig_after = results["csp"]
    print(f"Trips simulated      : {n2}")
    print(f"Average travel time  : fixed = {before:.2f} min, CSP = {after:.2f} min")
    print(f"Improvement          : {(before - after) / before * 100:.1f}%")
    print(f"Avg signal delay     : fixed = {sig_before:.1f} s, CSP = {sig_after:.1f} s per junction")
    print(f"A* vs Dijkstra costs : {mis1 + mis2} mismatches (0 means A* stayed optimal)")
    save_plot(before, after)
