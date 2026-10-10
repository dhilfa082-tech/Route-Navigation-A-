"""
Signal timing as a Constraint Satisfaction Problem (CSP).

Variables : green time (seconds) of every phase at every junction,
            e.g. "J1_NS", "J1_EW", "J1_TURN".
Domains   : 10, 15, 20, ... 60 seconds (pedestrian minimum removes small values).
Constraints (per junction):
  1. Cycle: NS + EW + TURN + lost_time == CYCLE_LENGTH
  2. Pedestrian: every phase gets at least PED_MIN seconds
  3. Priority: a phase with higher demand gets >= green than a phase with lower demand
  4. No conflicting greens: phases run one after another (never together),
     so this is guaranteed by the cycle model.

Two solvers are provided and compared:
  - plain backtracking
  - backtracking + forward checking
Random demand is seeded with the register number 15152.
"""

import random
import time

SEED = 15152          # register number VH15152
CYCLE_LENGTH = 90     # fixed cycle length in seconds
LOST_TIME = 5          # yellow + all-red time per cycle (multiple of 5 so sums can match)
PED_MIN = 15          # minimum green so pedestrians can cross
PHASES = ["NS", "EW", "TURN"]
NUM_JUNCTIONS = 3


def make_demand(num_junctions=NUM_JUNCTIONS, seed=SEED):
    """Random vehicles-per-minute demand for every phase of every junction."""
    rng = random.Random(seed)
    demand = {}
    for j in range(1, num_junctions + 1):
        for p in PHASES:
            demand[f"J{j}_{p}"] = rng.randint(10, 60) if p != "TURN" else rng.randint(5, 25)
    return demand


def build_csp(num_junctions=NUM_JUNCTIONS, demand=None):
    """Return (variables, domains, junction groups, demand)."""
    if demand is None:
        demand = make_demand(num_junctions)
    variables, domains, groups = [], {}, {}
    for j in range(1, num_junctions + 1):
        group = [f"J{j}_{p}" for p in PHASES]
        groups[j] = group
        for v in group:
            variables.append(v)
            domains[v] = list(range(PED_MIN, 61, 5))   # unary pedestrian constraint
    return variables, domains, groups, demand


def group_ok(group, assignment, demand):
    """Check all constraints of one junction on the variables assigned so far."""
    assigned = [v for v in group if v in assignment]
    # Priority constraint: higher demand => green >= lower demand's green
    for a in assigned:
        for b in assigned:
            if demand[a] > demand[b] and assignment[a] < assignment[b]:
                return False
    total = sum(assignment[v] for v in assigned)
    available = CYCLE_LENGTH - LOST_TIME
    if len(assigned) == len(group):
        return total == available            # cycle length must match exactly
    return total < available                 # partial sum must still leave room


def solve_plain(variables, domains, groups, demand):
    """Plain backtracking: constraints checked only after each assignment."""
    var_group = {v: g for g in groups.values() for v in g}
    stats = {"assignments": 0}

    def backtrack(assignment):
        if len(assignment) == len(variables):
            return dict(assignment)
        var = variables[len(assignment)]
        for value in domains[var]:
            stats["assignments"] += 1
            assignment[var] = value
            if group_ok(var_group[var], assignment, demand):
                result = backtrack(assignment)
                if result:
                    return result
            del assignment[var]
        return None

    start = time.perf_counter()
    solution = backtrack({})
    return solution, stats["assignments"], time.perf_counter() - start


def solve_forward_checking(variables, domains, groups, demand):
    """Backtracking + forward checking: prune neighbours' domains after each assignment."""
    var_group = {v: g for g in groups.values() for v in g}
    stats = {"assignments": 0}

    def forward_check(var, assignment, doms):
        """Remove values from unassigned variables of the same junction that now fail."""
        for other in var_group[var]:
            if other in assignment:
                continue
            kept = []
            for value in doms[other]:
                assignment[other] = value
                if group_ok(var_group[var], assignment, demand):
                    kept.append(value)
                del assignment[other]
            doms[other] = kept
            if not kept:
                return False                 # domain wipe-out -> backtrack early
        return True

    def backtrack(assignment, doms):
        if len(assignment) == len(variables):
            return dict(assignment)
        var = variables[len(assignment)]
        for value in doms[var]:
            stats["assignments"] += 1
            assignment[var] = value
            new_doms = {v: list(d) for v, d in doms.items()}
            new_doms[var] = [value]
            if group_ok(var_group[var], assignment, demand) and \
                    forward_check(var, assignment, new_doms):
                result = backtrack(assignment, new_doms)
                if result:
                    return result
            del assignment[var]
        return None

    start = time.perf_counter()
    solution = backtrack({}, {v: list(d) for v, d in domains.items()})
    return solution, stats["assignments"], time.perf_counter() - start


def print_plan(solution, demand, groups):
    """Readable signal plan with demand next to each green time."""
    for j, group in groups.items():
        parts = [f"{v.split('_')[1]}={solution[v]}s (demand {demand[v]})" for v in group]
        print(f"Junction {j}: " + ", ".join(parts) +
              f", lost={LOST_TIME}s, total={sum(solution[v] for v in group) + LOST_TIME}s")


def compare(sizes=(2, 3, 4)):
    """Plain vs forward checking for increasing numbers of junctions."""
    print(f"{'Junctions':<10}{'Plain tried':<14}{'Plain time(s)':<15}"
          f"{'FC tried':<12}{'FC time(s)':<12}")
    for n in sizes:
        variables, domains, groups, demand = build_csp(n)
        _, p_count, p_time = solve_plain(variables, domains, groups, demand)
        _, f_count, f_time = solve_forward_checking(variables, domains, groups, demand)
        print(f"{n:<10}{p_count:<14}{p_time:<15.5f}{f_count:<12}{f_time:<12.5f}")


if __name__ == "__main__":
    variables, domains, groups, demand = build_csp()
    solution, tried, secs = solve_forward_checking(variables, domains, groups, demand)
    if solution is None:
        print("No feasible signal plan with these constraints.")
    else:
        print("Signal plan (backtracking + forward checking):")
        print_plan(solution, demand, groups)
    print()
    compare()
