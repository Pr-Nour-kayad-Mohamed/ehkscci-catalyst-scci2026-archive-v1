#!/usr/bin/env python3
"""SCCI-2026 Layer 1 canonical bridge validator."""

from __future__ import annotations

import csv
import json
from collections import deque
from pathlib import Path
from typing import Dict, List, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "canonical_bridge_graph_edges.csv"
RESULTS_DIR = ROOT / "results"

ALPHA = 0.5
R_MAX_PASS = 3
R_MAX_EXCLUDED = 2
EXPECTED_BRIDGE_CURVATURE = -1.0 / 3.0
BRIDGE_EDGE = (2, 3)
TRANSPORT_PAIR = (1, 5)


def load_edges(path: Path) -> List[Tuple[int, int]]:
    edges: List[Tuple[int, int]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not {"source", "target"}.issubset(reader.fieldnames or []):
            raise ValueError("CSV must contain source and target columns")
        for row in reader:
            source = int(row["source"])
            target = int(row["target"])
            if source == target:
                raise ValueError("Self-loops are not allowed")
            edge = (min(source, target), max(source, target))
            if edge not in edges:
                edges.append(edge)
    if not edges:
        raise ValueError("No edges loaded")
    return edges


def build_adjacency(edges: List[Tuple[int, int]]) -> Dict[int, Set[int]]:
    adjacency: Dict[int, Set[int]] = {}
    for source, target in edges:
        adjacency.setdefault(source, set()).add(target)
        adjacency.setdefault(target, set()).add(source)
    return adjacency


def shortest_distances(adjacency: Dict[int, Set[int]], source: int) -> Dict[int, int]:
    distances = {source: 0}
    queue = deque([source])
    while queue:
        node = queue.popleft()
        for neighbour in adjacency.get(node, set()):
            if neighbour not in distances:
                distances[neighbour] = distances[node] + 1
                queue.append(neighbour)
    return distances


def geodesic_distance(adjacency: Dict[int, Set[int]], source: int, target: int) -> int:
    if source == target:
        return 0
    distances = shortest_distances(adjacency, source)
    if target not in distances:
        raise ValueError(f"Nodes {source} and {target} are disconnected")
    return distances[target]


class MinCostFlow:
    def __init__(self, node_count: int) -> None:
        self.graph: List[List[list]] = [[] for _ in range(node_count)]

    def add_edge(self, source: int, target: int, capacity: float, cost: int) -> None:
        forward = [target, capacity, cost, len(self.graph[target])]
        backward = [source, 0.0, -cost, len(self.graph[source])]
        self.graph[source].append(forward)
        self.graph[target].append(backward)

    def solve(self, source: int, target: int) -> Tuple[float, float]:
        node_count = len(self.graph)
        total_flow = 0.0
        total_cost = 0.0

        while True:
            distance = [float("inf")] * node_count
            previous_node = [-1] * node_count
            previous_edge = [-1] * node_count
            in_queue = [False] * node_count

            distance[source] = 0.0
            queue = deque([source])
            in_queue[source] = True

            while queue:
                node = queue.popleft()
                in_queue[node] = False
                for edge_index, edge in enumerate(self.graph[node]):
                    neighbour, capacity, cost, _ = edge
                    if capacity > 0 and distance[node] + cost < distance[neighbour]:
                        distance[neighbour] = distance[node] + cost
                        previous_node[neighbour] = node
                        previous_edge[neighbour] = edge_index
                        if not in_queue[neighbour]:
                            queue.append(neighbour)
                            in_queue[neighbour] = True

            if distance[target] == float("inf"):
                break

            bottleneck = float("inf")
            node = target
            while node != source:
                edge = self.graph[previous_node[node]][previous_edge[node]]
                bottleneck = min(bottleneck, edge[1])
                node = previous_node[node]

            node = target
            while node != source:
                edge = self.graph[previous_node[node]][previous_edge[node]]
                edge[1] -= bottleneck
                reverse = self.graph[edge[0]][edge[3]]
                reverse[1] += bottleneck
                node = previous_node[node]

            total_flow += bottleneck
            total_cost += bottleneck * distance[target]

        return total_flow, total_cost


def node_mass(adjacency: Dict[int, Set[int]], node: int, alpha: float) -> Dict[int, float]:
    neighbours = adjacency[node]
    mass = {node: alpha}
    share = (1.0 - alpha) / len(neighbours)
    for neighbour in neighbours:
        mass[neighbour] = mass.get(neighbour, 0.0) + share
    return mass


def exact_w1_transport(
    adjacency: Dict[int, Set[int]],
    source_mass: Dict[int, float],
    target_mass: Dict[int, float],
) -> float:
    nodes = sorted(set(source_mass) | set(target_mass))
    index = {node: position for position, node in enumerate(nodes)}
    source_id = len(nodes)
    target_id = source_id + 1
    network = MinCostFlow(target_id + 1)

    total_mass = 0.0
    for node, mass in source_mass.items():
        if mass > 0:
            network.add_edge(source_id, index[node], mass, 0)
            total_mass += mass

    for node, mass in target_mass.items():
        if mass > 0:
            network.add_edge(index[node], target_id, mass, 0)

    for source_node in source_mass:
        for target_node in target_mass:
            distance = geodesic_distance(adjacency, source_node, target_node)
            if distance > 0:
                network.add_edge(
                    index[source_node],
                    index[target_node],
                    float("inf"),
                    distance,
                )

    transported, cost = network.solve(source_id, target_id)
    if abs(transported - total_mass) > 1e-9:
        raise ValueError("Transport plan did not conserve mass")

    return cost / total_mass


def ollivier_ricci_curvature(
    adjacency: Dict[int, Set[int]], source: int, target: int, alpha: float
) -> float:
    if not 0.0 <= alpha <= 1.0:
        raise ValueError("Alpha must be between 0 and 1")

    source_mass = node_mass(adjacency, source, alpha)
    target_mass = node_mass(adjacency, target, alpha)
    w1 = exact_w1_transport(adjacency, source_mass, target_mass)
    distance = geodesic_distance(adjacency, source, target)
    return 1.0 - w1 / distance


def validate(edges: List[Tuple[int, int]]) -> Dict[str, object]:
    adjacency = build_adjacency(edges)

    if BRIDGE_EDGE[1] not in adjacency.get(BRIDGE_EDGE[0], set()):
        raise ValueError("Canonical bridge edge (2,3) is missing")

    bridge_distance = geodesic_distance(adjacency, *BRIDGE_EDGE)
    if bridge_distance != 1:
        raise ValueError("Canonical bridge edge must have distance 1")

    transport_pair_distance = geodesic_distance(adjacency, *TRANSPORT_PAIR)
    if transport_pair_distance != 3:
        raise ValueError("Canonical transport pair distance must be 3")

    curvature = ollivier_ricci_curvature(adjacency, *BRIDGE_EDGE, ALPHA)
    passed = abs(curvature - EXPECTED_BRIDGE_CURVATURE) < 1e-9

    excluded = {
        "status": "EXCLUDED",
        "edge": list(BRIDGE_EDGE),
        "r_max": R_MAX_EXCLUDED,
        "reason": "Transport pair distance exceeds selected radius policy",
        "pair_distance": transport_pair_distance,
    }

    resolved = {
        "status": "PASS" if passed else "FAIL",
        "edge": list(BRIDGE_EDGE),
        "r_max": R_MAX_PASS,
        "alpha": ALPHA,
        "pair_distance": transport_pair_distance,
        "curvature": curvature,
        "expected_curvature": EXPECTED_BRIDGE_CURVATURE,
        "tolerance": 1e-9,
    }

    return {
        "package": "EHK-SCCI/CATALYST SCCI-2026 Archival Package v1",
        "scope": "Local reproducibility and feasibility artefact",
        "canonical_graph": "two triangles connected by bridge edge (2,3)",
        "alpha": ALPHA,
        "bridge_edge": list(BRIDGE_EDGE),
        "bridge_distance": bridge_distance,
        "transport_pair_distance": transport_pair_distance,
        "r_max_excluded": R_MAX_EXCLUDED,
        "r_max_pass": R_MAX_PASS,
        "r2_result": excluded,
        "r3_result": resolved,
        "overall_status": "PASS" if passed else "FAIL",
        "claim_limit": (
            "This result does not validate the complete EHK-SCCI/CATALYST "
            "system, Implication (A), Implication (B), the target equivalence, "
            "spectral dynamics, or the De Sitter attractor."
        ),
    }


def main() -> int:
    if not DATA_FILE.exists():
        print(f"FAIL: missing data file: {DATA_FILE}")
        return 1

    try:
        edges = load_edges(DATA_FILE)
        report = validate(edges)
    except Exception as error:
        print(f"FAIL: {error}")
        return 1

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    r3_path = RESULTS_DIR / "canonical_bridge_audit_r3.json"
    r2_path = RESULTS_DIR / "canonical_bridge_audit_r2_excluded.json"

    r3_path.write_text(
        json.dumps(report["r3_result"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    r2_path.write_text(
        json.dumps(report["r2_result"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(f"Bridge distance: {report['bridge_distance']}")
    print(f"Transport pair distance: {report['transport_pair_distance']}")
    print(f"r_max = {R_MAX_EXCLUDED}: {report['r2_result']['status']}")
    print(
        f"r_max = {R_MAX_PASS}: {report['r3_result']['status']} "
        f"curvature = {report['r3_result']['curvature']:.8f}"
    )
    print(f"Overall status: {report['overall_status']}")
    print(f"Wrote: {r3_path}")
    print(f"Wrote: {r2_path}")

    return 0 if report["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
