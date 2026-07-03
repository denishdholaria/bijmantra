"""
CHAITANYA (चैतन्य) - The Orchestrator / Consciousness

Central coordination between RAKSHAKA (healing) and PRAHARI (defense).
Provides unified system awareness and adaptive response.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from app.modules.ai.services.orchestrator_state import OrchestratorMissionStateService


logger = logging.getLogger(__name__)

_CHAITANYA_OBJECTIVE_PREFIX = "CHAITANYA posture transition: "
_CHAITANYA_MANUAL_PREFIX = "Manual posture override: "
_CHAITANYA_AUTO_PREFIX = "Automatic posture transition: "
_CHAITANYA_PRODUCER_KEY = "chaitanya"
_CHAITANYA_SOURCE_RE = re.compile(
    r"^(?P<prefix>Manual posture override|Automatic posture transition): "
    r"(?P<from>[a-z]+) -> (?P<to>[a-z]+)\. ?(?P<reason>.*)$"
)
_CHAITANYA_ACTION_SUMMARY_RE = re.compile(
    r"^System=(?P<system>[^;]+); action=(?P<action>[^;]+); result=(?P<result>.*)$"
)


class PostureLevel(StrEnum):
    """System security posture levels."""
    NORMAL = "normal"  # Business as usual
    ELEVATED = "elevated"  # Increased monitoring
    HIGH = "high"  # Active threats detected
    SEVERE = "severe"  # Under attack, maximum defense
    LOCKDOWN = "lockdown"  # Emergency mode, minimal operations


@dataclass
class SystemPosture:
    """Current system security and health posture."""
    level: PostureLevel
    health_score: float  # 0-100
    security_score: float  # 0-100
    overall_score: float  # 0-100
    active_threats: int
    active_anomalies: int
    blocked_ips: int
    last_incident: datetime | None
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "level": self.level.value,
            "health_score": self.health_score,
            "security_score": self.security_score,
            "overall_score": self.overall_score,
            "active_threats": self.active_threats,
            "active_anomalies": self.active_anomalies,
            "blocked_ips": self.blocked_ips,
            "last_incident": self.last_incident.isoformat() if self.last_incident else None,
            "recommendations": self.recommendations,
        }


@dataclass
class OrchestratedAction:
    """Record of an orchestrated action across systems."""
    id: str
    timestamp: datetime
    trigger: str  # What triggered this action
    systems_involved: list[str]  # rakshaka, prahari, etc.
    actions_taken: list[dict[str, Any]]
    posture_before: PostureLevel
    posture_after: PostureLevel
    success: bool
    notes: str = ""


class Chaitanya:
    """
    CHAITANYA - Central Orchestration Engine.

    Coordinates RAKSHAKA (self-healing) and PRAHARI (defense) systems.
    Maintains unified awareness of system health and security.
    """

    def __init__(self):
        self._current_posture = PostureLevel.NORMAL
        self._posture_history: list[dict] = []
        self._orchestrated_actions: list[OrchestratedAction] = []
        self._action_counter = 0
        self._last_assessment: datetime | None = None
        self._auto_response_enabled = True

        # Posture escalation thresholds
        self._thresholds = {
            "elevated": {"threats": 1, "anomalies": 3, "security_score": 70},
            "high": {"threats": 3, "anomalies": 5, "security_score": 50},
            "severe": {"threats": 5, "anomalies": 10, "security_score": 30},
            "lockdown": {"threats": 10, "anomalies": 20, "security_score": 10},
        }

    @staticmethod
    def _priority_for_posture(level: PostureLevel) -> str:
        priorities = {
            PostureLevel.NORMAL: "p3",
            PostureLevel.ELEVATED: "p2",
            PostureLevel.HIGH: "p1",
            PostureLevel.SEVERE: "p0",
            PostureLevel.LOCKDOWN: "p0",
        }
        return priorities[level]

    @staticmethod
    def _posture_source_request(old: PostureLevel, new: PostureLevel, *, reason: str, manual: bool) -> str:
        prefix = "Manual posture override" if manual else "Automatic posture transition"
        return f"{prefix}: {old.value} -> {new.value}. {reason}".strip()

    async def _record_mission_state(
        self,
        *,
        old: PostureLevel,
        new: PostureLevel,
        reason: str,
        manual: bool,
        actions_taken: list[dict[str, Any]],
        mission_state: "OrchestratorMissionStateService" | None,
    ) -> None:
        if mission_state is None:
            return

        from app.modules.ai.services.orchestrator_state import SubtaskStatus, VerificationResult

        try:
            mission = await mission_state.register_mission(
                objective=f"CHAITANYA posture transition: {old.value} -> {new.value}",
                owner="OmShriMaatreNamaha",
                priority=self._priority_for_posture(new),
                producer_key=_CHAITANYA_PRODUCER_KEY,
                source_request=self._posture_source_request(old, new, reason=reason, manual=manual),
            )
            posture_evidence = await mission_state.record_evidence(
                mission_id=mission.id,
                kind="security_posture",
                source_path="backend/app/modules/ai/services/chaitanya/orchestrator.py",
                evidence_class="runtime_posture_transition",
                summary=(
                    f"CHAITANYA posture changed from {old.value} to {new.value}. "
                    f"Manual={manual}. Reason: {reason}"
                ),
            )
            await mission_state.record_decision_note(
                mission_id=mission.id,
                decision_class="posture_transition",
                rationale=(
                    f"Recorded CHAITANYA posture transition from {old.value} to {new.value}. "
                    f"Reason: {reason}"
                ),
                authority_source="CHAITANYA",
            )

            if actions_taken:
                subtask = await mission_state.add_subtask(
                    mission_id=mission.id,
                    title=f"Execute CHAITANYA responses for {new.value} posture",
                    owner_role="CHAITANYA",
                )
                for system_name in sorted({item["system"] for item in actions_taken}):
                    await mission_state.assign_subtask(
                        subtask_id=subtask.id,
                        assigned_role=system_name.upper(),
                        handoff_reason=(
                            f"Triggered by CHAITANYA posture transition {old.value} -> {new.value}"
                        ),
                    )
                for item in actions_taken:
                    await mission_state.record_evidence(
                        subtask_id=subtask.id,
                        kind="orchestrated_action",
                        source_path="backend/app/modules/ai/services/chaitanya/orchestrator.py",
                        evidence_class="runtime_action",
                        summary=(
                            f"System={item['system']}; action={item['action']}; result={item['result']}"
                        ),
                    )
                await mission_state.record_verification_run(
                    subject_id=subtask.id,
                    verification_type="chaitanya_auto_response",
                    result=VerificationResult.PASSED,
                    evidence_ref=posture_evidence.id,
                )
                await mission_state.update_subtask_status(subtask.id, SubtaskStatus.COMPLETED)

            await mission_state.complete_mission(
                mission.id,
                (
                    f"CHAITANYA posture transition recorded for {old.value} -> {new.value}"
                    if not actions_taken
                    else f"CHAITANYA posture transition and {len(actions_taken)} orchestrated action(s) recorded"
                ),
            )
        except Exception:
            logger.exception("Failed to persist CHAITANYA mission-state transition")

    def _generate_action_id(self) -> str:
        self._action_counter += 1
        return f"ORC-{datetime.now(UTC).strftime('%Y%m%d')}-{self._action_counter:06d}"

    @staticmethod
    def _parse_chaitanya_transition(source_request: str) -> dict[str, str] | None:
        match = _CHAITANYA_SOURCE_RE.match(source_request)
        if match is None:
            return None
        parsed = match.groupdict()
        return {
            "from": parsed["from"],
            "to": parsed["to"],
            "reason": parsed["reason"],
            "manual": str(parsed["prefix"] == "Manual posture override").lower(),
        }

    @staticmethod
    def _parse_action_summary(summary: str) -> dict[str, str] | None:
        match = _CHAITANYA_ACTION_SUMMARY_RE.match(summary)
        return match.groupdict() if match is not None else None

    @staticmethod
    def _is_chaitanya_mission(mission: Any) -> bool:
        return (
            mission.objective.startswith(_CHAITANYA_OBJECTIVE_PREFIX)
            and Chaitanya._parse_chaitanya_transition(mission.source_request) is not None
        )

    async def _list_chaitanya_snapshots(
        self,
        mission_state: "OrchestratorMissionStateService",
    ) -> list[Any]:
        missions = await mission_state.repository.list_missions()
        relevant = [mission for mission in missions if self._is_chaitanya_mission(mission)]
        relevant.sort(key=lambda item: (item.created_at, item.id))
        snapshots = []
        for mission in relevant:
            snapshots.append(await mission_state.get_mission_snapshot(mission.id))
        return snapshots

    async def _get_chaitanya_snapshot(
        self,
        mission_state: "OrchestratorMissionStateService",
        mission_id: str,
    ) -> Any | None:
        try:
            snapshot = await mission_state.get_mission_snapshot(mission_id)
        except ValueError:
            return None
        if not self._is_chaitanya_mission(snapshot.mission):
            return None
        if self._parse_chaitanya_transition(snapshot.mission.source_request) is None:
            return None
        return snapshot

    @staticmethod
    def _verification_summary(snapshot: Any) -> dict[str, Any]:
        passed = sum(1 for item in snapshot.verification_runs if item.result.value == "passed")
        warned = sum(1 for item in snapshot.verification_runs if item.result.value == "warned")
        failed = sum(1 for item in snapshot.verification_runs if item.result.value == "failed")
        last_verified_at = max((item.executed_at for item in snapshot.verification_runs), default=None)
        return {
            "passed": passed,
            "warned": warned,
            "failed": failed,
            "last_verified_at": last_verified_at.isoformat() if last_verified_at else None,
        }

    def _mission_projection(self, snapshot: Any) -> dict[str, Any]:
        parsed = self._parse_chaitanya_transition(snapshot.mission.source_request)
        if parsed is None:
            raise ValueError(f"Mission {snapshot.mission.id} is not a CHAITANYA mission")

        verification = self._verification_summary(snapshot)
        blocker_count = len(snapshot.blockers)
        escalation_needed = any(item.escalation_needed for item in snapshot.blockers)
        completed_subtasks = sum(1 for item in snapshot.subtasks if item.status.value == "completed")
        action_items = self._project_durable_actions([snapshot], limit=100)
        systems_involved = action_items[0]["systems_involved"] if action_items else []

        return {
            "mission_id": snapshot.mission.id,
            "display_title": f"Posture {parsed['from']} -> {parsed['to']}",
            "status": snapshot.mission.status.value,
            "priority": snapshot.mission.priority,
            "owner_role": snapshot.mission.owner,
            "created_at": snapshot.mission.created_at.isoformat(),
            "updated_at": snapshot.mission.updated_at.isoformat(),
            "posture_before": parsed["from"],
            "posture_after": parsed["to"],
            "manual": parsed["manual"] == "true",
            "subtask_total": len(snapshot.subtasks),
            "subtask_completed": completed_subtasks,
            "action_count": sum(1 for item in snapshot.evidence_items if item.kind == "orchestrated_action"),
            "systems_involved": systems_involved,
            "blocker_count": blocker_count,
            "escalation_needed": escalation_needed,
            "verification": verification,
            "final_summary": snapshot.mission.final_summary,
        }

    def _mission_detail_projection(self, snapshot: Any) -> dict[str, Any]:
        summary = self._mission_projection(snapshot)
        assignments = sorted(snapshot.assignments, key=lambda item: (item.started_at, item.id))
        subtasks = sorted(snapshot.subtasks, key=lambda item: (item.created_at, item.id))
        action_items = self._project_durable_actions([snapshot], limit=100)
        verification = self._verification_summary(snapshot)

        return {
            **summary,
            "subtasks": [
                {
                    "id": item.id,
                    "title": item.title,
                    "status": item.status.value,
                    "owner_role": item.owner_role,
                }
                for item in subtasks
            ],
            "assignments": [
                {
                    "id": item.id,
                    "assigned_role": item.assigned_role,
                    "started_at": item.started_at.isoformat(),
                    "completed_at": item.completed_at.isoformat() if item.completed_at else None,
                }
                for item in assignments
            ],
            "actions": action_items[0]["actions_taken"] if action_items else [],
            "decision_classes": sorted({item.decision_class for item in snapshot.decision_notes}),
            "verification_types": sorted({item.verification_type for item in snapshot.verification_runs}),
            "blocker_types": sorted({item.blocker_type for item in snapshot.blockers}),
            "verification": verification,
        }

    async def list_mission_inspection(
        self,
        mission_state: "OrchestratorMissionStateService",
        *,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        snapshots = await self._list_chaitanya_snapshots(mission_state)
        snapshots.sort(key=lambda item: (item.mission.created_at, item.mission.id), reverse=True)
        return [self._mission_projection(item) for item in snapshots[:limit]]

    async def get_mission_inspection_detail(
        self,
        mission_state: "OrchestratorMissionStateService",
        mission_id: str,
    ) -> dict[str, Any] | None:
        snapshot = await self._get_chaitanya_snapshot(mission_state, mission_id)
        if snapshot is None:
            return None
        return self._mission_detail_projection(snapshot)

    def _project_durable_posture_history(self, snapshots: list[Any], limit: int) -> list[dict[str, Any]]:
        history: list[dict[str, Any]] = []
        for snapshot in snapshots:
            parsed = self._parse_chaitanya_transition(snapshot.mission.source_request)
            if parsed is None:
                continue
            item: dict[str, Any] = {
                "timestamp": snapshot.mission.created_at.isoformat(),
                "from": parsed["from"],
                "to": parsed["to"],
            }
            if parsed["manual"] == "true":
                item["manual"] = True
                item["reason"] = parsed["reason"]
            history.append(item)
        return history[-limit:]

    def _project_durable_actions(self, snapshots: list[Any], limit: int) -> list[dict[str, Any]]:
        actions: list[dict[str, Any]] = []
        for snapshot in snapshots:
            parsed = self._parse_chaitanya_transition(snapshot.mission.source_request)
            if parsed is None:
                continue
            action_evidence = sorted(
                [item for item in snapshot.evidence_items if item.kind == "orchestrated_action"],
                key=lambda item: (item.recorded_at, item.id),
            )
            if not action_evidence:
                continue

            actions_taken: list[dict[str, Any]] = []
            for evidence in action_evidence:
                parsed_action = self._parse_action_summary(evidence.summary)
                if parsed_action is None:
                    continue
                actions_taken.append(
                    {
                        "system": parsed_action["system"],
                        "action": parsed_action["action"],
                        "result": parsed_action["result"],
                    }
                )

            systems_involved = sorted(
                {
                    assignment.assigned_role.lower()
                    for assignment in snapshot.assignments
                }
                or {item["system"] for item in actions_taken}
            )
            actions.append(
                {
                    "id": snapshot.mission.id,
                    "timestamp": action_evidence[0].recorded_at.isoformat(),
                    "trigger": f"posture_change_{parsed['from']}_to_{parsed['to']}",
                    "systems_involved": systems_involved,
                    "actions_taken": actions_taken,
                    "posture_before": parsed["from"],
                    "posture_after": parsed["to"],
                    "success": all(item.result.value == "passed" for item in snapshot.verification_runs)
                    if snapshot.verification_runs
                    else snapshot.mission.status.value == "completed",
                    "notes": snapshot.mission.final_summary or "",
                }
            )
        return actions[-limit:]

    async def assess_posture(
        self,
        mission_state: "OrchestratorMissionStateService" | None = None,
    ) -> SystemPosture:
        """Assess current system posture by querying RAKSHAKA and PRAHARI."""

        # Import here to avoid circular imports
        from app.modules.core.services.prahari import security_observer, threat_analyzer, threat_responder
        from app.modules.core.services.rakshaka import anomaly_detector, health_monitor

        # Get health metrics from RAKSHAKA
        health = health_monitor.get_overall_health()
        anomalies = anomaly_detector.get_active_anomalies()

        # Get security metrics from PRAHARI
        security_stats = security_observer.get_stats()
        threat_stats = threat_analyzer.get_stats()
        response_stats = threat_responder.get_stats()

        # Calculate scores
        health_score = self._calculate_health_score(health)
        security_score = self._calculate_security_score(security_stats, threat_stats)
        overall_score = (health_score * 0.4 + security_score * 0.6)

        # Count active issues
        active_threats = threat_stats.get("assessments_24h", 0)
        active_anomalies = len(anomalies)
        blocked_ips = response_stats.get("blocked_ips", 0)

        # Determine posture level
        posture_level = self._determine_posture_level(
            active_threats, active_anomalies, security_score
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            health, security_stats, threat_stats, posture_level
        )

        # Find last incident
        recent_events = security_observer.get_recent_events(limit=1)
        last_incident = None
        if recent_events:
            last_incident = datetime.fromisoformat(recent_events[0]["timestamp"])

        posture = SystemPosture(
            level=posture_level,
            health_score=round(health_score, 1),
            security_score=round(security_score, 1),
            overall_score=round(overall_score, 1),
            active_threats=active_threats,
            active_anomalies=active_anomalies,
            blocked_ips=blocked_ips,
            last_incident=last_incident,
            recommendations=recommendations,
        )

        # Update posture if changed
        if posture_level != self._current_posture:
            await self._handle_posture_change(
                self._current_posture,
                posture_level,
                mission_state=mission_state,
            )
            self._current_posture = posture_level

        self._last_assessment = datetime.now(UTC)
        return posture

    def _calculate_health_score(self, health: dict) -> float:
        """Calculate health score from RAKSHAKA metrics."""
        score = 100.0

        # CPU impact
        cpu = health.get("system", {}).get("cpu", {}).get("percent", 0)
        if cpu > 90:
            score -= 30
        elif cpu > 70:
            score -= 15

        # Memory impact
        mem = health.get("system", {}).get("memory", {}).get("percent", 0)
        if mem > 90:
            score -= 30
        elif mem > 70:
            score -= 15

        # API latency impact
        latency = health.get("api", {}).get("avg_latency_ms", 0)
        if latency > 1000:
            score -= 20
        elif latency > 500:
            score -= 10

        # Error rate impact
        error_rate = health.get("api", {}).get("error_rate_percent", 0)
        if error_rate > 5:
            score -= 25
        elif error_rate > 1:
            score -= 10

        return max(0, score)

    def _calculate_security_score(self, security_stats: dict, threat_stats: dict) -> float:
        """Calculate security score from PRAHARI metrics."""
        score = 100.0

        # Events in last hour
        events_hour = security_stats.get("events_last_hour", 0)
        if events_hour > 50:
            score -= 30
        elif events_hour > 20:
            score -= 15
        elif events_hour > 10:
            score -= 5

        # Severity distribution
        by_severity = security_stats.get("by_severity", {})
        score -= by_severity.get("critical", 0) * 15
        score -= by_severity.get("high", 0) * 8
        score -= by_severity.get("medium", 0) * 3

        # Threat assessments
        threats_24h = threat_stats.get("assessments_24h", 0)
        if threats_24h > 20:
            score -= 25
        elif threats_24h > 10:
            score -= 15
        elif threats_24h > 5:
            score -= 5

        return max(0, score)

    def _determine_posture_level(self, threats: int, anomalies: int,
                                 security_score: float) -> PostureLevel:
        """Determine appropriate posture level based on metrics."""

        if (threats >= self._thresholds["lockdown"]["threats"] or
            security_score <= self._thresholds["lockdown"]["security_score"]):
            return PostureLevel.LOCKDOWN

        if (threats >= self._thresholds["severe"]["threats"] or
            anomalies >= self._thresholds["severe"]["anomalies"] or
            security_score <= self._thresholds["severe"]["security_score"]):
            return PostureLevel.SEVERE

        if (threats >= self._thresholds["high"]["threats"] or
            anomalies >= self._thresholds["high"]["anomalies"] or
            security_score <= self._thresholds["high"]["security_score"]):
            return PostureLevel.HIGH

        if (threats >= self._thresholds["elevated"]["threats"] or
            anomalies >= self._thresholds["elevated"]["anomalies"] or
            security_score <= self._thresholds["elevated"]["security_score"]):
            return PostureLevel.ELEVATED

        return PostureLevel.NORMAL

    def _generate_recommendations(self, health: dict, security_stats: dict,
                                  threat_stats: dict, posture: PostureLevel) -> list[str]:
        """Generate actionable recommendations."""
        recommendations = []

        # Health-based recommendations
        if health.get("system", {}).get("cpu", {}).get("percent", 0) > 80:
            recommendations.append("Consider scaling compute resources - CPU usage high")

        if health.get("system", {}).get("memory", {}).get("percent", 0) > 80:
            recommendations.append("Memory pressure detected - review memory usage")

        if health.get("api", {}).get("error_rate_percent", 0) > 2:
            recommendations.append("Elevated error rate - investigate failing endpoints")

        # Security-based recommendations
        if security_stats.get("suspicious_ips_count", 0) > 5:
            recommendations.append("Multiple suspicious IPs detected - review and block if needed")

        by_severity = security_stats.get("by_severity", {})
        if by_severity.get("critical", 0) > 0:
            recommendations.append("CRITICAL security events detected - immediate review required")

        # Posture-based recommendations
        if posture == PostureLevel.ELEVATED:
            recommendations.append("Elevated posture - increase monitoring frequency")
        elif posture == PostureLevel.HIGH:
            recommendations.append("High alert - consider enabling additional security controls")
        elif posture == PostureLevel.SEVERE:
            recommendations.append("Severe threat level - activate incident response team")
        elif posture == PostureLevel.LOCKDOWN:
            recommendations.append("LOCKDOWN - restrict access to essential operations only")

        return recommendations[:5]  # Limit to top 5

    async def _handle_posture_change(
        self,
        old: PostureLevel,
        new: PostureLevel,
        *,
        mission_state: "OrchestratorMissionStateService" | None = None,
    ):
        """Handle posture level change with appropriate actions."""

        logger.warning(f"Posture change: {old.value} -> {new.value}")

        self._posture_history.append({
            "timestamp": datetime.now(UTC).isoformat(),
            "from": old.value,
            "to": new.value,
        })

        # Auto-response based on posture escalation
        if not self._auto_response_enabled:
            return

        actions_taken = []

        if new in [PostureLevel.SEVERE, PostureLevel.LOCKDOWN]:
            # Trigger RAKSHAKA healing
            from app.modules.core.services.rakshaka import healer
            from app.modules.core.services.rakshaka.healer import HealingStrategy

            action = await healer.heal(HealingStrategy.RATE_LIMIT, params={
                "duration_seconds": 300,
                "requests_per_second": 5,
            })
            actions_taken.append({"system": "rakshaka", "action": "rate_limit", "result": action.result})

        if new == PostureLevel.LOCKDOWN:
            # Additional lockdown measures
            logger.critical("LOCKDOWN MODE ACTIVATED")
            actions_taken.append({"system": "chaitanya", "action": "lockdown_alert", "result": "Alert sent"})

        # Record orchestrated action
        if actions_taken:
            self._orchestrated_actions.append(OrchestratedAction(
                id=self._generate_action_id(),
                timestamp=datetime.now(UTC),
                trigger=f"posture_change_{old.value}_to_{new.value}",
                systems_involved=list({a["system"] for a in actions_taken}),
                actions_taken=actions_taken,
                posture_before=old,
                posture_after=new,
                success=True,
            ))

        await self._record_mission_state(
            old=old,
            new=new,
            reason="Posture reassessment triggered by CHAITANYA runtime",
            manual=False,
            actions_taken=actions_taken,
            mission_state=mission_state,
        )

    async def handle_security_event(
        self,
        event_data: dict,
        mission_state: "OrchestratorMissionStateService" | None = None,
    ) -> dict[str, Any]:
        """
        Handle a security event by coordinating PRAHARI analysis and response.
        This is the main entry point for security event processing.
        """
        from app.modules.core.services.prahari import (
            EventSeverity,
            ObservationLayer,
            SecurityEvent,
            security_observer,
            threat_analyzer,
            threat_responder,
        )

        # Create security event
        event = SecurityEvent(
            id=event_data.get("id", security_observer._generate_event_id()),
            timestamp=datetime.now(UTC),
            layer=ObservationLayer(event_data.get("layer", "application")),
            event_type=event_data.get("event_type", "unknown"),
            source_ip=event_data.get("source_ip"),
            user_id=event_data.get("user_id"),
            endpoint=event_data.get("endpoint"),
            details=event_data.get("details", {}),
            severity=EventSeverity(event_data.get("severity", "low")),
        )

        # Analyze threat
        assessment = await threat_analyzer.analyze(event)

        # Auto-respond if enabled and threat is significant
        responses = []
        if self._auto_response_enabled and assessment.confidence_score >= 50:
            responses = await threat_responder.respond(assessment)

        # Re-assess posture
        posture = await self.assess_posture(mission_state=mission_state)

        return {
            "event_id": event.id,
            "assessment": assessment.to_dict(),
            "responses": [r.to_dict() for r in responses],
            "current_posture": posture.to_dict(),
        }

    async def handle_health_anomaly(
        self,
        anomaly_data: dict,
        mission_state: "OrchestratorMissionStateService" | None = None,
    ) -> dict[str, Any]:
        """
        Handle a health anomaly by coordinating RAKSHAKA healing.
        """
        from app.modules.core.services.rakshaka import healer

        anomaly_type = anomaly_data.get("type", "unknown")

        # Get recommended healing strategies
        strategies = healer.recommend_strategies(anomaly_type)

        # Execute healing if auto-response enabled
        healing_results = []
        if self._auto_response_enabled and strategies:
            for strategy in strategies[:2]:  # Limit to 2 strategies
                action = await healer.heal(strategy, anomaly_data.get("id"))
                healing_results.append(healer._action_to_dict(action))

        # Re-assess posture
        posture = await self.assess_posture(mission_state=mission_state)

        return {
            "anomaly_type": anomaly_type,
            "recommended_strategies": [s.value for s in strategies],
            "healing_actions": healing_results,
            "current_posture": posture.to_dict(),
        }

    async def set_posture(
        self,
        level: PostureLevel,
        reason: str = "",
        mission_state: "OrchestratorMissionStateService" | None = None,
    ) -> dict[str, Any]:
        """Manually set system posture level."""
        old = self._current_posture
        self._current_posture = level

        self._posture_history.append({
            "timestamp": datetime.now(UTC).isoformat(),
            "from": old.value,
            "to": level.value,
            "manual": True,
            "reason": reason,
        })

        logger.warning(f"Manual posture change: {old.value} -> {level.value}. Reason: {reason}")

        await self._record_mission_state(
            old=old,
            new=level,
            reason=reason or "Manual override",
            manual=True,
            actions_taken=[],
            mission_state=mission_state,
        )

        return {
            "previous": old.value,
            "current": level.value,
            "reason": reason,
        }

    def set_auto_response(self, enabled: bool) -> dict[str, Any]:
        """Enable or disable automatic response."""
        old = self._auto_response_enabled
        self._auto_response_enabled = enabled
        return {
            "auto_response_enabled": enabled,
            "previous": old,
        }

    async def get_posture_history(
        self,
        limit: int = 50,
        mission_state: "OrchestratorMissionStateService" | None = None,
    ) -> list[dict]:
        """Get posture change history."""
        if mission_state is not None:
            snapshots = await self._list_chaitanya_snapshots(mission_state)
            durable = self._project_durable_posture_history(snapshots, limit)
            if durable:
                return durable
        return self._posture_history[-limit:]

    async def get_orchestrated_actions(
        self,
        limit: int = 50,
        mission_state: "OrchestratorMissionStateService" | None = None,
    ) -> list[dict]:
        """Get history of orchestrated actions."""
        if mission_state is not None:
            snapshots = await self._list_chaitanya_snapshots(mission_state)
            durable = self._project_durable_actions(snapshots, limit)
            if durable:
                return durable
        return [
            {
                "id": a.id,
                "timestamp": a.timestamp.isoformat(),
                "trigger": a.trigger,
                "systems_involved": a.systems_involved,
                "actions_taken": a.actions_taken,
                "posture_before": a.posture_before.value,
                "posture_after": a.posture_after.value,
                "success": a.success,
                "notes": a.notes,
            }
            for a in self._orchestrated_actions[-limit:]
        ]

    def get_config(self) -> dict[str, Any]:
        """Get current orchestrator configuration."""
        return {
            "auto_response_enabled": self._auto_response_enabled,
            "current_posture": self._current_posture.value,
            "thresholds": self._thresholds,
            "last_assessment": self._last_assessment.isoformat() if self._last_assessment else None,
        }

    def update_thresholds(self, thresholds: dict[str, dict]) -> dict[str, Any]:
        """Update posture escalation thresholds."""
        for level, values in thresholds.items():
            if level in self._thresholds:
                self._thresholds[level].update(values)
        return {"thresholds": self._thresholds}

    async def get_unified_dashboard(
        self,
        mission_state: "OrchestratorMissionStateService" | None = None,
    ) -> dict[str, Any]:
        """Get unified dashboard data from all systems."""
        from app.modules.core.services.prahari import security_observer, threat_analyzer, threat_responder
        from app.modules.core.services.rakshaka import anomaly_detector, healer, health_monitor

        posture = await self.assess_posture(mission_state=mission_state)

        return {
            "posture": posture.to_dict(),
            "health": {
                "overall": health_monitor.get_overall_health(),
                "anomalies": anomaly_detector.get_active_anomalies()[:5],
                "healing_stats": healer.get_stats(),
            },
            "security": {
                "events": security_observer.get_recent_events(limit=10),
                "threat_stats": threat_analyzer.get_stats(),
                "response_stats": threat_responder.get_stats(),
                "blocked_ips": threat_responder.get_blocked_ips()[:5],
            },
            "orchestration": {
                "recent_actions": await self.get_orchestrated_actions(limit=5, mission_state=mission_state),
                "posture_history": await self.get_posture_history(limit=5, mission_state=mission_state),
                "config": self.get_config(),
            },
        }


# Global instance
chaitanya = Chaitanya()
