"""
main.py
Entry point: builds the campus graph, runs A* between a start and goal
location, and compares nodes expanded against plain BFS.

Usage:
    python src/main.py
    python src/main.py --start MainGate --goal Hostel
"""

import argparse
from graph import build_graph, NODE_COORDS
from astar import astar, bfs


def print_path(label, path, cost, nodes_expanded):
    print(f"\n--- {label} ---")
    if path is None:
        print("No path found.")
        return
    print("Path:", " -> ".join(path))
    if cost is not None:
        print(f"Total cost: {cost:.2f}")
    print(f"Nodes expanded: {nodes_expanded}")


def main():
    parser = argparse.ArgumentParser(description="A* route navigation on Vel Tech campus graph")
    parser.add_argument("--start", default="MainGate", choices=NODE_COORDS.keys())
    parser.add_argument("--goal", default="Hostel", choices=NODE_COORDS.keys())
    args = parser.parse_args()

    graph = build_graph(jitter=True)

    astar_path, astar_cost, astar_nodes = astar(graph, NODE_COORDS, args.start, args.goal)
    print_path("A* Search", astar_path, astar_cost, astar_nodes)

    bfs_path, bfs_nodes = bfs(graph, args.start, args.goal)
    print_path("BFS (baseline, ignores weights)", bfs_path, None, bfs_nodes)

    print(f"\nSummary: A* expanded {astar_nodes} nodes vs BFS's {bfs_nodes} nodes "
          f"to reach {args.goal} from {args.start}.")


if __name__ == "__main__":
    main()
