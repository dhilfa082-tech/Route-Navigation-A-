"""
interactive.py - run the Smart Traffic Management System with YOUR OWN inputs.

    python src/interactive.py

Menu
  1. Plan a route    : you type start, goal, hour, rain, accident road, ambulance, fairness
  2. Plan a signal   : you type the traffic demand of one junction
  3. Exit

Every plan is also saved as a picture in the docs folder:
  docs/my_route.png   and   docs/my_signal.png   (they open automatically on Windows)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib.pyplot as plt                                                        # noqa: E402

import plots                                                                           # noqa: E402
from ai.congestion import (build_expected_graph, make_sensitivity, real_expected_time,  # noqa: E402
                           zones_on_path)
from ai.explain import explain_route, explain_signal_plan                              # noqa: E402
from csp.signal_csp import build_csp, solve_forward_checking, solve_plain              # noqa: E402
from ai.congestion import SENSITIVE_EDGES                                              # noqa: E402
from rules.incident_rules import (apply_facts_to_graph, astar, build_demo_map,         # noqa: E402
                                  edge_key, forward_chain)
from simulate import FIXED_PLAN, best_csp_plan, junction_delay                       # noqa: E402


# ------------------------------------------------------------ input helpers
def ask(prompt):
    try:
        return input(prompt).strip()
    except EOFError:
        print()
        sys.exit(0)


def ask_int(prompt, low, high):
    while True:
        text = ask(prompt)
        if text.lstrip("-").isdigit() and low <= int(text) <= high:
            return int(text)
        print(f"  Please type a whole number from {low} to {high}.")


def ask_yes_no(prompt):
    while True:
        text = ask(prompt + " (y/n): ").lower()
        if text in ("y", "yes"):
            return True
        if text in ("n", "no"):
            return False
        print("  Please type y or n.")


def ask_node(prompt, nodes):
    while True:
        text = ask(prompt).upper()
        if text in nodes:
            return text
        print(f"  Please choose one of: {', '.join(nodes)}")


def ask_road(graph):
    """Return a road like ('B', 'D'), or None if the user presses Enter."""
    roads = sorted({edge_key(u, v) for u in graph for v in graph[u]})
    print("  Roads:", ", ".join(f"{u}-{v}" for u, v in roads))
    while True:
        text = ask("  Accident on which road? (example B-D, or press Enter for none): ").upper()
        if not text:
            return None
        parts = text.replace(" ", "-").split("-")
        if len(parts) == 2 and edge_key(parts[0], parts[1]) in roads:
            return edge_key(parts[0], parts[1])
        print("  That road does not exist. Choose from the list above.")


# ------------------------------------------------------------ picture output
def show_picture(fig, name):
    """Save the figure in docs/ and open it (opens automatically on Windows)."""
    os.makedirs(plots.DOCS, exist_ok=True)
    path = os.path.normpath(os.path.join(plots.DOCS, name))
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"\nPicture saved: {os.path.relpath(path)}")
    try:
        if hasattr(os, "startfile"):
            os.startfile(path)
    except OSError:
        pass


def draw_route_picture(graph, coords, path, start, goal, settings, exp_time=None, zones=()):
    fig, ax = plt.subplots(figsize=(8, 5.2))
    plots._draw_roads(ax, graph, coords, blocked=[settings["accident"]] if settings["accident"] else [])
    for key, label in SENSITIVE_EDGES.items():
        (x1, y1), (x2, y2) = coords[key[0]], coords[key[1]]
        ax.plot([x1, x2], [y1, y2], color="#cc0000", lw=1.5, ls="--", zorder=1)
        ax.text((x1 + x2) / 2 - 0.3, (y1 + y2) / 2 + 0.25, label, color="#cc0000", fontsize=8, ha="right")
    for node in ("B", "C", "D"):
        x, y = coords[node]
        ax.scatter([x], [y], s=900, facecolors="none", edgecolors="#f2a900", linewidths=2.5, zorder=2)
    if path:
        plots._draw_path(ax, path, coords, "#2a7", 0)
    for node, tag, col in ((start, "START", "#2a7"), (goal, "GOAL", "#c33")):
        x, y = coords[node]
        ax.text(x, y - 0.9, tag, color=col, fontweight="bold", fontsize=9, ha="center")
    if path:
        title = f"Route {' > '.join(path)}   expected time {exp_time:.1f} min"
        if zones:
            title += "\n(warning: crosses " + ", ".join(zones) + ")"
    else:
        title = f"No route from {start} to {goal}"
    ax.set_title(title, fontsize=11)
    notes = [f"Hour {settings['hour']:02d}:00", "Rain" if settings["rain"] else "No rain",
             f"Accident on {settings['accident'][0]}-{settings['accident'][1]}" if settings["accident"] else "No accident",
             "Ambulance green corridor" if settings["ambulance"] else "No ambulance",
             "Fairness ON" if settings["fairness"] else "Fairness OFF"]
    fig.text(0.5, 0.01, "  |  ".join(notes) + "     (yellow ring = signal, red dashed = school/residential road)",
             ha="center", fontsize=7.5)
    show_picture(fig, "my_route.png")


def draw_signal_picture(demands, plan, fixed_plan, mine, fixed):
    phases = ["NS", "EW", "TURN"]
    fig, ax = plt.subplots(figsize=(7, 4.4))
    width = 0.35
    xs = range(len(phases))
    mine_vals = [plan[f"J1_{p}"] for p in phases]
    fixed_vals = [fixed_plan[p] for p in phases]
    ax.bar([x - width / 2 for x in xs], fixed_vals, width, color="#bbbbbb", label=f"Fixed plan (delay {fixed:.1f} s)")
    ax.bar([x + width / 2 for x in xs], mine_vals, width, color="#2a7", label=f"CSP plan (delay {mine:.1f} s)")
    for x, v in zip(xs, mine_vals):
        ax.text(x + width / 2, v + 1, f"{v}s", ha="center", fontsize=9)
    for x, v in zip(xs, fixed_vals):
        ax.text(x - width / 2, v + 1, f"{v}s", ha="center", fontsize=9)
    ax.set_xticks(list(xs))
    ax.set_xticklabels([f"{p}\n(demand {demands[p]})" for p in phases])
    ax.set_ylabel("Green time (s)")
    ax.set_ylim(0, 70)
    ax.set_title("Signal plan for the demand you typed (cycle 90 s)")
    ax.legend()
    show_picture(fig, "my_signal.png")


# ------------------------------------------------------------ option 1: route
def plan_route():
    graph, coords = build_demo_map()
    sens = make_sensitivity(graph)
    nodes = sorted(coords)
    print("\n--- Route planner ---")
    print("Places:", ", ".join(nodes), "  (signals at B, C, D; school road A-C, residential road C-E)")
    start = ask_node("Start place: ", nodes)
    goal = ask_node("Goal place: ", nodes)
    while goal == start:
        print("  Goal must be different from the start.")
        goal = ask_node("Goal place: ", nodes)
    hour = ask_int("Hour of day (0-23): ", 0, 23)
    rain = ask_yes_no("Is it raining?")
    accident = ask_road(graph)
    ambulance = ask_yes_no("Is an emergency vehicle on this route?")
    fairness = ask_yes_no("Avoid school and residential roads?")

    facts_in = []
    if rain:
        facts_in.append(("Rain",))
    if hour >= 22 or hour <= 5:
        facts_in.append(("Night",))
    if accident:
        facts_in.append(("Accident", accident))

    def plan(facts_list):
        facts, trace = forward_chain(facts_list)
        dyn = apply_facts_to_graph(graph, facts)
        exp_graph = build_expected_graph(dyn, hour, sens, avoid_sensitive=fairness)
        path, _, _ = astar(exp_graph, coords, start, goal)
        return facts, trace, dyn, path

    facts, trace, dyn, path = plan(facts_in)
    if path is not None and ambulance:
        route = list(zip(path, path[1:]))
        facts, trace, dyn, path = plan(facts_in + [("EmergencyVehicle", "amb1"), ("RouteOf", "amb1", route)])

    print("\nFacts used:", [f for f in facts if f[0] in ("Rain", "Night", "Accident")] or "none")
    print("Rules that fired:")
    for line in trace:
        print("  ", line)
    if not trace:
        print("   (no rule fired)")
    settings = {"hour": hour, "rain": rain, "accident": accident, "ambulance": ambulance, "fairness": fairness}
    if path is None:
        print(f"\nNo route exists from {start} to {goal} with these road closures.")
        draw_route_picture(graph, coords, None, start, goal, settings)
        return
    exp_time = real_expected_time(path, dyn, hour, sens)
    print()
    print(explain_route(path, exp_time, hour, None, zones_on_path(path)))
    draw_route_picture(graph, coords, path, start, goal, settings, exp_time, zones_on_path(path))


# ------------------------------------------------------------ option 2: signal
def plan_signal():
    print("\n--- Signal planner (one junction, cycle 90 s) ---")
    print("Type the traffic demand in vehicles per minute (1 to 100).")
    demands = {
        "NS": ask_int("  North-South demand: ", 1, 100),
        "EW": ask_int("  East-West demand: ", 1, 100),
        "TURN": ask_int("  Turning demand: ", 1, 100),
    }
    own = {f"J1_{p}": v for p, v in demands.items()}
    variables, domains, groups, demand = build_csp(1, demand=own)

    plan, _ = best_csp_plan(groups[1], demand)
    _, plain_count, _ = solve_plain(variables, domains, groups, demand)
    _, fc_count, _ = solve_forward_checking(variables, domains, groups, demand)

    print()
    print(explain_signal_plan(1, groups[1], plan, demand))
    mine = junction_delay({p.split("_")[1]: plan[p] for p in plan}, demands) * 60
    fixed = junction_delay(FIXED_PLAN, demands) * 60
    print(f"\nAverage delay: CSP plan = {mine:.1f} s, fixed plan (30/30/25) = {fixed:.1f} s")
    print(f"Assignments tried: plain backtracking = {plain_count}, forward checking = {fc_count}")
    draw_signal_picture(demands, plan, FIXED_PLAN, mine, fixed)


# ------------------------------------------------------------ menu
def main():
    print("=== Smart Traffic Management System (interactive) ===")
    while True:
        print("\n1. Plan a route\n2. Plan a signal\n3. Exit")
        choice = ask("Choose 1, 2 or 3: ")
        if choice == "1":
            plan_route()
        elif choice == "2":
            plan_signal()
        elif choice == "3":
            print("Goodbye.")
            break
        else:
            print("  Please type 1, 2 or 3.")


if __name__ == "__main__":
    main()