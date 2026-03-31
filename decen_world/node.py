#!/usr/bin/env python3
"""
node.py — stable decentralized gossip node

Core semantics:
- last_seen        : direct contact only
- heard_about_ts   : ANY mention in gossip (indirect liveness)
- confidence       : linear belief score (≠ liveness)
- prune            : only if BOTH direct & indirect are stale
- tombstones       : prevent resurrection except by direct contact
"""

import requests
import sys
import socket
import threading
import time
import json
import random

BOOTSTRAP_URL = "http://localhost:8000"

# ---------------- CONFIG ----------------
GOSSIP_INTERVAL = 0.5
PRUNE_INTERVAL = 0.5
PEER_REFRESH_INTERVAL = 5.0
DEAD_NODE_TIMEOUT = 15.0

SNAPSHOT_MIN_INTERVAL = 0.3

CONFIDENCE_INC = 0.05
CONFIDENCE_DIRECT_INC = 0.12
CONFIDENCE_DEC = 0.02

SOCKET_TIMEOUT = 1.0
# ---------------------------------------


def random_lat_lon():
    return (
        round(random.uniform(-90.0, 90.0), 6),
        round(random.uniform(-180.0, 180.0), 6),
    )


class Node:
    def __init__(self, node_id, host, port):
        self.node_id = node_id
        self.host = host
        self.port = port

        self.lat, self.lon = random_lat_lon()

        self.peers = []
        self.world = {}        # node_id -> record
        self.tombstones = {}   # node_id -> prune time

        self.seq = 0
        self.last_published = 0.0
        self.lock = threading.Lock()

    # ---------------- LOCAL STATE ----------------
    def local_state(self):
        now = time.time()
        return {
            "node_id": self.node_id,
            "lat": self.lat,
            "lon": self.lon,
            "seq": self.seq,
            "confidence": 1.0,
            "last_seen": now,          # direct
            "heard_about_ts": now,     # indirect (self)
            "ts": now,
        }

    # ---------------- SNAPSHOT ----------------
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

    # ---------------- MERGE GOSSIP ----------------
    def merge_world(self, incoming_world):
        if not isinstance(incoming_world, dict):
            return

        now = time.time()
        changed = False

        with self.lock:
            for nid, inc in incoming_world.items():
                if not isinstance(inc, dict):
                    continue

                # tombstone protection
                if nid in self.tombstones:
                    if now - self.tombstones[nid] < DEAD_NODE_TIMEOUT:
                        continue
                    else:
                        del self.tombstones[nid]

                inc_ts = inc.get("ts", 0.0)
                if inc_ts < now - DEAD_NODE_TIMEOUT:
                    continue

                local = self.world.get(nid)

                # ---------------- HEARD ABOUT (CRITICAL FIX) ----------------
                if local is not None:
                    local["heard_about_ts"] = now

                if local is None:
                    entry = {
                        "node_id": nid,
                        "lat": inc.get("lat"),
                        "lon": inc.get("lon"),
                        "seq": inc.get("seq", 0),
                        "confidence": min(1.0, inc.get("confidence", 0.0) + CONFIDENCE_INC),
                        "last_seen": 0.0,          # no direct contact
                        "heard_about_ts": now,     # indirect evidence
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
                    local["confidence"] = min(1.0, local["confidence"] + CONFIDENCE_INC)
                    local["ts"] = inc_ts
                    changed = True
                    continue

                if inc_seq == local.get("seq", 0):
                    local["confidence"] = min(1.0, local["confidence"] + CONFIDENCE_INC)
                    changed = True

        if changed:
            self.publish_snapshot_if_needed()

    # ---------------- SERVER (DIRECT CONTACT) ----------------
    def start_server(self):
        def loop():
            s = socket.socket()
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen()

            while True:
                try:
                    conn, _ = s.accept()
                    data = conn.recv(65536)
                    if not data:
                        conn.close()
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
                                rec["confidence"] = min(
                                    1.0, rec.get("confidence", 0.0) + CONFIDENCE_DIRECT_INC
                                )
                                rec["ts"] = now

                    self.merge_world(incoming_world)

                    conn.close()
                except Exception:
                    time.sleep(0.05)

        threading.Thread(target=loop, daemon=True).start()

    # ---------------- GOSSIP ----------------
    def gossip_loop(self):
        while True:
            time.sleep(GOSSIP_INTERVAL)
            now = time.time()

            with self.lock:
                self.seq += 1
                self.world[self.node_id] = self.local_state()

                for nid, rec in self.world.items():
                    if nid == self.node_id:
                        continue
                    heard_ts = rec.get("heard_about_ts", 0.0)
                    if now - heard_ts > GOSSIP_INTERVAL * 2:
                        rec["confidence"] = max(
                            0.0, rec.get("confidence", 0.0) - CONFIDENCE_DEC
                        )

                payload = {"from": self.node_id, "world": dict(self.world)}

            self.publish_snapshot_if_needed()

            for peer in list(self.peers):
                try:
                    sock = socket.socket()
                    sock.settimeout(SOCKET_TIMEOUT)
                    sock.connect((peer["host"], peer["port"]))
                    sock.send(json.dumps(payload).encode())
                    sock.close()
                except Exception:
                    pass

    # ---------------- PRUNE ----------------
    def prune_loop(self):
        while True:
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
                print(f"[{self.node_id}] ❌ pruned {removed}")
                self.publish_snapshot_if_needed(force=True)

    # ---------------- PEER REFRESH ----------------
    def refresh_peers_loop(self):
        while True:
            time.sleep(PEER_REFRESH_INTERVAL)
            try:
                r = requests.post(
                    f"{BOOTSTRAP_URL}/register",
                    json={
                        "node_id": self.node_id,
                        "host": self.host,
                        "port": self.port,
                        "lat": self.lat,
                        "lon": self.lon,
                    },
                    timeout=2,
                )
                self.peers = [
                    p for p in r.json().get("peers", [])
                    if p.get("node_id") != self.node_id
                ]
            except Exception:
                pass

    # ---------------- START ----------------
    def start(self):

        print("\n---------------------------")
        print(f"Node ID    : {self.node_id}")
        print(f"Latitude   : {self.lat}")
        print(f"Longitude  : {self.lon}")
        print("---------------------------\n")

        self.start_server()
        threading.Thread(target=self.gossip_loop, daemon=True).start()
        threading.Thread(target=self.prune_loop, daemon=True).start()
        threading.Thread(target=self.refresh_peers_loop, daemon=True).start()

        while True:
            time.sleep(2)
            with self.lock:
                summary = {nid: round(rec.get("confidence", 0.0), 2) for nid, rec in self.world.items()}
            print(f"[{self.node_id}] world: {summary}")


# ---------------- MAIN ----------------
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python node.py <node_id> <port>")
        sys.exit(1)

    Node(sys.argv[1], "127.0.0.1", int(sys.argv[2])).start()