import matplotlib.cm as cm
import matplotlib.colors as colors
import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt

# Define the coordinate as (latitude, longitude)
center_point = (10.991343783982689, 77.0044269727586)

# Download road network around the coordinate (radius in meters)
G_directed = ox.graph_from_point(center_point, dist=5000, network_type="drive")

# FIX: Use the new convert module for undirected conversion
gu = ox.convert.to_undirected(G_directed)

# Heuristic Calculation
for u, v, k, data in gu.edges(keys=True, data=True):
    # Example: length / lanes (higher is "more costly")
    length = data.get('length', 1)
    if type(data.get('lanes')) == list:
        lanes = float(data.get('lanes')[0])
    elif type(data.get('lanes')) == int:    
        lanes = float(data.get('lanes'))
    else:
        lanes = 1.0
    data['my_heuristic'] = length / lanes

# Get the heuristic values to determine the color range
edge_values = [data['my_heuristic'] for u, v, k, data in gu.edges(keys=True, data=True)]

# Create a color map (Low = Green/Blue, High = Red)
# 'inferno' or 'Reds' are good choices here
norm = colors.Normalize(vmin=min(edge_values), vmax=max(edge_values))
cmap = cm.get_cmap('Reds') # Use 'Reds' so higher weight = more red

# Assign a color to each edge based on its heuristic
ec = [cmap(norm(val)) for val in edge_values]

# # Plot the graph
# fig, ax = ox.plot_graph(
#     gu, 
#     edge_color=ec, 
#     edge_linewidth=2, 
#     node_size=0, 
#     bgcolor='k' # Black background makes the colors pop
# )

startpoint = (11.0183, 76.9631)
endpoint = (10.991343783982689, 77.0044269727586)

orig_node = ox.distance.nearest_nodes(gu, X=startpoint[1], Y=startpoint[0])
dest_node = ox.distance.nearest_nodes(gu, X=endpoint[1], Y=endpoint[0])

route = nx.shortest_path(gu, orig_node, dest_node, weight='my_heuristic')
# Plot the route
fig, ax = ox.plot_graph_route(gu, route, route_linewidth=6, node_size=0, bgcolor='k')
plt.show()  

routewithoutheuristic = nx.shortest_path(gu, orig_node, dest_node)
fig, ax = ox.plot_graph_route(gu, routewithoutheuristic, route_linewidth=6, node_size=0, bgcolor='k')
plt.show()  
