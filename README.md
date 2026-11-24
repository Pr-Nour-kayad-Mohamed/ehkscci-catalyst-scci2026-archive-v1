# EHK-SCCI / CATALYST — SCCI-2026 Archival Package v1

This repository contains a local reproducibility and feasibility artefact
for the SCCI-2026 Layer 1 geometric diagnostic workflow.

It includes:

- A Python standard-library validator.
- Nine unit tests covering PASS, EXCLUDED and FAIL-CLOSED paths.
- SHA-256 provenance manifests.
- A canonical two-triangle bridge graph.
- A LaTeX working manuscript.
- Audit reports for r_max = 2 and r_max = 3.

## Scope

This package demonstrates local numerical feasibility, internal consistency
and reproducible artefact integrity.

It does not validate the complete EHK-SCCI/CATALYST system, Implication (A),
Implication (B), the target equivalence, spectral dynamics, the De Sitter
attractor, or any physical, economic or public-policy claim.

## Run validation

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_scci.py
sha256sum --check --strict SHA256SUMS
