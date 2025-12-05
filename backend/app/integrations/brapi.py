"""
BrAPI Integration Adapter

Enables data exchange with other BrAPI-compatible breeding databases.
"""

import httpx
from typing import List, Optional, Dict, Any
from .base import IntegrationAdapter, IntegrationConfig, IntegrationStatus, SyncResult
from .registry import register_adapter


@register_adapter
class BrAPIAdapter(IntegrationAdapter):
    """
    Integration with external BrAPI servers.
    
    Allows importing/exporting data from other breeding databases
    like BMS, BIMS, BreedBase, etc.
    """
    
    id = "brapi"
    name = "BrAPI"
    description = "Connect to BrAPI-compatible breeding databases"
    required_config = ["base_url"]
    optional_config = ["api_key", "username", "password"]
    
    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self._client = httpx.AsyncClient(timeout=config.timeout_seconds)
    
    async def test_connection(self) -> bool:
        """Test connection to BrAPI server."""
        try:
            url = f"{self.config.base_url}/brapi/v2/serverinfo"
            headers = self._get_headers()
            response = await self._client.get(url, headers=headers)
            return response.status_code == 200
        except Exception as e:
            self._last_error = str(e)
            return False
    
    async def get_status(self) -> IntegrationStatus:
        """Get current connection status."""
        if not self.config.base_url:
            return IntegrationStatus.NOT_CONFIGURED
        
        if await self.test_connection():
            return IntegrationStatus.CONNECTED
        
        return IntegrationStatus.ERROR
    
    async def sync(self, direction: str = "pull") -> SyncResult:
        """
        Sync data with external BrAPI server.
        
        Args:
            direction: "pull" to import, "push" to export
        """
        import time
        start = time.time()
        
        try:
            if direction == "pull":
                result = await self._pull_data()
            else:
                result = await self._push_data()
            
            result.duration_ms = (time.time() - start) * 1000
            self._last_sync = result.timestamp
            return result
            
        except Exception as e:
            self._last_error = str(e)
            return SyncResult(
                success=False,
                errors=[str(e)],
                duration_ms=(time.time() - start) * 1000,
            )
    
    async def _pull_data(self) -> SyncResult:
        """Pull data from external BrAPI server."""
        records = 0
        errors = []
        
        # Pull germplasm
        try:
            germplasm = await self.get_germplasm()
            records += len(germplasm)
        except Exception as e:
            errors.append(f"Germplasm pull failed: {e}")
        
        # Pull programs
        try:
            programs = await self.get_programs()
            records += len(programs)
        except Exception as e:
            errors.append(f"Programs pull failed: {e}")
        
        return SyncResult(
            success=len(errors) == 0,
            records_synced=records,
            errors=errors,
        )
    
    async def _push_data(self) -> SyncResult:
        """Push data to external BrAPI server."""
        # TODO: Implement push functionality
        return SyncResult(
            success=False,
            errors=["Push not yet implemented"],
        )
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers including auth if configured."""
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers
    
    # BrAPI endpoint methods
    
    async def get_server_info(self) -> Dict[str, Any]:
        """Get server info from BrAPI endpoint."""
        url = f"{self.config.base_url}/brapi/v2/serverinfo"
        response = await self._client.get(url, headers=self._get_headers())
        response.raise_for_status()
        return response.json().get("result", {})
    
    async def get_programs(self, page: int = 0, page_size: int = 100) -> List[Dict]:
        """Get programs from BrAPI endpoint."""
        url = f"{self.config.base_url}/brapi/v2/programs"
        params = {"page": page, "pageSize": page_size}
        response = await self._client.get(url, params=params, headers=self._get_headers())
        response.raise_for_status()
        return response.json().get("result", {}).get("data", [])
    
    async def get_germplasm(self, page: int = 0, page_size: int = 100) -> List[Dict]:
        """Get germplasm from BrAPI endpoint."""
        url = f"{self.config.base_url}/brapi/v2/germplasm"
        params = {"page": page, "pageSize": page_size}
        response = await self._client.get(url, params=params, headers=self._get_headers())
        response.raise_for_status()
        return response.json().get("result", {}).get("data", [])
    
    async def get_trials(self, page: int = 0, page_size: int = 100) -> List[Dict]:
        """Get trials from BrAPI endpoint."""
        url = f"{self.config.base_url}/brapi/v2/trials"
        params = {"page": page, "pageSize": page_size}
        response = await self._client.get(url, params=params, headers=self._get_headers())
        response.raise_for_status()
        return response.json().get("result", {}).get("data", [])
