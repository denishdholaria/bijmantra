import numpy as np
import math
from typing import List, Dict, Tuple, Optional, Any
from .kinematics import RobotState

class Sensors:
    def __init__(self, gnss_std_dev: float = 0.5):
        self.gnss_std_dev = gnss_std_dev

    def get_gnss_reading(self, true_x: float, true_y: float) -> Tuple[float, float]:
        """
        Simulate GNSS reading with Gaussian noise.
        """
        noise_x = np.random.normal(0, self.gnss_std_dev)
        noise_y = np.random.normal(0, self.gnss_std_dev)
        return true_x + noise_x, true_y + noise_y

    def simulate_lidar(self, state: RobotState, obstacles: List[Any],
                       max_range: float = 20.0, fov_deg: float = 360.0,
                       num_rays: int = 360) -> List[Tuple[float, float]]:
        """
        Simulate 2D LiDAR scan. Returns list of (x, y) points of hits.
        obstacles: List of numpy arrays (N, 2) representing polygons in local coordinates.
        """
        hits = []
        angle_step = math.radians(fov_deg) / num_rays
        start_angle = state.theta - math.radians(fov_deg) / 2

        # Convert obstacles to segments
        segments = []
        for obs in obstacles:
            if isinstance(obs, np.ndarray):
                points = obs
                for i in range(len(points)):
                    p1 = points[i]
                    p2 = points[(i + 1) % len(points)]
                    segments.append((p1, p2))

        # Ray casting
        for i in range(num_rays):
            ray_angle = start_angle + i * angle_step
            ray_dir = np.array([math.cos(ray_angle), math.sin(ray_angle)])

            closest_dist = max_range
            hit_point = None

            p_start = np.array([state.x, state.y])
            p_end = p_start + ray_dir * max_range

            # Check intersection with segments
            for p1, p2 in segments:
                p1 = np.array(p1)
                p2 = np.array(p2)

                # Line-Line intersection
                # Ray: p_start + t * ray_dir
                # Segment: p1 + u * (p2 - p1)

                v1 = p_start - p1
                v2 = p2 - p1
                v3 = np.array([-ray_dir[1], ray_dir[0]])

                dot = np.dot(v2, v3)
                if abs(dot) < 1e-6:
                    continue

                t1 = np.cross(v2, v1) / dot
                t2 = np.dot(v1, v3) / dot

                if t1 >= 0 and t1 <= closest_dist and 0 <= t2 <= 1: # t1 <= closest_dist because ray length is max_range
                    # Actually t1 is distance if ray_dir is normalized?
                    # No, t1 is scalar for ray vector. If ray_dir is normalized, t1 is distance.
                    # My ray_dir is normalized.

                    # Wait, np.cross for 2D vectors returns scalar (z-component).
                    # a x b = ax*by - ay*bx
                    cross_v2_v1 = v2[0]*v1[1] - v2[1]*v1[0]
                    # dot v2 . v3? v3 is orthogonal to ray_dir.
                    # This is standard parametric intersection.

                    # Let's use simpler logic if possible, but this is fine.
                    # t = (q - p) x s / (r x s)

                    # p = p_start, r = ray_dir
                    # q = p1, s = p2 - p1

                    r = ray_dir
                    s = p2 - p1
                    r_cross_s = r[0]*s[1] - r[1]*s[0]

                    if abs(r_cross_s) < 1e-6:
                        continue

                    q_minus_p = p1 - p_start
                    t = (q_minus_p[0]*s[1] - q_minus_p[1]*s[0]) / r_cross_s
                    u = (q_minus_p[0]*r[1] - q_minus_p[1]*r[0]) / r_cross_s

                    if 0 <= t <= closest_dist and 0 <= u <= 1:
                        closest_dist = t
                        hit_point = p_start + t * r

            if hit_point is not None:
                hits.append((float(hit_point[0]), float(hit_point[1])))

        return hits

    def get_camera_fov(self, state: RobotState, h_fov_deg: float = 60.0,
                       aspect_ratio: float = 1.33, height: float = 1.5,
                       pitch_deg: float = -30.0) -> List[Tuple[float, float]]:
        """
        Calculate the 4 corners of the camera footprint on the ground (z=0).
        height: Camera height from ground.
        pitch_deg: Camera pitch (0 is horizontal, -90 is looking down).
        """
        # Simple pinhole model projection
        # We transform 4 corners of image plane to ground plane

        # Camera coordinates: X right, Y down, Z forward
        # World coordinates: X East, Y North, Z Up

        # This can be complex. Let's simplify.
        # We project rays from camera center through image corners to intersection with Z=0 plane.

        v_fov_deg = 2 * math.degrees(math.atan(math.tan(math.radians(h_fov_deg)/2) / aspect_ratio))

        pitch = math.radians(pitch_deg)
        yaw = state.theta

        # Direction vectors for 4 corners in camera frame
        # Top-Left, Top-Right, Bottom-Right, Bottom-Left
        # Assuming camera looks down (pitch < 0)

        half_h = math.tan(math.radians(h_fov_deg) / 2)
        half_v = math.tan(math.radians(v_fov_deg) / 2)

        # Rays in Camera Frame (Forward is +Z)
        # But usually in robotics: X forward, Y left, Z up for body.
        # Camera frame: Z forward, X right, Y down.

        corners_cam = [
            np.array([-half_h, -half_v, 1]), # TL
            np.array([ half_h, -half_v, 1]), # TR
            np.array([ half_h,  half_v, 1]), # BR
            np.array([-half_h,  half_v, 1]), # BL
        ]

        # Rotation from Camera to World
        # 1. Camera to Body (Pitch down)
        # R_pitch = Rotation around X axis?
        # If camera looks forward (X body), Z camera is X body.
        # Let's align Camera Z with Look direction.

        # Look vector in World:
        # L = [cos(pitch)cos(yaw), cos(pitch)sin(yaw), sin(pitch)]

        # Right vector in World (assume no roll):
        # R = [sin(yaw), -cos(yaw), 0]

        # Up vector (orthogonal):
        # U = cross(R, L)

        # Ray casting from Camera Position (x, y, height)
        cam_pos = np.array([state.x, state.y, height])

        ground_points = []

        # Construct rotation matrix from Camera to World
        # Cam X -> World Right
        # Cam Y -> World Up (actually Down in image)
        # Cam Z -> World Look

        # L (Look)
        cx, sx = math.cos(yaw), math.sin(yaw)
        cp, sp = math.cos(pitch), math.sin(pitch)

        L = np.array([cp*cx, cp*sx, sp])

        # R (Right) - horizontal
        R = np.array([sx, -cx, 0]) # Wait, if yaw=0 (East), L=[1,0,0], R=[0,-1,0] (South). Correct?
        # Usually East=X, North=Y. Yaw=0 -> X.
        # Right of X is -Y (South). So [0, -1, 0].
        # sin(0)=0, -cos(0)=-1. Correct.

        # U (Up relative to camera) - actually "Down" in camera Y is "Up" in world
        # U_cam = cross(R, L)
        U_cam = np.cross(R, L)

        # Camera orientation matrix M = [R, -U_cam, L] ?
        # Cam x (right) -> R
        # Cam y (down) -> -U_cam (since U_cam is "up" relative to look)
        # Cam z (forward) -> L

        Rot = np.column_stack((R, -U_cam, L))

        for ray_cam in corners_cam:
            ray_world = Rot @ ray_cam
            ray_world = ray_world / np.linalg.norm(ray_world)

            # Intersect with Z=0
            # P = O + t * D
            # P.z = O.z + t * D.z = 0 => t = -O.z / D.z

            if abs(ray_world[2]) > 1e-6:
                t = -cam_pos[2] / ray_world[2]
                if t > 0:
                    p_ground = cam_pos + t * ray_world
                    ground_points.append((float(p_ground[0]), float(p_ground[1])))
                else:
                    # Ray points up (horizon or sky)
                    # Use a max distance or horizon points
                    p_ground = cam_pos + 100 * ray_world # Far point
                    ground_points.append((float(p_ground[0]), float(p_ground[1])))
            else:
                # Parallel to ground
                 p_ground = cam_pos + 100 * ray_world
                 ground_points.append((float(p_ground[0]), float(p_ground[1])))

        return ground_points
