import matplotlib.pyplot as plt
from graph import build_graph, NODE_COORDS
from astar import astar


def draw_graph(graph, path=None, explored=None):
    explored = explored or []

    plt.figure(figsize=(10, 7))

    # Draw all edges
    for node, neighbours in graph.items():
        x1, y1 = NODE_COORDS[node]

        for neighbour, weight in neighbours:
            x2, y2 = NODE_COORDS[neighbour]

            # Draw each undirected edge only once
            if NODE_COORDS[node] < NODE_COORDS[neighbour]:
                plt.plot(
                    [x1, x2],
                    [y1, y2],
                    linewidth=1
                )

                # Edge weight
                mid_x = (x1 + x2) / 2
                mid_y = (y1 + y2) / 2

                plt.text(
                    mid_x,
                    mid_y,
                    str(weight),
                    fontsize=8
                )

    # Draw nodes
    for node, (x, y) in NODE_COORDS.items():

        if path and node in path:
            plt.scatter(x, y, s=500)
        elif node in explored:
            plt.scatter(x, y, s=400)
        else:
            plt.scatter(x, y, s=400)

        plt.text(
            x,
            y + 0.25,
            node,
            ha="center",
            fontsize=9
        )

    # Highlight final A* path
    if path:
        for i in range(len(path) - 1):

            x1, y1 = NODE_COORDS[path[i]]
            x2, y2 = NODE_COORDS[path[i + 1]]

            plt.plot(
                [x1, x2],
                [y1, y2],
                linewidth=4
            )

    plt.title("A* Route Navigation Simulation")
    plt.xlabel("X Coordinate")
    plt.ylabel("Y Coordinate")
    plt.grid(True)

    plt.show()


def main():

    graph = build_graph(jitter=True)

    start = "MainGate"
    goal = "Hostel"

    path, cost, nodes = astar(
        graph,
        NODE_COORDS,
        start,
        goal
    )

    print("\nFinal A* Path:")
    print(" -> ".join(path))
    print("Total Cost:", round(cost, 2))
    print("Nodes Processed:", nodes)

    draw_graph(
        graph,
        path=path
    )


if __name__ == "__main__":
    main()