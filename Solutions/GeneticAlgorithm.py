import random
import numpy as np
from typing import List, Optional
from collections import defaultdict
from sklearn.cluster import KMeans, SpectralClustering
from Simulation_Frame import Solution, Simulation, Node, Path, Cluster


# function to convert Node objects
def nodes_to_positions(nodes: List[Node]) -> np.ndarray:
    """Convert list of Node objects to numpy array of positions."""
    return np.array([node.location.to_tuple() for node in nodes])


def build_distance_matrix(nodes: List[Node]) -> np.ndarray:
    """Build distance matrix from Node objects."""
    N = len(nodes)
    dist_matrix = np.zeros((N, N))
    for i in range(N):
        for j in range(N):
            dist_matrix[i][j] = nodes[i].get_distance(nodes[j])
    return dist_matrix


# GA utility functions
def route_distance(route: List[int], source_idx: int, dist_matrix: np.ndarray) -> float:
    """Compute total round-trip distance for a route starting/ending at source."""
    if len(route) <= 1:
        return 0.0
    # Ensure source is first
    if route[0] != source_idx:
        route = [source_idx] + [r for r in route if r != source_idx]
    dist = 0.0
    # Distance from source through all nodes
    for i in range(len(route) - 1):
        dist += dist_matrix[route[i]][route[i+1]]
    # Return to source
    dist += dist_matrix[route[-1]][source_idx]
    return dist


def initial_population(size: int, nodes: List[int], source_idx: int) -> List[List[int]]:
    """Random population of valid routes with source always first."""
    pop = []
    sink_nodes = [n for n in nodes if n != source_idx]
    for _ in range(size):
        r = sink_nodes.copy()
        random.shuffle(r)
        pop.append([source_idx] + r)
    return pop


def selection(pop: List[List[int]], dist_matrix: np.ndarray, source_idx: int):
    """Tournament selection."""
    contenders = random.sample(pop, 3)
    return min(contenders, key=lambda r: route_distance(r, source_idx, dist_matrix))


def rsscx(parent1: List[int], parent2: List[int], source_idx: int, dist_matrix: np.ndarray) -> List[int]:
    """Random Start Sequential Constructive Crossover - source stays first."""
    n = len(parent1)
    offspring = [source_idx]
    visited = {source_idx}
    
    # Remove source from parents for processing
    p1_sinks = [x for x in parent1 if x != source_idx]
    p2_sinks = [x for x in parent2 if x != source_idx]
    
    while len(offspring) < n:
        last = offspring[-1]
        # Find next nodes in parents
        if last in p1_sinks:
            i1 = p1_sinks.index(last)
            next1 = p1_sinks[(i1 + 1) % len(p1_sinks)] if len(p1_sinks) > 0 else None
        else:
            next1 = None
            
        if last in p2_sinks:
            i2 = p2_sinks.index(last)
            next2 = p2_sinks[(i2 + 1) % len(p2_sinks)] if len(p2_sinks) > 0 else None
        else:
            next2 = None
            
        choices = [c for c in [next1, next2] if c is not None and c not in visited]
        if choices:
            next_city = min(choices, key=lambda c: dist_matrix[last][c])
        else:
            unvisited = [c for c in p1_sinks if c not in visited]
            if unvisited:
                next_city = min(unvisited, key=lambda c: dist_matrix[last][c])
            else:
                break
        offspring.append(next_city)
        visited.add(next_city)
    return offspring


def mutate(route: List[int], source_idx: int, prob: float = 0.1) -> List[int]:
    """Swap mutation - never move the source."""
    if random.random() < prob and len(route) > 2:
        # Only swap sink nodes (indices 1 onwards)
        i, j = random.sample(range(1, len(route)), 2)
        route[i], route[j] = route[j], route[i]
    return route


def genetic_algorithm(nodes: List[int], source_idx: int, dist_matrix: np.ndarray, 
                      generations: int = 150, pop_size: int = 30, 
                      mutation_rate: float = 0.1) -> List[int]:
    """GA route optimization for one source - enforces source at start/end."""
    population = initial_population(pop_size, nodes, source_idx)
    best = min(population, key=lambda r: route_distance(r, source_idx, dist_matrix))

    for gen in range(generations):
        new_pop = []
        for _ in range(pop_size):
            p1, p2 = selection(population, dist_matrix, source_idx), selection(population, dist_matrix, source_idx)
            child = rsscx(p1, p2, source_idx, dist_matrix)
            child = mutate(child, source_idx, mutation_rate)
            new_pop.append(child)
        population = new_pop
        current_best = min(population, key=lambda r: route_distance(r, source_idx, dist_matrix))
        if route_distance(current_best, source_idx, dist_matrix) < route_distance(best, source_idx, dist_matrix):
            best = current_best
    return best


class GeneticAlgorithm(Solution):
    def __init__(self, simulation: Optional[Simulation], 
                 geo_size: int = 50,
                 ga_generations: int = 150,
                 ga_pop_size: int = 30,
                 ga_mutation_rate: float = 0.1,
                 name: Optional[str] = "Genetic Algorithm"):
        self.paths = []
        self.simulation = simulation if simulation else None
        self.geo_size = geo_size
        self.ga_generations = ga_generations
        self.ga_pop_size = ga_pop_size
        self.ga_mutation_rate = ga_mutation_rate
        self.name = name
        self.metrics = {
            "algorithm_name": name,
            "total_distance": 0,
            "total_nodes": simulation.size if simulation else 0,
            "satisfaction_percentage": 0
        }

    def set_simulation(self, simulation):
        return super().set_simulation(simulation)

    def geographical_cluster(self, nodes: List[Node], num_points: int = 50) -> List[Cluster]:
        """Cluster nodes geographically using SpectralClustering."""
        cluster_list: List[Cluster] = []
        
        spc = SpectralClustering(
            n_clusters=self.simulation.size // num_points if self.simulation.size // num_points != 0 else 1,
            random_state=42,
            affinity="nearest_neighbors",
        )
        
        positions = []
        for node in nodes:
            positions.append(node.location.to_tuple())
        
        spc.fit(positions)
        cluster_labels = spc.labels_
        clusters = defaultdict(list)
        
        for i, label in enumerate(cluster_labels):
            clusters[label].append(self.simulation.get_nodes()[i])
        
        for cluster_nodes in clusters.values():
            cluster = Cluster(nodes=[])
            for node in cluster_nodes:
                if not node.is_source:
                    cluster.add_sink(node)
                else:
                    cluster.add_source(node)
            cluster_list.append(cluster)
        
        return cluster_list

    def assign_sinks_to_sources(self, cluster: Cluster) -> dict:
        """Assign sinks to sources using KMeans clustering with capacity constraints."""
        if not cluster.sources or not cluster.sinks:
            return {}
        
        # Get positions
        source_positions = nodes_to_positions(cluster.sources)
        sink_positions = nodes_to_positions(cluster.sinks)
        
        # KMeans clustering: assign sinks to nearest source
        n_sources = len(cluster.sources)
        kmeans = KMeans(n_clusters=n_sources, random_state=0).fit(sink_positions)
        
        # Map sink indices to source indices
        assignments = defaultdict(list)
        for sink_idx, label in enumerate(kmeans.labels_):
            sink_node = cluster.sinks[sink_idx]
            source_node = cluster.sources[label]
            assignments[source_node].append(sink_node)
        
        # Apply capacity constraints - split assignments if capacity exceeded
        capacity_aware_assignments = defaultdict(list)
        for source_node, assigned_sinks in assignments.items():
            source_capacity = abs(source_node.value)  # Capacity is absolute value
            current_demand = 0
            
            for sink_node in assigned_sinks:
                sink_demand = abs(sink_node.value)  # Demand is absolute value
                if current_demand + sink_demand <= source_capacity:
                    capacity_aware_assignments[source_node].append(sink_node)
                    current_demand += sink_demand
                # If capacity exceeded, sink remains unassigned (will be handled separately)
        
        return capacity_aware_assignments

    def solve(self) -> List[Path]:
        """Main solve method that runs GA optimization with source/sink and capacity constraints."""
        if not self.simulation:
            print("No simulation present")
            return []
        
        self.paths = []
        nodes = self.simulation.get_nodes()
        
        # Step 1: Geographical clustering
        geo_clusters = self.geographical_cluster(nodes, num_points=self.geo_size)
        
        # Step 2: For each cluster, assign sinks to sources and optimize routes
        for cluster in geo_clusters:
            if not cluster.sources or not cluster.sinks:
                continue
            
            # Assign sinks to sources
            assignments = self.assign_sinks_to_sources(cluster)
            
            # Build distance matrix for this cluster (all nodes: sources + sinks)
            all_cluster_nodes = cluster.sources + cluster.sinks
            node_to_index = {node: idx for idx, node in enumerate(all_cluster_nodes)}
            dist_matrix = build_distance_matrix(all_cluster_nodes)
            
            # Step 3: Run GA for each source
            for source_node, assigned_sinks in assignments.items():
                if not assigned_sinks:
                    continue
                
                source_idx = node_to_index[source_node]
                sink_indices = [node_to_index[sink] for sink in assigned_sinks]
                route_node_indices = [source_idx] + sink_indices
                
                # Run GA with source constraint
                best_route_indices = genetic_algorithm(
                    route_node_indices, 
                    source_idx,
                    dist_matrix,
                    generations=self.ga_generations,
                    pop_size=self.ga_pop_size,
                    mutation_rate=self.ga_mutation_rate
                )
                
                # Ensure route starts and ends at source
                if best_route_indices[0] != source_idx:
                    best_route_indices = [source_idx] + [r for r in best_route_indices if r != source_idx]
                if best_route_indices[-1] != source_idx:
                    best_route_indices.append(source_idx)
                
                # Convert indices back to Node objects
                route_nodes = [all_cluster_nodes[idx] for idx in best_route_indices]
                
                # Create path and mark nodes as satisfied
                path = Path(nodes=route_nodes)
                self.paths.append(path)
                
                for node in route_nodes:
                    self.simulation.satisfy_node(node)
        
        return self.paths

    def get_total_distance(self):
        return super().get_total_distance()

    def get_unsatisfied_nodes(self):
        return self.simulation.get_unsatisfied_nodes()

    def get_satisfaction_metrics(self, show: bool = False):
        tot_nodes = self.simulation.size
        unsat_nodes = len(self.get_unsatisfied_nodes())
        satisfaction_percent = ((tot_nodes - unsat_nodes) / tot_nodes) * 100
        print(f"Total Nodes: {tot_nodes}")
        print(f"Unsatisfied Nodes: {unsat_nodes}")
        print(f"Satisfaction Percentage: {satisfaction_percent:.2f}%")
        self.metrics["satisfaction_percentage"] = satisfaction_percent
        return satisfaction_percent

    def get_all_metrics(self, out: Optional[str] = None, name: Optional[str] = None):
        if name is None:
            name = self.name
        tot_dist = self.get_total_distance()
        satisfaction_percent = self.get_satisfaction_metrics()
        
        if not out:
            print(f"Total Distance of all Paths: {tot_dist}")
            print(f"Satisfaction Percentage: {satisfaction_percent:.2f}%")
        else:
            with open(out, 'a') as f:
                f.write(f"{name} Algorithm Metrics:\n")
                f.write(f"Total Distance of all Paths: {tot_dist}\n")
                f.write(f"Satisfaction Percentage: {satisfaction_percent:.2f}%\n\n")

    def print_paths(self):
        return super().print_paths()

    def visualize_paths(self):
        return super().visualize_paths()
