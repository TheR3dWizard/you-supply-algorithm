from typing import Optional,List
from Simulation_Frame import Warehouse,Location,Node,Solution,Simulation,Path,Driver
import matplotlib.pyplot as plt


class Warehouses(Solution):
    def __init__(self,simulation:Optional[Simulation],name:Optional[str]="Warehouses",range:Optional[int]=2500):
        self.paths = []
        self.source_paths = []
        self.sink_paths = []
        self.simulation = simulation if simulation else None
        self.name = name
        self.range = range
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
        # warehouse:Warehouse = Warehouse([],Location(center,center)) #set it at the center of the map (just a placeholder for now)
        nodes = self.simulation.get_nodes()


        #set mutliple warehouses 
        warehouses:List[Warehouse] = []
        x,y = 0,0
        area = self.simulation.area
        while x <= area:
            while y <= area:
                warehouses.append(Warehouse([],Location(x,y)))
                y += 2*self.range
            x += 2*self.range
            y = 0
        self.warehouses = warehouses


        #fill warehouse with all the sources
        source_drivers:List[Driver] = []

        sources = list(filter(lambda x: x.is_source,nodes))
        while not self.simulation.all_nodes_satisfied(sources=True):
            for start in sources:
                if self.simulation.is_node_satisfied(start):
                    continue
                path = Path()
                driver = Driver(self.driver_capacity)
                path.add_node(start)
                if not driver.can_add_node(start):
                    continue
                self.simulation.satisfy_node(start)
                driver.add_node(start)
                available_sources = list(filter(lambda x: not self.simulation.is_node_satisfied(x),sources))
                closest_sources = sorted(available_sources,key=lambda x:driver.location.get_distance(x.location))
                for source in closest_sources:
                    if self.simulation.is_node_satisfied(source):
                        continue
                    if not driver.is_full():
                        if not driver.can_add_node(source):
                            available = driver.get_remaining_capacity()
                            driver.add_item(source.item,available,node=source)
                            source.reduce_source(source.value - available)
                            self.simulation.satisfy_node(source)
                            path.add_node(source)    
                        driver.add_node(source)
                        self.simulation.satisfy_node(source)
                        path.add_node(source)
                        
                closest_warehouse = min(warehouses,key=lambda x:driver.location.get_distance(x.location))
                path.add_node(closest_warehouse)
                closest_warehouse.add_inventory(driver.inventory)
                paths.append(path)
                self.source_paths.append(path)
        
        # if show == True:
        #     print(len(self.simulation.get_unsatisfied_nodes()))
        
        #from warehouse, create all the different Drivers
        sink_drivers:List[Driver] = []
        for warehouse in warehouses:
            inventory = warehouse.inventory
            while not inventory.is_empty():
                driver = Driver(self.driver_capacity,location=warehouse.location)
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
                sink_drivers.append(driver)

        # if show:
        #     for driver in sink_drivers:
        #         print(driver)

        #generate the path for each driver from the warehouse
        sinks = list(filter(lambda x: not x.is_source,nodes))
        for driver in sink_drivers:
            path = Path()
            closest_warehouse = min(warehouses,key=lambda x:driver.location.get_distance(x.location))
            path.add_node(closest_warehouse)
            driver.set_location(closest_warehouse.location)
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
    
    def sum_of_all_paths(self):
        sum = 0
        for path in self.paths:
            sum += len(path) - 1
        return sum

    def num_unique_nodes_in_paths(self):
        nodes = set()
        for path in self.paths:
            for node in path.nodes:
                nodes.add(node)
        return len(nodes)

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

        warehouse_x = [warehouse.location.x for warehouse in self.warehouses]
        warehouse_y = [warehouse.location.y for warehouse in self.warehouses]

        colors = plt.colormaps.get_cmap('hsv').resampled(len(self.source_paths) + 1)
        for i, path in enumerate(self.source_paths):
            x = [node.location.x for node in path.nodes]
            y = [node.location.y for node in path.nodes]
            plt.plot(x, y, color=colors(i), label=f'Path {i+1}')
        plt.scatter(warehouse_x,warehouse_y,s=200,marker='o',edgecolors='white',linewidths=1.5,label='Warehouses')
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
        plt.scatter(warehouse_x,warehouse_y,s=200,marker='o',edgecolors='white',linewidths=1.5,label='Warehouses')
        plt.xlabel("X Position")
        plt.ylabel("Y Position")
        plt.title("All Paths")
        # plt.legend()
        plt.show()




                




        
                     





        


        
            
        
