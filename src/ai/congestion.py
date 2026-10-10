"""
Probabilistic, time-dependent congestion + expected-travel-time routing.

Idea
  Every road is in one of three congestion levels: LOW, MEDIUM, HIGH.
  The probability of each level depends on the hour of the day (peak hours are worse).
  Expected travel time of a road = sum over levels of  P(level) * time_in_that_level.
  A* then runs on the expected times, so it returns the route with the minimum
  EXPECTED travel time.

Fairness
  Roads inside school / residential zones get an extra penalty, so the router avoids
  them unless the detour is much longer. The penalty is only a routing cost: the
  reported travel time is always the real expected time.

Why A* stays optimal
  Expected time >= free-flow time and penalties are >= 0, so the straight-line
  heuristic is still admissible.

Seeded with register number 15152.
"""

import os
import random
import sys

# allow "from rules.incident_rules import ..." when run as: python src/ai/congestion.py
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from rules.incident_rules import astar, build_demo_map, edge_key  # noqa: E402

SEED = 15152
LEVELS = ["LOW", "MEDIUM", "HIGH"]
SLOWDOWN = {"LOW": 1.0, "MEDIUM": 1.5, "HIGH": 2.2}      # travel-time multiplier per level
SCHOOL_PENALTY = 6.0                                       # extra routing cost (fairness)

# Edges in sensitive zones (school / residential) for the demo map
SENSITIVE_EDGES = {edge_key("A", "C"): "school zone", edge_key("C", "E"): "residential zone"}


def level_probabilities(hour):
    """P(LOW), P(MEDIUM), P(HIGH) for an hour 0-23."""
    if 8 <= hour <= 10 or 17 <= hour <= 19:       # peak hours
        return [0.10, 0.30, 0.60]
    if 22 <= hour or hour <= 5:                   # night
        return [0.80, 0.15, 0.05]
    return [0.50, 0.35, 0.15]                     # normal daytime


def make_sensitivity(graph, seed=SEED):
    """How strongly each road reacts to congestion (0.5 = calm, 1.5 = jam-prone).
    Random (seeded), except the demo's main highway A-B-D-F, which is jam-prone."""
    rng = random.Random(seed)
    sens = {}
    for u in graph:
        for v in graph[u]:
            key = edge_key(u, v)
            if key not in sens:
                sens[key] = rng.choice([0.5, 1.0, 1.5])
    for u, v in [("A", "B"), ("B", "D"), ("D", "F")]:
        sens[edge_key(u, v)] = 1.5
    for u, v in [("A", "C"), ("C", "E"), ("E", "F")]:
        sens[edge_key(u, v)] = 0.5
    return sens


def expected_multiplier(hour, sensitivity):
    """Expected slowdown of one road at this hour."""
    probs = level_probabilities(hour)
    return sum(p * (1 + sensitivity * (SLOWDOWN[lv] - 1)) for p, lv in zip(probs, LEVELS))


def build_expected_graph(graph, hour, sens, avoid_sensitive=True):
    """New graph: time = expected time (+ fairness penalty on school/residential roads)."""
    new_graph = {u: {} for u in graph}
    for u in graph:
        for v, e in graph[u].items():
            key = edge_key(u, v)
            exp_time = e["time"] * expected_multiplier(hour, sens[key])
            penalty = SCHOOL_PENALTY if (avoid_sensitive and key in SENSITIVE_EDGES) else 0
            new_graph[u][v] = {"time": exp_time + penalty, "delay": e["delay"]}
    return new_graph


def real_expected_time(path, graph, hour, sens):
    """Expected travel time of a path WITHOUT the fairness penalty."""
    total = 0.0
    for u, v in zip(path, path[1:]):
        e = graph[u][v]
        total += e["time"] * expected_multiplier(hour, sens[edge_key(u, v)]) + e["delay"]
    return total


def zones_on_path(path):
    return [SENSITIVE_EDGES[edge_key(u, v)] for u, v in zip(path, path[1:])
            if edge_key(u, v) in SENSITIVE_EDGES]


def route_report(graph, coords, sens, hour, start, goal, avoid_sensitive):
    eg = build_expected_graph(graph, hour, sens, avoid_sensitive)
    path, _, expanded = astar(eg, coords, start, goal)
    exp_time = real_expected_time(path, graph, hour, sens)
    return path, exp_time, expanded


def explain(hour, path, exp_time, zones, avoid_sensitive):
    probs = level_probabilities(hour)
    text = (f"At {hour:02d}:00 congestion probabilities are LOW={probs[0]:.2f}, "
            f"MEDIUM={probs[1]:.2f}, HIGH={probs[2]:.2f}. "
            f"Chose {' -> '.join(path)} because it has the lowest expected travel cost "
            f"(expected time {exp_time:.2f} min)")
    if avoid_sensitive:
        text += (". It avoids school/residential zones." if not zones
                 else f". It still crosses {', '.join(zones)} because every detour was much slower.")
    return text


if __name__ == "__main__":
    graph, coords = build_demo_map()
    sens = make_sensitivity(graph)
    start, goal = "A", "F"

    print(f"{'Hour':<6}{'Fairness':<10}{'Path':<18}{'Expected time':<15}{'Zones crossed'}")
    for hour in (3, 14, 8, 18):
        for avoid in (False, True):
            path, t, _ = route_report(graph, coords, sens, hour, start, goal, avoid)
            zones = zones_on_path(path)
            print(f"{hour:02d}:00 {'ON' if avoid else 'OFF':<10}{' -> '.join(path):<18}"
                  f"{t:<15.2f}{', '.join(zones) if zones else '-'}")

    print("\nExplanation example:")
    path, t, _ = route_report(graph, coords, sens, 8, start, goal, True)
    print(explain(8, path, t, zones_on_path(path), True))
