import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.qtl_mapping import QTLMappingService
from app.modules.bio_analytics.models import QTL, CandidateGene

@pytest.fixture
def service():
    return QTLMappingService()

@pytest.mark.asyncio
async def test_list_qtls(service):
    mock_db = AsyncMock()

    # Mock data
    qtl = MagicMock(spec=QTL)
    qtl.id = 1
    qtl.organization_id = 1
    qtl.trait = "Yield"
    qtl.chromosome = "Chr1"
    qtl.start_position = 1000.0
    qtl.end_position = 2000.0
    qtl.peak_position = 1500.0
    qtl.lod_score = 5.5
    qtl.pve = 10.0
    qtl.method = "CIM"
    qtl.analysis_date = None

    # Mock execute result
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [qtl]
    mock_db.execute.return_value = mock_result

    result = await service.list_qtls(mock_db, organization_id=1, trait="Yield")

    assert len(result) == 1
    assert result[0]["trait"] == "Yield"
    assert result[0]["lod"] == 5.5
    assert result[0]["id"] == "1"

@pytest.mark.asyncio
async def test_get_candidate_genes(service):
    mock_db = AsyncMock()

    # Mock data
    gene = MagicMock(spec=CandidateGene)
    gene.id = 1
    gene.organization_id = 1
    gene.qtl_id = 1
    gene.gene_id = "AT1G12345"
    gene.gene_name = "TEST1"
    gene.chromosome = "Chr1"
    gene.start_position = 1200
    gene.end_position = 1800
    gene.source = "Araport"
    gene.description = "Test gene"
    gene.go_terms = ["GO:0001234"]

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [gene]
    mock_db.execute.return_value = mock_result

    result = await service.get_candidate_genes(mock_db, organization_id=1, qtl_id="1")

    assert len(result) == 1
    assert result[0]["gene_name"] == "TEST1"
    assert result[0]["go_terms"] == ["GO:0001234"]
    assert result[0]["id"] == "1"

@pytest.mark.asyncio
async def test_get_go_enrichment(service):
    mock_db = AsyncMock()

    # Mock data
    gene1 = MagicMock(spec=CandidateGene)
    gene1.go_terms = ["GO:1"]

    gene2 = MagicMock(spec=CandidateGene)
    gene2.go_terms = ["GO:1", "GO:2"]

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [gene1, gene2]
    mock_db.execute.return_value = mock_result

    result = await service.get_go_enrichment(mock_db, organization_id=1)

    assert len(result) == 2
    # result is sorted by count desc
    # GO:1 appears twice, GO:2 appears once

    first = result[0]
    second = result[1]

    assert first["go_term"] == "GO:1"
    assert first["count"] == 2

    assert second["go_term"] == "GO:2"
    assert second["count"] == 1
