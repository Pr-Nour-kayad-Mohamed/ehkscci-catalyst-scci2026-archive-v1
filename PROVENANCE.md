# PROVENANCE — EHK-SCCI / CATALYST SCCI-2026

Package: EHK-SCCI / CATALYST — SCCI-2026 Archival Package v1  
Status: Local reproducibility and feasibility artefact  
Date: 2026-11-24  
Environment: Termux ARM64  
Language: Python 3, standard library only  

## Purpose

This package records a local, reproducible demonstration of the SCCI-2026
Layer 1 geometric diagnostic workflow.

It verifies exact Wasserstein-1 transport, radius-dependent edge inclusion,
and Ollivier-Ricci curvature on a canonical two-triangle bridge graph.

## Canonical result

The bridge edge is (2,3). The transport pair (1,5) has geodesic distance 3.

- At r_max = 2, the bridge edge is EXCLUDED.
- At r_max = 3, the bridge edge is PASS.
- The bridge curvature is -0.3333333333333337, consistent with -1/3.

## Scope limitation

This artefact does not validate the complete EHK-SCCI/CATALYST system,
Implication (A), Implication (B), the target equivalence, spectral dynamics,
the De Sitter attractor, or any physical, economic, clinical or public-policy
claim.

## Reproducibility

Run:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_scci.py
