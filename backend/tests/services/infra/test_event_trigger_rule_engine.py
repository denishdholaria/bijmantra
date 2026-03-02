import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, UTC
import uuid

from app.services.infra.event_trigger_rule_engine import (
    EventTriggerRuleEngine,
    Rule,
    RuleCondition,
    RuleAction,
    ConditionOperator,
    ActionType,
    EventType
)
from app.services.event_bus import Event

class TestEventTriggerRuleEngine(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.engine = EventTriggerRuleEngine()
        # Mock event_bus in the module
        self.event_bus_patcher = patch('app.services.infra.event_trigger_rule_engine.event_bus')
        self.mock_event_bus = self.event_bus_patcher.start()
        self.mock_event_bus.subscribe.return_value = "sub_123"

    def tearDown(self):
        self.event_bus_patcher.stop()

    def test_add_remove_rule(self):
        rule = Rule(
            name="Test Rule",
            event_type=EventType.GERMPLASM_CREATED,
            conditions=[],
            actions=[]
        )

        rule_id = self.engine.add_rule(rule)
        self.assertEqual(rule_id, rule.id)
        self.assertIn(rule.id, self.engine._rules)
        self.mock_event_bus.subscribe.assert_called_once()

        # Add another rule for same event type, should not subscribe again
        rule2 = Rule(
            name="Test Rule 2",
            event_type=EventType.GERMPLASM_CREATED,
            conditions=[],
            actions=[]
        )
        self.engine.add_rule(rule2)
        self.mock_event_bus.subscribe.assert_called_once()

        # Remove rule 1
        self.engine.remove_rule(rule.id)
        self.assertNotIn(rule.id, self.engine._rules)
        self.mock_event_bus.unsubscribe.assert_not_called()

        # Remove rule 2, should unsubscribe
        self.engine.remove_rule(rule2.id)
        self.mock_event_bus.unsubscribe.assert_called_once_with("sub_123")

    def test_evaluate_condition_equals(self):
        event = Event(
            id="1",
            type=EventType.GERMPLASM_CREATED,
            source="test",
            data={"status": "active"},
            timestamp=datetime.now(UTC)
        )

        condition = RuleCondition(
            field="status",
            operator=ConditionOperator.EQUALS,
            value="active"
        )

        self.assertTrue(self.engine._evaluate_condition(condition, event))

        condition.value = "inactive"
        self.assertFalse(self.engine._evaluate_condition(condition, event))

    def test_evaluate_condition_nested(self):
        event = Event(
            id="1",
            type=EventType.GERMPLASM_CREATED,
            source="test",
            data={"meta": {"priority": 5}},
            timestamp=datetime.now(UTC)
        )

        condition = RuleCondition(
            field="meta.priority",
            operator=ConditionOperator.GREATER_THAN,
            value=3
        )
        self.assertTrue(self.engine._evaluate_condition(condition, event))

    def test_evaluate_condition_contains(self):
        event = Event(
            id="1",
            type=EventType.GERMPLASM_CREATED,
            source="test",
            data={"tags": ["a", "b", "c"]},
            timestamp=datetime.now(UTC)
        )

        condition = RuleCondition(
            field="tags",
            operator=ConditionOperator.CONTAINS,
            value="b"
        )
        self.assertTrue(self.engine._evaluate_condition(condition, event))

    async def test_handle_event_match(self):
        rule = Rule(
            name="Match Rule",
            event_type=EventType.GERMPLASM_CREATED,
            conditions=[
                RuleCondition(field="status", operator=ConditionOperator.EQUALS, value="active")
            ],
            actions=[
                RuleAction(type=ActionType.LOG, config={"message": "Matched!"})
            ]
        )
        self.engine.add_rule(rule)

        event = Event(
            id="1",
            type=EventType.GERMPLASM_CREATED,
            source="test",
            data={"status": "active"},
            timestamp=datetime.now(UTC)
        )

        with patch.object(self.engine, '_execute_actions', new_callable=AsyncMock) as mock_exec:
            await self.engine._handle_event(event)
            mock_exec.assert_awaited_once_with(rule, event)

    async def test_handle_event_no_match(self):
        rule = Rule(
            name="No Match Rule",
            event_type=EventType.GERMPLASM_CREATED,
            conditions=[
                RuleCondition(field="status", operator=ConditionOperator.EQUALS, value="active")
            ],
            actions=[]
        )
        self.engine.add_rule(rule)

        event = Event(
            id="1",
            type=EventType.GERMPLASM_CREATED,
            source="test",
            data={"status": "inactive"},
            timestamp=datetime.now(UTC)
        )

        with patch.object(self.engine, '_execute_actions', new_callable=AsyncMock) as mock_exec:
            await self.engine._handle_event(event)
            mock_exec.assert_not_called()

    @patch("httpx.AsyncClient")
    async def test_execute_webhook(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        action = RuleAction(
            type=ActionType.WEBHOOK,
            config={"url": "http://example.com", "method": "POST"}
        )

        event = Event(
            id="1",
            type=EventType.GERMPLASM_CREATED,
            source="test",
            data={"key": "value"},
            timestamp=datetime.now(UTC)
        )

        rule = Rule(
            name="Test Rule",
            event_type=EventType.GERMPLASM_CREATED,
            conditions=[],
            actions=[]
        )

        await self.engine._execute_webhook(action, event, rule)

        mock_client.request.assert_awaited_once()
        args, kwargs = mock_client.request.call_args
        self.assertEqual(args[0], "POST")
        self.assertEqual(args[1], "http://example.com")
        self.assertEqual(kwargs["json"]["data"], {"key": "value"})
        self.assertEqual(kwargs["json"]["rule_id"], rule.id)

if __name__ == '__main__':
    unittest.main()
