# MandateGuard source specification

This folder archives the source specification package used for the
MandateGuard implementation merged in PR #68.

## Provenance

- Source path: `C:\Users\Ludo\Documents\Projet Trois dé\mandateguard_claude_docs`
- Archive date: 2026-05-23
- Archived files: 31
- Destination: `docs/mandateguard/spec/`

## Layout

The `spec/` directory preserves the original source tree:

- Root coordination files: `AGENTS.md`, `ALL_IN_ONE.md`, `CLAUDE.md`, `README.md`
- Architecture decisions: `adr/`
- Sprint backlog: `backlog/`
- Functional and technical specification: `docs/`

Implementation code lives in the MandateGuard merge on `main`, including
`src/p2p_fraud/sepa`, `src/p2p_fraud/risk_core`, `src/p2p_fraud/evidence`,
`src/p2p_fraud/ai/redact.py`, and `apps/web/app/risk-lab-sepa/page.tsx`.
