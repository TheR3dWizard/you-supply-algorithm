# gui_visualizer_enhanced.py
import sys
import math
import time
import json
import queue
import threading
from datetime import datetime
import requests
import networkx as nx

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QHBoxLayout,
    QFrame, QPushButton, QLineEdit, QCheckBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QSlider, QSizePolicy, QToolBar, QAction
)
from PyQt5.QtCore import QTimer, Qt
import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure

# websocket-client
import websocket

BOOTSTRAP_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws_snapshot"

# ---------- WS listener thread (pushes snapshots into a queue) ----------
class SnapshotListener(threading.Thread):
    def __init__(self, ws_url, out_queue):
        super().__init__(daemon=True)
        self.ws_url = ws_url
        self.out_queue = out_queue
        self.ws_app = None
        self.running = True

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
        except Exception:
            return
        # keep only latest snapshot
        try:
            while True:
                self.out_queue.get_nowait()
        except queue.Empty:
            pass
        self.out_queue.put(data)

    def on_error(self, ws, error):
        print("WS error:", error)

    def on_close(self, ws, code, reason):
        print("WS closed:", code, reason)

    def on_open(self, ws):
        # optional handshake
        try:
            ws.send("gui_connected")
        except Exception:
            pass

    def run(self):
        while self.running:
            try:
                self.ws_app = websocket.WebSocketApp(
                    self.ws_url,
                    on_message=self.on_message,
                    on_error=self.on_error,
                    on_close=self.on_close,
                    on_open=self.on_open
                )
                self.ws_app.run_forever(ping_interval=20, ping_timeout=10)
            except Exception as e:
                print("WS run error:", e)
            time.sleep(1)

    def stop(self):
        self.running = False
        try:
            if self.ws_app:
                self.ws_app.close()
        except Exception:
            pass

# ---------- Matplotlib canvas ----------
class GraphCanvas(FigureCanvasQTAgg):
    def __init__(self, on_node_click):
        self.fig = Figure(figsize=(6,6), tight_layout=True)
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)

        self.on_node_click = on_node_click
        self.graph = nx.Graph()
        self.pos = {}
        self.node_meta = {}
        self.selected = None
        self.show_edge_labels = True

        # connect click
        self.mpl_connect("button_press_event", self._on_click)

    def update_graph(self, nodes, edges, selected=None):
        """
        nodes: dict node_id -> dict {lat, lon, confidence, last_seen, gossip_ts, seq, ...}
        edges: list of dicts with keys 'from','to','distance_m' or 'distance'
        """
        self.selected = selected
        self.ax.clear()
        self.graph.clear()
        self.node_meta = {}

        # Add nodes
        for nid, data in nodes.items():
            self.graph.add_node(nid)
            # store meta
            self.node_meta[nid] = data or {}
            # set position if lat/lon present
            lat = data.get("lat")
            lon = data.get("lon")
            if lat is not None and lon is not None:
                # using lon,lat as x,y
                self.pos[nid] = (float(lon), float(lat))
            else:
                # leave pos for spring_layout fallback
                if nid not in self.pos:
                    self.pos[nid] = (len(self.pos), 0.0)

        # Add edges
        for e in edges:
            a = e.get("from") or e.get("u") or e.get("src")
            b = e.get("to") or e.get("v") or e.get("dst")
            if a in self.graph and b in self.graph:
                dist = e.get("distance_m", e.get("distance", 0.0))
                self.graph.add_edge(a, b, distance=dist)

        # if geocoords are not present or only <2, compute spring layout
        coords_have_good = sum(1 for v in self.pos.values() if isinstance(v, tuple)) >= 2 and len(self.pos) >= 2
        try:
            if coords_have_good and len(self.pos) == self.graph.number_of_nodes():
                layout = self.pos
            else:
                layout = nx.spring_layout(self.graph, pos=self.pos, seed=42)
                # merge into self.pos for next runs
                self.pos.update(layout)
        except Exception:
            layout = nx.spring_layout(self.graph, seed=42)
            self.pos.update(layout)

        # Draw nodes with color/size by confidence
        node_sizes = []
        node_colors = []
        edge_colors = []
        labels = {}
        for nid in self.graph.nodes():
            meta = self.node_meta.get(nid, {})
            conf = float(meta.get("confidence") or 0.0)
            # size scales from 200..1200
            size = 200 + conf * 1200
            node_sizes.append(size)
            # color selection
            if conf >= 0.75:
                color = "#2ECC71"
            elif conf >= 0.4:
                color = "#F4D03F"
            else:
                color = "#E74C3C"
            node_colors.append(color)
            labels[nid] = nid

        # draw nodes; highlight selected by edgecolor
        edgecolors = []
        linewidths = []
        for nid in self.graph.nodes():
            if nid == self.selected:
                edgecolors.append("#000000")
                linewidths.append(2.5)
            else:
                edgecolors.append("#333333")
                linewidths.append(0.8)

        nx.draw_networkx_nodes(self.graph, layout, ax=self.ax,
                               node_size=node_sizes, node_color=node_colors,
                               edgecolors=edgecolors, linewidths=linewidths)

        nx.draw_networkx_labels(self.graph, layout, labels=labels, font_size=8, ax=self.ax)

        # draw edges
        nx.draw_networkx_edges(self.graph, layout, ax=self.ax)

        # edge labels (distance)
        if self.show_edge_labels:
            edge_labels = {}
            for u, v, d in self.graph.edges(data=True):
                dist = d.get("distance", d.get("distance_m", 0.0))
                try:
                    lbl = f"{float(dist):.1f} m"
                except Exception:
                    lbl = str(dist)
                edge_labels[(u, v)] = lbl
            nx.draw_networkx_edge_labels(self.graph, layout, edge_labels=edge_labels, font_size=7, ax=self.ax)

        # title with counts
        self.ax.set_title(f"Distributed World — nodes: {self.graph.number_of_nodes()}  edges: {self.graph.number_of_edges()}")
        self.ax.axis("off")
        self.draw()

    def _on_click(self, event):
        if event.xdata is None or event.ydata is None:
            return
        # find nearest node by straight Euclidean distance in layout coords
        min_d = float("inf")
        sel = None
        for nid, (x, y) in self.pos.items():
            try:
                d = math.hypot(event.xdata - x, event.ydata - y)
            except Exception:
                continue
            if d < min_d:
                min_d = d
                sel = nid
        # threshold depends on coordinate scale; be forgiving
        if sel is not None:
            self.on_node_click(sel)

# ---------- Inspector & Node List ----------
def human_time(ts):
    if not ts:
        return "-"
    try:
        return datetime.fromtimestamp(ts).strftime("%H:%M:%S")
    except Exception:
        return str(ts)

class Inspector(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.title = QLabel("<b>Node Inspector</b>")
        self.layout.addWidget(self.title)
        self.fields = {}
        for k in ["node_id", "lat", "lon", "seq", "confidence", "last_seen", "gossip_ts"]:
            lbl = QLabel(f"{k}: -")
            lbl.setStyleSheet("font-size:12px;")
            self.fields[k] = lbl
            self.layout.addWidget(lbl)
        self.center_btn = QPushButton("Center on Node")
        self.layout.addWidget(self.center_btn)
        self.layout.addStretch()

    def update(self, nid, data):
        self.fields["node_id"].setText(f"node_id: {nid}")
        self.fields["lat"].setText(f"lat: {data.get('lat', '-')}")
        self.fields["lon"].setText(f"lon: {data.get('lon', '-')}")
        self.fields["seq"].setText(f"seq: {data.get('seq', '-')}")
        self.fields["confidence"].setText(f"confidence: {round(float(data.get('confidence',0.0)),2)}")
        self.fields["last_seen"].setText(f"last_seen: {human_time(data.get('last_seen'))}")
        self.fields["gossip_ts"].setText(f"gossip_ts: {human_time(data.get('gossip_ts'))}")

class NodeTable(QTableWidget):
    def __init__(self):
        super().__init__(0, 5)
        self.setHorizontalHeaderLabels(["Node ID", "Confidence", "Last Seen", "Gossip TS", "Lat/Lon"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(self.SelectRows)
        self.setEditTriggers(self.NoEditTriggers)

    def update_nodes(self, nodes_dict):
        self.setRowCount(0)
        items = []
        for nid, d in nodes_dict.items():
            conf = round(float(d.get("confidence", 0.0)),2) if d else 0.0
            last_seen = human_time(d.get("last_seen")) if d else "-"
            gossip_ts = human_time(d.get("gossip_ts")) if d else "-"
            latlon = f"{d.get('lat','-')},{d.get('lon','-')}"
            items.append((nid, conf, last_seen, gossip_ts, latlon))
        # sort by confidence desc
        items.sort(key=lambda x: -x[1])
        for row, it in enumerate(items):
            self.insertRow(row)
            self.setItem(row, 0, QTableWidgetItem(str(it[0])))
            self.setItem(row, 1, QTableWidgetItem(str(it[1])))
            self.setItem(row, 2, QTableWidgetItem(it[2]))
            self.setItem(row, 3, QTableWidgetItem(it[3]))
            self.setItem(row, 4, QTableWidgetItem(it[4]))

# ---------- Main Window ----------
class WorldVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Decentralized World Visualizer — Enhanced")
        self.resize(1200, 800)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout()
        central.setLayout(main_layout)

        # Left: canvas + toolbar
        left_frame = QVBoxLayout()
        main_layout.addLayout(left_frame, 3)

        self.canvas = GraphCanvas(self.on_node_clicked)
        left_frame.addWidget(self.canvas)

        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        left_frame.addWidget(self.toolbar)

        # Top controls (search and toggles)
        top_controls = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search node id...")
        self.search_btn = QPushButton("Find")
        self.toggle_edges_cb = QCheckBox("Show edge labels")
        self.toggle_edges_cb.setChecked(True)
        self.follow_cb = QCheckBox("Follow selection")
        self.follow_cb.setChecked(False)
        self.refresh_btn = QPushButton("Refresh now")

        top_controls.addWidget(self.search_input)
        top_controls.addWidget(self.search_btn)
        top_controls.addWidget(self.toggle_edges_cb)
        top_controls.addWidget(self.follow_cb)
        top_controls.addWidget(self.refresh_btn)
        left_frame.addLayout(top_controls)

        # Right: inspector + node list
        right_frame = QVBoxLayout()
        main_layout.addLayout(right_frame, 1)

        self.inspector = Inspector()
        right_frame.addWidget(self.inspector)

        # Node actions
        self.center_btn = self.inspector.center_btn
        right_frame.addWidget(QLabel("<b>Nodes</b>"))
        self.node_table = NodeTable()
        right_frame.addWidget(self.node_table)

        # confidence slider to filter low confidence nodes
        right_frame.addWidget(QLabel("Min confidence filter"))
        self.conf_slider = QSlider(Qt.Horizontal)
        self.conf_slider.setMinimum(0)
        self.conf_slider.setMaximum(100)
        self.conf_slider.setValue(0)
        right_frame.addWidget(self.conf_slider)

        # status bar label
        self.status_label = QLabel("No snapshot yet")
        right_frame.addWidget(self.status_label)

        # internal state
        self.snap_q = queue.Queue(maxsize=2)
        self.listener = SnapshotListener(WS_URL, self.snap_q)
        self.listener.start()

        self.last_snapshot = None
        self.selected_node = None
        self.follow_selection = False

        # connections
        self.search_btn.clicked.connect(self.on_search)
        self.toggle_edges_cb.stateChanged.connect(self.on_toggle_edges)
        self.refresh_btn.clicked.connect(self.force_refresh)
        self.node_table.cellClicked.connect(self.on_table_click)
        self.center_btn.clicked.connect(self.center_on_selected)
        self.conf_slider.valueChanged.connect(self.on_conf_filter_change)
        self.follow_cb.stateChanged.connect(self.on_follow_changed)

        # timer to apply snapshots (200ms)
        self.timer = QTimer()
        self.timer.timeout.connect(self._refresh)
        self.timer.start(200)

    # ---------- UI callbacks ----------
    def on_node_clicked(self, node_id):
        # selection from canvas
        self.select_node(node_id)

    def on_table_click(self, r, c):
        item = self.node_table.item(r, 0)
        if item:
            self.select_node(item.text())

    def select_node(self, node_id):
        self.selected_node = node_id
        # update inspector with last_snapshot nodes map
        nodes = (self.last_snapshot or {}).get("nodes", {})
        node_data = nodes.get(node_id, {})
        self.inspector.update(node_id, node_data or {})
        # redraw with highlight
        self.canvas.update_graph(nodes, (self.last_snapshot or {}).get("edges", []), selected=node_id)
        if self.follow_selection:
            self.center_on_selected()

    def center_on_selected(self):
        if not self.selected_node:
            return
        pos = self.canvas.pos.get(self.selected_node)
        if not pos:
            return
        x, y = pos
        # set axis limits to center around node
        span = 0.5  # degree span; may need adjusting for global coords
        self.canvas.ax.set_xlim(x - span, x + span)
        self.canvas.ax.set_ylim(y - span, y + span)
        self.canvas.draw()

    def on_search(self):
        q = self.search_input.text().strip()
        if not q or not self.last_snapshot:
            return
        nodes = self.last_snapshot.get("nodes", {})
        if q in nodes:
            self.select_node(q)

    def on_toggle_edges(self, _):
        self.canvas.show_edge_labels = self.toggle_edges_cb.isChecked()
        # redraw
        if self.last_snapshot:
            self.canvas.update_graph(self.last_snapshot.get("nodes", {}), self.last_snapshot.get("edges", []), selected=self.selected_node)

    def on_conf_filter_change(self, v):
        if not self.last_snapshot:
            return

        min_conf = v / 100.0

        nodes = self.last_snapshot.get("nodes", {})
        filtered_nodes = {
            nid: d for nid, d in nodes.items()
            if float(d.get("confidence", 0.0)) >= min_conf
        }

        edges = [
            e for e in self.last_snapshot.get("edges", [])
            if e.get("from") in filtered_nodes and e.get("to") in filtered_nodes
        ]

        self.canvas.update_graph(
            filtered_nodes,
            edges,
            selected=self.selected_node
        )
    def on_follow_changed(self, state):
        self.follow_selection = bool(state)

    def force_refresh(self):
        try:
            r = requests.get(f"{BOOTSTRAP_URL}/latest_snapshot", timeout=1.0)
            snap = r.json()
            try:
                while True:
                    self.snap_q.get_nowait()
            except queue.Empty:
                pass
            self.snap_q.put(snap)
        except Exception as e:
            print("refresh failed:", e)

    # ---------- main refresh loop ----------
    def _refresh(self):
        # take WS snapshot if available
        try:
            snap = self.snap_q.get_nowait()
            self.last_snapshot = snap
            self.apply_snapshot(snap)
            return
        except queue.Empty:
            pass

        # fallback occasional polling if no WS data yet
        if self.last_snapshot is None:
            try:
                r = requests.get(f"{BOOTSTRAP_URL}/latest_snapshot", timeout=1.0)
                snap = r.json()
                self.last_snapshot = snap
                self.apply_snapshot(snap)
            except Exception:
                pass

    def apply_snapshot(self, snapshot):
        nodes = snapshot.get("nodes", {}) or {}
        edges = snapshot.get("edges", []) or []
        ts = snapshot.get("timestamp")
        if ts:
            tstr = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        else:
            tstr = "N/A"
        self.status_label.setText(f"Snapshot by {snapshot.get('publisher')} @ {tstr}  nodes:{len(nodes)} edges:{len(edges)}")

        # update node table
        self.node_table.update_nodes(nodes)

        # apply filter min confidence
        min_conf = self.conf_slider.value() / 100.0
        filtered_nodes = {nid: d for nid, d in nodes.items() if float(d.get("confidence", 0.0)) >= min_conf}

        # redraw canvas (show filtered nodes; keep edges as provided but drawing will ignore missing nodes)
        self.canvas.update_graph(filtered_nodes, edges, selected=self.selected_node)

        # if a node is selected but not present now, clear inspector
        if self.selected_node and self.selected_node not in nodes:
            self.selected_node = None
            # clear inspector
            self.inspector.update("-", {})

# ---------- run ----------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = WorldVisualizer()
    win.show()
    sys.exit(app.exec_())