import numpy as np
import cv2
import heapq
import math
from typing import List, Tuple, Dict, Optional
from .geo_utils import GeoUtils

class PathPlanner:
    def __init__(self):
        pass

    def parse_boundary(self, geojson: Dict, ref_lat: float, ref_lon: float) -> np.ndarray:
        """
        Parses GeoJSON polygon and returns local XY coordinates as a numpy array of shape (N, 2).
        """
        # Assuming GeoJSON is a Feature or Geometry
        if geojson.get('type') == 'Feature':
            geometry = geojson['geometry']
        else:
            geometry = geojson

        if geometry['type'] != 'Polygon':
            raise ValueError("Only Polygon geometries are supported")

        coords = geometry['coordinates'][0]  # Outer ring

        local_coords = []
        for lon, lat in coords:
            x, y = GeoUtils.latlon_to_xy(lat, lon, ref_lat, ref_lon)
            local_coords.append([x, y])

        return np.array(local_coords, dtype=np.float32)

    def generate_ab_lines(self, boundary: np.ndarray, width: float, angle_deg: float = 0.0) -> List[List[Tuple[float, float]]]:
        """
        Generate AB lines (parallel swaths) for coverage.
        boundary: (N, 2) array of polygon vertices.
        width: Swath width in meters.
        angle_deg: Angle of the lines in degrees.
        """
        # Rotate boundary to align with angle
        angle_rad = math.radians(-angle_deg)
        c, s = math.cos(angle_rad), math.sin(angle_rad)
        rotation_matrix = np.array([[c, -s], [s, c]])

        rotated_boundary = boundary @ rotation_matrix.T

        min_x, min_y = np.min(rotated_boundary, axis=0)
        max_x, max_y = np.max(rotated_boundary, axis=0)

        if width <= 0:
            raise ValueError("Width must be greater than 0")

        lines = []
        current_y = min_y + width / 2

        # We need integer coordinates for cv2.pointPolygonTest
        # But we can implement a simple ray casting or intersection manually if we want float precision.
        # Or use cv2 with scaling.

        # Using cv2.pointPolygonTest requires creating a contour.
        # Let's scale up to keep precision (since cv2 usually works with ints for pixels)
        scale = 100
        contour = (rotated_boundary * scale).astype(np.int32)

        while current_y < max_y:
            # Create a line segment spanning the X range
            # We need to find intersections of y = current_y with the polygon edges.
            intersections = []

            num_points = len(rotated_boundary)
            for i in range(num_points):
                p1 = rotated_boundary[i]
                p2 = rotated_boundary[(i + 1) % num_points]

                # Check if edge crosses current_y
                if (p1[1] <= current_y < p2[1]) or (p2[1] <= current_y < p1[1]):
                    # Calculate x intersection
                    if p1[1] != p2[1]:
                        x_int = p1[0] + (current_y - p1[1]) * (p2[0] - p1[0]) / (p2[1] - p1[1])
                        intersections.append(x_int)

            intersections.sort()

            # Create segments from pairs of intersections
            for i in range(0, len(intersections), 2):
                if i + 1 < len(intersections):
                    x_start = intersections[i]
                    x_end = intersections[i+1]

                    # Transform back to original frame
                    p_start = np.array([x_start, current_y])
                    p_end = np.array([x_end, current_y])

                    # Inverse rotation
                    inv_rotation_matrix = np.array([[c, s], [-s, c]]) # Transpose of rotation matrix (which is orthogonal)

                    # Actually, rotation_matrix was R. rotated = orig @ R.T -> orig = rotated @ R
                    # Wait, R = [[c, -s], [s, c]].
                    # rotated_v = R @ v (column vector) or v @ R.T (row vector).
                    # orig_v = rotated_v @ R (if row vector)
                    # Let's verify:
                    # v = [x, y]. R.T = [[c, s], [-s, c]].
                    # v @ R.T = [x*c - y*s, x*s + y*c]. Correct rotation.
                    # Inverse: v' @ R = [x'*c + y'*s, -x'*s + y'*c].

                    orig_start = p_start @ rotation_matrix
                    orig_end = p_end @ rotation_matrix

                    lines.append([(float(orig_start[0]), float(orig_start[1])),
                                  (float(orig_end[0]), float(orig_end[1]))])

            current_y += width

        return lines

    def a_star(self, start: Tuple[float, float], goal: Tuple[float, float],
               boundary: np.ndarray, obstacles: List[Dict], resolution: float = 1.0) -> List[Tuple[float, float]]:
        """
        A* path planning on a grid.
        """
        min_x, min_y = np.min(boundary, axis=0)
        max_x, max_y = np.max(boundary, axis=0)

        width = int((max_x - min_x) / resolution) + 1
        height = int((max_y - min_y) / resolution) + 1

        grid_origin = np.array([min_x, min_y])

        def to_grid(pos):
            return int((pos[0] - min_x) / resolution), int((pos[1] - min_y) / resolution)

        def to_world(grid_pos):
            return grid_pos[0] * resolution + min_x, grid_pos[1] * resolution + min_y

        start_node = to_grid(start)
        goal_node = to_grid(goal)

        # Check bounds
        if not (0 <= start_node[0] < width and 0 <= start_node[1] < height):
            return [] # Start outside

        # Create obstacle map
        # Use cv2 to fill polygon and obstacles
        # Scale to grid
        scale = 1.0 / resolution
        boundary_grid = ((boundary - grid_origin) * scale).astype(np.int32)

        # 0 = blocked, 1 = free
        grid_map = np.zeros((height, width), dtype=np.uint8)

        # Fill polygon (free space)
        # cv2 uses (x,y) for points, but numpy uses (row, col) = (y, x).
        # fillPoly expects (N, 2) where 2 is (x, y).
        cv2.fillPoly(grid_map, [boundary_grid], 1)

        # Add obstacles (blocked)
        for obs in obstacles:
            # obs is assumed to be numpy array of shape (N, 2) in local coordinates
            if isinstance(obs, np.ndarray):
                obs_grid = ((obs - grid_origin) * scale).astype(np.int32)
                cv2.fillPoly(grid_map, [obs_grid], 0)

        # Ensure start and goal are walkable (sometimes they might be slightly off due to resolution)
        # If strict, we return fail.
        if grid_map[start_node[1], start_node[0]] == 0:
             # Try to find nearest free
             pass

        # A* Implementation
        open_set = []
        heapq.heappush(open_set, (0, start_node))
        came_from = {}
        g_score = {start_node: 0}
        f_score = {start_node: math.hypot(goal_node[0]-start_node[0], goal_node[1]-start_node[1])}

        while open_set:
            current = heapq.heappop(open_set)[1]

            if current == goal_node:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(to_world(current))
                    current = came_from[current]
                path.append(to_world(start_node))
                return path[::-1]

            # Neighbors (8-connectivity)
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]:
                neighbor = (current[0] + dx, current[1] + dy)

                if 0 <= neighbor[0] < width and 0 <= neighbor[1] < height:
                    if grid_map[neighbor[1], neighbor[0]] == 1:
                        dist = math.hypot(dx, dy)
                        tentative_g = g_score[current] + dist

                        if neighbor not in g_score or tentative_g < g_score[neighbor]:
                            came_from[neighbor] = current
                            g_score[neighbor] = tentative_g
                            f = tentative_g + math.hypot(goal_node[0]-neighbor[0], goal_node[1]-neighbor[1])
                            f_score[neighbor] = f
                            heapq.heappush(open_set, (f, neighbor))

        return [] # No path found

    def boustrophedon(self, boundary: np.ndarray, width: float) -> List[Tuple[float, float]]:
        """
        Generates a boustrophedon (snake-like) path.
        """
        lines = self.generate_ab_lines(boundary, width)

        path = []
        for i, line in enumerate(lines):
            p1, p2 = line
            if i % 2 == 0:
                path.append(p1)
                path.append(p2)
            else:
                path.append(p2)
                path.append(p1)

        return path
