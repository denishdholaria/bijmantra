"""
RAKSHAKA Healer - Self-healing response system
Pillar 7: SANJEEVANI (संजीवनी) - Life-giving herb - Recovery & restoration
Pillar 8: VIKASA (विकास) - Evolution - Adapt & improve
"""

import asyncio
import gc
from datetime import datetime, UTC
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum


class HealingStrategy(str, Enum):
    RESTART_SERVICE = "restart_service"
    CLEAR_CACHE = "clear_cache"
    RESET_CONNECTIONS = "reset_connections"
    GARBAGE_COLLECT = "garbage_collect"
    RATE_LIMIT = "rate_limit"
    CIRCUIT_BREAK = "circuit_break"
    SCALE_UP = "scale_up"
    ROLLBACK = "rollback"


class HealingStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class HealingAction:
    id: str
    strategy: HealingStrategy
    anomaly_id: Optional[str]
    status: HealingStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    result: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


class Healer:
    """
    Self-healing response system.
    Executes healing strategies based on detected anomalies.
    """
    
    def __init__(self):
        self._actions: List[HealingAction] = []
        self._action_counter = 0
        self._strategies: Dict[HealingStrategy, Callable] = {
            HealingStrategy.CLEAR_CACHE: self._clear_cache,
            HealingStrategy.GARBAGE_COLLECT: self._garbage_collect,
            HealingStrategy.RESET_CONNECTIONS: self._reset_connections,
            HealingStrategy.RATE_LIMIT: self._apply_rate_limit,
            HealingStrategy.CIRCUIT_BREAK: self._circuit_break,
        }
        
        # Strategy recommendations based on anomaly type
        self._strategy_map = {
            "latency_spike": [HealingStrategy.CLEAR_CACHE, HealingStrategy.RESET_CONNECTIONS],
            "error_rate": [HealingStrategy.CIRCUIT_BREAK, HealingStrategy.RATE_LIMIT],
            "memory_pressure": [HealingStrategy.GARBAGE_COLLECT, HealingStrategy.CLEAR_CACHE],
            "cpu_spike": [HealingStrategy.RATE_LIMIT],
            "connection_pool": [HealingStrategy.RESET_CONNECTIONS],
        }
    
    def get_available_strategies(self) -> List[Dict[str, str]]:
        """Get list of available healing strategies"""
        return [
            {"id": s.value, "name": s.name.replace("_", " ").title(), 
             "description": self._get_strategy_description(s)}
            for s in HealingStrategy
        ]
    
    def _get_strategy_description(self, strategy: HealingStrategy) -> str:
        descriptions = {
            HealingStrategy.RESTART_SERVICE: "Restart a specific service or process",
            HealingStrategy.CLEAR_CACHE: "Clear application and query caches",
            HealingStrategy.RESET_CONNECTIONS: "Reset database connection pool",
            HealingStrategy.GARBAGE_COLLECT: "Force Python garbage collection",
            HealingStrategy.RATE_LIMIT: "Apply temporary rate limiting",
            HealingStrategy.CIRCUIT_BREAK: "Open circuit breaker for failing service",
            HealingStrategy.SCALE_UP: "Request additional resources",
            HealingStrategy.ROLLBACK: "Rollback to previous stable state",
        }
        return descriptions.get(strategy, "No description available")

    def recommend_strategies(self, anomaly_type: str) -> List[HealingStrategy]:
        """Recommend healing strategies for an anomaly type"""
        return self._strategy_map.get(anomaly_type, [HealingStrategy.CLEAR_CACHE])
    
    async def heal(self, strategy: HealingStrategy, anomaly_id: str = None,
                   params: Dict[str, Any] = None) -> HealingAction:
        """Execute a healing strategy"""
        self._action_counter += 1
        action = HealingAction(
            id=f"HEAL-{self._action_counter:06d}",
            strategy=strategy,
            anomaly_id=anomaly_id,
            status=HealingStatus.IN_PROGRESS,
            started_at=datetime.now(UTC),
            details=params or {}
        )
        self._actions.append(action)
        
        try:
            handler = self._strategies.get(strategy)
            if handler:
                result = await handler(params or {})
                action.status = HealingStatus.SUCCESS
                action.result = result
            else:
                action.status = HealingStatus.SKIPPED
                action.result = f"Strategy {strategy.value} not implemented"
        except Exception as e:
            action.status = HealingStatus.FAILED
            action.result = str(e)
        
        action.completed_at = datetime.now(UTC)
        return action
    
    async def _clear_cache(self, params: Dict) -> str:
        """Clear application caches"""
        # In a real implementation, this would clear Redis/Memcached
        # For now, simulate cache clearing
        await asyncio.sleep(0.1)
        return "Cache cleared successfully"
    
    async def _garbage_collect(self, params: Dict) -> str:
        """Force garbage collection"""
        collected = gc.collect()
        return f"Garbage collection completed. {collected} objects collected."
    
    async def _reset_connections(self, params: Dict) -> str:
        """Reset database connection pool"""
        # In a real implementation, this would reset SQLAlchemy pool
        await asyncio.sleep(0.1)
        return "Connection pool reset successfully"

    async def _apply_rate_limit(self, params: Dict) -> str:
        """Apply temporary rate limiting"""
        duration = params.get("duration_seconds", 60)
        limit = params.get("requests_per_second", 10)
        # In a real implementation, this would configure rate limiter
        return f"Rate limit applied: {limit} req/s for {duration}s"
    
    async def _circuit_break(self, params: Dict) -> str:
        """Open circuit breaker for a service"""
        service = params.get("service", "unknown")
        duration = params.get("duration_seconds", 30)
        # In a real implementation, this would open circuit breaker
        return f"Circuit breaker opened for {service} for {duration}s"
    
    def get_healing_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent healing actions"""
        sorted_actions = sorted(self._actions, key=lambda x: x.started_at, reverse=True)
        return [self._action_to_dict(a) for a in sorted_actions[:limit]]
    
    def get_action(self, action_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific healing action"""
        for action in self._actions:
            if action.id == action_id:
                return self._action_to_dict(action)
        return None
    
    def _action_to_dict(self, action: HealingAction) -> Dict[str, Any]:
        return {
            "id": action.id,
            "strategy": action.strategy.value,
            "anomaly_id": action.anomaly_id,
            "status": action.status.value,
            "started_at": action.started_at.isoformat(),
            "completed_at": action.completed_at.isoformat() if action.completed_at else None,
            "duration_ms": int((action.completed_at - action.started_at).total_seconds() * 1000) 
                          if action.completed_at else None,
            "result": action.result,
            "details": action.details
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get healing statistics"""
        total = len(self._actions)
        success = sum(1 for a in self._actions if a.status == HealingStatus.SUCCESS)
        failed = sum(1 for a in self._actions if a.status == HealingStatus.FAILED)
        
        return {
            "total_actions": total,
            "successful": success,
            "failed": failed,
            "success_rate": round(success / total * 100, 1) if total > 0 else 100,
            "by_strategy": self._count_by_strategy()
        }
    
    def _count_by_strategy(self) -> Dict[str, int]:
        counts = {}
        for action in self._actions:
            key = action.strategy.value
            counts[key] = counts.get(key, 0) + 1
        return counts


# Singleton instance
healer = Healer()
