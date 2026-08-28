"""
graph.py
Defines the campus map as a weighted graph.

Nodes  -> named locations with (x, y) coordinates (used for the heuristic)
Edges  -> road segments with a real-valued distance (the edge weight / cost)

Personalisation: edge weights are lightly jittered using a seed derived
from my register number (VH15152) so that this graph/instance is unique
to me, per the "anti-copy" rule in the assignment.
"""

import random

REGISTER_NUMBER = "VH15152"
SEED = int("".join(ch for ch in REGISTER_NUMBER if ch.isdigit()))  # 15152
random.seed(SEED)

# --- Node coordinates (arbitrary campus-plan units, used for the A* heuristic) ---
NODE_COORDS = {
    "MainGate":      (0, 0),
    "AdminBlock":    (2, 1),
    "AIMLBlock":     (4, 3),
    "Library":       (3, 5),
    "Hostel":        (6, 6),
    "Canteen":       (2, 4),
    "SportsGround":  (5, 0),
    "Auditorium":    (1, 3),
    "CSEBlock":      (4, 1),
    "Parking":       (0, 2),
}

# --- Base edges (location_a, location_b, base_distance) ---
BASE_EDGES = [
    ("MainGate", "AdminBlock", 2.5),
    ("MainGate", "Parking", 2.0),
    ("AdminBlock", "CSEBlock", 2.2),
    ("AdminBlock", "Auditorium", 2.8),
    ("Parking", "Auditorium", 1.9),
    ("CSEBlock", "AIMLBlock", 2.1),
    ("CSEBlock", "SportsGround", 2.4),
    ("Auditorium", "Canteen", 1.6),
    ("AIMLBlock", "Library", 2.6),
    ("AIMLBlock", "Canteen", 2.3),
    ("Canteen", "Library", 1.7),
    ("Library", "Hostel", 3.0),
    ("AIMLBlock", "Hostel", 3.6),
    ("SportsGround", "Hostel", 4.2),
]


def build_graph(jitter=True):
    """
    Returns an adjacency dict: {node: [(neighbour, weight), ...]}
    The graph is undirected (roads can be walked both ways).
    If jitter=True, each base distance gets a small, seeded random
    offset so this instance differs from a generic/shared graph.
    """
    adjacency = {node: [] for node in NODE_COORDS}

    for a, b, base_weight in BASE_EDGES:
        weight = base_weight
        if jitter:
            weight = round(base_weight + random.uniform(-0.2, 0.2), 2)
            weight = max(weight, 0.1)  # keep weights positive
        adjacency[a].append((b, weight))
        adjacency[b].append((a, weight))

    return adjacency


if __name__ == "__main__":
    g = build_graph()
    for node, edges in g.items():
        print(node, "->", edges)
