from collections import defaultdict
from typing import Optional,List
from Simulation_Frame import Warehouse,Location,Node,Solution,Simulation,Path,Driver
import matplotlib.pyplot as plt


class Warehouses(Solution):
    def __init__(self,simulation:Optional[Simulation],name:Optional[str]="Warehouses"):
        self.paths = []
        self.source_paths = []
        self.sink_paths = []
        self.simulation = simulation if simulation else None
        self.name = name
        self.driver_capacity = 50
        self.metrics = {
            "algorithm_name":name,
            "total_distance":0,
            "total_nodes":self.simulation.size,
            "satisfaction_percentage":0
            }
        
    def solve(self,show=False):
        paths:List[Path] = []
        center = self.simulation.area/2
        warehouse:Warehouse = Warehouse([],Location(center,center)) #set it at the center of the map (just a placeholder for now)
        nodes = self.simulation.get_nodes()

        #fill warehouse with all the sources
        sources = list(filter(lambda x: x.is_source,nodes))
        for source in sources:
            fill_path = Path([source,warehouse])
            warehouse.add_node(source)
            self.simulation.satisfy_node(source)
            paths.append(fill_path)
            self.source_paths.append(fill_path)
        
        #from warehouse, create all the different Drivers
        drivers:List[Driver] = []
        inventory = warehouse.inventory
        while not inventory.is_empty():
            driver = Driver(self.driver_capacity)
            for item in inventory.get_items():
                if driver.is_full():
                    break
                available = inventory.get_amount(item)
                if available <= driver.get_remaining_capacity():
                    driver.add_item(item,available)
                    inventory.remove_item(item,available)
                    continue
                else:
                    add_amt = driver.get_remaining_capacity()
                    driver.add_item(item,add_amt)
                    inventory.remove_item(item,add_amt)
                    break
            drivers.append(driver)

        if show:
            for driver in drivers:
                print(driver)

        #generate the path for each driver from the warehouse
        sinks = list(filter(lambda x: not x.is_source,nodes))
        for driver in drivers:
            path = Path()
            path.add_node(warehouse)
            items = driver.get_items()
            for item in items:
                amount_left = driver.get_amount(item)
                available_sinks = list(filter(driver.inventory.is_feasible_sink,sinks))
                min_sink = min(available_sinks,key= lambda x: abs(x.value)).value
                closest_sinks = sorted(available_sinks,key=lambda x:driver.location.get_distance(x.location))
                for sink in closest_sinks:
                    if self.simulation.is_node_satisfied(sink):
                        continue

                    val = abs(sink.value)
                    if val <= amount_left:
                        path.add_node(sink)
                        self.simulation.satisfy_node(sink)
                        amount_left -= val

                    if amount_left < min_sink:
                        break

            if len(path.nodes) == 1: #No sinks
                continue
            paths.append(path)
            self.sink_paths.append(path)

        self.paths = paths
        return paths
    
    def get_satisfaction_metrics(self):
        tot_nodes = self.simulation.size
        unsat_nodes = len(self.simulation.get_unsatisfied_nodes())
        satisfaction_percent = ((tot_nodes - unsat_nodes) / tot_nodes) * 100
        print(f"Total Nodes: {tot_nodes}")
        print(f"Unsatisfied Nodes: {unsat_nodes}")
        print(f"Satisfaction Percentage: {satisfaction_percent:.2f}%")
        self.metrics["satisfaction_percentage"] = satisfaction_percent
        return satisfaction_percent

    def visualize_paths(self, paths):
        return None
    
    def print_paths(self):
        return super().print_paths()

    def get_all_metrics(self,out:Optional[str]=None,name:Optional[str]="Warehouses"):
        tot_dist = self.get_total_distance()
        satisfaction_percent = self.get_satisfaction_metrics()

        if not out:
            print(f"Total Distance of all Paths: {tot_dist}")
            print(f"Satisfaction Percentage: {satisfaction_percent:.2f}%")
        else:
            with open(out,'a') as f:
                f.write(f"{name} Algorithm Metrics:\n")
                f.write(f"Total Distance of all Paths: {tot_dist}\n")
                f.write(f"Satisfaction Percentage: {satisfaction_percent:.2f}%\n\n")

    def plot_warehouse_paths(self):
        """
        Plots all the different plots into one graph with each path in a different color.
        """
        # plt.figure(figsize=(10, 10))

        colors = plt.colormaps.get_cmap('hsv').resampled(len(self.source_paths) + 1)
        for i, path in enumerate(self.source_paths):
            x = [node.location.x for node in path.nodes]
            y = [node.location.y for node in path.nodes]
            plt.plot(x, y, color=colors(i), label=f'Path {i+1}')
        plt.xlabel("X Position")
        plt.ylabel("Y Position")
        plt.title("All Paths")
        # plt.legend()
        plt.show()

        colors = plt.colormaps.get_cmap('hsv').resampled(len(self.sink_paths) + 1)
        for i, path in enumerate(self.sink_paths):
            x = [node.location.x for node in path.nodes]
            y = [node.location.y for node in path.nodes]
            plt.plot(x, y, color=colors(i), label=f'Path {i+1}')
        plt.xlabel("X Position")
        plt.ylabel("Y Position")
        plt.title("All Paths")
        # plt.legend()
        plt.show()




                




        
                     





        


        
            
        
