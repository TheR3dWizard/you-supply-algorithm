import networkx as nx
import random
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import sys


# ------------------------------
# Load undirected graph from GraphML (10-edge subgraph)
# ------------------------------

# Path to your GraphML file (update as needed)
GRAPHML_PATH = "../graphml/test2.graphml"

# Load graph from GraphML
G = nx.read_graphml(GRAPHML_PATH)

# Ensure undirected
if G.is_directed():
    G = G.to_undirected()

# NOTE:
# We previously restricted to the first 10 edges, which drops any nodes
# that are not incident to those edges. For a small custom test graph
# (like `test.graphml` with nodes 2..16), that means some nodes never
# appear. We now keep the full graph so all nodes are visible.

# Positions: use existing x/y attributes if present, else spring layout
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
    # Fallback: spring layout already in [0, 1]-ish range
    pos = nx.spring_layout(G, seed=42)

# ------------------------------
# Adaptive Model
# ------------------------------
class AdaptiveDamageModel:

    def __init__(self):
        self.alpha_max = 5.0
        self.beta_max = 5.0

    @staticmethod
    def clip(x, lo=0.0, hi=1.0):
        return max(lo, min(x, hi))

    def predict_time(self, data):
        a = data["adaptive"]
        return a["T0"] * (1 + a["alpha"] * (1 - a["h"]))

    def update_alpha(self, data, T_obs):
        a = data["adaptive"]
        T_pred = self.predict_time(data)
        grad = ((T_obs - T_pred) / a["T0"]) * (1 - a["h"])
        a["alpha"] = self.clip(a["alpha"] + a["eta_alpha"] * grad, 0.0, self.alpha_max)

    def update_health(self, data, T_obs):
        a = data["adaptive"]
        h_before = a["h"]
        damage = a["mu"] * a["beta"] + a["nu"] * ((T_obs - a["T0"]) / a["T0"])
        a["h"] = self.clip(h_before - damage)
        return a["h"] - h_before

    def update_beta(self, data, delta_h):
        a = data["adaptive"]
        if delta_h < 0 and a["h"] > 0:
            grad = (-delta_h) / a["h"]
            a["beta"] = self.clip(a["beta"] + a["eta_beta"] * grad, 0.0, self.beta_max)

    def expected_cost(self, data):
        a = data["adaptive"]
        T_pred = self.predict_time(data)
        return T_pred * (1 + a["lambda_risk"] * (1 - a["h"]))

    def on_traversal(self, data, T_obs):
        self.update_alpha(data, T_obs)
        delta_h = self.update_health(data, T_obs)
        self.update_beta(data, delta_h)
        data["heuristic"] = self.expected_cost(data)

# ------------------------------
# Initialize edges
# ------------------------------
model = AdaptiveDamageModel()

for u, v, data in G.edges(data=True):
    base_time = random.uniform(5, 15)
    degradation_factor = random.uniform(0.5, 2.0)

    data["adaptive"] = {
        "T0": base_time,
        "alpha": 0.5,
        "beta": 0.1,
        "h": 1.0,
        "eta_alpha": 0.05,
        "eta_beta": 0.02,
        "mu": 0.001 * degradation_factor,
        "nu": 0.05 * degradation_factor,
        "lambda_risk": 1.0,
    }
    data["heuristic"] = base_time
    data["degradation_factor"] = degradation_factor

# Severity colormap:
# less worse (good) -> more green, more worse (bad) -> more red
_severity_cmap = mcolors.LinearSegmentedColormap.from_list(
    "severity_white_to_redish",
    ["white", "#2ecc71", "#f1c40f", "#f39c12", "#e74c3c"],
    N=256,
)

# ------------------------------
# Live Simulation Loop (plot + terminal overwrite table)
# ------------------------------
plt.ion()
fig, ax = plt.subplots(figsize=(10, 6), facecolor="black")
fig.patch.set_facecolor("black")
ax.set_facecolor("black")
ax.set_axis_off()

nodes_sorted = sorted(G.nodes())
nodes_count = len(nodes_sorted)

# Fixed line count for stable overwriting:
# 2 header lines + 1 separator + one line per node
terminal_block_lines = 3 + nodes_count

for step in range(1000):
    # simulate random traversal
    u, v = random.choice(list(G.edges()))
    data = G[u][v]

    noise = random.uniform(0.9, 1.3)
    T_obs = data["adaptive"]["T0"] * noise * data["degradation_factor"]

    model.on_traversal(data, T_obs)

    # normalize heuristics to [0, 1] for consistent coloring
    edges_list = list(G.edges(data=True))
    heuristics = [d["heuristic"] for _, _, d in edges_list]
    max_h = max(heuristics)
    min_h = min(heuristics)
    norm = np.array([(h - min_h) / (max_h - min_h + 1e-6) for h in heuristics])

    # plot
    ax.clear()
    ax.set_facecolor("black")
    ax.set_axis_off()

    # Dynamically fit axes to the full graph extent (with a small margin),
    # regardless of how large or small the graph is.
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    x_span = x_max - x_min if x_max > x_min else 1.0
    y_span = y_max - y_min if y_max > y_min else 1.0
    margin_x = 0.1 * x_span
    margin_y = 0.1 * y_span
    ax.set_xlim(x_min - margin_x, x_max + margin_x)
    ax.set_ylim(y_min - margin_y, y_max + margin_y)

    nx.draw(
        G,
        pos,
        ax=ax,
        with_labels=True,
        node_size=300,
        node_color="#9e9e9e",
        font_color="black",
        edge_color=norm,
        edge_cmap=_severity_cmap,
        edge_vmin=0.0,
        edge_vmax=1.0,
        width=6,   # increased edge width
        alpha=0.9,
    )
    # Draw per-edge health on top of roads.
    edge_health_labels = {(eu, ev): f"{edata['adaptive']['h']:.2f}" for eu, ev, edata in edges_list}
    nx.draw_networkx_edge_labels(
        G,
        pos,
        edge_labels=edge_health_labels,
        font_size=7,
        font_color="white",
        bbox={"facecolor": "black", "edgecolor": "none", "alpha": 0.8},
        ax=ax,
    )

    # terminal overwrite table (one row per node)
    lines = []
    lines.append(f"Step {step} | traversed edge: {u} - {v} | T_obs: {T_obs:.3f}")
    lines.append(f"{'Node':>6} | {'AvgHealth':>10} | {'AvgHeuristic':>14}")
    lines.append("-" * 40)

    for n in nodes_sorted:
        incident = [d for _, _, d in G.edges(n, data=True)]
        if incident:
            avg_health = float(np.mean([d["adaptive"]["h"] for d in incident]))
            avg_heur = float(np.mean([d["heuristic"] for d in incident]))
        else:
            avg_health = float("nan")
            avg_heur = float("nan")

        lines.append(f"{str(n):>6} | {avg_health:>10.2f} | {avg_heur:>14.2f}")

    block = "\n".join(lines)

    # Move cursor to top-left and overwrite block.
    # (ANSII escape code works in most terminals; if it doesn't, it will just print.)
    sys.stdout.write("\033[H" + block + "\n")
    sys.stdout.flush()

    # Keep the plot responsive
    plt.pause(0.05)

plt.ioff()
plt.show()
