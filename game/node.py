# game/node.py
from dataclasses import dataclass
from typing import Optional

class NodeType:
    START = "START"
    EMPTY = "EMPTY"
    ENCOUNTER = "ENCOUNTER"
    SHOP = "SHOP"
    BOSS = "BOSS"

@dataclass
class Node:
    id: int
    x: int
    y: int
    ntype: str = NodeType.EMPTY
    visited: bool = False        # player has been here at least once
    event_done: bool = False     # the node's event (fight/shop) was already executed
    seed: int = 0
