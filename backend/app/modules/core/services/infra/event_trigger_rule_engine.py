"""
Event Trigger Rule Engine Service
Evaluates rules against events and triggers infrastructure actions.
"""

import logging
import uuid
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.http_tracing import create_traced_async_client
from app.modules.core.services.event_bus import Event, EventType, event_bus


logger = logging.getLogger(__name__)


class ConditionOperator(StrEnum):
    """Operators for rule conditions"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    CONTAINS = "contains"
    IN = "in"
    NOT_IN = "not_in"


class ActionType(StrEnum):
    """Types of actions to trigger"""
    WEBHOOK = "webhook"
    LOG = "log"


class RuleCondition(BaseModel):
    """Condition to evaluate against event data"""
    field: str = Field(..., description="Field path in event data (e.g. 'temperature' or 'sensor.id')")
    operator: ConditionOperator
    value: Any = Field(..., description="Value to compare against")

    model_config = ConfigDict(from_attributes=True)


class RuleAction(BaseModel):
    """Action to execute when rule matches"""
    type: ActionType
    config: dict[str, Any] = Field(..., description="Configuration for the action")

    model_config = ConfigDict(from_attributes=True)


class Rule(BaseModel):
    """Rule definition"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    event_type: EventType
    conditions: list[RuleCondition]
    actions: list[RuleAction]
    enabled: bool = True

    model_config = ConfigDict(from_attributes=True)


class EventTriggerRuleEngine:
    """
    Engine to manage and evaluate event trigger rules.
    """

    def __init__(self):
        self._rules: dict[str, Rule] = {}
        self._subscriptions: dict[EventType, str] = {}  # event_type -> subscription_id

    def add_rule(self, rule: Rule) -> str:
        """Add a new rule and subscribe to event if needed"""
        self._rules[rule.id] = rule
        self._ensure_subscription(rule.event_type)
        logger.info(f"Added rule: {rule.name} ({rule.id}) for {rule.event_type}")
        return rule.id

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule and unsubscribe if no longer needed"""
        if rule_id not in self._rules:
            return False

        rule = self._rules.pop(rule_id)
        logger.info(f"Removed rule: {rule.name} ({rule_id})")

        # Check if we need to unsubscribe
        self._cleanup_subscription(rule.event_type)
        return True

    def get_rule(self, rule_id: str) -> Rule | None:
        """Get a rule by ID"""
        return self._rules.get(rule_id)

    def list_rules(self) -> list[Rule]:
        """List all rules"""
        return list(self._rules.values())

    def _ensure_subscription(self, event_type: EventType):
        """Subscribe to event type if not already subscribed"""
        if event_type not in self._subscriptions:
            sub_id = event_bus.subscribe(
                event_type=event_type,
                handler=self._handle_event,
                module="event_trigger_rule_engine"
            )
            self._subscriptions[event_type] = sub_id
            logger.info(f"Subscribed to {event_type} for rule engine")

    def _cleanup_subscription(self, event_type: EventType):
        """Unsubscribe if no rules leverage this event type"""
        # Check if any other rules use this event type
        has_rules = any(r.event_type == event_type for r in self._rules.values())

        if not has_rules and event_type in self._subscriptions:
            sub_id = self._subscriptions.pop(event_type)
            event_bus.unsubscribe(sub_id)
            logger.info(f"Unsubscribed from {event_type} as no rules remain")

    async def _handle_event(self, event: Event):
        """Handle incoming event and evaluate rules"""
        # Find matching rules for this event type
        matching_rules = [
            r for r in self._rules.values()
            if r.enabled and r.event_type == event.type
        ]

        for rule in matching_rules:
            try:
                if self._evaluate_rule(rule, event):
                    logger.info(f"Rule matched: {rule.name} ({rule.id})")
                    await self._execute_actions(rule, event)
            except Exception as e:
                logger.error(f"Error processing rule {rule.id}: {e}", exc_info=True)

    def _evaluate_rule(self, rule: Rule, event: Event) -> bool:
        """Evaluate all conditions of a rule against the event"""
        for condition in rule.conditions:
            if not self._evaluate_condition(condition, event):
                return False
        return True

    def _evaluate_condition(self, condition: RuleCondition, event: Event) -> bool:
        """Evaluate a single condition"""
        # Extract value from event data using dot notation
        value = self._get_value_from_event(event, condition.field)

        op = condition.operator
        target = condition.value

        try:
            if op == ConditionOperator.EQUALS:
                return value == target
            elif op == ConditionOperator.NOT_EQUALS:
                return value != target
            elif op == ConditionOperator.GREATER_THAN:
                return value > target
            elif op == ConditionOperator.LESS_THAN:
                return value < target
            elif op == ConditionOperator.GREATER_THAN_OR_EQUAL:
                return value >= target
            elif op == ConditionOperator.LESS_THAN_OR_EQUAL:
                return value <= target
            elif op == ConditionOperator.CONTAINS:
                return target in value
            elif op == ConditionOperator.IN:
                return value in target
            elif op == ConditionOperator.NOT_IN:
                return value not in target
            return False
        except TypeError:
            # Comparison between incompatible types
            return False

    def _get_value_from_event(self, event: Event, field_path: str) -> Any:
        """Extract value from event object or data dictionary using dot notation"""
        parts = field_path.split(".")
        current = event.data

        # Handle special top-level fields
        if parts[0] in ["id", "source", "user_id", "organization_id", "correlation_id"]:
            if len(parts) == 1:
                return getattr(event, parts[0])
            # If accessing properties of these fields, usually unlikely but possible
            # Logic here assumes we mostly care about `data` or top-level string fields

        # Traverse data dictionary
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None

            if current is None:
                return None

        return current

    async def _execute_actions(self, rule: Rule, event: Event):
        """Execute all actions for a matched rule"""
        for action in rule.actions:
            try:
                if action.type == ActionType.WEBHOOK:
                    await self._execute_webhook(action, event, rule)
                elif action.type == ActionType.LOG:
                    self._execute_log(action, event, rule)
            except Exception as e:
                logger.error(f"Failed to execute action {action.type} for rule {rule.id}: {e}")

    async def _execute_webhook(self, action: RuleAction, event: Event, rule: Rule):
        """Execute webhook action"""
        url = action.config.get("url")
        method = action.config.get("method", "POST")
        headers = action.config.get("headers", {})

        if not url:
            logger.warning("Webhook action missing URL")
            return

        payload = {
            "event_id": event.id,
            "event_type": event.type,
            "timestamp": event.timestamp.isoformat(),
            "data": event.data,
            "rule_id": rule.id,
            "rule_name": rule.name,
        }

        async with create_traced_async_client() as client:
            response = await client.request(method, url, json=payload, headers=headers)
            response.raise_for_status()
            logger.info(f"Webhook sent to {url}: {response.status_code}")

    def _execute_log(self, action: RuleAction, event: Event, rule: Rule):
        """Execute log action"""
        level = action.config.get("level", "INFO").upper()
        message = action.config.get("message", f"Rule matched event {event.id}")

        log_func = getattr(logger, level.lower(), logger.info)
        log_func(f"[RuleEngine] {message} | Rule: {rule.name} ({rule.id}) | Event: {event.type}")


# Global instance
rule_engine = EventTriggerRuleEngine()
