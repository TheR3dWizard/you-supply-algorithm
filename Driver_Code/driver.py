from Simulation_Frame import Simulation
from Solutions import DirectMatching,YouSupplyAlgo

sim = Simulation(area=1000,size=1000,range=10)
sim.populate_nodes()
# print(sim)

sol = YouSupplyAlgo(sim,geo_size=50)
paths = sol.solve()
sol.print_paths()
tot_dist = sol.get_total_distance()
print(f"Total Distance of all Paths with YouSupply: {tot_dist}")

sol = DirectMatching(sim)
paths = sol.solve()
sol.print_paths()
tot_dist = sol.get_total_distance()
print(f"Total Distance of all Paths with DirectMatching: {tot_dist}")