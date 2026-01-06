from Simulation_Frame import Simulation
from Solutions import DirectMatching

sim = Simulation(area=1000,size=50,range=10)
sim.populate_nodes()
# print(sim)

sol = DirectMatching(sim)
paths = sol.solve()

for i in range(len(paths)):
    RED = "\033[0;31m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    print(f"{RED}{BOLD}{i+1}th path{RESET}\n")
    print(paths[i])