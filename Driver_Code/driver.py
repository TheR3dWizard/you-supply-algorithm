from Simulation_Frame import Simulation
from Solutions import DirectMatching

sim = Simulation(area=1000,size=50,range=10)
sim.populate_nodes()
# print(sim)

sol = DirectMatching(sim)
paths = sol.solve()
sol.print_paths()
tot_dist = sol.get_total_distance()
print(f"Total Distance of all Paths: {tot_dist}")
unsat_nodes = sol.get_unsatisfied_nodes()
print(f"Number of unsatisifed nodes: {len(unsat_nodes)}")