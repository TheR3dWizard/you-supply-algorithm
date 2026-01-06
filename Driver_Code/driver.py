from Simulation_Frame import Simulation
from Solutions import DirectMatching,YouSupplyAlgo

sim = Simulation(area=1000,size=1000,range=10)
sim.populate_nodes()
# print(sim)

# sol = DirectMatching(sim)
# paths = sol.solve()
# sol.print_paths()
# tot_dist = sol.get_total_distance()
# print(f"Total Distance of all Paths: {tot_dist}")
# unsat_nodes = sol.get_unsatisfied_nodes()
# print(f"Number of unsatisifed nodes: {len(unsat_nodes)}")
size = 0
sol = YouSupplyAlgo(sim)
clusters = sol.geographical_cluster(sim.get_nodes(),num_points=10)
for i,cluster in enumerate(clusters):
    print(f"Cluster {i}:")
    print(f"  Size: {cluster.get_size()}")
    size += cluster.get_size()
    print(f"  Sources: {cluster.sources}")
    print(f"  Sinks: {cluster.sinks}")

print(f"Total nodes in clusters: {size}")
print(f"Total nodes in simulation: {sim.size}")