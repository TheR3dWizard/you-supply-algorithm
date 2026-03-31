from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import networkx as nx
import numpy as np
import osmnx as ox


# ------------------------------
# Adaptive Damage Model
# ------------------------------
# Note: The existing `Simulation_Frame/osmx.gradient.py` is a runnable script
# (not import-friendly). To keep this new simulation self-contained, we reuse
# the same model logic here.


class AdaptiveDamageModel:
    def __init__(self):
        self.alpha_max = 5.0
        self.beta_max = 5.0

    @staticmethod
    def clip(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
        return max(lo, min(x, hi))

    def predict_time(self, data: dict) -> float:
        a = data["adaptive"]
        return a["T0"] * (1 + a["alpha"] * (1 - a["h"]))

    def update_alpha(self, data: dict, T_obs: float) -> None:
        a = data["adaptive"]
        T_pred = self.predict_time(data)
        grad = ((T_obs - T_pred) / a["T0"]) * (1 - a["h"])
        a["alpha"] = self.clip(a["alpha"] + a["eta_alpha"] * grad, 0.0, self.alpha_max)

    def update_health(self, data: dict, T_obs: float) -> float:
        a = data["adaptive"]
        h_before = a["h"]
        damage = a["mu"] * a["beta"] + a["nu"] * ((T_obs - a["T0"]) / a["T0"])
        a["h"] = self.clip(h_before - damage)
        return a["h"] - h_before

    def update_beta(self, data: dict, delta_h: float) -> None:
        a = data["adaptive"]
        if delta_h < 0 and a["h"] > 0:
            grad = (-delta_h) / a["h"]
            a["beta"] = self.clip(a["beta"] + a["eta_beta"] * grad, 0.0, self.beta_max)

    def expected_cost(self, data: dict) -> float:
        # Interpreting "cost" as expected traversal time in seconds.
        a = data["adaptive"]
        T_pred = self.predict_time(data)
        return T_pred * (1 + a["lambda_risk"] * (1 - a["h"]))

    def on_traversal(self, data: dict, T_obs: float) -> None:
        self.update_alpha(data, T_obs)
        delta_h = self.update_health(data, T_obs)
        self.update_beta(data, delta_h)
        # Store predicted/expected traversal time (seconds).
        data["heuristic_time_s"] = self.expected_cost(data)


# ------------------------------
# Utilities
# ------------------------------


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance (meters)."""
    r = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@dataclass(frozen=True)
class City:
    lat: float
    lon: float


# A few major cities: lat/lon (degrees).
MAJOR_CITIES: Dict[str, City] = {
    "chennai": City(lat=13.0827, lon=80.2707),
    "bengaluru": City(lat=12.9716, lon=77.5946),
    "hyderabad": City(lat=17.3850, lon=78.4867),
    "coimbatore": City(lat=10.995907840386451, lon=76.95482942602024),
    "washington": City(lat=38.90717252385287, lon=-77.03654700873811),
    "madrid": City(lat=40.42790121890256, lon=-3.69577108966905),
    "seoul": City(lat=37.508479378257285, lon=127.03866126151253),
}


def ensure_simple_undirected_graph(G: nx.Graph | nx.MultiGraph) -> nx.Graph:
    """
    Convert OSMnx graph (often MultiGraph) to a simple undirected Graph.
    For parallel edges, keep the minimum `length` edge.
    """
    if not G.is_multigraph():
        Gu = G
        if Gu.is_directed():
            Gu = Gu.to_undirected()
        return nx.Graph(Gu)

    Gu = nx.Graph()
    for n, data in G.nodes(data=True):
        Gu.add_node(n, **dict(data))

    # Keep min-length edge for each u-v.
    best: Dict[Tuple[int, int], dict] = {}
    for u, v, k, data in G.edges(keys=True, data=True):
        if u == v:
            continue
        length = float(data.get("length", 1.0))
        a = (u, v) if u <= v else (v, u)
        if a not in best or length < float(best[a].get("length", 1.0)):
            best[a] = dict(data)
            best[a]["length"] = length

    for (u, v), data in best.items():
        Gu.add_edge(u, v, **data)
    return Gu


def get_node_latlon(G: nx.Graph, n) -> Tuple[float, float]:
    # OSMnx uses: x=lon, y=lat
    data = G.nodes[n]
    return float(data["y"]), float(data["x"])


def build_osm_undirected_graph(center: City, dist_m: float, network_type: str) -> nx.Graph:
    """
    Download a road network around a center point and return an undirected simple Graph.
    """
    G = ox.graph_from_point((center.lat, center.lon), dist=dist_m, network_type=network_type)
    G = ox.convert.to_undirected(G)
    return ensure_simple_undirected_graph(G)


def initialize_edge_damage_and_time(
    G: nx.Graph,
    speed_mps: float,
    rng: random.Random,
    base_noise_lo: float = 0.90,
    base_noise_hi: float = 1.10,
) -> None:
    """
    For each edge (u, v), attach an adaptive model state and a baseline traversal time in seconds.
    """
    for u, v, data in G.edges(data=True):
        length_m = float(data.get("length", 1.0))
        base_time_s = length_m / speed_mps
        degradation_factor = rng.uniform(0.5, 2.0)

        data["degradation_factor"] = degradation_factor
        data["length_m"] = length_m

        # Adaptive parameters mirror osmx.gradient.py.
        data["adaptive"] = {
            "T0": base_time_s,
            "alpha": 0.5,
            "beta": 0.1,
            "h": 1.0,  # health in [0,1], 1=perfect
            "eta_alpha": 0.05,
            "eta_beta": 0.02,
            "mu": 0.001 * degradation_factor,
            "nu": 0.05 * degradation_factor,
            "lambda_risk": 1.0,
        }

        # Track average predicted time (seconds) over many "traversals".
        data["time_accum_s"] = 0.0

        # Initial prediction
        data["heuristic_time_s"] = base_time_s

        # Store noise range for reproducibility/debug.
        data["obs_noise_lo"] = base_noise_lo
        data["obs_noise_hi"] = base_noise_hi


def run_edge_traversal_simulation(
    G: nx.Graph,
    num_steps: int,
    seed: int,
    speed_mps: float,
) -> None:
    """
    Run `num_steps` full-edge update iterations.
    For each step, traverse every edge once with a slightly perturbed observed time.
    After the loop, set `data['time_seconds']` as the average predicted traversal time (seconds).
    """
    rng = random.Random(seed)
    model = AdaptiveDamageModel()

    # Initialize per-edge adaptive state once.
    initialize_edge_damage_and_time(G, speed_mps=speed_mps, rng=rng)

    edges = list(G.edges(data=True))
    for step in range(num_steps):
        for _, _, data in edges:
            a = data["adaptive"]
            # Observed time is slightly higher/lower than baseline, scaled by degradation.
            noise = rng.uniform(float(data["obs_noise_lo"]), float(data["obs_noise_hi"]))
            T_obs = a["T0"] * noise * float(data["degradation_factor"])

            model.on_traversal(data, T_obs)
            # Accumulate predicted time as the "time required to cross" the edge.
            data["time_accum_s"] += float(data["heuristic_time_s"])

    # Finalize: average predicted crossing time in seconds.
    for _, _, data in G.edges(data=True):
        data["time_seconds"] = data["time_accum_s"] / float(num_steps)


# ------------------------------
# A* routing experiments
# ------------------------------


def build_heuristics(G: nx.Graph, speed_mps: float):
    """
    Precompute node lat/lon for fast heuristics.
    """
    latlon = {n: get_node_latlon(G, n) for n in G.nodes()}

    def dist_heuristic(n1, n2):
        lat1, lon1 = latlon[n1]
        lat2, lon2 = latlon[n2]
        return haversine_m(lat1, lon1, lat2, lon2)  # meters (admissible for edge length)

    def time_heuristic(n1, n2):
        return dist_heuristic(n1, n2) / speed_mps

    return dist_heuristic, time_heuristic


def run_trips_with_astar(
    G: nx.Graph,
    num_trips: int,
    seed: int,
    speed_mps: float,
):
    rng = random.Random(seed)
    nodes = list(G.nodes())
    dist_heuristic, time_heuristic = build_heuristics(G, speed_mps=speed_mps)

    # Baseline route choice: shortest by distance (length_m).
    # IMPORTANT: We evaluate BOTH strategies on the SAME time surface (`time_seconds`)
    # so this is a fair comparison.
    baseline_dist_sum = 0.0
    baseline_time_sum = 0.0
    baseline_ok = 0

    # Health-aware route choice: shortest by predicted time_seconds (health included).
    health_dist_sum = 0.0
    health_time_sum = 0.0
    health_ok = 0

    # Optional: collect distributions for extra charts/metrics.
    baseline_trip_times: List[float] = []
    health_trip_times: List[float] = []

    for _ in range(num_trips):
        s = rng.choice(nodes)
        t = rng.choice(nodes)
        while t == s:
            t = rng.choice(nodes)

        # Baseline (distance shortest), but evaluate time on degraded/learned edge times.
        try:
            path = nx.astar_path(
                G,
                s,
                t,
                heuristic=lambda n, goal: dist_heuristic(n, goal),
                weight="length_m",
            )
            dist_m = 0.0
            time_s = 0.0
            for i in range(len(path) - 1):
                u = path[i]
                v = path[i + 1]
                edata = G[u][v]
                length_m = float(edata.get("length_m", edata.get("length", 1.0)))
                dist_m += length_m
                time_s += float(edata.get("time_seconds", length_m / speed_mps))
            baseline_dist_sum += dist_m
            baseline_time_sum += time_s
            baseline_ok += 1
            baseline_trip_times.append(time_s)
        except nx.NetworkXNoPath:
            pass

        # Health-aware (time shortest), evaluated on same edge times.
        try:
            path = nx.astar_path(
                G,
                s,
                t,
                heuristic=lambda n, goal: time_heuristic(n, goal),
                weight="time_seconds",
            )
            dist_m = 0.0
            time_s = 0.0
            for i in range(len(path) - 1):
                u = path[i]
                v = path[i + 1]
                edata = G[u][v]
                dist_m += float(edata.get("length_m", edata.get("length", 1.0)))
                time_s += float(edata.get("time_seconds", 0.0))
            health_dist_sum += dist_m
            health_time_sum += time_s
            health_ok += 1
            health_trip_times.append(time_s)
        except nx.NetworkXNoPath:
            pass

    return {
        "baseline_ok": baseline_ok,
        "health_ok": health_ok,
        "baseline_dist_sum": baseline_dist_sum,
        "baseline_time_sum": baseline_time_sum,
        "health_dist_sum": health_dist_sum,
        "health_time_sum": health_time_sum,
        "baseline_trip_times": baseline_trip_times,
        "health_trip_times": health_trip_times,
    }


def plot_bar_comparison(
    baseline_dist_sum: float,
    health_dist_sum: float,
    baseline_time_sum: float,
    health_time_sum: float,
    baseline_ok: int,
    health_ok: int,
    title_prefix: str = "",
) -> None:
    baseline_dist_avg = baseline_dist_sum / max(1, baseline_ok)
    health_dist_avg = health_dist_sum / max(1, health_ok)
    baseline_time_avg = baseline_time_sum / max(1, baseline_ok)
    health_time_avg = health_time_sum / max(1, health_ok)

    labels = ["Baseline (distance)", "Health-aware (time)"]

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle(f"{title_prefix}A* Trips Comparison")

    # 1) distance summation
    axes[0, 0].bar(labels, [baseline_dist_sum, health_dist_sum], color=["#4c78a8", "#54a24b"])
    axes[0, 0].set_title("1) Total Distance (sum) [m]")
    axes[0, 0].tick_params(axis="x", rotation=20)

    # 2) time summation
    axes[0, 1].bar(labels, [baseline_time_sum, health_time_sum], color=["#4c78a8", "#54a24b"])
    axes[0, 1].set_title("2) Total Time (sum) [s]")
    axes[0, 1].tick_params(axis="x", rotation=20)

    # 3) distance average
    axes[1, 0].bar(labels, [baseline_dist_avg, health_dist_avg], color=["#4c78a8", "#54a24b"])
    axes[1, 0].set_title("3) Average Distance [m]")
    axes[1, 0].tick_params(axis="x", rotation=20)

    # 4) time average
    axes[1, 1].bar(labels, [baseline_time_avg, health_time_avg], color=["#4c78a8", "#54a24b"])
    axes[1, 1].set_title("4) Average Time [s]")
    axes[1, 1].tick_params(axis="x", rotation=20)

    plt.tight_layout()
    plt.show()


# ------------------------------
# Main
# ------------------------------


def main() -> None:
    # ---- choose the city/center ----
    city_name = "coimbatore"
    dist_m = 2000  # OSM radius in meters
    network_type = "drive"

    # ---- simulation parameters ----
    speed_kmh = 40.0  # baseline average speed for converting length -> seconds
    speed_mps = (speed_kmh * 1000.0) / 3600.0
    edge_steps = 999
    num_trips = 9999

    seed = 42
    random.seed(seed)
    np.random.seed(seed)

    if city_name.lower() not in MAJOR_CITIES:
        raise ValueError(f"Unknown city '{city_name}'. Choose from: {sorted(MAJOR_CITIES.keys())}")

    center = MAJOR_CITIES[city_name.lower()]
    print(f"Downloading road graph for {city_name} around (lat={center.lat}, lon={center.lon}) ...")
    G = build_osm_undirected_graph(center=center, dist_m=dist_m, network_type=network_type)
    print(f"Graph loaded: nodes={G.number_of_nodes()} edges={G.number_of_edges()}")

    # ---- run adaptive traversal model to derive time_seconds per edge ----
    print(f"Running edge traversal simulation: {edge_steps} steps across all edges ...")
    run_edge_traversal_simulation(G, num_steps=edge_steps, seed=seed, speed_mps=speed_mps)

    # Sanity: confirm time_seconds exists
    any_edge = next(iter(G.edges(data=True)))[2] if G.number_of_edges() > 0 else {}
    if "time_seconds" not in any_edge:
        raise RuntimeError("time_seconds missing after simulation; something went wrong.")

    # ---- run A* trips baseline vs health-aware ----
    print(f"Running {num_trips} A* trips (baseline vs health-aware) ...")
    results = run_trips_with_astar(G, num_trips=num_trips, seed=seed + 1, speed_mps=speed_mps)

    print("\n=== RESULTS ===")
    print(f"Baseline trips successful: {results['baseline_ok']} / {num_trips}")
    print(f"Health-aware trips successful: {results['health_ok']} / {num_trips}")
    print(f"Baseline total distance (m): {results['baseline_dist_sum']:.2f}")
    print(f"Health total distance (m): {results['health_dist_sum']:.2f}")
    print(f"Baseline total time (s): {results['baseline_time_sum']:.2f}")
    print(f"Health total time (s): {results['health_time_sum']:.2f}")

    plot_bar_comparison(
        baseline_dist_sum=results["baseline_dist_sum"],
        health_dist_sum=results["health_dist_sum"],
        baseline_time_sum=results["baseline_time_sum"],
        health_time_sum=results["health_time_sum"],
        baseline_ok=results["baseline_ok"],
        health_ok=results["health_ok"],
        title_prefix=f"{city_name} | dist={dist_m}m | speed={speed_kmh}km/h | ",
    )

    # Optional extra stats: percent improvement in average time.
    if results["baseline_ok"] > 0 and results["health_ok"] > 0:
        baseline_avg_time = results["baseline_time_sum"] / results["baseline_ok"]
        health_avg_time = results["health_time_sum"] / results["health_ok"]
        pct = (baseline_avg_time - health_avg_time) / max(1e-9, baseline_avg_time) * 100.0
        print(f"\nAverage time improvement (health - baseline): {pct:.2f}% faster (positive means faster).")


if __name__ == "__main__":
    main()

