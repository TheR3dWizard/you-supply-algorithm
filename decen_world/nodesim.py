#!/usr/bin/env python3
"""
nodesim.py — spawn many simulated nodes that act like real nodes (register, gossip, merge, prune)

Usage:
    python nodesim.py 80 10010
This starts 80 simulated nodes with ports 10010 .. 10010+79
"""

import sys
import threading
import time
import json
import random
import socket
import requests

BOOTSTRAP_URL = "http://localhost:8000"

# tuning (keep aligned with your node.py)
GOSSIP_INTERVAL = 0.5
PRUNE_INTERVAL = 0.5
PEER_REFRESH_INTERVAL = 5.0
DEAD_NODE_TIMEOUT = 15.0
SNAPSHOT_MIN_INTERVAL = 1.0

CONFIDENCE_INC = 0.05
CONFIDENCE_DIRECT_INC = 0.12
CONFIDENCE_DEC = 0.02

SOCKET_TIMEOUT = 0.6

# random coordinate bbox (optional) - set to your city/region if desired
DEFAULT_BBOX = None  # e.g. (12.8,13.1,77.4,77.8) for Bangalore


def rand_lat_lon(bbox=None):
    if bbox:
        min_lat, max_lat, min_lon, max_lon = bbox
        return round(random.uniform(min_lat, max_lat), 6), round(random.uniform(min_lon, max_lon), 6)
    return round(random.uniform(-90.0, 90.0), 6), round(random.uniform(-180.0, 180.0), 6)


class SimNode:
    def __init__(self, node_id, host, port, bbox=None):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.lat, self.lon = rand_lat_lon(bbox)
        self.peers = []
        self.world = {}        # node_id -> record
        self.tombstones = {}
        self.seq = 0
        self.last_published = 0.0
        self.lock = threading.Lock()
        self._stop = False

    def local_state(self):
        now = time.time()
        return {
            "node_id": self.node_id,
            "lat": self.lat,
            "lon": self.lon,
            "seq": self.seq,
            "confidence": 1.0,
            "last_seen": now,
            "heard_about_ts": now,
            "ts": now,
        }

    def register(self):
        try:
            r = requests.post(
                f"{BOOTSTRAP_URL}/register",
                json={"node_id": self.node_id, "host": self.host, "port": self.port, "lat": self.lat, "lon": self.lon},
                timeout=2,
            )
            peers = r.json().get("peers", [])
            self.peers = [p for p in peers if p.get("node_id") != self.node_id]
        except Exception:
            # ignore; will retry in periodic refresh
            pass

    def publish_snapshot_if_needed(self, force=False):
        now = time.time()
        if not force and (now - self.last_published < SNAPSHOT_MIN_INTERVAL):
            return
        with self.lock:
            snapshot = {
                "publisher": self.node_id,
                "nodes": dict(self.world),
                "edges": [],
                "timestamp": now,
            }
        try:
            requests.post(f"{BOOTSTRAP_URL}/snapshot", json=snapshot, timeout=1)
            self.last_published = now
        except Exception:
            pass

    def merge_world(self, incoming_world):
        if not isinstance(incoming_world, dict):
            return
        now = time.time()
        changed = False
        with self.lock:
            for nid, inc in incoming_world.items():
                if not isinstance(inc, dict):
                    continue
                if nid in self.tombstones:
                    if now - self.tombstones[nid] < DEAD_NODE_TIMEOUT:
                        continue
                    else:
                        del self.tombstones[nid]
                inc_ts = inc.get("ts", 0.0)
                if inc_ts < now - DEAD_NODE_TIMEOUT:
                    continue
                local = self.world.get(nid)
                # heard_about_ts: mark mention even if we don't merge metadata
                if local is not None:
                    local["heard_about_ts"] = now
                if local is None:
                    entry = {
                        "node_id": nid,
                        "lat": inc.get("lat"),
                        "lon": inc.get("lon"),
                        "seq": inc.get("seq", 0),
                        "confidence": min(1.0, float(inc.get("confidence", 0.0)) + CONFIDENCE_INC),
                        "last_seen": 0.0,
                        "heard_about_ts": now,
                        "ts": inc_ts,
                    }
                    self.world[nid] = entry
                    changed = True
                    continue
                inc_seq = inc.get("seq", 0)
                if inc_seq > local.get("seq", 0):
                    local["seq"] = inc_seq
                    local["lat"] = inc.get("lat", local.get("lat"))
                    local["lon"] = inc.get("lon", local.get("lon"))
                    local["confidence"] = min(1.0, local.get("confidence", 0.0) + CONFIDENCE_INC)
                    local["ts"] = inc_ts
                    changed = True
                    continue
                if inc_seq == local.get("seq", 0):
                    local["confidence"] = min(1.0, local.get("confidence", 0.0) + CONFIDENCE_INC)
                    changed = True
        if changed:
            # publish snapshot occasionally to help GUI (not required for gossip)
            self.publish_snapshot_if_needed()

    def start_server(self):
        def server_loop():
            s = socket.socket()
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((self.host, self.port))
            except Exception as e:
                print(f"[{self.node_id}] failed to bind {self.host}:{self.port} -> {e}")
                return
            s.listen()
            while not self._stop:
                try:
                    conn, _ = s.accept()
                    try:
                        data = conn.recv(65536)
                        if not data:
                            continue
                        payload = json.loads(data.decode())
                        sender = payload.get("from")
                        incoming_world = payload.get("world", {})
                        now = time.time()
                        if sender:
                            with self.lock:
                                if sender in self.tombstones:
                                    del self.tombstones[sender]
                                rec = self.world.get(sender)
                                if rec is None:
                                    rec = {
                                        "node_id": sender,
                                        "lat": incoming_world.get(sender, {}).get("lat"),
                                        "lon": incoming_world.get(sender, {}).get("lon"),
                                        "seq": incoming_world.get(sender, {}).get("seq", 0),
                                        "confidence": 0.0,
                                        "last_seen": now,
                                        "heard_about_ts": now,
                                        "ts": now,
                                    }
                                    self.world[sender] = rec
                                else:
                                    rec["last_seen"] = now
                                    rec["heard_about_ts"] = now
                                    rec["confidence"] = min(1.0, rec.get("confidence", 0.0) + CONFIDENCE_DIRECT_INC)
                                    rec["ts"] = now
                        # merge indirect info
                        self.merge_world(incoming_world)
                    except Exception:
                        pass
                    finally:
                        try:
                            conn.close()
                        except Exception:
                            pass
                except Exception:
                    time.sleep(0.01)
            try:
                s.close()
            except Exception:
                pass

        t = threading.Thread(target=server_loop, daemon=True)
        t.start()

    def gossip_loop(self):
        while not self._stop:
            time.sleep(GOSSIP_INTERVAL)
            now = time.time()
            with self.lock:
                self.seq += 1
                self.world[self.node_id] = self.local_state()
                # decay confidence only if not heard recently
                for nid, rec in list(self.world.items()):
                    if nid == self.node_id:
                        continue
                    heard_ts = rec.get("heard_about_ts", 0.0)
                    if now - heard_ts > GOSSIP_INTERVAL * 2:
                        rec["confidence"] = max(0.0, rec.get("confidence", 0.0) - CONFIDENCE_DEC)
                payload = {"from": self.node_id, "world": dict(self.world)}
            # best-effort gossip to peers
            for peer in list(self.peers):
                try:
                    sock = socket.socket()
                    sock.settimeout(SOCKET_TIMEOUT)
                    sock.connect((peer["host"], peer["port"]))
                    sock.send(json.dumps(payload).encode())
                    sock.close()
                except Exception:
                    pass
            # occasionally publish a snapshot to bootstrap for GUI convenience
            if random.random() < 0.05:
                self.publish_snapshot_if_needed()

    def prune_loop(self):
        while not self._stop:
            time.sleep(PRUNE_INTERVAL)
            now = time.time()
            removed = []
            with self.lock:
                for nid, rec in list(self.world.items()):
                    if nid == self.node_id:
                        continue
                    last_seen = rec.get("last_seen", 0.0)
                    heard_ts = rec.get("heard_about_ts", 0.0)
                    if (now - last_seen > DEAD_NODE_TIMEOUT) and (now - heard_ts > DEAD_NODE_TIMEOUT):
                        removed.append(nid)
                        del self.world[nid]
                        self.tombstones[nid] = now
            if removed:
                # very occasional snapshot push
                try:
                    self.publish_snapshot_if_needed(force=True)
                except Exception:
                    pass

    def refresh_peers_loop(self):
        while not self._stop:
            time.sleep(PEER_REFRESH_INTERVAL)
            try:
                r = requests.post(f"{BOOTSTRAP_URL}/register", json={
                    "node_id": self.node_id, "host": self.host, "port": self.port, "lat": self.lat, "lon": self.lon
                }, timeout=2)
                peers = r.json().get("peers", [])
                self.peers = [p for p in peers if p.get("node_id") != self.node_id]
            except Exception:
                pass

    def start(self):
        # initial register
        self.register()
        # start server + loops
        self.start_server()
        threading.Thread(target=self.gossip_loop, daemon=True).start()
        threading.Thread(target=self.prune_loop, daemon=True).start()
        threading.Thread(target=self.refresh_peers_loop, daemon=True).start()

    def stop(self):
        self._stop = True


def spawn_sim(count, start_port=10010, bbox=None):
    host = "127.0.0.1"
    nodes = []
    for i in range(count):
        nid = f"sim{str(i).zfill(3)}"
        port = start_port + i
        node = SimNode(nid, host, port, bbox=bbox)
        node.start()
        nodes.append(node)
        # small stagger to avoid mass register storms
        time.sleep(0.01)
    return nodes


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python nodesim.py <count> [start_port] [min_lat max_lat min_lon max_lon]")
        sys.exit(1)

    count = int(sys.argv[1])
    start_port = int(sys.argv[2]) if len(sys.argv) >= 3 else 10010
    bbox = None
    if len(sys.argv) == 7:
        try:
            min_lat = float(sys.argv[3]); max_lat = float(sys.argv[4])
            min_lon = float(sys.argv[5]); max_lon = float(sys.argv[6])
            bbox = (min_lat, max_lat, min_lon, max_lon)
        except Exception:
            bbox = None

    print(f"Starting simulator: {count} nodes from port {start_port}")
    sims = spawn_sim(count, start_port=start_port, bbox=bbox)

    try:
        while True:
            alive = sum(1 for s in sims if not s._stop)
            print(f"[nodesim] alive sims: {alive} world-snapshot-sample: ", end="")
            # print a tiny sample of one sim's world to show progress
            if sims:
                with sims[0].lock:
                    sample = list(sims[0].world.keys())[:10]
                print(sample)
            else:
                print("none")
            time.sleep(2)
    except KeyboardInterrupt:
        print("Stopping simulator...")
        for s in sims:
            s.stop()
        time.sleep(0.5)
        print("Stopped.")