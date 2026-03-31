import networkx as nx
import random
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

# ------------------------------
# Create small undirected graph (10 edges)
# ------------------------------
G = nx.random_geometric_graph(8, 0.6)
G = nx.Graph(G)
pos = nx.get_node_attributes(G, "pos")
edges = list(G.edges())[:10]
G = G.edge_subgraph(edges).copy()

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

# White -> red colormap (edges start white, go to red as cost increases)
_white_red = mcolors.LinearSegmentedColormap.from_list(
    "white_red", ["white", "#ffcccc", "#ff6666", "#cc0000", "darkred"], N=256
)

# ------------------------------
# Live Simulation Loop
# ------------------------------
plt.ion()
fig = plt.figure(figsize=(10, 6))
# Graph on the left, table on the right
ax = fig.add_axes([0.05, 0.08, 0.6, 0.88])
ax_table = fig.add_axes([0.68, 0.08, 0.3, 0.88])
ax_table.set_axis_off()

for step in range(1000):
    ax.clear()
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    ax.set_aspect("equal")

    # simulate random traversal
    u, v = random.choice(list(G.edges()))
    data = G[u][v]

    noise = random.uniform(0.9, 1.3)
    T_obs = data["adaptive"]["T0"] * noise * data["degradation_factor"]

    model.on_traversal(data, T_obs)

    # normalize heuristics to [0, 1] for consistent coloring (0 = white, 1 = red)
    heuristics = [d["heuristic"] for _, _, d in G.edges(data=True)]
    max_h = max(heuristics)
    min_h = min(heuristics)
    norm = np.array([(h - min_h) / (max_h - min_h + 1e-6) for h in heuristics])

    # draw graph with fixed color scale so 0 = white, 1 = red
    nx.draw(
        G,
        pos,
        ax=ax,
        with_labels=True,
        node_size=300,
        edge_color=norm,
        edge_cmap=_white_red,
        edge_vmin=0.0,
        edge_vmax=1.0,
        width=3,
    )

    ax.set_title("Adaptive Road Degradation Simulation")

    # table in its own axes so it doesn't overlap and updates cleanly
    ax_table.clear()
    ax_table.set_axis_off()

    table_data = []
    for (u, v, d) in G.edges(data=True):
        table_data.append([
            f"{u}-{v}",
            round(d["adaptive"]["h"], 2),
            round(d["heuristic"], 2),
        ])

    table = ax_table.table(
        cellText=table_data,
        colLabels=["Edge", "Health", "Heuristic"],
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.15, 2.2)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("gray")
        if row == 0:
            cell.set_facecolor("#e0e0e0")
            cell.set_text_props(weight="bold")

    plt.pause(0.05)

plt.ioff()
plt.show()
