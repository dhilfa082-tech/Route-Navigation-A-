"""
Basic sanity tests for the A* implementation.
Run with: python -m pytest tests/  (from project root, with src/ on PYTHONPATH)
or simply: python tests/test_astar.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from graph import build_graph, NODE_COORDS
from astar import astar, bfs


def test_path_exists():
    graph = build_graph()
    path, cost, expanded = astar(graph, NODE_COORDS, "MainGate", "Hostel")
    assert path is not None, "A* should find a path between connected nodes"
    assert path[0] == "MainGate"
    assert path[-1] == "Hostel"
    assert cost > 0


def test_same_start_and_goal():
    graph = build_graph()
    path, cost, expanded = astar(graph, NODE_COORDS, "Library", "Library")
    assert path == ["Library"]
    assert cost == 0


def test_astar_cost_not_worse_than_bfs_hops_imply():
    # A* must return the minimum-cost path, so its cost should never
    # exceed the cost of the BFS (fewest-hops) path on the same edges.
    graph = build_graph()
    astar_path, astar_cost, _ = astar(graph, NODE_COORDS, "MainGate", "Hostel")
    bfs_path, _ = bfs(graph, "MainGate", "Hostel")

    def path_cost(path):
        total = 0
        for a, b in zip(path, path[1:]):
            for neighbour, weight in graph[a]:
                if neighbour == b:
                    total += weight
                    break
        return total

    assert astar_cost <= path_cost(bfs_path) + 1e-6


def test_disconnected_node_returns_no_path():
    graph = build_graph()
    graph["Isolated"] = []  # simulate an unreachable node
    path, cost, expanded = astar(graph, {**NODE_COORDS, "Isolated": (99, 99)}, "MainGate", "Isolated")
    assert path is None


if __name__ == "__main__":
    test_path_exists()
    test_same_start_and_goal()
    test_astar_cost_not_worse_than_bfs_hops_imply()
    test_disconnected_node_returns_no_path()
    print("All tests passed.")
