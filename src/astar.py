"""
astar.py
A* search for optimal route navigation over the campus graph,
using straight-line (Euclidean) distance as the heuristic h(n).

Also includes a plain BFS implementation (unweighted shortest-hop
path) purely so main.py can report a nodes-expanded comparison,
as required in the report.
"""

import heapq
import math
from collections import deque


def euclidean_heuristic(node, goal, coords):
    (x1, y1) = coords[node]
    (x2, y2) = coords[goal]
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def astar(graph, coords, start, goal):
    """
    Returns (path, total_cost, nodes_expanded).
    f(n) = g(n) + h(n)
      g(n) = cost so far from start to n
      h(n) = straight-line distance from n to goal (admissible: it never
             overestimates the true road distance, so A* stays optimal)
    """
    open_heap = [(euclidean_heuristic(start, goal, coords), 0, start, [start])]
    best_g = {start: 0}
    nodes_expanded = 0

    while open_heap:
        f, g, current, path = heapq.heappop(open_heap)
        nodes_expanded += 1

        if current == goal:
            return path, g, nodes_expanded

        for neighbour, weight in graph[current]:
            new_g = g + weight
            if new_g < best_g.get(neighbour, float("inf")):
                best_g[neighbour] = new_g
                new_f = new_g + euclidean_heuristic(neighbour, goal, coords)
                heapq.heappush(open_heap, (new_f, new_g, neighbour, path + [neighbour]))

    return None, float("inf"), nodes_expanded  # no path found


def bfs(graph, start, goal):
    """
    Plain BFS (counts hops, ignores edge weights).
    Used only as a baseline for the nodes-expanded comparison in the report,
    since BFS does not use any heuristic guidance.
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
                queue.append((neighbour, path + [neighbour]))

    return None, nodes_expanded
