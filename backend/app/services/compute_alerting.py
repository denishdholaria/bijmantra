"""
Compute Alerting Service
Monitors compute metrics and triggers alerts

Features:
- Threshold-based alerting
- Sentry integration for critical alerts
- Alert history tracking
- Configurable alert rules
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

try:
    import sentry_sdk
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

from app.core.redis import redis_client
from app.services.task_queue import task_queue

logger = logging.getLogger(__name__)


class AlertRule:
    """Alert rule definition"""
    
    def __init__(
        self,
        rule_id: str,
        name: str,
        metric: str,
        threshold: float,
        operator: str,  # "gt" | "lt" | "eq"
        severity: str,  # "warning" | "critical"
        message_template: str,
        cooldown_minutes: int = 30,
    ):
        self.rule_id = rule_id
        self.name = name
        self.metric = metric
        self.threshold = threshold
        self.operator = operator
        self.severity = severity
        self.message_template = message_template
        self.cooldown_minutes = cooldown_minutes
    
    def check(self, current_value: float) -> bool:
        """Check if alert condition is met"""
        if self.operator == "gt":
            return current_value > self.threshold
        elif self.operator == "lt":
            return current_value < self.threshold
        elif self.operator == "eq":
            return current_value == self.threshold
        return False
    
    def format_message(self, current_value: float) -> str:
        """Format alert message"""
        return self.message_template.format(
            current_value=current_value,
            threshold=self.threshold,
        )


class ComputeAlertingService:
    """
    Service for monitoring compute metrics and triggering alerts
    
    Alert Rules (from design.md):
    - Compute job failure rate > 5%
    - Queue depth > 1000 jobs
    - Worker utilization < 20% (underutilized)
    - Worker utilization > 90% (overloaded)
    """
    
    def __init__(self):
        self.enabled = True
        self.sentry_enabled = SENTRY_AVAILABLE
        
        # Define alert rules
        self.rules = [
            AlertRule(
                rule_id="compute_failure_rate_high",
                name="High Compute Failure Rate",
                metric="compute_job_failure_rate",
                threshold=0.05,  # 5%
                operator="gt",
                severity="critical",
                message_template="Compute job failure rate is {current_value:.1%} (threshold: {threshold:.1%})",
                cooldown_minutes=30,
            ),
            AlertRule(
                rule_id="queue_depth_high",
                name="High Queue Depth",
                metric="queue_depth",
                threshold=1000,
                operator="gt",
                severity="warning",
                message_template="Queue depth is {current_value:.0f} jobs (threshold: {threshold:.0f})",
                cooldown_minutes=15,
            ),
            AlertRule(
                rule_id="worker_utilization_low",
                name="Low Worker Utilization",
                metric="worker_utilization",
                threshold=0.20,  # 20%
                operator="lt",
                severity="warning",
                message_template="Worker utilization is {current_value:.1%} (threshold: {threshold:.1%})",
                cooldown_minutes=60,
            ),
            AlertRule(
                rule_id="worker_utilization_high",
                name="High Worker Utilization",
                metric="worker_utilization",
                threshold=0.90,  # 90%
                operator="gt",
                severity="critical",
                message_template="Worker utilization is {current_value:.1%} (threshold: {threshold:.1%})",
                cooldown_minutes=15,
            ),
        ]
    
    async def check_alerts(self) -> list[dict[str, Any]]:
        """
        Check all alert rules and trigger alerts if needed
        
        Returns:
            List of triggered alerts
        """
        if not self.enabled:
            return []
        
        triggered_alerts = []
        
        # Get current metrics
        metrics = await self._get_current_metrics()
        
        # Check each rule
        for rule in self.rules:
            metric_value = metrics.get(rule.metric)
            
            if metric_value is None:
                continue
            
            # Check if alert condition is met
            if rule.check(metric_value):
                # Check cooldown
                if await self._is_in_cooldown(rule.rule_id):
                    continue
                
                # Trigger alert
                alert = await self._trigger_alert(rule, metric_value)
                triggered_alerts.append(alert)
        
        return triggered_alerts
    
    async def _get_current_metrics(self) -> dict[str, float]:
        """Get current compute metrics"""
        metrics = {}
        
        # Get task queue stats
        queue_stats = task_queue.get_stats()
        
        # Calculate failure rate
        total_completed = queue_stats["completed"] + queue_stats["failed"]
        if total_completed > 0:
            failure_rate = queue_stats["failed"] / total_completed
            metrics["compute_job_failure_rate"] = failure_rate
        
        # Queue depth
        metrics["queue_depth"] = queue_stats["queue_size"]
        
        # Worker utilization
        try:
            # Get worker stats from Redis
            light_workers = await self._get_worker_count("light")
            heavy_workers = await self._get_worker_count("heavy")
            gpu_workers = await self._get_worker_count("gpu")
            
            total_workers = light_workers["total"] + heavy_workers["total"] + gpu_workers["total"]
            active_workers = light_workers["active"] + heavy_workers["active"] + gpu_workers["active"]
            
            if total_workers > 0:
                metrics["worker_utilization"] = active_workers / total_workers
        except Exception as e:
            logger.error(f"Error getting worker stats: {e}")
        
        return metrics
    
    async def _get_worker_count(self, worker_type: str) -> dict[str, int]:
        """Get worker count for a specific type"""
        try:
            worker_keys = await redis_client.keys(f"worker:{worker_type}:*")
            total = len(worker_keys)
            
            active = 0
            for key in worker_keys:
                worker_data = await redis_client.get(key)
                if worker_data and worker_data.get("status") == "running":
                    active += 1
            
            return {"total": total, "active": active}
        except Exception:
            return {"total": 0, "active": 0}
    
    async def _is_in_cooldown(self, rule_id: str) -> bool:
        """Check if alert is in cooldown period"""
        try:
            last_triggered = await redis_client.get(f"alert:cooldown:{rule_id}")
            if not last_triggered:
                return False
            
            last_triggered_time = datetime.fromisoformat(last_triggered)
            rule = next((r for r in self.rules if r.rule_id == rule_id), None)
            
            if not rule:
                return False
            
            cooldown_end = last_triggered_time + timedelta(minutes=rule.cooldown_minutes)
            return datetime.now(UTC) < cooldown_end
        except Exception:
            return False
    
    async def _trigger_alert(self, rule: AlertRule, current_value: float) -> dict[str, Any]:
        """Trigger an alert"""
        timestamp = datetime.now(UTC)
        
        alert = {
            "id": f"{rule.rule_id}-{timestamp.timestamp()}",
            "rule_id": rule.rule_id,
            "name": rule.name,
            "severity": rule.severity,
            "metric": rule.metric,
            "threshold": rule.threshold,
            "current_value": current_value,
            "message": rule.format_message(current_value),
            "triggered_at": timestamp.isoformat(),
        }
        
        # Log alert
        log_level = logging.CRITICAL if rule.severity == "critical" else logging.WARNING
        logger.log(log_level, f"[ALERT] {alert['message']}")
        
        # Send to Sentry if critical
        if self.sentry_enabled and rule.severity == "critical":
            sentry_sdk.capture_message(
                f"[CRITICAL ALERT] {alert['message']}",
                level="error",
                extras={
                    "alert_id": alert["id"],
                    "rule_id": rule.rule_id,
                    "metric": rule.metric,
                    "threshold": rule.threshold,
                    "current_value": current_value,
                },
            )
        
        # Store alert in Redis
        try:
            await redis_client.set(
                f"alert:history:{alert['id']}",
                alert,
                ttl_seconds=86400,  # 24 hours
            )
            
            # Set cooldown
            await redis_client.set(
                f"alert:cooldown:{rule.rule_id}",
                timestamp.isoformat(),
                ttl_seconds=rule.cooldown_minutes * 60,
            )
        except Exception as e:
            logger.error(f"Error storing alert: {e}")
        
        return alert
    
    async def get_alert_history(self, hours: int = 24) -> list[dict[str, Any]]:
        """
        Get alert history
        
        Args:
            hours: Number of hours to look back
        
        Returns:
            List of alerts
        """
        try:
            alert_keys = await redis_client.keys("alert:history:*")
            alerts = []
            
            cutoff = datetime.now(UTC) - timedelta(hours=hours)
            
            for key in alert_keys:
                alert = await redis_client.get(key)
                if alert:
                    triggered_at = datetime.fromisoformat(alert["triggered_at"])
                    if triggered_at >= cutoff:
                        alerts.append(alert)
            
            # Sort by triggered_at descending
            alerts.sort(key=lambda a: a["triggered_at"], reverse=True)
            
            return alerts
        except Exception as e:
            logger.error(f"Error getting alert history: {e}")
            return []


# Global alerting service instance
compute_alerting = ComputeAlertingService()


async def run_alert_check_loop():
    """
    Background task to periodically check alerts
    
    Usage:
        # In main.py lifespan
        asyncio.create_task(run_alert_check_loop())
    """
    logger.info("[ComputeAlerting] Starting alert check loop")
    
    while True:
        try:
            alerts = await compute_alerting.check_alerts()
            
            if alerts:
                logger.info(f"[ComputeAlerting] Triggered {len(alerts)} alerts")
            
            # Check every 5 minutes
            await asyncio.sleep(300)
            
        except Exception as e:
            logger.error(f"[ComputeAlerting] Error in alert check loop: {e}")
            await asyncio.sleep(60)


# Import asyncio at the end to avoid circular imports
import asyncio
