import unittest
import sys
import os

# Add backend to path to allow imports
sys.path.append(os.path.abspath("backend"))

from app.modules.core.services.infra.websocket_crdt_sync_manager import WebsocketCRDTSyncManager, PresenceMetadata

class TestWebsocketCRDTSyncManager(unittest.TestCase):

    def setUp(self):
        self.manager = WebsocketCRDTSyncManager()

    def test_initial_state(self):
        self.assertEqual(self.manager.get_active_peers(), {})
        self.assertEqual(self.manager.get_state_snapshot(), {})

    def test_update_peer(self):
        user_id = "user1"
        metadata: PresenceMetadata = {"username": "Alice", "session_id": "s1"}
        ts = 100.0

        changed = self.manager.update_peer(user_id, metadata, ts)
        self.assertTrue(changed)

        peers = self.manager.get_active_peers()
        self.assertIn(user_id, peers)
        self.assertEqual(peers[user_id], metadata)

        # Verify snapshot structure
        snapshot = self.manager.get_state_snapshot()
        self.assertEqual(snapshot[user_id]["value"], metadata)
        self.assertEqual(snapshot[user_id]["timestamp"], ts)
        self.assertFalse(snapshot[user_id]["is_deleted"])

    def test_lww_update(self):
        user_id = "user1"
        meta1: PresenceMetadata = {"username": "Alice", "session_id": "s1"}
        ts1 = 100.0

        meta2: PresenceMetadata = {"username": "Alice", "session_id": "s2"}
        ts2 = 101.0

        # First update
        self.manager.update_peer(user_id, meta1, ts1)
        self.assertEqual(self.manager.get_active_peers()[user_id]["session_id"], "s1")

        # Newer update should overwrite
        changed = self.manager.update_peer(user_id, meta2, ts2)
        self.assertTrue(changed)
        self.assertEqual(self.manager.get_active_peers()[user_id]["session_id"], "s2")

        # Older update should be ignored
        changed = self.manager.update_peer(user_id, meta1, ts1)
        self.assertFalse(changed)
        self.assertEqual(self.manager.get_active_peers()[user_id]["session_id"], "s2")

    def test_remove_peer(self):
        user_id = "user1"
        meta: PresenceMetadata = {"username": "Alice", "session_id": "s1"}
        ts1 = 100.0
        ts2 = 101.0

        self.manager.update_peer(user_id, meta, ts1)
        self.assertIn(user_id, self.manager.get_active_peers())

        # Remove with newer timestamp
        changed = self.manager.remove_peer(user_id, ts2)
        self.assertTrue(changed)
        self.assertNotIn(user_id, self.manager.get_active_peers())

        # Check snapshot for tombstone
        snapshot = self.manager.get_state_snapshot()
        self.assertTrue(snapshot[user_id]["is_deleted"])
        self.assertEqual(snapshot[user_id]["timestamp"], ts2)

    def test_remove_peer_out_of_order(self):
        user_id = "user1"
        ts_remove = 101.0
        ts_old_add = 100.0

        # Receive remove first
        self.manager.remove_peer(user_id, ts_remove)
        self.assertNotIn(user_id, self.manager.get_active_peers())

        # Receive older add later
        meta: PresenceMetadata = {"username": "Alice", "session_id": "s1"}
        changed = self.manager.update_peer(user_id, meta, ts_old_add)
        self.assertFalse(changed)
        self.assertNotIn(user_id, self.manager.get_active_peers())

    def test_merge_state(self):
        # Local state: user1 (ts=100), user2 (ts=100)
        self.manager.update_peer("user1", {"username": "Alice"}, 100.0)
        self.manager.update_peer("user2", {"username": "Bob"}, 100.0)

        # Remote state:
        # user1 (ts=101) -> newer update
        # user2 (ts=99) -> older update (ignored)
        # user3 (ts=100) -> new user
        # user4 (ts=100, deleted) -> new deleted user

        remote_state = {
            "user1": {"value": {"username": "AliceUpdated"}, "timestamp": 101.0, "is_deleted": False},
            "user2": {"value": {"username": "BobOld"}, "timestamp": 99.0, "is_deleted": False},
            "user3": {"value": {"username": "Charlie"}, "timestamp": 100.0, "is_deleted": False},
            "user4": {"value": {}, "timestamp": 100.0, "is_deleted": True},
        }

        self.manager.merge(remote_state)

        active = self.manager.get_active_peers()
        self.assertEqual(active["user1"]["username"], "AliceUpdated")
        self.assertEqual(active["user2"]["username"], "Bob") # Kept local
        self.assertIn("user3", active)
        self.assertNotIn("user4", active)

        snapshot = self.manager.get_state_snapshot()
        self.assertTrue(snapshot["user4"]["is_deleted"])

    def test_prune(self):
        current_time = 200.0
        ttl = 50

        # Active user (should keep)
        self.manager.update_peer("user1", {}, 100.0)

        # Recent tombstone (190.0, age=10 < TTL=50) -> Keep
        self.manager.remove_peer("user2", 190.0)

        # Old tombstone (140.0, age=60 > TTL=50) -> Prune
        self.manager.remove_peer("user3", 140.0)

        pruned_count = self.manager.prune(ttl, current_time)
        self.assertEqual(pruned_count, 1)

        snapshot = self.manager.get_state_snapshot()
        self.assertIn("user1", snapshot)
        self.assertIn("user2", snapshot)
        self.assertNotIn("user3", snapshot)

if __name__ == '__main__':
    unittest.main()
