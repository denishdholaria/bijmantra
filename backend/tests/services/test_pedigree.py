
import pytest
import numpy as np
from app.services.pedigree import pedigree_service

class TestPedigreeService:
    
    def test_build_graph_simple(self):
        """Test simple parent-child graph construction"""
        records = [
            {"id": "P1", "label": "Parent 1"},
            {"id": "C1", "parent_a": "P1", "label": "Child 1"}
        ]
        
        G = pedigree_service.build_graph(records)
        assert len(G.nodes) == 2
        assert len(G.edges) == 1
        # Edge should be P1 -> C1
        assert G.has_edge("P1", "C1")

    def test_visualization_json(self):
        """Test Cytoscape JSON format"""
        records = [
            {"id": "A"},
            {"id": "B", "parent_a": "A"},
            {"id": "C", "parent_a": "B"}
        ]
        G = pedigree_service.build_graph(records)
        
        # Test full graph
        viz = pedigree_service.get_visualization_json(G)
        assert len(viz["nodes"]) == 3
        assert len(viz["edges"]) == 2
        
        # Test depth limitation (Root C, depth 1 -> C and B)
        viz_depth = pedigree_service.get_visualization_json(G, root_id="C", depth=1)
        node_ids = {n["data"]["id"] for n in viz_depth["nodes"]}
        assert "C" in node_ids
        assert "B" in node_ids
        assert "A" not in node_ids # Depth 1 means direct parents

    def test_a_matrix_half_sibs(self):
        """Test A-Matrix for Half-Sibs (share 1 parent)"""
        records = [
            {"id": "P1"}, # Common Parent
            {"id": "HS1", "parent_a": "P1"},
            {"id": "HS2", "parent_a": "P1"}
        ]
        
        A, ids = pedigree_service.compute_a_matrix(records)
        
        # Indices
        idx_p1 = ids.index("P1")
        idx_hs1 = ids.index("HS1")
        idx_hs2 = ids.index("HS2")
        
        # Diagonal elements (1 + F)
        assert A[idx_p1, idx_p1] == 1.0
        assert A[idx_hs1, idx_hs1] == 1.0
        assert A[idx_hs2, idx_hs2] == 1.0
        
        # Off-Diagonal
        # Rel(P1, HS1) = 0.5
        assert A[idx_p1, idx_hs1] == 0.5
        
        # Rel(HS1, HS2) = 0.25
        assert abs(A[idx_hs1, idx_hs2] - 0.25) < 1e-6
        
    def test_a_matrix_full_sibs(self):
        """Test A-Matrix for Full-Sibs (share 2 parents)"""
        records = [
            {"id": "P1"},
            {"id": "P2"},
            {"id": "FS1", "parent_a": "P1", "parent_b": "P2"},
            {"id": "FS2", "parent_a": "P1", "parent_b": "P2"}
        ]
        
        A, ids = pedigree_service.compute_a_matrix(records)
        
        idx_fs1 = ids.index("FS1")
        idx_fs2 = ids.index("FS2")
        
        # Rel(FS1, FS2) should be 0.5
        assert abs(A[idx_fs1, idx_fs2] - 0.5) < 1e-6

