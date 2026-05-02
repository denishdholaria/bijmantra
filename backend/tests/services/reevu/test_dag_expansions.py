"""
Tests for DAG topological sorter and fallback path finder.
"""

import pytest
from app.modules.ai.services.reevu.expansions.dag_topological_sorter import TopologicalSorter, CycleError
from app.modules.ai.services.reevu.expansions.dag_fallback_path import FallbackPathFinder


def test_topological_sort_basic():
    """Test basic topological sort."""
    graph = {
        "C": ["A", "B"],
        "B": ["A"],
        "A": []
    }
    sorter = TopologicalSorter(graph)
    sorted_nodes = sorter.sort()

    assert sorted_nodes.index("A") < sorted_nodes.index("B")
    assert sorted_nodes.index("A") < sorted_nodes.index("C")
    assert sorted_nodes.index("B") < sorted_nodes.index("C")

    assert len(sorted_nodes) == 3


def test_topological_sort_cycle():
    """Test cycle detection."""
    graph = {
        "A": ["B"],
        "B": ["C"],
        "C": ["A"]
    }
    sorter = TopologicalSorter(graph)
    with pytest.raises(CycleError):
        sorter.sort()


def test_topological_sort_disconnected():
    """Test disconnected components."""
    graph = {
        "B": ["A"],
        "D": ["C"]
    }
    sorter = TopologicalSorter(graph)
    sorted_nodes = sorter.sort()

    # A must come before B, C must come before D
    assert sorted_nodes.index("A") < sorted_nodes.index("B")
    assert sorted_nodes.index("C") < sorted_nodes.index("D")
    assert len(sorted_nodes) == 4


def test_fallback_path_shortest():
    """Test finding shortest path avoiding nodes."""
    graph = {
        "A": ["B", "C"],
        "B": ["D"],
        "C": ["D"],
        "D": ["E"],
        "E": []
    }
    finder = FallbackPathFinder(graph)

    # Path A -> B -> D -> E (length 4) or A -> C -> D -> E (length 4)
    path = finder.find_shortest_path("A", "E")
    assert path is not None
    assert path[0] == "A"
    assert path[-1] == "E"
    assert len(path) == 4

    # Avoid B -> must go through C
    path_avoid_b = finder.find_shortest_path("A", "E", avoid_nodes={"B"})
    assert path_avoid_b == ["A", "C", "D", "E"]

    # Avoid C -> must go through B
    path_avoid_c = finder.find_shortest_path("A", "E", avoid_nodes={"C"})
    assert path_avoid_c == ["A", "B", "D", "E"]

    # Avoid both (no path)
    path_avoid_both = finder.find_shortest_path("A", "E", avoid_nodes={"B", "C"})
    assert path_avoid_both is None


def test_fallback_path_all():
    """Test finding all paths."""
    graph = {
        "A": ["B", "C"],
        "B": ["D"],
        "C": ["D"],
        "D": ["E"]
    }
    finder = FallbackPathFinder(graph)
    paths = finder.find_all_paths("A", "E")

    # Expected paths: A->B->D->E and A->C->D->E
    assert len(paths) == 2
    assert ["A", "B", "D", "E"] in paths
    assert ["A", "C", "D", "E"] in paths


def test_suggest_alternatives():
    """Test suggesting alternatives."""
    graph = {
        "Start": ["Step1", "Step2", "Step3"],
        "Step1": ["End"],
        "Step2": ["End"],
        "Step3": ["End"]
    }
    finder = FallbackPathFinder(graph)

    alts = finder.suggest_alternatives("Step1")
    assert "Step2" in alts
    assert "Step3" in alts
    assert "Step1" not in alts
    assert len(alts) == 2

    # With adequacy check
    def adequacy(node):
        return node == "Step2"

    alts_adequate = finder.suggest_alternatives("Step1", adequacy_check=adequacy)
    assert alts_adequate == ["Step2"]
