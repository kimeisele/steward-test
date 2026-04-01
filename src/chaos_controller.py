#!/usr/bin/env python3
"""
steward-test chaos controller — self-managed state machine.

Phases:
  ALIVE   (4 runs): normal heartbeat, health=1.0
  SILENT  (2 runs): no heartbeat emitted — steward detects SUSPECT→DEAD
  CORRUPT (1 run):  invalidate peer.json — steward RepoHealer fires PR
  RECOVERY(1 run):  restore peer.json, normal heartbeat, auto-merge PR

State persisted in data/federation/test_state.json
"""
import json
import subprocess
import sys
from pathlib import Path

STATE_PATH = Path("data/federation/test_state.json")
PEER_PATH = Path("data/federation/peer.json")

PHASES = [
    ("ALIVE", 4),
    ("SILENT", 2),
    ("CORRUPT", 1),
    ("RECOVERY", 1),
]

VALID_PEER = {
    "identity": {
        "city_id": "steward-test",
        "slug": "steward-test",
        "repo": "kimeisele/steward-test",
        "node_id": "ag_test_01"
    },
    "capabilities": ["testing", "federation_relay", "chaos_emitter"],
    "nadi": {
        "outbox": "data/federation/nadi_outbox.json",
        "inbox": "data/federation/nadi_inbox.json"
    }
}

CORRUPT_PEER = {
    "identity": {},
    "capabilities": [],
}


def load_state():
    try:
        return json.loads(STATE_PATH.read_text())
    except Exception:
        return {"phase": "ALIVE", "run_count": 0, "phase_run": 0}


def save_state(state):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n")


def advance_state(state):
    state["run_count"] += 1
    state["phase_run"] += 1
    current_phase = state["phase"]
    phase_duration = dict(PHASES)[current_phase]
    if state["phase_run"] >= phase_duration:
        idx = [p[0] for p in PHASES].index(current_phase)
        next_idx = (idx + 1) % len(PHASES)
        state["phase"] = PHASES[next_idx][0]
        state["phase_run"] = 0
        print(f"CHAOS: phase transition {current_phase} → {state['phase']}")
    return state


def run():
    state = load_state()
    phase = state["phase"]
    print(f"CHAOS: run={state['run_count']} phase={phase} phase_run={state['phase_run']}")

    if phase == "ALIVE":
        # Normal heartbeat — nadi handles it
        PEER_PATH.write_text(json.dumps(VALID_PEER, indent=2) + "\n")
        print("CHAOS: ALIVE — sending normal heartbeat")
        sys.exit(0)  # workflow continues to nadi heartbeat step

    elif phase == "SILENT":
        # No heartbeat — write empty outbox, skip nadi
        PEER_PATH.write_text(json.dumps(VALID_PEER, indent=2) + "\n")
        Path("data/federation/nadi_outbox.json").write_text("[]\n")
        print("CHAOS: SILENT — suppressing heartbeat, steward should detect SUSPECT")
        sys.exit(1)  # non-zero exit skips subsequent steps (if: success())

    elif phase == "CORRUPT":
        # Corrupt peer.json — steward RepoHealer should detect and PR
        PEER_PATH.write_text(json.dumps(CORRUPT_PEER, indent=2) + "\n")
        print("CHAOS: CORRUPT — invalidated peer.json, steward RepoHealer should fire")
        sys.exit(1)  # suppress heartbeat relay

    elif phase == "RECOVERY":
        # Restore peer.json, auto-merge any open steward PRs
        PEER_PATH.write_text(json.dumps(VALID_PEER, indent=2) + "\n")
        print("CHAOS: RECOVERY — restored peer.json, resuming normal operation")
        # Auto-merge any open steward PRs using shell
        subprocess.run(
            ["bash", "-c", 
             'gh pr list --repo kimeisele/steward-test --json number,title --jq '
             '".[] | select(.title | contains(\\"steward\\")) | .number" | '
             'while read pr_num; do gh pr merge "$pr_num" --repo kimeisele/steward-test --squash --auto; done'],
            capture_output=True
        )
        print("CHAOS: auto-merged steward PRs if any")
        sys.exit(0)

    state = advance_state(state)
    save_state(state)


if __name__ == "__main__":
    run()
