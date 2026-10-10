"""
Rule-based incident manager (forward chaining) for the Smart Traffic system.

Facts are tuples, for example:
    ("Accident", ("B", "D"))          an accident on road B-D
    ("Rain",), ("Night",)             weather / time of day
    ("EmergencyVehicle", "amb1")      an ambulance is on the road
    ("RouteOf", "amb1", [("A","B"), ("B","D")])   the road it will use

Rules:
    R1: Accident(e)                     -> Blocked(e)
    R2: Rain AND Night                  -> SpeedFactor(0.7)
    R3: EmergencyVehicle(v), RouteOf(v) -> GreenCorridor(e) for every road e on the route

Forward chaining keeps firing rules until no new fact appears.
The derived facts then change the edge costs, and A* re-plans.

Graph format used here:  graph[u][v] = {"time": travel_time, "delay": signal_delay}
cost of an edge = time + delay. If your IA-1 graph is different, only
apply_facts_to_graph() and the A* call need to be adapted.
"""

import heapq
import math
import random

SEED = 15152   # register number VH15152


# ----------------------------------------------------------------- rules
def rule_accident(facts):
    """R1: Accident(e) -> Blocked(e)"""
    return [("Blocked", f[1]) for f in facts if f[0] == "Accident"]


def rule_rain_night(facts):
    """R2: Rain AND Night -> SpeedFactor(0.7)"""
    if ("Rain",) in facts and ("Night",) in facts:
        return [("SpeedFactor", 0.7)]
    return []


def rule_emergency(facts):
    """R3: EmergencyVehicle(v) AND RouteOf(v, edges) -> GreenCorridor(e)"""
    derived = []
    for f in facts:
        if f[0] == "EmergencyVehicle":
            for g in facts:
                if g[0] == "RouteOf" and g[1] == f[1]:
                    derived += [("GreenCorridor", e) for e in g[2]]
    return derived


RULES = [
    ("R1 Accident(e) -> Blocked(e)", rule_accident),
    ("R2 Rain ^ Night -> SpeedFactor(0.7)", rule_rain_night),
    ("R3 EmergencyVehicle(v) -> GreenCorridor(route)", rule_emergency),
]


def forward_chain(initial_facts):
    """Fire rules until nothing new is derived. Returns (all facts, trace)."""
    facts = set()
    for f in initial_facts:                      # lists are not hashable, store as tuples
        facts.add(tuple(tuple(x) if isinstance(x, list) else x for x in f))
    trace = []
    changed = True
    while changed:
        changed = False
        for name, rule in RULES:
            for new in rule(facts):
                new = tuple(tuple(x) if isinstance(x, list) else x for x in new)
                if new not in facts:
                    facts.add(new)
                    trace.append(f"{name}  =>  derived {new}")
                    changed = True
    return facts, trace


# ------------------------------------------------- facts change the graph
def edge_key(u, v):
    return tuple(sorted((u, v)))


def apply_facts_to_graph(graph, facts):
    """Return a NEW graph whose edge costs reflect the derived facts."""
    blocked = {edge_key(*f[1]) for f in facts if f[0] == "Blocked"}
    green = {edge_key(*f[1]) for f in facts if f[0] == "GreenCorridor"}
    factor = min([f[1] for f in facts if f[0] == "SpeedFactor"], default=1.0)

    new_graph = {u: {} for u in graph}
    for u in graph:
        for v, e in graph[u].items():
            key = edge_key(u, v)
            if key in blocked:
                continue                                  # road closed: edge removed
            delay = 0 if key in green else e["delay"]     # green corridor: no signal wait
            new_graph[u][v] = {"time": e["time"] / factor, "delay": delay}
    return new_graph


# ------------------------------------------------------------------ A*
def astar(graph, coords, start, goal):
    """A* with f = g + h. h = straight-line distance (never above true cost)."""
    def h(n):
        return math.dist(coords[n], coords[goal])

    open_heap = [(h(start), 0, start, [start])]
    best_g = {start: 0}
    expanded = 0
    while open_heap:
        f, g, node, path = heapq.heappop(open_heap)
        if node == goal:
            return path, g, expanded
        if g > best_g.get(node, float("inf")):
            continue
        expanded += 1
        for nxt, e in graph[node].items():
            ng = g + e["time"] + e["delay"]
            if ng < best_g.get(nxt, float("inf")):
                best_g[nxt] = ng
                heapq.heappush(open_heap, (ng + h(nxt), ng, nxt, path + [nxt]))
    return None, float("inf"), expanded


# --------------------------------------------------------------- demo map
def build_demo_map(seed=SEED):
    """Small road network. Travel time = distance * detour (>= 1), so h stays admissible."""
    rng = random.Random(seed)
    coords = {"A": (0, 0), "B": (4, 1), "C": (3, 5), "D": (8, 2), "E": (7, 6), "F": (12, 4)}
    roads = [("A", "B"), ("A", "C"), ("B", "C"), ("B", "D"), ("C", "E"),
             ("D", "E"), ("D", "F"), ("E", "F")]
    graph = {n: {} for n in coords}
    for u, v in roads:
        t = math.dist(coords[u], coords[v]) * rng.uniform(1.0, 1.3)
        d = rng.choice([0, 2, 3])                     # signal delay at the end of the road
        graph[u][v] = {"time": t, "delay": d}
        graph[v][u] = {"time": t, "delay": d}
    return graph, coords


def show(label, path, cost, expanded):
    print(f"{label:<28} path={' -> '.join(path)}  cost={cost:.2f}  nodes expanded={expanded}")


if __name__ == "__main__":
    graph, coords = build_demo_map()
    start, goal = "A", "F"

    path0, cost0, exp0 = astar(graph, coords, start, goal)
    show("Normal conditions:", path0, cost0, exp0)

    # Incident: accident on the first road of the normal path, rain at night
    accident_edge = (path0[1], path0[2])
    facts_in = [("Accident", accident_edge), ("Rain",), ("Night",)]
    facts, trace = forward_chain(facts_in)
    print("\nForward chaining trace:")
    for line in trace:
        print("  ", line)

    graph2 = apply_facts_to_graph(graph, facts)
    path1, cost1, exp1 = astar(graph2, coords, start, goal)
    print()
    show("After accident + rain/night:", path1, cost1, exp1)

    # Emergency vehicle: green corridor along its own route, then re-plan
    amb_route = list(zip(path1, path1[1:]))
    facts_in += [("EmergencyVehicle", "amb1"), ("RouteOf", "amb1", amb_route)]
    facts, trace = forward_chain(facts_in)
    print("\nTrace with emergency vehicle (new facts only matter for R3):")
    for line in trace:
        if line.startswith("R3"):
            print("  ", line)
    graph3 = apply_facts_to_graph(graph, facts)
    path2, cost2, exp2 = astar(graph3, coords, start, goal)
    print()
    show("Ambulance with green corridor:", path2, cost2, exp2)