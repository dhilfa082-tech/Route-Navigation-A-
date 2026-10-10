"""
Tests for the Smart Traffic Management System.
Run from the project root:  python -m unittest discover tests
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from ai.congestion import (SENSITIVE_EDGES, build_expected_graph, expected_multiplier,  # noqa: E402
                           level_probabilities, make_sensitivity, route_report)
from ai.explain import explain_route, explain_signal_plan                                # noqa: E402
from csp.signal_csp import (CYCLE_LENGTH, LOST_TIME, PED_MIN, build_csp,                 # noqa: E402
                            solve_forward_checking, solve_plain)
from rules.incident_rules import (apply_facts_to_graph, astar, build_demo_map,           # noqa: E402
                                  edge_key, forward_chain)
from simulate import dijkstra_cost                                                       # noqa: E402


class TestSignalCSP(unittest.TestCase):
    def setUp(self):
        self.variables, self.domains, self.groups, self.demand = build_csp(3)

    def test_solution_satisfies_all_constraints(self):
        sol, _, _ = solve_forward_checking(self.variables, self.domains, self.groups, self.demand)
        self.assertIsNotNone(sol)
        for group in self.groups.values():
            greens = [sol[v] for v in group]
            self.assertEqual(sum(greens) + LOST_TIME, CYCLE_LENGTH)       # fixed cycle
            self.assertTrue(all(g >= PED_MIN for g in greens))            # pedestrian minimum
            for a in group:                                               # priority
                for b in group:
                    if self.demand[a] > self.demand[b]:
                        self.assertGreaterEqual(sol[a], sol[b])

    def test_forward_checking_tries_fewer_assignments(self):
        _, plain, _ = solve_plain(self.variables, self.domains, self.groups, self.demand)
        _, fc, _ = solve_forward_checking(self.variables, self.domains, self.groups, self.demand)
        self.assertLess(fc, plain)

    def test_both_solvers_find_a_solution(self):
        self.assertIsNotNone(solve_plain(self.variables, self.domains, self.groups, self.demand)[0])


class TestRules(unittest.TestCase):
    def test_accident_derives_blocked(self):
        facts, trace = forward_chain([("Accident", ("B", "D"))])
        self.assertIn(("Blocked", ("B", "D")), facts)
        self.assertEqual(len(trace), 1)

    def test_rain_and_night_needed_together(self):
        facts, _ = forward_chain([("Rain",)])
        self.assertNotIn(("SpeedFactor", 0.7), facts)
        facts, _ = forward_chain([("Rain",), ("Night",)])
        self.assertIn(("SpeedFactor", 0.7), facts)

    def test_emergency_vehicle_gives_green_corridor(self):
        facts, _ = forward_chain([("EmergencyVehicle", "amb1"),
                                  ("RouteOf", "amb1", [("A", "C"), ("C", "E")])])
        self.assertIn(("GreenCorridor", ("A", "C")), facts)
        self.assertIn(("GreenCorridor", ("C", "E")), facts)

    def test_blocked_edge_removed_from_graph(self):
        graph, _ = build_demo_map()
        facts, _ = forward_chain([("Accident", ("B", "D"))])
        new_graph = apply_facts_to_graph(graph, facts)
        self.assertNotIn("D", new_graph["B"])
        self.assertNotIn("B", new_graph["D"])
        self.assertIn("D", graph["B"])                 # original graph untouched


class TestAStar(unittest.TestCase):
    def setUp(self):
        self.graph, self.coords = build_demo_map()

    def test_astar_matches_dijkstra_for_all_pairs(self):
        nodes = sorted(self.coords)
        for s in nodes:
            for g in nodes:
                if s != g:
                    _, cost, _ = astar(self.graph, self.coords, s, g)
                    self.assertAlmostEqual(cost, dijkstra_cost(self.graph, s, g), places=9)

    def test_astar_stays_optimal_after_accident(self):
        facts, _ = forward_chain([("Accident", ("B", "D")), ("Rain",), ("Night",)])
        dyn = apply_facts_to_graph(self.graph, facts)
        _, cost, _ = astar(dyn, self.coords, "A", "F")
        self.assertAlmostEqual(cost, dijkstra_cost(dyn, "A", "F"), places=9)

    def test_no_path_when_goal_cut_off(self):
        facts, _ = forward_chain([("Accident", ("D", "F")), ("Accident", ("E", "F"))])
        dyn = apply_facts_to_graph(self.graph, facts)
        path, cost, _ = astar(dyn, self.coords, "A", "F")
        self.assertIsNone(path)


class TestCongestion(unittest.TestCase):
    def setUp(self):
        self.graph, self.coords = build_demo_map()
        self.sens = make_sensitivity(self.graph)

    def test_probabilities_sum_to_one(self):
        for hour in range(24):
            self.assertAlmostEqual(sum(level_probabilities(hour)), 1.0)

    def test_peak_hour_slower_than_night(self):
        self.assertGreater(expected_multiplier(8, 1.0), expected_multiplier(3, 1.0))

    def test_fairness_avoids_sensitive_roads_at_peak(self):
        path, _, _ = route_report(self.graph, self.coords, self.sens, 8, "A", "F", True)
        used = {edge_key(u, v) for u, v in zip(path, path[1:])}
        self.assertTrue(used.isdisjoint(SENSITIVE_EDGES))

    def test_expected_graph_not_cheaper_than_free_flow(self):
        eg = build_expected_graph(self.graph, 8, self.sens, avoid_sensitive=False)
        for u in self.graph:
            for v in self.graph[u]:
                self.assertGreaterEqual(eg[u][v]["time"], self.graph[u][v]["time"])


class TestExplain(unittest.TestCase):
    def test_signal_explanation_mentions_priority(self):
        _, _, groups, demand = build_csp(3)
        sol, _, _ = solve_forward_checking(*build_csp(3)[:3], demand)
        text = explain_signal_plan(1, groups[1], sol, demand)
        self.assertIn("priority", text)

    def test_route_explanation_mentions_astar(self):
        self.assertIn("A*", explain_route(["A", "B"], 5.0, 8, None, []))


if __name__ == "__main__":
    unittest.main()
