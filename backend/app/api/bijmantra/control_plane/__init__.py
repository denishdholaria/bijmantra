"""Thin router package for developer control plane responsibilities.

Each sub-module owns one responsibility domain:
  - lanes.py       — active-board CRUD, versions, restore, completion
  - missions.py    — runtime/mission-state lifecycle
  - verification.py — runtime/silent-monitors, autonomy-cycle, watchdog, completion-assist
  - telemetry.py   — overnight-queue/status, closeout-receipt, learnings
"""
