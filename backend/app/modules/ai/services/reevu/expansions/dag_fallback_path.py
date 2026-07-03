"""
DAG Fallback Path Finder for REEVU Step Adequacy.

Provides functionality to find alternative execution paths when a step fails
adequacy checks or execution.
"""

from collections import deque
from typing import Generic, Hashable, TypeVar, Callable

T = TypeVar("T", bound=Hashable)


class FallbackPathFinder(Generic[T]):
    """
    Finds alternative paths in a DAG avoiding specified nodes.
    """

    def __init__(self, graph: dict[T, list[T]]):
        """
        Initialize with a graph.
        :param graph: Adjacency list representation (node -> [next_nodes]).
                      Note: This is standard adjacency list where edges are directed
                      from key to values (e.g., A -> [B, C]).
                      If using dependency maps (B depends on A), you must invert it first.
        """
        self._graph = graph

    def find_shortest_path(
        self,
        start_node: T,
        end_node: T,
        avoid_nodes: set[T] | None = None
    ) -> list[T] | None:
        """
        Find the shortest path from start_node to end_node avoiding avoid_nodes using BFS.
        :param start_node: Starting node.
        :param end_node: Target node.
        :param avoid_nodes: Set of nodes to exclude from the path.
        :return: List of nodes representing the path, or None if no path found.
        """
        avoid_nodes = avoid_nodes or set()

        if start_node in avoid_nodes or end_node in avoid_nodes:
            return None

        # Queue stores (current_node, path_so_far)
        queue: deque[tuple[T, list[T]]] = deque([(start_node, [start_node])])
        visited: set[T] = {start_node}

        while queue:
            current, path = queue.popleft()

            if current == end_node:
                return path

            for neighbor in self._graph.get(current, []):
                if neighbor not in visited and neighbor not in avoid_nodes:
                    visited.add(neighbor)
                    new_path = list(path)
                    new_path.append(neighbor)
                    queue.append((neighbor, new_path))

        return None

    def find_all_paths(
        self,
        start_node: T,
        end_node: T,
        avoid_nodes: set[T] | None = None
    ) -> list[list[T]]:
        """
        Find all simple paths from start to end avoiding specified nodes.
        Uses DFS.
        """
        avoid_nodes = avoid_nodes or set()
        if start_node in avoid_nodes or end_node in avoid_nodes:
            return []

        paths = []

        def dfs(current: T, current_path: list[T]):
            if current == end_node:
                paths.append(list(current_path))
                return

            for neighbor in self._graph.get(current, []):
                if neighbor not in current_path and neighbor not in avoid_nodes:
                    current_path.append(neighbor)
                    dfs(neighbor, current_path)
                    current_path.pop()

        dfs(start_node, [start_node])
        return paths

    def suggest_alternatives(
        self,
        failed_node: T,
        adequacy_check: Callable[[T], bool] | None = None
    ) -> list[T]:
        """
        Suggest alternative nodes that share the same predecessors as the failed node.
        Useful for finding parallel branches that can substitute the failed step.
        """
        # Build predecessor map
        predecessors: dict[T, list[T]] = {}
        for u, neighbors in self._graph.items():
            for v in neighbors:
                if v not in predecessors:
                    predecessors[v] = []
                predecessors[v].append(u)

        parents = predecessors.get(failed_node, [])
        alternatives = set()

        for p in parents:
            # Check siblings
            for sibling in self._graph.get(p, []):
                if sibling != failed_node:
                     if adequacy_check is None or adequacy_check(sibling):
                        alternatives.add(sibling)

        return list(alternatives)
