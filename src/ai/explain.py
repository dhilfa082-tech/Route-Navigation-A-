"""
Plain-English explanations (Explainable AI) for signal plans and route choices.
"""

from csp.signal_csp import CYCLE_LENGTH, LOST_TIME, PED_MIN


def explain_signal_plan(junction, group, solution, demand):
    """Why did this junction get these green times?"""
    ranked = sorted(group, key=lambda v: demand[v], reverse=True)
    busiest = ranked[0].split("_")[1]
    lines = [f"Junction {junction}: cycle {CYCLE_LENGTH}s, {LOST_TIME}s lost to yellow/all-red, "
             f"so {CYCLE_LENGTH - LOST_TIME}s of green are shared."]
    for v in ranked:
        phase = v.split("_")[1]
        lines.append(f"  - {phase}: {solution[v]}s green for demand {demand[v]} veh/min "
                     f"(never below the {PED_MIN}s pedestrian minimum).")
    lines.append(f"  The busiest approach ({busiest}) gets at least as much green as any "
                 f"less busy approach (priority constraint).")
    return "\n".join(lines)


def explain_route(path, expected_time, hour, fired_rules=None, zones=None):
    """Why did the router choose this path?"""
    lines = [f"Route {' -> '.join(path)} at {hour:02d}:00, expected travel time {expected_time:.1f} min."]
    if fired_rules:
        lines.append("Rules that changed the map: " + "; ".join(fired_rules))
    if zones:
        lines.append("Warning: crosses " + ", ".join(zones) + " (no faster alternative).")
    else:
        lines.append("It avoids school and residential zones.")
    lines.append("A* with f = g + h found the minimum-cost path on the updated map.")
    return "\n".join(lines)
