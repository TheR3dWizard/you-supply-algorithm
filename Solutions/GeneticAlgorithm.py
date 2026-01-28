import random
import numpy as np
from typing import List, Optional
from collections import defaultdict
from sklearn.cluster import KMeans, SpectralClustering
from Simulation_Frame import Solution, Simulation, Node, Path, Cluster
from Solutions.yousupplyalgo import YouSupplyAlgo
from random import choice,sample
from Solutions.yousupplyalgo import YouSupplyAlgo
from random import choice, sample


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
def path_fitness(path: Path) -> float:
    """
    Proper fitness function evaluating different metrics for a path.
    
    Metrics considered:
    - Total distance traveled
    - Number of unsatisfied nodes (penalty)
    - Capacity violations (penalty)
    """
    distance = path.get_total_distance()
    
    # Penalty for capacity violations
    capacity_penalty = 0
    inventory = defaultdict(int)
    for node in path.nodes:
        inventory[node.item] += node.value
        # If inventory goes negative, we have a capacity violation
        if inventory[node.item] < 0:
            capacity_penalty += abs(inventory[node.item]) * 1000  # Heavy penalty
    
    # Penalty for unsatisfied sinks (nodes that couldn't be visited)
    unsatisfied_penalty = 0
    
    # Total fitness 
    fitness = distance + capacity_penalty + unsatisfied_penalty
    return fitness


def route_distance_with_path(path: Path) -> float:
    """Compute total round-trip distance using Path object."""
    return path.get_total_distance()


def initial_population_from_cluster(cluster: Cluster, pop_size: int) -> List[Path]:
    """
    Generate initial population of paths using YouSupply logic.
    Each path starts from a source and visits sinks in a feasible order.
    """
    population = []
    
    for i in range(pop_size):
        visited = set()
        inventory = defaultdict(int)
        
        # Start with a random source
        start_source = random.choice(cluster.sources)
        path = Path()
        path.add_node(start_source)
        visited.add(start_source)
        inventory[start_source.item] += start_source.value
        
        # Build the path
        while len(visited) < cluster.size:
            current = path.get_end()
            
            # Find feasible sinks (those we have inventory to satisfy)
            feasible_sinks = [
                node for node in cluster.sinks 
                if node not in visited and 
                node.item in inventory and 
                inventory[node.item] >= abs(node.value)
            ]
            
            # Find unvisited sources
            unvisited_sources = [
                node for node in cluster.sources 
                if node not in visited
            ]
            
            # Combine possibilities
            possibilities = feasible_sinks + unvisited_sources
            
            if not possibilities:
                # If no feasible moves, try to find nearest unvisited node
                unvisited = [n for n in cluster.sources + cluster.sinks if n not in visited]
                if unvisited:
                    # Pick nearest unvisited node
                    possibilities = [min(unvisited, key=lambda n: current.get_distance(n))]
                else:
                    break
            
            # Choose next node (random for diversity, can be made more sophisticated)
            if random.random() < 0.7 and feasible_sinks:
                # Prefer feasible sinks 70% of the time
                next_node = random.choice(feasible_sinks)
            else:
                next_node = random.choice(possibilities)
            
            path.add_node(next_node)
            visited.add(next_node)
            inventory[next_node.item] += next_node.value
        
        population.append(path)
    
    return population


def selection_with_paths(population: List[Path]) -> Path:
    """Tournament selection using Path objects and fitness function."""
    contenders = random.sample(population, min(3, len(population)))
    return min(contenders, key=lambda p: path_fitness(p))


def crossover_paths(parent1: Path, parent2: Path, cluster: Cluster) -> Path:
    """
    Crossover operation for Path objects.
    Creates offspring by combining segments from both parents while maintaining feasibility.
    """
    # Extract node sequences 
    p1_nodes = parent1.nodes.copy()
    p2_nodes = parent2.nodes.copy()
    
    # Start with a random source from either parent
    sources = [n for n in p1_nodes + p2_nodes if n in cluster.sources]
    if sources:
        start_source = random.choice(sources)
    else:
        start_source = random.choice(cluster.sources)
    
    offspring = Path()
    offspring.add_node(start_source)
    visited = {start_source}
    inventory = defaultdict(int)
    inventory[start_source.item] = start_source.value
    
    # Alternate between parents for choosing next nodes
    parents = [p1_nodes, p2_nodes]
    parent_idx = 0
    
    max_iterations = cluster.size * 2  # Prevent infinite loops
    iterations = 0
    
    while len(visited) < cluster.size and iterations < max_iterations:
        iterations += 1
        current = offspring.get_end()
        
        # Try to find next node from current parent
        current_parent = parents[parent_idx]
        
        # Find position of current node in parent
        try:
            current_pos = current_parent.index(current)
            # Look at next few nodes in parent
            candidates = []
            for j in range(1, min(4, len(current_parent))):
                next_idx = (current_pos + j) % len(current_parent)
                candidate = current_parent[next_idx]
                if candidate not in visited:
                    candidates.append(candidate)
            
            # Filter for feasible candidates
            feasible = []
            for cand in candidates:
                if cand in cluster.sources:
                    feasible.append(cand)
                elif cand.item in inventory and inventory[cand.item] >= abs(cand.value):
                    feasible.append(cand)
            
            if feasible:
                next_node = min(feasible, key=lambda n: current.get_distance(n))
            else:
                # No feasible from this parent, try other parent
                parent_idx = 1 - parent_idx
                continue
                
        except (ValueError, IndexError):
            # Current not in parent or error, switch parent
            parent_idx = 1 - parent_idx
            continue
        
        # Add node to offspring
        offspring.add_node(next_node)
        visited.add(next_node)
        inventory[next_node.item] += next_node.value
        
        # Switch parent for next iteration
        parent_idx = 1 - parent_idx
    
    # Fill remaining nodes if needed
    while len(visited) < cluster.size:
        current = offspring.get_end()
        unvisited = [n for n in cluster.sources + cluster.sinks if n not in visited]
        
        if not unvisited:
            break
        
        # Prefer feasible sinks, then sources, then any
        feasible_sinks = [
            n for n in unvisited 
            if n in cluster.sinks and 
            n.item in inventory and 
            inventory[n.item] >= abs(n.value)
        ]
        
        if feasible_sinks:
            next_node = min(feasible_sinks, key=lambda n: current.get_distance(n))
        else:
            next_node = min(unvisited, key=lambda n: current.get_distance(n))
        
        offspring.add_node(next_node)
        visited.add(next_node)
        inventory[next_node.item] += next_node.value
    
    return offspring


def mutate_path(path: Path, cluster: Cluster, prob: float = 0.1) -> Path:
    """
    Mutation operator for Path objects.
    
    Strategy:
    - Can swap consecutive sinks (that don't violate capacity constraints)
    - Can reorder sources (which requires recomputing path segments)
    - Uses small probability to maintain diversity
    """
    if random.random() > prob or len(path.nodes) <= 2:
        return path
    
    # Choose mutation type
    mutation_type = random.choice(['swap_sinks', 'reorder_sources', 'insert_source'])
    
    if mutation_type == 'swap_sinks':
        # Swap two consecutive sinks if capacity allows
        sink_positions = [i for i, node in enumerate(path.nodes) if node in cluster.sinks]
        
        if len(sink_positions) >= 2:
            # Find consecutive sinks
            consecutive_pairs = []
            for i in range(len(sink_positions) - 1):
                pos1, pos2 = sink_positions[i], sink_positions[i + 1]
                # Check if they're in same segment (between same sources)
                # Simple check: if no source between them
                has_source_between = any(
                    path.nodes[j] in cluster.sources 
                    for j in range(pos1 + 1, pos2)
                )
                if not has_source_between:
                    consecutive_pairs.append((pos1, pos2))
            
            if consecutive_pairs:
                pos1, pos2 = random.choice(consecutive_pairs)
                # Swap
                path.nodes[pos1], path.nodes[pos2] = path.nodes[pos2], path.nodes[pos1]
    
    elif mutation_type == 'reorder_sources':
        # Change position of a source (requires path reconstruction)
        source_positions = [i for i, node in enumerate(path.nodes) if node in cluster.sources]
        
        if len(source_positions) >= 2:
            # Pick a source to move
            src_idx = random.choice(source_positions)
            source_node = path.nodes[src_idx]
            
            # Remove it
            new_nodes = [n for i, n in enumerate(path.nodes) if i != src_idx]
            
            # Insert at random new position
            new_pos = random.randint(0, len(new_nodes))
            new_nodes.insert(new_pos, source_node)
            
            # Rebuild path with YouSupply logic to ensure feasibility
            mutated_path = Path()
            visited = set()
            inventory = defaultdict(int)
            
            for node in new_nodes:
                if node not in visited:
                    mutated_path.add_node(node)
                    visited.add(node)
                    inventory[node.item] += node.value
            
            return mutated_path
    
    elif mutation_type == 'insert_source':
        # Try to insert an unvisited source if any exist
        unvisited_sources = [s for s in cluster.sources if s not in path.nodes]
        
        if unvisited_sources:
            new_source = random.choice(unvisited_sources)
            insert_pos = random.randint(0, len(path.nodes))
            path.nodes.insert(insert_pos, new_source)
    
    return path


def genetic_algorithm(cluster: Cluster, generations: int = 150, 
                                 pop_size: int = 30, mutation_rate: float = 0.1) -> Path:
    
    # Initialize population
    population = initial_population_from_cluster(cluster, pop_size)
    
    # Track best solution
    best = min(population, key=lambda p: path_fitness(p))
    best_fitness = path_fitness(best)
    
    stagnation_counter = 0
    max_stagnation = 30
    
    for gen in range(generations):
        new_population = []
        
        # Elitism: keep best solution
        new_population.append(best)
        
        # Generate rest of population
        while len(new_population) < pop_size:
            # Selection
            parent1 = selection_with_paths(population)
            parent2 = selection_with_paths(population)
            
            # Crossover
            offspring = crossover_paths(parent1, parent2, cluster)
            
            # Mutation
            offspring = mutate_path(offspring, cluster, mutation_rate)
            
            new_population.append(offspring)
        
        population = new_population
        
        # Update best
        current_best = min(population, key=lambda p: path_fitness(p))
        current_fitness = path_fitness(current_best)
        
        if current_fitness < best_fitness:
            best = current_best
            best_fitness = current_fitness
            stagnation_counter = 0
        else:
            stagnation_counter += 1
        
        # Early stopping if stagnated
        if stagnation_counter >= max_stagnation:
            break
    
    return best


class GeneticAlgorithm(YouSupplyAlgo):
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
        self.clusterlist:List[Cluster] = []
        self.metrics = {
            "algorithm_name": name,
            "total_distance": 0,
            "total_nodes": simulation.size if simulation else 0,
            "satisfaction_percentage": 0
        }

    def set_simulation(self, simulation):
        return super().set_simulation(simulation)
    
    
    def geographical_cluster(self, nodes: List[Node], num_points: int = 50) -> List[Cluster]:
        return super().geographical_cluster(nodes=nodes, num_points=num_points)

    
    def assign_sinks_to_sources(self, cluster: Cluster) -> dict:
        """Assign sinks to sources using KMeans clustering with capacity constraints."""
        if not cluster.sources or not cluster.sinks:
            return {}
        
        # Get positions
        source_positions = nodes_to_positions(cluster.sources)
        sink_positions = nodes_to_positions(cluster.sinks)
        
        n_sources = len(cluster.sources)
        n_sinks = len(cluster.sinks)
        
        # Map sink indices to source indices
        assignments = defaultdict(list)
        
        # If more sources than sinks, assign each sink to nearest source directly
        if n_sources > n_sinks:
            for sink_idx, sink_node in enumerate(cluster.sinks):
                sink_pos = sink_positions[sink_idx]
                # Find nearest source
                min_dist = float('inf')
                nearest_source_idx = 0
                for source_idx, source_pos in enumerate(source_positions):
                    dist = np.linalg.norm(sink_pos - source_pos)
                    if dist < min_dist:
                        min_dist = dist
                        nearest_source_idx = source_idx
                assignments[cluster.sources[nearest_source_idx]].append(sink_node)
        else:
            # KMeans clustering: assign sinks to nearest source
            kmeans = KMeans(n_clusters=n_sources, random_state=0).fit(sink_positions)
            
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
        
        # Step 2: For each cluster, optimize using GA with Path objects
        for cluster in geo_clusters:
            if not cluster.sources or not cluster.sinks:
                continue
            
            
            # Initialize population 
            optimized_path = genetic_algorithm(
                cluster,
                generations=self.ga_generations,
                pop_size=self.ga_pop_size,
                mutation_rate=self.ga_mutation_rate
            )
            
            # Add optimized path to solution
            self.paths.append(optimized_path)
            
            # Mark nodes as satisfied
            for node in optimized_path.nodes:
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