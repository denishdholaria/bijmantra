"""
DAG Topological Sorter for REEVU Execution Planning.

Provides functionality to order execution steps based on dependencies.
"""

from collections import deque, defaultdict
from typing import Generic, Hashable, TypeVar

T = TypeVar("T", bound=Hashable)


class CycleError(ValueError):
    """Raised when a cycle is detected in the graph."""
    pass


class TopologicalSorter(Generic[T]):
    """
    Sorts nodes in a Directed Acyclic Graph (DAG) such that for every directed
    edge from node A to node B, node A comes before node B in the ordering.
    """

    def __init__(self, graph: dict[T, list[T]] | None = None):
        """
        Initialize with an optional graph represented as dependency map.
        :param graph: Dictionary where keys are nodes and values are lists of dependencies (prerequisites).
                      Example: {'step2': ['step1'], 'step3': ['step1', 'step2']}
                      This implies step1 -> step2, step1 -> step3, step2 -> step3.
        """
        self._graph: dict[T, list[T]] = graph or {}

    def sort(self) -> list[T]:
        """
        Perform topological sort using Kahn's algorithm.
        :return: List of nodes in topological order.
        :raises CycleError: If the graph contains a cycle.
        """
        # 1. Build Adjacency List (Reverse of dependency map) and In-Degree count
        # adjacency[u] = [v, ...] means u is a prerequisite for v
        adjacency: dict[T, list[T]] = defaultdict(list)
        in_degree: dict[T, int] = defaultdict(int)

        # Collect all unique nodes
        all_nodes = set(self._graph.keys())
        for deps in self._graph.values():
            all_nodes.update(deps)

        # Initialize in-degree for all nodes
        for node in all_nodes:
            in_degree[node] = 0

        # Populate adjacency and in-degree based on dependencies
        for node, dependencies in self._graph.items():
            # If node depends on dep, then edge is dep -> node
            for dep in dependencies:
                adjacency[dep].append(node)
                in_degree[node] += 1

        # 2. Initialize Queue with nodes having 0 in-degree (no dependencies)
        queue = deque([node for node in all_nodes if in_degree[node] == 0])
        sorted_nodes: list[T] = []

        # 3. Process Queue
        while queue:
            u = queue.popleft()
            sorted_nodes.append(u)

            for v in adjacency[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)

        # 4. Check for Cycles
        if len(sorted_nodes) != len(all_nodes):
            # Identifying the nodes involved in the cycle (those with non-zero in-degree)
            remaining_nodes = [n for n in all_nodes if in_degree[n] > 0]
            raise CycleError(f"Cycle detected involving nodes: {remaining_nodes}")

        return sorted_nodes
