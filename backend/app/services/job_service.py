"""
Job Service - Abstraction for background job management

Uses Redis when available, falls back to in-memory storage.
All jobs have TTL (Time To Live) and auto-expire.

Key patterns:
- compute:job:{job_id} - Compute job status
- search:result:{search_id} - Search result cache
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, UTC
from enum import Enum
import uuid

from app.core.redis import redis_client, _fallback

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job status enum"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobService:
    """
    Service for managing background jobs with Redis/fallback support.
    
    Features:
    - Automatic TTL (1 hour default for jobs)
    - Redis when available, in-memory fallback
    - JSON serialization for complex data
    """
    
    # Key prefixes
    COMPUTE_JOB_PREFIX = "compute:job:"
    SEARCH_RESULT_PREFIX = "search:result:"
    
    # TTL settings (in seconds)
    JOB_TTL = 3600  # 1 hour
    SEARCH_TTL = 1800  # 30 minutes
    
    # ============================================
    # COMPUTE JOBS
    # ============================================
    
    async def create_job(
        self,
        job_type: str = "compute",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new job and return job_id.
        
        Args:
            job_type: Type of job (compute, export, etc.)
            metadata: Additional job metadata
            
        Returns:
            job_id: Unique job identifier
        """
        job_id = str(uuid.uuid4())
        job_data = {
            "job_id": job_id,
            "job_type": job_type,
            "status": JobStatus.PENDING.value,
            "progress": 0.0,
            "result": None,
            "error": None,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
            "completed_at": None,
            "metadata": metadata or {}
        }
        
        key = f"{self.COMPUTE_JOB_PREFIX}{job_id}"
        
        if redis_client.is_available:
            await redis_client.set(key, job_data, ttl_seconds=self.JOB_TTL)
        else:
            _fallback.set(key, job_data, ttl_seconds=self.JOB_TTL)
        
        logger.info(f"Created job {job_id} (type={job_type})")
        return job_id
    
    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job by ID.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job data dict or None if not found/expired
        """
        key = f"{self.COMPUTE_JOB_PREFIX}{job_id}"
        
        if redis_client.is_available:
            return await redis_client.get(key)
        else:
            return _fallback.get(key)
    
    async def update_job(
        self,
        job_id: str,
        status: Optional[JobStatus] = None,
        progress: Optional[float] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> bool:
        """
        Update job status/progress.
        
        Args:
            job_id: Job identifier
            status: New status
            progress: Progress (0.0 to 1.0)
            result: Job result data
            error: Error message if failed
            
        Returns:
            True if updated, False if job not found
        """
        job = await self.get_job(job_id)
        if not job:
            return False
        
        if status:
            job["status"] = status.value
        if progress is not None:
            job["progress"] = progress
        if result is not None:
            job["result"] = result
        if error is not None:
            job["error"] = error
        
        job["updated_at"] = datetime.now(UTC).isoformat()
        
        if status in [JobStatus.COMPLETED, JobStatus.FAILED]:
            job["completed_at"] = datetime.now(UTC).isoformat()
        
        key = f"{self.COMPUTE_JOB_PREFIX}{job_id}"
        
        if redis_client.is_available:
            await redis_client.set(key, job, ttl_seconds=self.JOB_TTL)
        else:
            _fallback.set(key, job, ttl_seconds=self.JOB_TTL)
        
        return True
    
    async def delete_job(self, job_id: str) -> bool:
        """Delete a job."""
        key = f"{self.COMPUTE_JOB_PREFIX}{job_id}"
        
        if redis_client.is_available:
            return await redis_client.delete(key)
        else:
            return _fallback.delete(key)
    
    async def list_jobs(self, job_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all active jobs.
        
        Args:
            job_type: Filter by job type
            
        Returns:
            List of job data dicts
        """
        pattern = f"{self.COMPUTE_JOB_PREFIX}*"
        jobs = []
        
        if redis_client.is_available:
            keys = await redis_client.keys(pattern)
            for key in keys:
                job = await redis_client.get(key)
                if job:
                    if job_type is None or job.get("job_type") == job_type:
                        jobs.append(job)
        else:
            keys = _fallback.keys(pattern)
            for key in keys:
                job = _fallback.get(key)
                if job:
                    if job_type is None or job.get("job_type") == job_type:
                        jobs.append(job)
        
        return jobs
    
    # ============================================
    # SEARCH RESULT CACHE
    # ============================================
    
    async def cache_search_result(
        self,
        search_type: str,
        request_data: Dict[str, Any],
        results: List[Dict[str, Any]]
    ) -> str:
        """
        Cache search results and return search_id.
        
        Args:
            search_type: Type of search (programs, germplasm, etc.)
            request_data: Original search request
            results: Search results
            
        Returns:
            search_id: Unique search result identifier
        """
        search_id = str(uuid.uuid4())
        cache_data = {
            "search_id": search_id,
            "search_type": search_type,
            "request": request_data,
            "results": results,
            "total_count": len(results),
            "created_at": datetime.now(UTC).isoformat()
        }
        
        key = f"{self.SEARCH_RESULT_PREFIX}{search_id}"
        
        if redis_client.is_available:
            await redis_client.set(key, cache_data, ttl_seconds=self.SEARCH_TTL)
        else:
            _fallback.set(key, cache_data, ttl_seconds=self.SEARCH_TTL)
        
        logger.debug(f"Cached search result {search_id} (type={search_type}, count={len(results)})")
        return search_id
    
    async def get_search_result(self, search_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached search result by ID.
        
        Args:
            search_id: Search result identifier
            
        Returns:
            Cached search data or None if not found/expired
        """
        key = f"{self.SEARCH_RESULT_PREFIX}{search_id}"
        
        if redis_client.is_available:
            return await redis_client.get(key)
        else:
            return _fallback.get(key)
    
    async def delete_search_result(self, search_id: str) -> bool:
        """Delete a cached search result."""
        key = f"{self.SEARCH_RESULT_PREFIX}{search_id}"
        
        if redis_client.is_available:
            return await redis_client.delete(key)
        else:
            return _fallback.delete(key)
    
    # ============================================
    # STATISTICS
    # ============================================
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get job service statistics."""
        jobs = await self.list_jobs()
        
        stats = {
            "total_jobs": len(jobs),
            "pending": sum(1 for j in jobs if j.get("status") == JobStatus.PENDING.value),
            "running": sum(1 for j in jobs if j.get("status") == JobStatus.RUNNING.value),
            "completed": sum(1 for j in jobs if j.get("status") == JobStatus.COMPLETED.value),
            "failed": sum(1 for j in jobs if j.get("status") == JobStatus.FAILED.value),
            "redis_available": redis_client.is_available,
            "storage_backend": "redis" if redis_client.is_available else "in-memory"
        }
        
        return stats


# Singleton instance
job_service = JobService()
