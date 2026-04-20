import pytest
from unittest.mock import AsyncMock, MagicMock
from app.modules.genomics.services.qtl_mapping_service import QTLMappingService
from app.modules.bio_analytics.models import BioQTL

@pytest.fixture
def service():
    return QTLMappingService()

@pytest.mark.asyncio
async def test_list_qtls(service):
    mock_db = AsyncMock()

    # Mock data
    qtl = MagicMock(spec=BioQTL)
    qtl.id = 1
    qtl.qtl_db_id = "qtl_1"
    qtl.qtl_name = "QTL_Yield_Chr1"
    qtl.organization_id = 1
    qtl.trait = "Yield"
    qtl.population = "TestPop"
    qtl.method = "CIM"
    qtl.chromosome = "Chr1"
    qtl.start_position = 1000.0
    qtl.end_position = 2000.0
    qtl.peak_position = 1500.0
    qtl.lod = 5.5
    qtl.lod_score = 5.5
    qtl.pve = 10.0
    qtl.add_effect = 1.2
    qtl.dom_effect = 0.8
    qtl.marker_name = "Marker123"
    qtl.confidence_interval_low = 1200.0
    qtl.confidence_interval_high = 1800.0
    qtl.candidate_genes = []
    qtl.additional_info = {}
    qtl.analysis_date = None

    # Mock execute result
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [qtl]
    mock_db.execute.return_value = mock_result

    result = await service.list_qtls(mock_db, organization_id=1, trait="Yield")

    assert len(result) == 1
    assert result[0]["trait"] == "Yield"
    assert result[0]["lod"] == 5.5
    assert result[0]["qtl_id"] == "qtl_1"


@pytest.mark.asyncio
async def test_list_qtls_serializes_candidate_gene_relationships(service):
    mock_db = AsyncMock()

    candidate_gene = MagicMock()
    candidate_gene.id = 9
    candidate_gene.gene_id = "LOC_Os06g17900"
    candidate_gene.gene_name = "Pi9"
    candidate_gene.chromosome = "6"
    candidate_gene.start_position = 17641000
    candidate_gene.end_position = 17657500
    candidate_gene.source = "IRGSP-1.0"
    candidate_gene.description = "Rice blast resistance candidate gene"
    candidate_gene.go_terms = ["GO:0006952"]

    qtl = MagicMock(spec=BioQTL)
    qtl.id = 1
    qtl.qtl_db_id = "qtl_1"
    qtl.qtl_name = "qBLAST6.1"
    qtl.organization_id = 1
    qtl.trait = "Blast Resistance"
    qtl.population = "Demo Panel"
    qtl.method = "CIM"
    qtl.chromosome = "6"
    qtl.start_position = 17400000.0
    qtl.end_position = 17900000.0
    qtl.peak_position = 17652341.0
    qtl.lod = 6.8
    qtl.lod_score = 6.8
    qtl.pve = 18.4
    qtl.add_effect = -1.2
    qtl.dom_effect = -0.3
    qtl.marker_name = "Pi9-STS"
    qtl.confidence_interval_low = 17500000.0
    qtl.confidence_interval_high = 17800000.0
    qtl.candidate_genes = [candidate_gene]
    qtl.candidate_genes_json = []
    qtl.additional_info = {}
    qtl.analysis_date = None

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [qtl]
    mock_db.execute.return_value = mock_result

    result = await service.list_qtls(mock_db, organization_id=1, trait="Blast Resistance")

    assert result[0]["candidate_genes"] == [
        {
            "id": "9",
            "gene_id": "LOC_Os06g17900",
            "gene_name": "Pi9",
            "chromosome": "6",
            "start": 17641000,
            "end": 17657500,
            "source": "IRGSP-1.0",
            "description": "Rice blast resistance candidate gene",
            "go_terms": ["GO:0006952"],
        }
    ]

@pytest.mark.asyncio
async def test_get_candidate_genes(service):
    mock_db = AsyncMock()

    # Mock data
    gene = MagicMock()
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

    # Mock get_candidate_genes to return some genes
    async def mock_get_candidate_genes(db, org_id, qtl_id):
        return [{"gene_id": "gene1"}, {"gene_id": "gene2"}]
    
    service.get_candidate_genes = mock_get_candidate_genes

    # Mock genes with GO terms
    go1 = MagicMock(go_id="GO:1", term="Term 1", category="BP")
    go2 = MagicMock(go_id="GO:2", term="Term 2", category="MF")

    gene1 = MagicMock()
    gene1.go_terms = [go1]

    gene2 = MagicMock()
    gene2.go_terms = [go1, go2]

    candidate_result = MagicMock()
    candidate_result.scalars.return_value.all.return_value = [gene1, gene2]

    total_result = MagicMock()
    total_result.scalar.return_value = 10

    go1_count_result = MagicMock()
    go1_count_result.scalar.return_value = 5

    go2_count_result = MagicMock()
    go2_count_result.scalar.return_value = 1

    mock_db.execute.side_effect = [
        candidate_result,
        total_result,
        go1_count_result,
        go2_count_result,
    ]

    result = await service.get_go_enrichment(mock_db, organization_id=1, qtl_ids=["qtl_1"])

    assert len(result) == 2
    by_id = {entry["go_id"]: entry for entry in result}

    assert by_id["GO:1"]["term"] == "Term 1"
    assert by_id["GO:1"]["category"] == "BP"
    assert by_id["GO:1"]["count_in_candidates"] == 2
    assert by_id["GO:1"]["count_in_background"] == 5
    assert by_id["GO:1"]["total_candidates"] == 2
    assert by_id["GO:1"]["total_background"] == 10

    assert by_id["GO:2"]["term"] == "Term 2"
    assert by_id["GO:2"]["category"] == "MF"
    assert by_id["GO:2"]["count_in_candidates"] == 1
    assert by_id["GO:2"]["count_in_background"] == 1
