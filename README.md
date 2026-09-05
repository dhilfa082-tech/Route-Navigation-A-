# Route Navigation using A*

**Course:** Foundations of Artificial Intelligence (25ML35T)
**Student:** Dhilfa A — VH15152
**Batch 7** — assigned problem: *Route Navigation using A\**

## Problem

Given a map of Vel Tech campus locations connected by roads of known
distance, find the lowest-cost route between a start and a goal
location using the A* search algorithm.

- **States:** a location on campus (e.g. `MainGate`, `Library`, `Hostel`)
- **Actions:** move along a road to an adjacent location
- **Goal test:** current location equals the requested goal location
- **Cost:** the sum of road distances travelled

## Approach

A* explores nodes in order of `f(n) = g(n) + h(n)`, where:
- `g(n)` = actual distance travelled so far from the start
- `h(n)` = straight-line (Euclidean) distance from `n` to the goal

The straight-line distance is an **admissible heuristic** — it can never
overestimate the true road distance, since roads never take a shorter
path than a straight line — which guarantees A* returns the optimal
(minimum-cost) route.

For comparison, a plain **BFS** (ignores edge weights, counts hops only)
is also run on the same graph, to show how many more nodes it expands
versus A*'s heuristic-guided search.

## Personalisation

Edge weights are seeded from my register number (**VH15152** → seed
`15152`) and lightly randomised (`src/graph.py`), so this graph
instance is unique to my submission.

## How to run

```bash
git clone <this-repo-url>
cd route-navigation-astar
pip install -r requirements.txt   # no external deps currently required
python src/main.py --start MainGate --goal Hostel
```

Run tests:
```bash
python tests/test_astar.py
```

## Sample I/O

```
$ python src/main.py --start MainGate --goal Hostel

--- A* Search ---
Path: MainGate -> Parking -> Auditorium -> Canteen -> Library -> Hostel
Total cost: 9.94
Nodes expanded: 7

--- BFS (baseline, ignores weights) ---
Path: MainGate -> AdminBlock -> CSEBlock -> AIMLBlock -> Hostel
Nodes expanded: 10

Summary: A* expanded 7 nodes vs BFS's 10 nodes to reach Hostel from MainGate.
```

## Limitations

- Campus graph is a simplified, hand-modelled representation (10 nodes),
  not a GPS-accurate map.
- Heuristic coordinates are illustrative campus-plan units, not real GPS coordinates.

## Honesty note

An AI assistant (Claude) was consulted for repo scaffolding and code
review. The algorithm, graph design, and all code were understood and
written with that assistance; I can explain and modify every part.
