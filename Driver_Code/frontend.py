import sys
import os
import streamlit as st
import matplotlib.pyplot as plt
from contextlib import contextmanager

# -------------------------------------------------
# Fix Python path (because frontend.py is in Driver_Code)
# -------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

# -------------------------------------------------
# Imports from your project
# -------------------------------------------------
from Simulation_Frame.simulation import Simulation

from Solutions.DirectMatching import DirectMatching
from Solutions.yousupplyalgo import YouSupplyAlgo
from Solutions.optimizeddirectmatching import OptimizedDirectMatching


# -------------------------------------------------
# Utility: render matplotlib safely in Streamlit
# -------------------------------------------------
def render_plot():
    st.pyplot(plt.gcf())
    plt.close()


@contextmanager
def suppress_matplotlib_show():
    original_show = plt.show
    plt.show = lambda *args, **kwargs: None
    try:
        yield
    finally:
        plt.show = original_show

def render_backend_plot(plot_func, size=(5, 5)):
    with suppress_matplotlib_show():
        fig = plt.figure(figsize=size, dpi=100)
        plot_func()
        fig.set_size_inches(*size, forward=True)
        st.pyplot(fig, use_container_width=False)
        plt.close(fig)


# -------------------------------------------------
# Streamlit UI
# -------------------------------------------------
st.set_page_config(page_title="YouSupply Simulation", layout="wide")
st.title("Decentralized Supply Chain Simulation")

st.sidebar.header("Simulation Parameters")

area = st.sidebar.number_input("Area", min_value=100, value=10000, step=100)
size = st.sidebar.number_input("Number of Nodes", min_value=10, value=1000, step=10)
node_range = st.sidebar.number_input("Node Range", min_value=1, value=20, step=1)
geo_size = st.sidebar.number_input("Geo Size (YouSupply)", min_value=10, value=50, step=5)

items = st.sidebar.text_input(
    "Items (comma separated)",
    value="1,2,3,4,5,6,7,8,9,10"
).split(",")

solution_name = st.sidebar.selectbox(
    "Solution Algorithm",
    [
        "Direct Matching",
        "Optimized Direct Matching",
        "YouSupply"
    ]
)

run_button = st.sidebar.button("Run Simulation")


# -------------------------------------------------
# Main execution
# -------------------------------------------------
if run_button:
    st.info("Running simulation...")

    # -------------------------
    # Initialize simulation
    # -------------------------
    sim = Simulation(
        area=area,
        size=size,
        range=node_range,
        items=[i.strip() for i in items]
    )
    sim.populate_nodes()

    # -------------------------
    # Select solution
    # -------------------------
    if solution_name == "Direct Matching":
        sol = DirectMatching(sim)
        sol.solve()
    elif solution_name == "Optimized Direct Matching":
        sol = OptimizedDirectMatching(sim, name="Optimized Direct Matching")
        sol.solve()
    else:
        sol = YouSupplyAlgo(sim, geo_size=geo_size)
        sol.solve(show=True)

    # -------------------------
    # Solve
    # -------------------------


    # =================================================
    # OUTPUTS (STRICT ORDER AS REQUESTED)
    # =================================================

    # 1. Entire simulation
    st.subheader("Entire Simulation")

    render_backend_plot(sim.plotnodes, size=(5, 5))

    # 2. Clusters (YouSupply only)
    if solution_name == "YouSupply" and hasattr(sol, "plotclusters"):
        st.subheader("Geographical Clusters")

        render_backend_plot(sol.plotclusters, size=(5, 5))


    # 3. All paths together
    st.subheader("All Paths (Combined)")

    render_backend_plot(sol.plotallpaths, size=(5, 5))

    # 4. Metrics (structured, not printed)
    st.subheader("Metrics")
    sol.get_all_metrics()
    metrics = sol.metrics

    col1, col2, col3 = st.columns(3)

    col1.metric("Algorithm", metrics["algorithm_name"])
    col2.metric("Total Distance", f"{metrics['total_distance']:.2f}")
    col3.metric(
        "Satisfaction %",
        f"{metrics['satisfaction_percentage']:.2f}%"
    )

    # 5. Individual paths (small figures)
    st.subheader("Individual Paths")

    if solution_name == "YouSupply" and hasattr(sol, "paths"):
        for idx, path in enumerate(sol.paths):
            st.markdown(f"**Path {idx + 1}**")

            render_backend_plot(path.plotpath)

