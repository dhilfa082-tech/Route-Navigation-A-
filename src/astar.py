"""
astar.py
A* search for optimal route navigation over the campus graph,
using straight-line (Euclidean) distance as the heuristic h(n).
"""

import heapq
import math
from collections import deque


def euclidean_heuristic(node, goal, coords):
    """Calculate straight-line distance h(n)."""
    x1, y1 = coords[node]
    x2, y2 = coords[goal]

    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def astar(graph, coords, start, goal):
    """
    A* Search

    f(n) = g(n) + h(n)

    g(n) = actual cost from start to current node
    h(n) = estimated straight-line distance to goal
    f(n) = total evaluation value
    """

    start_h = euclidean_heuristic(start, goal, coords)

    # (f, g, node, path)
    open_heap = [(start_h, 0, start, [start])]

    best_g = {start: 0}
    nodes_expanded = 0

    print("\n--- A* Search Process ---")
    print(f"{'Node':<15} {'g(n)':<10} {'h(n)':<10} {'f(n)=g+h':<12}")
    print("-" * 52)

    while open_heap:

        f, g, current, path = heapq.heappop(open_heap)
        nodes_expanded += 1

        # Calculate h for the current node
        h = euclidean_heuristic(current, goal, coords)

        # Display A* evaluation
        print(
            f"{current:<15} "
            f"{g:<10.2f} "
            f"{h:<10.2f} "
            f"{f:<12.2f}"
        )

        # Goal reached
        if current == goal:
            return path, g, nodes_expanded

        # Explore neighbouring nodes
        for neighbour, weight in graph[current]:

            # g(n) = actual cost so far
            new_g = g + weight

            if new_g < best_g.get(neighbour, float("inf")):

                best_g[neighbour] = new_g

                # h(n) = straight-line distance
                new_h = euclidean_heuristic(
                    neighbour,
                    goal,
                    coords
                )

                # f(n) = g(n) + h(n)
                new_f = new_g + new_h

                heapq.heappush(
                    open_heap,
                    (
                        new_f,
                        new_g,
                        neighbour,
                        path + [neighbour]
                    )
                )

    return None, float("inf"), nodes_expanded


def bfs(graph, start, goal):
    """
    Plain BFS for comparison.
    BFS ignores edge weights and finds the shortest-hop path.
    """

    visited = {start}
    queue = deque([(start, [start])])
    nodes_expanded = 0

    while queue:

        current, path = queue.popleft()
        nodes_expanded += 1

        if current == goal:
            return path, nodes_expanded

        for neighbour, _ in graph[current]:

            if neighbour not in visited:

                visited.add(neighbour)

                queue.append(
                    (neighbour, path + [neighbour])
                )

    return None, nodes_expanded