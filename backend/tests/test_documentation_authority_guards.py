from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text()


def test_current_architecture_truth_map_declares_active_authority() -> None:
    source = _read(".github/docs/architecture/CURRENT.md")

    assert "**Document Status:** ACTIVE" in source
    assert "ADR-035-domain-bounded-modular-monolith-with-hexagonal-architecture.md" in source
    assert "ADR-036-federated-research-asset-core-inside-modular-monolith.md" in source
    assert "domain-bounded modular monolith with hexagonal architecture inside each domain" in source
    assert "Monolith" in source
    assert "Modular domains" in source
    assert "Hexagonal internals" in source
    assert "industry-readable domain keys" in source
    assert "ResearchAsset" in source
    assert "FDCA" in source
    assert "Do not start a full Rust backend rewrite" in source
    assert "Historical Or Superseded Documents" in source


def test_document_authority_protocol_defines_required_status_vocabulary() -> None:
    source = _read(".github/docs/architecture/DOCUMENT_AUTHORITY.md")

    assert "**Document Status:** ACTIVE" in source
    for status in ("ACTIVE", "ACCEPTED", "SUPERSEDED", "HISTORICAL", "DRAFT", "EXPLORATORY"):
        assert status in source
    assert "Old documents may preserve memory" in source
    assert "full Rust backend rewrite" in source
    assert "domain-bounded modular monolith with hexagonal architecture inside each domain" in source
    assert "Monolith" in source
    assert "Modular domains" in source
    assert "Hexagonal internals per domain" in source


def test_architecture_terminology_redirects_old_names() -> None:
    old_adr = _read(".ai/decisions/ADR-035-loka-hexagonal-modular-monolith.md")
    new_adr = _read(".ai/decisions/ADR-035-domain-bounded-modular-monolith-with-hexagonal-architecture.md")
    old_roadmap = _read(".github/docs/architecture/2026-05-21-loka-hexagonal-recovery-roadmap.md")

    assert "**Document Status:** SUPERSEDED" in old_adr
    assert "ADR-035-domain-bounded-modular-monolith-with-hexagonal-architecture.md" in old_adr
    assert "# ADR-035: Domain-Bounded Modular Monolith With Hexagonal Architecture" in new_adr
    assert "The macro architecture is the modular monolith" in new_adr
    assert "**Document Status:** SUPERSEDED" in old_roadmap
    assert "2026-05-21-domain-bounded-modular-monolith-recovery-roadmap.md" in old_roadmap


def test_industry_domain_names_are_the_active_documentation_names() -> None:
    adr = _read(".ai/decisions/ADR-035-domain-bounded-modular-monolith-with-hexagonal-architecture.md")
    roadmap = _read(".github/docs/architecture/2026-05-21-domain-bounded-modular-monolith-recovery-roadmap.md")

    assert "- `germplasm`:" in adr
    assert "| `germplasm` |" in roadmap
    assert "- `intelligence`:" in adr
    assert "| `intelligence` |" in roadmap
    assert "`bija_kosha`: germplasm" not in adr
    assert "| `bija_kosha` |" not in roadmap
    assert "legacy aliases only" in adr
    assert "legacy aliases only" in roadmap


def test_high_risk_legacy_architecture_docs_are_quarantined() -> None:
    high_risk_docs = {
        ".ai/proposals/2026-04-20-bijmantra-rust-rewrite-feasibility.md": "ADR-035-domain-bounded-modular-monolith-with-hexagonal-architecture.md",
        ".github/docs/archive/documentation-reset-2026-05-21/architecture/core/ARCHITECTURE.md": ".github/docs/architecture/CURRENT.md",
    }

    for relative_path, current_authority in high_risk_docs.items():
        source = _read(relative_path)
        header = source[:600]
        assert "**Document Status:** HISTORICAL" in header
        assert "**Authority:**" in header
        assert "**Superseded By:**" in header
        assert current_authority in header


def test_fdca_is_reconciled_as_research_asset_spine_not_rewrite() -> None:
    adr = _read(".ai/decisions/ADR-036-federated-research-asset-core-inside-modular-monolith.md")
    current = _read(".github/docs/architecture/CURRENT.md")
    agents = _read("AGENTS.md")
    config = _read("agent.config.yaml")
    brief = _read(".github/agents/2026-05-28-agent-architecture-brief.md")

    for source in (adr, current, agents, config, brief):
        assert "ResearchAsset" in source
        assert "FDCA" in source

    assert "not as a replacement architecture" in adr
    assert "Do not bootstrap the `backend-rs/` action plan" in adr
    assert "ResearchAsset core inside the modular monolith" in config
    assert "does not authorize a backend rewrite" in agents
    assert "backend-rs/` FDCA drafts as active migration authority" in brief


def test_documentation_reset_keeps_active_paths_as_pointers() -> None:
    architecture_redirect = _read(".github/docs/architecture/core/ARCHITECTURE.md")
    important_plans_redirect = _read(".github/docs/important-plans/README.md")
    mcp_redirect = _read(".github/docs/architecture/mcps/README.md")
    pretext_redirect = _read(".github/docs/architecture/ui/pretext-update/README.md")

    assert "**Document Status:** RESET" in architecture_redirect
    assert "**Document Status:** RESET" in important_plans_redirect
    assert "**Document Status:** RESET" in mcp_redirect
    assert "**Document Status:** RESET" in pretext_redirect
    assert "Pointer only" in architecture_redirect
    assert "Pointer only" in important_plans_redirect
    assert "Pointer only" in mcp_redirect
    assert "Pointer only" in pretext_redirect
    assert "documentation-reset-2026-05-21" in architecture_redirect
    assert "documentation-reset-2026-05-21" in important_plans_redirect
    assert "documentation-reset-2026-05-21" in mcp_redirect
    assert "documentation-reset-2026-05-21" in pretext_redirect


def test_documentation_reset_archive_preserves_old_important_plans() -> None:
    archive_dir = REPO_ROOT / ".github/docs/archive/documentation-reset-2026-05-21/important-plans"
    archived_plan_names = {path.name for path in archive_dir.glob("*.md")}

    assert archived_plan_names == {
        "2026-03-08-ai-prototype-parabijmantra-roadmap.md",
        "2026-03-08-bounded-ai-workspace-inputs.md",
        "2026-03-08-development-lanes-decision.md",
        "2026-03-08-reevu-blocker-shortlist.md",
        "2026-03-10-reevu-canonical-chat-path.md",
        "2026-03-12-para-phase0-architecture-census-and-risk-audit.md",
        "2026-03-12-para-phase1-shell-and-dependency-boundary-map.md",
        "2026-03-12-para-workbench-and-architecture-evolution-plan.md",
        "2026-03-13-ollama-cloud-routing.md",
    }


def test_documentation_reset_archives_idea_and_vision_lanes() -> None:
    archive_root = REPO_ROOT / ".github/docs/archive/documentation-reset-2026-05-21"

    assert len(list((archive_root / "vision").rglob("*.md"))) == 26
    assert len(list((archive_root / "denish-ideas").rglob("*.md"))) == 3
    assert len(list((archive_root / "steppingStones").rglob("*.md"))) == 2

    assert (REPO_ROOT / ".github/docs/vision/README.md").exists()
    assert (REPO_ROOT / ".github/docs/steppingStones/README.md").exists()
    assert (REPO_ROOT / ".github/docs/denish-ideas/README.md").exists()
    assert (REPO_ROOT / ".github/docs/denish-ideas/2026-05-19-future-direction.md").exists()


def test_documentation_reset_archives_old_architecture_lanes() -> None:
    archive_root = REPO_ROOT / ".github/docs/archive/documentation-reset-2026-05-21/architecture"

    assert len(list((archive_root / "control-plane-history").rglob("*.md"))) == 19
    assert len(list((archive_root / "core-history").rglob("*.md"))) == 6
    assert len(list((archive_root / "domain-studies").rglob("*.md"))) == 2
    assert len(list((archive_root / "mcp-history").rglob("*.md"))) == 3
    assert len(list((archive_root / "plant-vision-history").rglob("*.md"))) == 4
    assert len(list((archive_root / "ui-history").rglob("*.md"))) == 3

    assert (REPO_ROOT / ".github/docs/architecture/core/README.md").exists()
    assert (REPO_ROOT / ".github/docs/architecture/core/ARCHITECTURE.md").exists()
    assert (REPO_ROOT / ".github/docs/architecture/mcps/README.md").exists()
    assert (REPO_ROOT / ".github/docs/architecture/plant-vision/README.md").exists()
    assert (REPO_ROOT / ".github/docs/architecture/ui/pretext-update/README.md").exists()


def test_strategy_vision_reading_order_uses_current_pointers() -> None:
    source = _read(".github/docs/strategy/STRATEGIC_VISION.md")

    assert "../denish-ideas/2026-05-19-future-direction.md" in source
    assert "../architecture/CURRENT.md" in source
    assert "../vision/1-current.md" not in source
    assert "../vision/1-future.md" not in source


def test_agent_document_authority_instruction_points_to_current_truth() -> None:
    source = _read(".github/instructions/document-authority.instructions.md")

    assert ".github/docs/architecture/CURRENT.md" in source
    assert "ADR-035" in source
    assert "proposals as context" in source
    assert "archives as historical memory" in source


def test_custom_agents_point_to_shared_architecture_brief() -> None:
    brief_path = ".github/agents/2026-05-28-agent-architecture-brief.md"
    brief = _read(brief_path)

    assert "Dominions" in brief
    assert "Backend domains" in brief
    assert "Capability manifests" in brief
    assert "BrAPI v2.1 remains first-class" in brief
    assert "Do not recommend a full backend Rust rewrite" in brief

    required_files = [
        ".github/agents/README.md",
        ".github/agents/devsena/README.md",
        ".github/agents/2026-03-13-phase1-agent-operator-guide.md",
        ".github/agents/2026-04-04-devsena-operator-guide.md",
        ".github/agents/2026-03-13-phase1-agent-prompt-cookbook.md",
        ".github/agents/om-shri-maatre-namaha.agent.md",
        ".github/copilot-instructions.md",
        "AGENTS.md",
        "agent.config.yaml",
    ]
    for relative_path in required_files:
        assert "2026-05-28-agent-architecture-brief.md" in _read(relative_path)

    active_agent_files = [
        *sorted((REPO_ROOT / ".github/agents/shivshakti").glob("*.agent.md")),
        *sorted((REPO_ROOT / ".github/agents/devsena").glob("*.agent.md")),
    ]
    assert active_agent_files
    for agent_file in active_agent_files:
        source = agent_file.read_text()
        assert "## Repository Architecture Baseline" in source
        assert brief_path in source
        assert "backend domains are open-ended code-ownership boundaries" in source


def test_agent_adjacent_control_surfaces_use_current_architecture_brief() -> None:
    quickstart = _read(".github/docs/ai/2026-03-30-ai-operator-quickstart.md")
    project_memory = _read(".github/docs/ai/2026-03-18-project-memory-surface.md")
    ai_protocol = _read(".ai/AGENT_COORDINATION_PROTOCOL.md")
    ai_readme = _read(".ai/README.md")
    governance = _read("docs/agent-governance/README.md")
    adapter_map = _read("docs/agent-governance/adapter-map.md")

    for source in (quickstart, project_memory, ai_protocol, ai_readme, governance, adapter_map):
        assert "2026-05-28-agent-architecture-brief.md" in source

    assert "confidential-docs/ai/2026-03-18-project-memory-surface.md" not in quickstart
    assert "Dominions" in _read(".github/agents/2026-05-28-agent-architecture-brief.md")
    assert "Product Knowledge Graph surfaces belong under Intelligence ownership" in project_memory
    assert "Product Knowledge Graph surfaces belong under Medha ownership" not in project_memory


def test_kiro_specs_do_not_use_legacy_domain_labels_for_affected_domains() -> None:
    legacy_patterns = (
        "Primary domain: medha",
        "Primary domain: rupa",
        "Secondary domains: bijkosha",
        "Secondary domains: medha",
        "`bijkosha`",
        "`sristi`",
        "`kshetra`",
        "`vani`",
        "`vidya`",
    )

    for requirements_path in (REPO_ROOT / ".kiro/specs").glob("*/requirements.md"):
        source = requirements_path.read_text()
        for pattern in legacy_patterns:
            assert pattern not in source
