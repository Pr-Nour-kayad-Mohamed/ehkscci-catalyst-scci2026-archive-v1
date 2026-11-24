#!/usr/bin/env python3
"""Unit tests for the SCCI-2026 canonical bridge validator."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_scci import (  # noqa: E402
    ALPHA,
    build_adjacency,
    geodesic_distance,
    load_edges,
    ollivier_ricci_curvature,
    validate,
)

DATA_FILE = ROOT / "data" / "canonical_bridge_graph_edges.csv"


class SCCIValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.edges = load_edges(DATA_FILE)
        self.adjacency = build_adjacency(self.edges)

    def test_01_csv_loads_seven_edges(self) -> None:
        self.assertEqual(len(self.edges), 7)

    def test_02_adjacency_contains_all_nodes(self) -> None:
        expected_nodes = {1, 2, 3, 4, 5, 6}
        self.assertEqual(set(self.adjacency), expected_nodes)

    def test_03_bridge_edge_is_present(self) -> None:
        self.assertIn(3, self.adjacency[2])
        self.assertIn(2, self.adjacency[3])

    def test_04_bridge_distance_is_one(self) -> None:
        self.assertEqual(geodesic_distance(self.adjacency, 2, 3), 1)

    def test_05_transport_pair_distance_is_three(self) -> None:
        self.assertEqual(geodesic_distance(self.adjacency, 1, 5), 3)

    def test_06_r2_policy_excludes_bridge(self) -> None:
        report = validate(self.edges)
        self.assertEqual(report["r2_result"]["status"], "EXCLUDED")
        self.assertEqual(report["r2_result"]["r_max"], 2)
        self.assertEqual(report["r2_result"]["pair_distance"], 3)

    def test_07_r3_policy_passes(self) -> None:
        report = validate(self.edges)
        self.assertEqual(report["r3_result"]["status"], "PASS")
        self.assertEqual(report["r3_result"]["r_max"], 3)

    def test_08_bridge_curvature_is_negative_one_third(self) -> None:
        curvature = ollivier_ricci_curvature(self.adjacency, 2, 3, ALPHA)
        self.assertAlmostEqual(curvature, -1.0 / 3.0, places=9)

    def test_09_fail_closed_on_disconnected_graph(self) -> None:
        with self.assertRaises(ValueError):
            validate([(1, 2)])


if __name__ == "__main__":
    unittest.main()
