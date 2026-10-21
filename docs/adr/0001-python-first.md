# ADR 0001: Python-first modular monorepo

Accepted 2026-10-21. Keep domain, orchestration, SDK, API and shared UI in Python. Confine necessary native or OS-specific dependencies to adapters. Reference snapshots remain local and excluded from Git. New implementations start independently; migration requires explicit review and tests.
