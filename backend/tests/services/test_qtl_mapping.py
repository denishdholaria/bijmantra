import pytest
from sqlalchemy import select, insert
from app.services.qtl_mapping import get_qtl_mapping_service
from app.models import BioQTL, GWASRun, GWASResult, Organization
from app.modules.bio_analytics.models import CandidateGene
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_qtl_mapping_service(async_db_session: AsyncSession):
    service = get_qtl_mapping_service()

    # Ensure organization exists
    result = await async_db_session.execute(select(Organization).filter_by(name="Test Organization"))
    org = result.scalar_one_or_none()
    if not org:
        org = Organization(name="Test Organization")
        async_db_session.add(org)
        await async_db_session.commit()
        await async_db_session.refresh(org)

    organization_id = org.id

    # Create test data
    qtl = BioQTL(
        organization_id=organization_id,
        qtl_db_id="qtl_001",
        qtl_name="QTL 1",
        trait="Yield",
        population="Pop A",
        method="CIM",
        chromosome="1H",
        start_position=10.0,
        end_position=20.0,
        peak_position=15.0,
        lod=5.5,
        pve=12.5,
        add_effect=1.2,
        dom_effect=0.5,
        marker_name="m1"
    )
    async_db_session.add(qtl)

    run = GWASRun(
        organization_id=organization_id,
        run_name="Run 1",
        trait_name="Yield",
        method="MLM"
    )
    async_db_session.add(run)
    await async_db_session.flush() # flush to get run.id

    gwas_res = GWASResult(
        organization_id=organization_id,
        run_id=run.id,
        marker_name="m2",
        chromosome="2H",
        position=50,
        p_value=0.001,
        neg_log10_p=3.0,
        is_significant=True
    )
    async_db_session.add(gwas_res)

    await async_db_session.commit()

    # Test list_qtls
    qtls = await service.list_qtls(async_db_session, organization_id, trait="Yield")
    assert len(qtls) == 1
    assert qtls[0]["qtl_id"] == "qtl_001"

    # Test get_qtl
    qtl_res = await service.get_qtl(async_db_session, organization_id, "qtl_001")
    assert qtl_res is not None
    assert qtl_res["qtl_name"] == "QTL 1"

    # Test get_gwas_results
    gwas_results = await service.get_gwas_results(async_db_session, organization_id, trait="Yield")
    assert len(gwas_results) == 1
    assert gwas_results[0]["marker_name"] == "m2"
    assert gwas_results[0]["trait"] == "Yield"

    # Test get_qtl_summary
    summary = await service.get_qtl_summary(async_db_session, organization_id)
    assert summary["total_qtls"] == 1
    assert "Yield" in summary["traits"]

    # Test get_gwas_summary
    gwas_summary = await service.get_gwas_summary(async_db_session, organization_id)
    assert gwas_summary["total_associations"] == 1
    assert "Yield" in gwas_summary["traits"]
from app.models.qtl import Gene, GOTerm, gene_go_terms
from app.models.core import Organization
from app.modules.bio_analytics.models import BioQTL

@pytest.fixture
def service():
    return get_qtl_mapping_service()

@pytest.mark.asyncio
async def test_go_enrichment(async_db_session, service):
    db = async_db_session

    # Setup Data
    org = Organization(name="Test Org")
    db.add(org)
    await db.commit()
    await db.refresh(org)

    # Create Genes (10 genes)
    genes = []
    for i in range(10):
        gene = Gene(
            organization_id=org.id,
            gene_id=f"G{i}",
            name=f"Gene{i}",
            chromosome="1",
            start=i*1000,
            end=i*1000+500,
            strand="+"
        )
        db.add(gene)
        genes.append(gene)
    await db.commit()
    for g in genes:
        await db.refresh(g)

    # Create GO Terms
    go1 = GOTerm(go_id="GO:001", term="Term1", category="BP", definition="Def1")
    go2 = GOTerm(go_id="GO:002", term="Term2", category="BP", definition="Def2")
    db.add(go1)
    db.add(go2)
    await db.commit()
    await db.refresh(go1)
    await db.refresh(go2)

    # Assign GO terms
    # Term1: G0, G1, G2, G3, G4 (5 genes)
    # Term2: G5, G6, G7, G8, G9 (5 genes)

    stmt1 = insert(gene_go_terms).values([
        {"gene_id": genes[i].id, "go_term_id": go1.id} for i in range(5)
    ])
    await db.execute(stmt1)

    stmt2 = insert(gene_go_terms).values([
        {"gene_id": genes[i].id, "go_term_id": go2.id} for i in range(5, 10)
    ])
    await db.execute(stmt2)

    await db.commit()

    # Create QTL covering G0-G2 (0-2600)
    qtl = BioQTL(
        organization_id=org.id,
        qtl_db_id="test_qtl_1",
        qtl_name="Test Yield QTL",
        trait="Yield",
        chromosome="1",
        peak_position=1000.0,
        start_position=0.0,
        end_position=2600.0,
        lod=5.0,
        pve=10.0
    )
    db.add(qtl)
    await db.commit()
    await db.refresh(qtl)

    # Add CandidateGenes for the QTL test
    for g in genes[:3]:  # G0, G1, G2
        c_gene = CandidateGene(
            organization_id=org.id,
            qtl_id=qtl.id,
            gene_id=g.gene_id,
            gene_name=g.name,
            chromosome=g.chromosome,
            start_position=g.start,
            end_position=g.end,
            source="Test",
            description="Test candidate"
        )
        db.add(c_gene)
    await db.commit()

    # Test get_candidate_genes
    candidate_genes = await service.get_candidate_genes(db, org.id, qtl.qtl_db_id)
    assert len(candidate_genes) == 3
    assert {g["gene_id"] for g in candidate_genes} == {"G0", "G1", "G2"}

    # Test get_go_enrichment
    results = await service.get_go_enrichment(db, org.id, [qtl.qtl_db_id])

    assert len(results) == 1
    res = results[0]

    assert res["go_id"] == "GO:001"
    assert res["count_in_candidates"] == 3
    assert res["total_candidates"] == 3
    assert res["count_in_background"] == 5
    assert res["total_background"] == 10

    # Check p_value is reasonable
    assert 0 < res["p_value"] < 1.0
