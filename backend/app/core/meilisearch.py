"""
Meilisearch Integration for Instant Search
Indexes BrAPI data for typo-tolerant, instant search
"""

import os
from typing import List, Dict, Any, Optional
from meilisearch import Client
from datetime import datetime

# Configuration
MEILISEARCH_HOST = os.getenv('MEILISEARCH_HOST', 'http://localhost:7700')
MEILISEARCH_API_KEY = os.getenv('MEILISEARCH_API_KEY', '')

# Index names
INDEXES = {
    'germplasm': 'germplasm',
    'traits': 'traits',
    'trials': 'trials',
    'locations': 'locations',
    'observations': 'observations',
}

# Index configurations
INDEX_SETTINGS = {
    'germplasm': {
        'searchableAttributes': [
            'germplasmName',
            'accessionNumber',
            'species',
            'genus',
            'subtaxa',
            'synonyms',
            'instituteCode',
            'countryOfOrigin',
        ],
        'filterableAttributes': [
            'species',
            'genus',
            'countryOfOrigin',
            'biologicalStatus',
            'instituteCode',
        ],
        'sortableAttributes': [
            'germplasmName',
            'accessionNumber',
            'createdAt',
        ],
        'displayedAttributes': [
            'germplasmDbId',
            'germplasmName',
            'accessionNumber',
            'species',
            'genus',
            'countryOfOrigin',
            'biologicalStatus',
            'synonyms',
        ],
    },
    'traits': {
        'searchableAttributes': [
            'observationVariableName',
            'trait.traitName',
            'trait.traitDescription',
            'method.methodName',
            'scale.scaleName',
            'ontologyReference.ontologyName',
        ],
        'filterableAttributes': [
            'trait.traitClass',
            'ontologyReference.ontologyName',
        ],
        'sortableAttributes': [
            'observationVariableName',
        ],
    },
    'trials': {
        'searchableAttributes': [
            'trialName',
            'trialDescription',
            'programName',
            'locationName',
        ],
        'filterableAttributes': [
            'programDbId',
            'locationDbId',
            'active',
            'startDate',
            'endDate',
        ],
        'sortableAttributes': [
            'trialName',
            'startDate',
            'endDate',
        ],
    },
    'locations': {
        'searchableAttributes': [
            'locationName',
            'locationType',
            'countryName',
            'instituteName',
        ],
        'filterableAttributes': [
            'countryCode',
            'locationType',
        ],
        'sortableAttributes': [
            'locationName',
        ],
    },
}


class MeilisearchService:
    """Service for managing Meilisearch indexes and search"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self._connected = False
    
    def connect(self) -> bool:
        """Connect to Meilisearch server"""
        try:
            # In development mode, Meilisearch may not require an API key
            api_key = MEILISEARCH_API_KEY if MEILISEARCH_API_KEY else None
            self.client = Client(MEILISEARCH_HOST, api_key)
            # Test connection
            self.client.health()
            self._connected = True
            print(f"[Meilisearch] Connected to {MEILISEARCH_HOST}")
            return True
        except Exception as e:
            print(f"[Meilisearch] Connection failed: {e}")
            self._connected = False
            return False
    
    @property
    def connected(self) -> bool:
        return self._connected
    
    def setup_indexes(self):
        """Create and configure all indexes"""
        if not self.client:
            raise RuntimeError("Not connected to Meilisearch")
        
        for index_name, settings in INDEX_SETTINGS.items():
            try:
                # Create index if not exists
                self.client.create_index(index_name, {'primaryKey': f'{index_name[:-1]}DbId'})
                print(f"[Meilisearch] Created index: {index_name}")
            except Exception:
                pass  # Index might already exist
            
            # Update settings
            index = self.client.index(index_name)
            index.update_settings(settings)
            print(f"[Meilisearch] Configured index: {index_name}")
    
    def index_germplasm(self, germplasm_list: List[Dict[str, Any]]):
        """Index germplasm documents"""
        if not self.client:
            return
        
        documents = []
        for g in germplasm_list:
            documents.append({
                'id': g.get('germplasmDbId'),
                'germplasmDbId': g.get('germplasmDbId'),
                'germplasmName': g.get('germplasmName'),
                'accessionNumber': g.get('accessionNumber'),
                'species': g.get('species'),
                'genus': g.get('genus'),
                'subtaxa': g.get('subtaxa'),
                'synonyms': g.get('synonyms', []),
                'instituteCode': g.get('instituteCode'),
                'countryOfOrigin': g.get('countryOfOriginCode'),
                'biologicalStatus': g.get('biologicalStatusOfAccessionCode'),
                'createdAt': datetime.utcnow().isoformat(),
            })
        
        index = self.client.index(INDEXES['germplasm'])
        task = index.add_documents(documents, primary_key='germplasmDbId')
        print(f"[Meilisearch] Indexed {len(documents)} germplasm documents (task: {task.task_uid})")
        return task
    
    def index_traits(self, traits_list: List[Dict[str, Any]]):
        """Index trait/observation variable documents"""
        if not self.client:
            return
        
        documents = []
        for t in traits_list:
            documents.append({
                'id': t.get('observationVariableDbId'),
                'observationVariableDbId': t.get('observationVariableDbId'),
                'observationVariableName': t.get('observationVariableName'),
                'trait': t.get('trait', {}),
                'method': t.get('method', {}),
                'scale': t.get('scale', {}),
                'ontologyReference': t.get('ontologyReference', {}),
            })
        
        index = self.client.index(INDEXES['traits'])
        task = index.add_documents(documents, primary_key='observationVariableDbId')
        print(f"[Meilisearch] Indexed {len(documents)} trait documents (task: {task.task_uid})")
        return task
    
    def index_trials(self, trials_list: List[Dict[str, Any]]):
        """Index trial documents"""
        if not self.client:
            return
        
        documents = []
        for t in trials_list:
            documents.append({
                'id': t.get('trialDbId'),
                'trialDbId': t.get('trialDbId'),
                'trialName': t.get('trialName'),
                'trialDescription': t.get('trialDescription'),
                'programDbId': t.get('programDbId'),
                'programName': t.get('programName'),
                'locationDbId': t.get('locationDbId'),
                'locationName': t.get('locationName'),
                'startDate': t.get('startDate'),
                'endDate': t.get('endDate'),
                'active': t.get('active', True),
            })
        
        index = self.client.index(INDEXES['trials'])
        task = index.add_documents(documents, primary_key='trialDbId')
        print(f"[Meilisearch] Indexed {len(documents)} trial documents (task: {task.task_uid})")
        return task
    
    def search(self, index_name: str, query: str, options: Dict = None) -> Dict:
        """Search an index"""
        if not self.client:
            return {'hits': [], 'query': query}
        
        index = self.client.index(index_name)
        return index.search(query, options or {})
    
    def search_all(self, query: str, limit: int = 10) -> List[Dict]:
        """Search across all indexes"""
        if not self.client:
            return []
        
        results = []
        per_index_limit = max(1, limit // len(INDEXES))
        
        for index_name in INDEXES.values():
            try:
                search_result = self.search(index_name, query, {'limit': per_index_limit})
                for hit in search_result.get('hits', []):
                    hit['_index'] = index_name
                    results.append(hit)
            except Exception as e:
                print(f"[Meilisearch] Search error in {index_name}: {e}")
        
        return results[:limit]
    
    def delete_document(self, index_name: str, document_id: str):
        """Delete a document from an index"""
        if not self.client:
            return
        
        index = self.client.index(index_name)
        index.delete_document(document_id)
    
    def clear_index(self, index_name: str):
        """Clear all documents from an index"""
        if not self.client:
            return
        
        index = self.client.index(index_name)
        index.delete_all_documents()


# Singleton instance
meilisearch_service = MeilisearchService()


# FastAPI dependency
def get_meilisearch() -> MeilisearchService:
    """Get Meilisearch service instance"""
    if not meilisearch_service.connected:
        meilisearch_service.connect()
    return meilisearch_service
