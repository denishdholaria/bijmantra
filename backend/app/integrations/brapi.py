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
        # Since this adapter doesn't have access to a local data repository directly,
        # and 'sync' implies automatic synchronization, we can't fully implement
        # an automatic push without a data source.
        #
        # However, the public `push_data` method is available for manual pushing.
        return SyncResult(
            success=False,
            errors=["Automatic sync push not implemented. Use push_data() manually."],
        )
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers including auth if configured."""
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make a request to the BrAPI server.

        Args:
            method: HTTP method (GET, POST, PUT, etc.)
            endpoint: API endpoint (relative to base_url/brapi/v2)
            **kwargs: Additional arguments passed to httpx client (params, json, etc.)

        Returns:
            JSON response body

        Raises:
            httpx.HTTPStatusError: If response status is 4xx or 5xx
        """
        # Ensure endpoint starts with slash if not provided, or handle cleanly
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"

        # Construct full URL
        # Assuming standard BrAPI v2 structure if not specified otherwise
        base_path = "/brapi/v2"
        if endpoint.startswith("/brapi"):
            url = f"{self.config.base_url}{endpoint}"
        else:
            url = f"{self.config.base_url}{base_path}{endpoint}"

        response = await self._client.request(
            method,
            url,
            headers=self._get_headers(),
            **kwargs
        )
        response.raise_for_status()
        return response.json()

    async def push_data(self, data_type: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Push data to BrAPI endpoint.

        Args:
            data_type: Type of data to push (e.g., 'germplasm', 'programs', 'trials')
            data: List of data dictionaries to push

        Returns:
            Response from the server
        """
        endpoint_map = {
            "germplasm": "germplasm",
            "programs": "programs",
            "trials": "trials"
        }

        if data_type not in endpoint_map:
            raise ValueError(f"Unsupported data type: {data_type}. Supported: {list(endpoint_map.keys())}")

        endpoint = endpoint_map[data_type]

        # BrAPI typically accepts a list of objects for POST
        return await self._make_request("POST", endpoint, json=data)

    # BrAPI endpoint methods
    
    async def get_server_info(self) -> Dict[str, Any]:
        """Get server info from BrAPI endpoint."""
        # serverinfo is often at the root of brapi/v2
        response_data = await self._make_request("GET", "serverinfo")
        return response_data.get("result", {})
    
    async def get_programs(self, page: int = 0, page_size: int = 100) -> List[Dict]:
        """Get programs from BrAPI endpoint."""
        params = {"page": page, "pageSize": page_size}
        response_data = await self._make_request("GET", "programs", params=params)
        return response_data.get("result", {}).get("data", [])
    
    async def get_germplasm(self, page: int = 0, page_size: int = 100) -> List[Dict]:
        """Get germplasm from BrAPI endpoint."""
        params = {"page": page, "pageSize": page_size}
        response_data = await self._make_request("GET", "germplasm", params=params)
        return response_data.get("result", {}).get("data", [])
    
    async def get_trials(self, page: int = 0, page_size: int = 100) -> List[Dict]:
        """Get trials from BrAPI endpoint."""
        params = {"page": page, "pageSize": page_size}
        response_data = await self._make_request("GET", "trials", params=params)
        return response_data.get("result", {}).get("data", [])
