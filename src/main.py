"""
main.py
Entry point for the Smart Traffic Management System (Final Project, IA-2).

Phase 1 (IA-1): A* route navigation on the campus graph, compared with BFS.
Phase 2 (IA-2): CSP signal timing, rule-based incident manager, expected-time
                routing with fairness, explanations and a before/after simulation.

Usage (run from the project root):
    python src/main.py
    python src/main.py --start MainGate --goal Hostel
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ---- Phase 1 (IA-1) modules
from graph import build_graph, NODE_COORDS                                          # noqa: E402
from astar import astar, bfs                                                        # noqa: E402

# ---- Phase 2 (IA-2) modules (A* of the demo map is renamed to avoid a clash)
from ai.congestion import make_sensitivity, route_report, zones_on_path             # noqa: E402
from ai.explain import explain_route, explain_signal_plan                           # noqa: E402
from csp.signal_csp import build_csp, compare, solve_forward_checking               # noqa: E402
from rules.incident_rules import (apply_facts_to_graph, build_demo_map,             # noqa: E402
                                  forward_chain)
from rules.incident_rules import astar as astar_demo                                # noqa: E402
import plots                                                                        # noqa: E402
import simulate                                                                     # noqa: E402


def print_path(label, path, cost, nodes_expanded):
    print(f"\n--- {label} ---")
    if path is None:
        print("No path found.")
        return
    print("Path:", " -> ".join(path))
    if cost is not None:
        print(f"Total cost: {cost:.2f}")
    print(f"Nodes expanded: {nodes_expanded}")


def section(title):
    print("\n" + "=" * 8 + f" {title} " + "=" * 8)


def phase1(start, goal):
    """IA-1: A* vs BFS on the campus graph."""
    section("Phase 1: A* vs BFS on the campus graph")
    campus = build_graph(jitter=True)

    astar_path, astar_cost, astar_nodes = astar(campus, NODE_COORDS, start, goal)
    print_path("A* Search", astar_path, astar_cost, astar_nodes)

    bfs_path, bfs_nodes = bfs(campus, start, goal)
    print_path("BFS (baseline, ignores weights)", bfs_path, None, bfs_nodes)

    print(f"\nSummary: A* expanded {astar_nodes} nodes vs BFS's {bfs_nodes} nodes "
          f"to reach {goal} from {start}.")


def phase2():
    """IA-2: CSP, rules, uncertainty, explanation, simulation."""
    graph, coords = build_demo_map()
    start, goal = "A", "F"

    section("1. CSP: signal timing")
    variables, domains, groups, demand = build_csp(3)
    solution, _, _ = solve_forward_checking(variables, domains, groups, demand)
    print(explain_signal_plan(1, groups[1], solution, demand))
    compare()

    section("2. Rules: incident manager + A*")
    path0, cost0, _ = astar_demo(graph, coords, start, goal)
    print(f"Normal: {' -> '.join(path0)} cost {cost0:.2f}")
    facts, trace = forward_chain([("Accident", (path0[1], path0[2])), ("Rain",), ("Night",)])
    for line in trace:
        print("  ", line)
    path1, cost1, _ = astar_demo(apply_facts_to_graph(graph, facts), coords, start, goal)
    print(f"After incident: {' -> '.join(path1)} cost {cost1:.2f}")

    section("3. Uncertainty + fairness + explanation")
    sens = make_sensitivity(graph)
    path, t, _ = route_report(graph, coords, sens, 8, start, goal, True)
    print(explain_route(path, t, 8, None, zones_on_path(path)))

    section("4. Simulation: before vs after")
    results, _, _ = simulate.run()
    before, after = results["fixed"][0], results["csp"][0]
    mismatches = results["fixed"][2] + results["csp"][2]
    sig_before, sig_after = results["fixed"][4], results["csp"][4]
    print(f"Average travel time: fixed = {before:.2f} min, CSP = {after:.2f} min "
          f"({(before - after) / before * 100:.1f}% better)")
    print(f"Average signal delay per junction: fixed = {sig_before:.1f} s, CSP = {sig_after:.1f} s")
    print(f"A* vs Dijkstra mismatches: {mismatches}")
    simulate.save_plot(before, after)

    section("5. Pictures saved in the docs folder")
    plots.make_all()


def main():
    parser = argparse.ArgumentParser(description="Smart Traffic Management System (A* + CSP + rules)")
    parser.add_argument("--start", default="MainGate", choices=NODE_COORDS.keys())
    parser.add_argument("--goal", default="Hostel", choices=NODE_COORDS.keys())
    args = parser.parse_args()

    phase1(args.start, args.goal)
    phase2()


if __name__ == "__main__":
    main()