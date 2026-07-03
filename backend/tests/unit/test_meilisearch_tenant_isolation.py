from types import SimpleNamespace

from app.core.meilisearch import INDEX_SETTINGS, MeilisearchService


class FakeIndex:
    def __init__(self):
        self.documents = []
        self.search_calls = []
        self.similar_calls = []
        self.delete_filters = []

    def add_documents(self, documents, primary_key=None):
        self.documents.extend(documents)
        self.primary_key = primary_key
        return SimpleNamespace(task_uid=1)

    def search(self, query, options):
        self.search_calls.append((query, options))
        return {"hits": [], "query": query}

    def search_similar_documents(self, document_id, options):
        self.similar_calls.append((document_id, options))
        return {"hits": []}

    def delete_documents_by_filter(self, filter_str):
        self.delete_filters.append(filter_str)
        return SimpleNamespace(task_uid=2)


class FakeClient:
    def __init__(self):
        self.indexes = {}
        self.multi_search_calls = []

    def index(self, index_name):
        return self.indexes.setdefault(index_name, FakeIndex())

    def multi_search(self, queries, options=None):
        self.multi_search_calls.append((queries, options))
        return {"hits": []}


def test_indexed_documents_include_organization_id_and_index_filterable_attribute():
    service = MeilisearchService()
    service.client = FakeClient()

    service.index_germplasm(
        [
            {
                "germplasmDbId": "g1",
                "germplasmName": "Tenant rice",
                "organization_id": 7,
            }
        ]
    )

    indexed_doc = service.client.indexes["germplasm"].documents[0]
    assert indexed_doc["organization_id"] == 7
    assert "organization_id" in INDEX_SETTINGS["germplasm"]["filterableAttributes"]


def test_search_merges_existing_filter_with_tenant_filter():
    service = MeilisearchService()
    service.client = FakeClient()

    service.search(
        "germplasm",
        "rice",
        {"filter": 'species = "Oryza"', "limit": 10},
        organization_id=7,
    )

    options = service.client.indexes["germplasm"].search_calls[0][1]
    assert options["filter"] == '(species = "Oryza") AND organization_id = 7'


def test_federated_search_adds_tenant_filter_to_each_index_query():
    service = MeilisearchService()
    service.client = FakeClient()

    service.federated_search(
        "rice",
        indexes=["germplasm", "trials"],
        limit=5,
        organization_id=7,
    )

    queries, federation_options = service.client.multi_search_calls[0]
    assert federation_options == {"federation": {"limit": 5}}
    assert [query["indexUid"] for query in queries] == ["germplasm", "trials"]
    assert all(query["filter"] == "organization_id = 7" for query in queries)


def test_similar_geo_and_delete_paths_are_tenant_filtered():
    service = MeilisearchService()
    service.client = FakeClient()

    service.get_similar_documents(
        "germplasm",
        "g1",
        filter_str='species = "Oryza"',
        organization_id=7,
    )
    service.geo_search("locations", "", 12.0, 77.0, organization_id=7)
    service.delete_documents_by_filter("germplasm", 'species = "Oryza"', organization_id=7)

    similar_options = service.client.indexes["germplasm"].similar_calls[0][1]
    geo_options = service.client.indexes["locations"].search_calls[0][1]
    delete_filter = service.client.indexes["germplasm"].delete_filters[0]

    assert similar_options["filter"] == '(species = "Oryza") AND organization_id = 7'
    assert geo_options["filter"].endswith("AND organization_id = 7")
    assert delete_filter == '(species = "Oryza") AND organization_id = 7'
