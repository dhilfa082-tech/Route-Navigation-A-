"""
plots.py - saves result pictures to the docs/ folder while the program runs.

  docs/route_map.png      route before and after an accident
  docs/signal_plan.png    green times chosen by the CSP for each junction
  docs/fairness_hours.png expected trip time over the day, fairness OFF vs ON
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from ai.congestion import SENSITIVE_EDGES, make_sensitivity, route_report  # noqa: E402
from csp.signal_csp import build_csp, solve_forward_checking              # noqa: E402
from rules.incident_rules import (apply_facts_to_graph, astar, build_demo_map,  # noqa: E402
                                  edge_key, forward_chain)

DOCS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs")


def _save(fig, name):
    os.makedirs(DOCS, exist_ok=True)
    path = os.path.normpath(os.path.join(DOCS, name))
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {os.path.relpath(path)}")


def _draw_roads(ax, graph, coords, blocked=()):
    drawn = set()
    for u in graph:
        for v in graph[u]:
            key = edge_key(u, v)
            if key in drawn:
                continue
            drawn.add(key)
            (x1, y1), (x2, y2) = coords[u], coords[v]
            ax.plot([x1, x2], [y1, y2], color="#bbbbbb", lw=2, zorder=1)
    for u, v in blocked:
        (x1, y1), (x2, y2) = coords[u], coords[v]
        ax.plot([x1, x2], [y1, y2], color="#cc0000", lw=3, ls=":", zorder=2)
        ax.text((x1 + x2) / 2, (y1 + y2) / 2, "X  accident", color="#cc0000", fontsize=9,
                fontweight="bold", ha="center", bbox=dict(fc="white", ec="none", pad=1))
    for n, (x, y) in coords.items():
        ax.scatter([x], [y], s=420, c="#9bb7e0", ec="#222", zorder=3)
        ax.text(x, y, n, ha="center", va="center", fontweight="bold", zorder=4)
    ax.axis("off")


def _draw_path(ax, path, coords, color, offset):
    xs = [coords[n][0] + offset for n in path]
    ys = [coords[n][1] + offset for n in path]
    ax.plot(xs, ys, color=color, lw=4, alpha=0.85, zorder=2)


def plot_route_map():
    """Route before and after an accident on the first road of the normal route."""
    graph, coords = build_demo_map()
    path0, cost0, _ = astar(graph, coords, "A", "F")
    accident = (path0[1], path0[2])
    facts, _ = forward_chain([("Accident", accident), ("Rain",), ("Night",)])
    path1, cost1, _ = astar(apply_facts_to_graph(graph, facts), coords, "A", "F")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    _draw_roads(axes[0], graph, coords)
    _draw_path(axes[0], path0, coords, "#2a7", 0)
    axes[0].set_title(f"Normal: {' > '.join(path0)}  (cost {cost0:.2f})")
    _draw_roads(axes[1], graph, coords, blocked=[accident])
    _draw_path(axes[1], path1, coords, "#e69100", 0)
    axes[1].set_title(f"After accident + rain at night: {' > '.join(path1)}  (cost {cost1:.2f})")
    fig.suptitle("A* re-plans after the rules change the road costs")
    _save(fig, "route_map.png")


def plot_signal_plan():
    """Green time of each phase at each junction (CSP solution) with the demand."""
    variables, domains, groups, demand = build_csp(3)
    sol, _, _ = solve_forward_checking(variables, domains, groups, demand)
    phases = ["NS", "EW", "TURN"]
    colors = ["#4c78a8", "#f58518", "#54a24b"]
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    width = 0.25
    for pi, ph in enumerate(phases):
        xs, vals = [], []
        for ji, group in groups.items():
            var = [v for v in group if v.endswith(ph)][0]
            xs.append(ji - 1 + (pi - 1) * width)
            vals.append(sol[var])
            ax.text(xs[-1], sol[var] + 1, f"{sol[var]}s\n(d={demand[var]})", ha="center", fontsize=7.5)
        ax.bar(xs, vals, width=width, color=colors[pi], label=ph)
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels([f"Junction {j}" for j in groups])
    ax.set_ylabel("Green time (s)")
    ax.set_ylim(0, 70)
    ax.set_title("CSP signal plan (d = demand in vehicles/min)")
    ax.legend(title="Phase")
    _save(fig, "signal_plan.png")


def plot_fairness_hours():
    """Expected trip time for every hour with the fairness penalty OFF and ON."""
    graph, coords = build_demo_map()
    sens = make_sensitivity(graph)
    hours = list(range(24))
    off, on = [], []
    for h in hours:
        off.append(route_report(graph, coords, sens, h, "A", "F", False)[1])
        on.append(route_report(graph, coords, sens, h, "A", "F", True)[1])
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ax.plot(hours, off, marker="o", color="#cc0000", label="Fairness OFF (may use school / residential roads)")
    ax.plot(hours, on, marker="s", color="#2a7", label="Fairness ON (avoids them)")
    for a, b in ((8, 10), (17, 19)):
        ax.axvspan(a, b, color="#ffe9a8", alpha=0.5)
    ax.text(9, min(off) - 1.5, "peak", ha="center", fontsize=8)
    ax.text(18, min(off) - 1.5, "peak", ha="center", fontsize=8)
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Expected trip time A to F (min)")
    ax.set_title("Cost of fairness over the day")
    ax.set_ylim(min(off) - 3, max(on) + 6)
    ax.legend(fontsize=8, loc="upper center")
    _save(fig, "fairness_hours.png")


def make_all():
    plot_route_map()
    plot_signal_plan()
    plot_fairness_hours()


if __name__ == "__main__":
    make_all()