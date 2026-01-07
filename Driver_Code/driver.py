from Simulation_Frame import Simulation
from Solutions import DirectMatching,YouSupplyAlgo

open("metrics.txt","w").close()

sim = Simulation(area=1000,size=1000,range=10)
sim.populate_nodes()
# print(sim)

sol = DirectMatching(sim)
paths = sol.solve()
sol.print_paths()
tot_dist = sol.get_total_distance()
print(f"Total Distance of all Paths with DirectMatching: {tot_dist}")
sol.get_satisfaction_metrics()
sol.get_all_metrics(out="metrics.txt")

sim.load_nodes(sim.get_nodes())
sol = YouSupplyAlgo(sim,geo_size=50)
paths = sol.solve()
sol.print_paths()
tot_dist = sol.get_total_distance()
print(f"Total Distance of all Paths with YouSupply: {tot_dist}")
sol.get_satisfaction_metrics()
sol.get_all_metrics(out="metrics.txt")
unsatisfied_nodes = sol.get_unsatisfied_nodes()

sim.load_nodes(unsatisfied_nodes)
sol = DirectMatching(sim)
paths = sol.solve()
sol.print_paths()
tot_dist = sol.get_total_distance()
print(f"Total Distance of all Paths with DirectMatching after YouSupply: {tot_dist}")
sol.get_satisfaction_metrics()
sol.get_all_metrics(out="metrics.txt")

