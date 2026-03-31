import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

# ------------------------------
# Load Graph
# ------------------------------
GRAPHML_PATH = "./test2.graphml"

G = nx.read_graphml(GRAPHML_PATH)

if G.is_directed():
    G = G.to_undirected()

# ------------------------------
# Position
# ------------------------------
first_node_data = next(iter(G.nodes(data=True)))[1] if G.number_of_nodes() > 0 else {}

if "x" in first_node_data and "y" in first_node_data:
    pos = {n: (d["x"], d["y"]) for n, d in G.nodes(data=True)}
else:
    pos = nx.spring_layout(G, seed=42)

# ------------------------------
# Edge weights (if available)
# ------------------------------
edges = list(G.edges(data=True))
values = [d.get("heuristic", 1.0) for _, _, d in edges]

values = np.array(values)
norm = (values - values.min()) / (values.max() - values.min() + 1e-6)

# ------------------------------
# Plot (publication style)
# ------------------------------
plt.figure(figsize=(8, 5), dpi=300)
ax = plt.gca()

# Clean look
ax.set_facecolor("white")
ax.axis("off")

# Draw edges first
nx.draw_networkx_edges(
    G,
    pos,
    edge_color=norm,
    edge_cmap=plt.cm.viridis,
    width=1.5,
    alpha=0.8,
)

# Draw nodes
nx.draw_networkx_nodes(
    G,
    pos,
    node_size=80,
    node_color="#2c3e50",
)

# Optional: labels (usually OFF for papers unless small graph)
# nx.draw_networkx_labels(G, pos, font_size=6)

# Save high-quality output
plt.tight_layout()
plt.savefig("graph_publication.png", dpi=300, bbox_inches="tight")
plt.savefig("graph_publication.pdf", bbox_inches="tight")

plt.show()