# BIJMANTRA JULES JOB CARD: D02
# Isolated Unit Test for DAG Fallback Strategies

import unittest
from unittest.mock import Mock, call
from typing import List, Dict, Any, Callable, Set, Optional
import logging

# Configure logging for the test run
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class NonCriticalFailure(Exception):
    """Exception representing a failure that should not abort the entire DAG."""
    pass

class CriticalFailure(Exception):
    """Exception representing a failure that must abort the entire DAG."""
    pass

class DagNode:
    """Represents a node in the DAG."""
    def __init__(
        self,
        node_id: str,
        func: Callable[[], Any],
        dependencies: Optional[List[str]] = None,
        is_critical: bool = False
    ):
        self.node_id = node_id
        self.func = func
        self.dependencies = dependencies or []
        self.is_critical = is_critical

    def __repr__(self):
        return f"DagNode(id={self.node_id}, deps={self.dependencies}, critical={self.is_critical})"

class DagEngine:
    """
    Simulates a DAG execution engine with fallback strategies.
    Strategies:
    - critical failure: abort immediately
    - non-critical failure: skip downstream nodes, continue independent branches
    - partial results: return whatever succeeded
    """
    def __init__(self, nodes: List[DagNode]):
        self.nodes = {node.node_id: node for node in nodes}
        self.results: Dict[str, Any] = {}
        self.status: Dict[str, str] = {node.node_id: 'PENDING' for node in nodes} # PENDING, RUNNING, COMPLETED, FAILED, SKIPPED
        self.errors: Dict[str, Exception] = {}

    def _get_execution_order(self) -> List[str]:
        """Simple topological sort."""
        visited = set()
        order = []

        def visit(node_id):
            if node_id in visited:
                return
            visited.add(node_id)
            for dep_id in self.nodes[node_id].dependencies:
                visit(dep_id)
            order.append(node_id)

        for node_id in self.nodes:
            visit(node_id)

        return order

    def _mark_downstream_skipped(self, failed_node_id: str):
        """Recursively mark downstream nodes as SKIPPED."""
        # Find all nodes that depend on failed_node_id
        # This is inefficient for large graphs but fine for simulation

        # Build dependency map (reverse graph)
        dependents = {n_id: [] for n_id in self.nodes}
        for n_id, node in self.nodes.items():
            for dep_id in node.dependencies:
                if dep_id in dependents:
                    dependents[dep_id].append(n_id)

        queue = [failed_node_id]
        visited = set()

        while queue:
            current_id = queue.pop(0)
            if current_id in visited:
                continue
            visited.add(current_id)

            # Skip dependents
            for downstream_id in dependents.get(current_id, []):
                if self.status[downstream_id] == 'PENDING':
                    self.status[downstream_id] = 'SKIPPED'
                    logger.info(f"Skipping downstream node {downstream_id} due to failure in {failed_node_id}")
                    queue.append(downstream_id)

    def execute(self) -> Dict[str, Any]:
        execution_order = self._get_execution_order()
        logger.info(f"Execution order: {execution_order}")

        for node_id in execution_order:
            node = self.nodes[node_id]

            # Check if dependencies failed or were skipped
            should_skip = False
            for dep_id in node.dependencies:
                if self.status[dep_id] in ('FAILED', 'SKIPPED'):
                    should_skip = True
                    break

            if should_skip:
                self.status[node_id] = 'SKIPPED'
                continue

            if self.status[node_id] == 'SKIPPED':
                continue

            self.status[node_id] = 'RUNNING'
            try:
                result = node.func()
                self.results[node_id] = result
                self.status[node_id] = 'COMPLETED'
            except NonCriticalFailure as e:
                logger.warning(f"Node {node_id} failed non-critically: {e}")
                self.status[node_id] = 'FAILED'
                self.errors[node_id] = e
                # Mark downstream as skipped
                self._mark_downstream_skipped(node_id)
            except CriticalFailure as e:
                logger.error(f"Node {node_id} failed critically: {e}")
                self.status[node_id] = 'FAILED'
                self.errors[node_id] = e
                # Abort execution immediately
                logger.error("Aborting DAG execution due to critical failure.")
                break # Stop processing the order
            except Exception as e:
                # Treat unknown exceptions as Critical for this simulation, or strictly non-critical depending on policy.
                # Let's say default is Critical if not specified, or use node.is_critical flag.
                if node.is_critical:
                    logger.error(f"Node {node_id} failed with critical exception: {e}")
                    self.status[node_id] = 'FAILED'
                    self.errors[node_id] = e
                    break
                else:
                    logger.warning(f"Node {node_id} failed with exception (treated as non-critical): {e}")
                    self.status[node_id] = 'FAILED'
                    self.errors[node_id] = e
                    self._mark_downstream_skipped(node_id)

        return self.results

class TestDagFallback(unittest.TestCase):

    def test_successful_execution(self):
        """Verify a simple DAG runs to completion."""
        # A -> B -> C
        task_a = Mock(return_value="Result A")
        task_b = Mock(return_value="Result B")
        task_c = Mock(return_value="Result C")

        nodes = [
            DagNode("A", task_a),
            DagNode("B", task_b, dependencies=["A"]),
            DagNode("C", task_c, dependencies=["B"])
        ]

        engine = DagEngine(nodes)
        results = engine.execute()

        self.assertEqual(results, {"A": "Result A", "B": "Result B", "C": "Result C"})
        self.assertEqual(engine.status["A"], "COMPLETED")
        self.assertEqual(engine.status["B"], "COMPLETED")
        self.assertEqual(engine.status["C"], "COMPLETED")

    def test_non_critical_failure(self):
        """
        Verify downstream nodes are skipped on non-critical failure.
        Verify independent nodes still run.
        """
        # A (fails) -> B
        # C (independent)

        task_a = Mock(side_effect=NonCriticalFailure("Oops A failed"))
        task_b = Mock(return_value="Result B")
        task_c = Mock(return_value="Result C")

        nodes = [
            DagNode("A", task_a),
            DagNode("B", task_b, dependencies=["A"]),
            DagNode("C", task_c)
        ]

        engine = DagEngine(nodes)
        results = engine.execute()

        # A failed, B skipped, C succeeded
        self.assertEqual(engine.status["A"], "FAILED")
        self.assertEqual(engine.status["B"], "SKIPPED")
        self.assertEqual(engine.status["C"], "COMPLETED")

        # Results should contain C only
        self.assertEqual(results, {"C": "Result C"})

        # Verify B was not called
        task_b.assert_not_called()
        task_c.assert_called_once()

    def test_critical_failure(self):
        """Verify execution aborts immediately when a critical node fails."""
        # A (critical, fails) -> B
        # C (independent, but should be aborted if order puts it after A or if abort stops EVERYTHING)
        # Note: Topological sort doesn't guarantee C runs after A unless dependent.
        # But `abort` implies stopping the engine loop.

        task_a = Mock(side_effect=CriticalFailure("CRITICAL ERROR"))
        task_b = Mock(return_value="Result B")
        task_c = Mock(return_value="Result C")

        # Force order A, B, C or similar by dependencies or just ensure A runs early.
        # If A fails critically, loop breaks.
        # If C is independent and scheduled AFTER A, it won't run.
        # If C is scheduled BEFORE A, it runs.
        # Let's make C depend on nothing but ensure deterministic order for test if possible.
        # Topological sort here is stable for insertion order if no dependencies?
        # Let's rely on standard list processing in `_get_execution_order` for unconnected nodes.
        # Standard DFS post-order reversal usually puts leaves first? No, reverse post-order.

        nodes = [
            DagNode("A", task_a, is_critical=True),
            DagNode("B", task_b, dependencies=["A"]),
            DagNode("C", task_c, dependencies=["B"]) # Chain to ensure they are downstream
        ]
        # Let's add an independent node D that *might* run if scheduled before A
        task_d = Mock(return_value="Result D")
        nodes.append(DagNode("D", task_d))

        engine = DagEngine(nodes)
        # We can't easily control topological sort order of independent nodes without more logic.
        # But we can check that B and C definitely don't run.
        results = engine.execute()

        self.assertEqual(engine.status["A"], "FAILED")
        self.assertEqual(engine.status["B"], "PENDING") # Never reached processing loop or skipped?
        # If loop breaks, status remains PENDING for untouched nodes.
        # B is downstream of A. If A failed, B would be skipped if we continued.
        # But critical failure breaks the loop. So B remains PENDING (or whatever initial state).

        # Ideally, critical failure aborts everything.

        # Check that B was not called
        task_b.assert_not_called()

    def test_complex_dependency_skip(self):
        """
        A -> B -> D
        A -> C -> E
        If B fails (non-critical), D should skip.
        C and E should run.
        """
        task_a = Mock(return_value="A")
        task_b = Mock(side_effect=NonCriticalFailure("Fail B"))
        task_c = Mock(return_value="C")
        task_d = Mock(return_value="D")
        task_e = Mock(return_value="E")

        nodes = [
            DagNode("A", task_a),
            DagNode("B", task_b, dependencies=["A"]),
            DagNode("C", task_c, dependencies=["A"]),
            DagNode("D", task_d, dependencies=["B"]),
            DagNode("E", task_e, dependencies=["C"]),
        ]

        engine = DagEngine(nodes)
        results = engine.execute()

        self.assertEqual(results.get("A"), "A")
        self.assertEqual(engine.status["B"], "FAILED")
        self.assertEqual(results.get("C"), "C")
        self.assertEqual(engine.status["D"], "SKIPPED")
        self.assertEqual(results.get("E"), "E")

        task_d.assert_not_called()
        task_e.assert_called()

    def test_partial_results_return(self):
        """Verify engine returns partial results when some nodes fail non-critically."""
        task_a = Mock(return_value="Val A")
        task_b = Mock(side_effect=NonCriticalFailure("Fail B"))

        nodes = [
            DagNode("A", task_a),
            DagNode("B", task_b, dependencies=["A"])
        ]

        engine = DagEngine(nodes)
        results = engine.execute()

        self.assertIn("A", results)
        self.assertNotIn("B", results)
        self.assertEqual(results["A"], "Val A")

if __name__ == "__main__":
    unittest.main()
