f# Route Navigation using A*

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

# Smart Traffic Management System (A* Route Navigation, Final Project v2.0)

Foundations of Artificial Intelligence (25ML35T), Innovative Assignment II
Dhilfa A, Register No. VH15152, CSE (AIML), Vel Tech High Tech Dr. Rangarajan Dr. Sakunthala Engineering College

## Problem
Phase 1 (IA-1) found the optimal route on a weighted road map using A* with a
straight-line-distance heuristic. Phase 2 (IA-2) extends it into a small smart-traffic
system for a city: signal timing, incident handling, uncertain congestion and
explanations.

## Approach (3 layers on top of A*)
| Layer | What it does | File |
|---|---|---|
| CSP | Chooses green times at 3 junctions (fixed 90 s cycle, 15 s pedestrian minimum, busier approach gets at least as much green). Solved with plain backtracking and with backtracking + forward checking. | `src/csp/signal_csp.py` |
| Knowledge and reasoning | Forward-chaining rule base: `Accident(e) -> Blocked(e)`, `Rain ^ Night -> SpeedFactor(0.7)`, `EmergencyVehicle(v) -> GreenCorridor(route)`. Derived facts change edge costs, then A* re-plans. | `src/rules/incident_rules.py` |
| Applied and responsible AI | Hour-of-day congestion probabilities (LOW / MEDIUM / HIGH), routes chosen by minimum expected travel time, penalty for school and residential roads (fairness), plain-English explanations. | `src/ai/congestion.py`, `src/ai/explain.py` |
| Evaluation | 100 simulated trips, fixed signal timing vs CSP timing, and an A* vs Dijkstra optimality check on the changed graph. | `src/simulate.py` |

`src/main.py` runs everything in order.

## How to run
Requires Python 3.9 or newer.

```
git clone https://github.com/dhilfa082-tech/Route-Navigation-A-.git
cd Route-Navigation-A-
pip install -r requirements.txt
python src/main.py
```

Run from the project root. Each file can also be run alone, for example
`python src/csp/signal_csp.py`. Tests: `python -m unittest discover tests`.

All randomness is seeded with the register number `15152`.

## Sample output (from `python src/main.py`)
```
======== 2. Rules: incident manager + A* ========
Normal: A -> B -> D -> F cost 18.00
   R1 Accident(e) -> Blocked(e)  =>  derived ('Blocked', ('B', 'D'))
   R2 Rain ^ Night -> SpeedFactor(0.7)  =>  derived ('SpeedFactor', 0.7)
After incident: A -> C -> E -> F cost 29.25

======== 4. Simulation: before vs after ========
Average travel time: fixed = 11.38 min, CSP = 11.34 min (0.4% better)
Average signal delay per junction: fixed = 29.4 s, CSP = 26.2 s
A* vs Dijkstra mismatches: 0
```

## Key results
- Forward checking tried far fewer assignments than plain backtracking (for 3 junctions: 37 vs 313).
- A* returned the same cost as Dijkstra on all 100 trips, so it stays optimal on the dynamic graph.
- CSP signal plans reduced average signal delay (29.4 s to 26.2 s) but only slightly improved total travel time (0.4%), because signal delay is a small part of a trip.
- With the fairness penalty on, routes avoid the school and residential roads at peak hours, at the cost of a longer expected trip.

## Limitations
- The map and traffic data are small and synthetic, not real city data.
- Signal delay uses a simplified uniform-delay formula and a single average demand per phase.
- The CSP model has no time-varying demand.
- Real traffic decisions would need human review. This is a teaching project, not a deployable system.

## Responsible AI notes
Fairness (school and residential zones protected), explainability (every route and signal plan has a stated reason), privacy (real GPS traces must be anonymised and minimised; this project uses none), accountability and governance (a human operator should be able to override rules and signal plans).
