import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

# ------------------------------
# Load GraphML
# ------------------------------
GRAPHML_PATH = "./test2.graphml"

G = nx.read_graphml(GRAPHML_PATH)

if G.is_directed():
    G = G.to_undirected()

# ------------------------------
# Position handling (same logic)
# ------------------------------
first_node_data = next(iter(G.nodes(data=True)))[1] if G.number_of_nodes() > 0 else {}

if "x" in first_node_data and "y" in first_node_data:
    raw_pos = {n: (d["x"], d["y"]) for n, d in G.nodes(data=True)}
    xs = [raw_pos[n][0] for n in G.nodes]
    ys = [raw_pos[n][1] for n in G.nodes]

    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    span_x = x_max - x_min if x_max > x_min else 1.0
    span_y = y_max - y_min if y_max > y_min else 1.0

    pos = {
        n: (
            (raw_pos[n][0] - x_min) / span_x,
            (raw_pos[n][1] - y_min) / span_y,
        )
        for n in G.nodes
    }
else:
    pos = nx.spring_layout(G, seed=42)

# ------------------------------
# Edge coloring (static heuristic-like)
# ------------------------------
# If heuristic exists use it, else fallback
edges = list(G.edges(data=True))
values = []

for _, _, d in edges:
    values.append(d.get("heuristic", np.random.rand()))

values = np.array(values)

# Normalize
norm = (values - values.min()) / (values.max() - values.min() + 1e-6)

# Same colormap
severity_cmap = mcolors.LinearSegmentedColormap.from_list(
    "severity",
    ["white", "#2ecc71", "#f1c40f", "#f39c12", "#e74c3c"],
    N=256,
)

# ------------------------------
# Plot
# ------------------------------
fig, ax = plt.subplots(figsize=(10, 6), facecolor="black")
ax.set_facecolor("black")
ax.set_axis_off()

nx.draw(
    G,
    pos,
    ax=ax,
    with_labels=True,
    node_size=300,
    node_color="grey",
    font_color="black",
    edge_color=norm,
    edge_cmap=severity_cmap,
    edge_vmin=0.0,
    edge_vmax=1.0,
    width=6,
    alpha=0.9,
)

plt.show()