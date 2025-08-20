# game/world.py
import random
from typing import Dict, List
from .node import Node, NodeType

class MapGraph:
    def __init__(self, w, h, node_count=14):
        self.nodes: Dict[int, Node] = {}
        self.edges: List[tuple] = []
        self.node_count = node_count
        self.start_id = 0
        self.boss_id = node_count - 1
        self._generate(w, h)

    def _generate(self, w, h):
        margin = 120
        for i in range(self.node_count):
            band = i / max(1, self.node_count - 1)
            nx = int(margin + random.random() * (w - 2*margin))
            ny = int(140 + band * (h - 320) + random.uniform(-35,35))
            self.nodes[i] = Node(i, nx, ny, NodeType.EMPTY, False, False, random.randint(0,999999))
        # create edges (directed-ish)
        for i in range(self.node_count):
            max_to = min(self.node_count, i+4)
            options = list(range(i+1, max_to))
            random.shuffle(options)
            for t in options[:random.randint(1,2)]:
                self.edges.append((i,t))
        # set special nodes
        self.nodes[self.start_id].ntype = NodeType.START
        self.nodes[self.boss_id].ntype = NodeType.BOSS
        for nid, node in self.nodes.items():
            if nid in (self.start_id, self.boss_id):
                continue
            r = random.random()
            if r < 0.56:
                node.ntype = NodeType.ENCOUNTER
            elif r < 0.78:
                node.ntype = NodeType.SHOP
            else:
                node.ntype = NodeType.EMPTY

    def neighbors(self, nid: int) -> List[int]:
        # return both outgoing and incoming neighbors (undirected behavior)
        outs = [t for s,t in self.edges if s == nid]
        ins = [s for s,t in self.edges if t == nid]
        neigh = outs + ins
        seen = set()
        res = []
        for n in neigh:
            if n not in seen:
                res.append(n); seen.add(n)
        return res
