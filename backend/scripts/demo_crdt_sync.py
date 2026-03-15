# BIJMANTRA JULES JOB CARD: D10
# OFFLINE CRDT SYNC DEMONSTRATION
#
# This script demonstrates the core CRDT logic specified in docs/gupt/manuals/OFFLINE_CRDT_SYNC_SPEC.md.
# It implements Vector Clocks, SyncableRecords, and conflict detection/resolution strategies.
#
# Usage: python backend/scripts/demo_crdt_sync.py

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ============================================
# DATA MODELS
# ============================================

class SyncStatus(Enum):
    SYNCED = "synced"
    PENDING = "pending"
    CONFLICT = "conflict"
    ERROR = "error"

@dataclass
class VectorClock:
    """Represents a Vector Clock for causal ordering."""
    clocks: dict[str, int] = field(default_factory=dict)

    def increment(self, node_id: str) -> None:
        """Increments the clock for the given node."""
        self.clocks[node_id] = self.clocks.get(node_id, 0) + 1

    def merge(self, other: 'VectorClock') -> 'VectorClock':
        """Merges with another Vector Clock by taking the max of each component."""
        new_clocks = self.clocks.copy()
        for node, count in other.clocks.items():
            new_clocks[node] = max(new_clocks.get(node, 0), count)
        return VectorClock(clocks=new_clocks)

    def compare(self, other: 'VectorClock') -> str:
        """
        Compares with another Vector Clock.
        Returns: 'before', 'after', 'concurrent', or 'equal'
        """
        all_nodes = set(self.clocks.keys()) | set(other.clocks.keys())
        self_is_at_least = True
        other_is_at_least = True

        for node in all_nodes:
            self_val = self.clocks.get(node, 0)
            other_val = other.clocks.get(node, 0)

            if self_val < other_val:
                self_is_at_least = False
            if other_val < self_val:
                other_is_at_least = False

        if self_is_at_least and other_is_at_least:
            return 'equal'
        if self_is_at_least and not other_is_at_least:
            return 'after'
        if not self_is_at_least and other_is_at_least:
            return 'before'
        return 'concurrent'

    def to_dict(self) -> dict[str, int]:
        return self.clocks

@dataclass
class SyncableRecord:
    """Represents a record that can be synced."""
    id: str
    data: dict[str, Any]
    vector_clock: VectorClock
    last_modified: float
    deleted_at: float | None = None
    sync_status: SyncStatus = SyncStatus.PENDING

    def update(self, node_id: str, new_data: dict[str, Any]) -> None:
        """Updates the record and increments the vector clock."""
        self.data.update(new_data)
        self.vector_clock.increment(node_id)
        self.last_modified = time.time()
        self.sync_status = SyncStatus.PENDING

# ============================================
# SYNC ENGINE LOGIC
# ============================================

class SyncEngine:
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.storage: dict[str, SyncableRecord] = {}

    def create_record(self, data: dict[str, Any]) -> SyncableRecord:
        record_id = str(uuid.uuid4())
        clock = VectorClock()
        clock.increment(self.node_id)

        record = SyncableRecord(
            id=record_id,
            data=data,
            vector_clock=clock,
            last_modified=time.time(),
            sync_status=SyncStatus.PENDING
        )
        self.storage[record_id] = record
        print(f"[{self.node_id}] Created record {record_id}: {data}")
        return record

    def update_record(self, record_id: str, updates: dict[str, Any]) -> SyncableRecord:
        if record_id not in self.storage:
            raise ValueError(f"Record {record_id} not found")

        record = self.storage[record_id]
        record.update(self.node_id, updates)
        print(f"[{self.node_id}] Updated record {record_id}: {updates}")
        return record

    def receive_sync(self, remote_record: SyncableRecord) -> str:
        """
        Receives a record from another node and attempts to sync.
        Returns the result of the sync operation.
        """
        local_record = self.storage.get(remote_record.id)

        if not local_record:
            # New record, just accept it
            self.storage[remote_record.id] = remote_record
            remote_record.sync_status = SyncStatus.SYNCED
            print(f"[{self.node_id}] Received NEW record {remote_record.id}")
            return "accepted_new"

        # Compare Vector Clocks
        comparison = local_record.vector_clock.compare(remote_record.vector_clock)

        if comparison == 'before': # Local is older, accept remote
            self.storage[remote_record.id] = remote_record
            remote_record.sync_status = SyncStatus.SYNCED
            print(f"[{self.node_id}] Accepted UPDATE for {remote_record.id} (Local was older)")
            return "accepted_update"

        elif comparison == 'after': # Local is newer, ignore remote (or send back update)
            print(f"[{self.node_id}] Ignored STALE update for {remote_record.id} (Local is newer)")
            return "ignored_stale"

        elif comparison == 'equal': # Already in sync
            print(f"[{self.node_id}] Record {remote_record.id} is already in sync")
            return "equal"

        else: # Concurrent - CONFLICT!
            print(f"[{self.node_id}] CONFLICT detected for {remote_record.id}!")
            return self.resolve_conflict(local_record, remote_record)

    def resolve_conflict(self, local: SyncableRecord, remote: SyncableRecord) -> str:
        """
        Resolves conflict using Last-Write-Wins (LWW) based on last_modified timestamp.
        """
        print(f"  - Local Time: {local.last_modified}")
        print(f"  - Remote Time: {remote.last_modified}")

        if remote.last_modified > local.last_modified:
            # Remote wins
            self.storage[remote.id] = remote
            remote.sync_status = SyncStatus.SYNCED
            # We must merge clocks to ensure future causality
            remote.vector_clock = remote.vector_clock.merge(local.vector_clock)
            print("  -> Resolved: REMOTE WINS (LWW)")
            return "resolved_remote_wins"
        else:
            # Local wins (keep local)
            # Merge clocks
            local.vector_clock = local.vector_clock.merge(remote.vector_clock)
            # We might want to mark it as pending to push back to remote
            local.sync_status = SyncStatus.PENDING
            print("  -> Resolved: LOCAL WINS (LWW)")
            return "resolved_local_wins"

# ============================================
# MAIN EXECUTION
# ============================================

def run_demo():
    print("=== BIJMANTRA OFFLINE CRDT SYNC DEMO ===")

    # 1. Setup Nodes
    server = SyncEngine("server-01")
    client_a = SyncEngine("client-A")
    client_b = SyncEngine("client-B")

    # 2. Client A creates a Trial
    print("\n--- Step 1: Client A creates a Trial ---")
    trial_data = {"name": "Maize Trial 2024", "location": "Plot-1"}
    record_a = client_a.create_record(trial_data)

    # 3. Client A syncs to Server
    print("\n--- Step 2: Client A syncs to Server ---")
    # Simulate network transfer (copy object)
    import copy
    transfer_record = copy.deepcopy(record_a)
    server.receive_sync(transfer_record)

    # 4. Client B pulls from Server
    print("\n--- Step 3: Client B pulls from Server ---")
    # Simulate server sending data to Client B
    server_record = server.storage[record_a.id]
    transfer_record_b = copy.deepcopy(server_record)
    client_b.receive_sync(transfer_record_b)

    # Verify all have same data
    assert client_b.storage[record_a.id].data["name"] == "Maize Trial 2024"
    print(">> Sync Successful: All nodes have 'Maize Trial 2024'")

    # 5. Concurrent Updates (Conflict Scenario)
    print("\n--- Step 4: Concurrent Updates (Conflict) ---")

    # Client A updates name
    print("Client A updates name to 'Maize Trial 2024 - UPDATED A'")
    client_a.update_record(record_a.id, {"name": "Maize Trial 2024 - UPDATED A"})

    # Client B updates location (concurrently, before receiving A's update)
    print("Client B updates location to 'Plot-99'")
    client_b.update_record(record_a.id, {"location": "Plot-99"})

    # 6. Sync Client A -> Server
    print("\n--- Step 5: Sync Client A -> Server ---")
    transfer_a = copy.deepcopy(client_a.storage[record_a.id])
    server.receive_sync(transfer_a)

    # 7. Sync Client B -> Server (Conflict happens here)
    print("\n--- Step 6: Sync Client B -> Server (Expect Conflict) ---")
    time.sleep(0.1) # Ensure timestamps differ slightly if needed, though LWW uses float
    transfer_b = copy.deepcopy(client_b.storage[record_a.id])

    # Manually forcing B's timestamp to be later for demonstration if needed,
    # but let's see natural order.
    # If python executes fast, timestamps might be close.
    # Let's force B to be 'newer' to win
    transfer_b.last_modified += 1.0

    result = server.receive_sync(transfer_b)

    # 8. Final State on Server
    final_server_rec = server.storage[record_a.id]
    print(f"\nFinal Server State: {final_server_rec.data}")
    print(f"Vector Clock: {final_server_rec.vector_clock.to_dict()}")

    if result == "resolved_remote_wins":
        print(">> verification: Remote (Client B) won as expected due to LWW.")
    elif result == "resolved_local_wins":
        print(">> verification: Local (Server/Client A) won.")

    print("\n=== DEMO COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    run_demo()
