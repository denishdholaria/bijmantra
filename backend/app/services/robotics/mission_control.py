import math
import numpy as np
from typing import Dict, List, Any
from .path_planning import PathPlanner
from .kinematics import Kinematics, RobotState
from .sensors import Sensors
from .geo_utils import GeoUtils

class MissionControl:
    def __init__(self):
        self.planner = PathPlanner()

    def simulate(self, mission_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a simulation based on mission data.
        """
        # 1. Setup Environment
        ref_lat = mission_data.get('origin', {}).get('lat', 0.0)
        ref_lon = mission_data.get('origin', {}).get('lon', 0.0)

        field_boundary = self.planner.parse_boundary(mission_data['field_boundary'], ref_lat, ref_lon)
        obstacles_data = mission_data.get('obstacles', [])

        local_obstacles = []
        for obs in obstacles_data:
            try:
                # Reuse parse_boundary for obstacles assuming they are GeoJSON polygons
                local_obs = self.planner.parse_boundary(obs, ref_lat, ref_lon)
                local_obstacles.append(local_obs)
            except Exception:
                # Log or skip invalid obstacles
                pass

        # 2. Plan Path
        path_type = mission_data.get('path_config', {}).get('type', 'coverage')
        width = mission_data.get('path_config', {}).get('width', 2.0)

        if path_type == 'coverage':
            path_points = self.planner.boustrophedon(field_boundary, width)
        elif path_type == 'astar':
            start = mission_data['path_config']['start'] # (x,y)
            goal = mission_data['path_config']['goal']
            path_points = self.planner.a_star(start, goal, field_boundary, local_obstacles)
        else:
            # Assume waypoints provided directly
            path_points = mission_data.get('waypoints', [])

        if not path_points:
            return {"error": "No path generated"}

        # 3. Setup Robot
        vehicle_config = mission_data.get('vehicle_config', {})
        kinematics = Kinematics(
            vehicle_type=vehicle_config.get('type', 'differential'),
            wheelbase=vehicle_config.get('wheelbase', 1.0),
            consumption_per_meter=vehicle_config.get('consumption', 0.01)
        )
        sensors = Sensors(gnss_std_dev=vehicle_config.get('gnss_noise', 0.5))

        start_x, start_y = path_points[0]
        # Initial heading towards second point
        if len(path_points) > 1:
            dx = path_points[1][0] - start_x
            dy = path_points[1][1] - start_y
            start_theta = math.atan2(dy, dx)
        else:
            start_theta = 0.0

        state = RobotState(x=start_x, y=start_y, theta=start_theta, battery_level=100.0)

        # 4. Simulation Loop
        dt = mission_data.get('simulation_config', {}).get('dt', 0.1)
        max_duration = mission_data.get('simulation_config', {}).get('duration', 600)
        target_speed = vehicle_config.get('speed', 1.0)

        telemetry = []
        current_time = 0.0

        current_idx = 0
        lookahead_dist = 2.0 # For Pure Pursuit

        while current_time < max_duration and current_idx < len(path_points):
            # Controller (Simple Pure Pursuit)
            target_pt = path_points[current_idx]
            dist_to_target = math.hypot(target_pt[0] - state.x, target_pt[1] - state.y)

            if dist_to_target < lookahead_dist:
                current_idx += 1
                if current_idx >= len(path_points):
                    break
                target_pt = path_points[current_idx]

            # Control Logic
            dx = target_pt[0] - state.x
            dy = target_pt[1] - state.y
            target_heading = math.atan2(dy, dx)

            angle_diff = target_heading - state.theta
            # Normalize angle
            angle_diff = (angle_diff + math.pi) % (2 * math.pi) - math.pi

            control = {}
            if kinematics.vehicle_type == 'differential':
                control['v'] = target_speed
                control['omega'] = 2.0 * angle_diff # P-controller for turn
            elif kinematics.vehicle_type == 'ackermann':
                control['v'] = target_speed
                # Pure Pursuit steering angle: phi = atan(2L sin(alpha) / ld)
                # alpha is angle difference between heading and lookahead vector
                # But here simple P control on heading error
                control['phi'] = np.clip(angle_diff, -0.5, 0.5) # limit steering

            # Step Physics
            state = kinematics.update(state, control, dt)

            # Step Sensors
            gnss_x, gnss_y = sensors.get_gnss_reading(state.x, state.y)
            gnss_lat, gnss_lon = GeoUtils.xy_to_latlon(gnss_x, gnss_y, ref_lat, ref_lon)

            lidar_hits = sensors.simulate_lidar(state, local_obstacles)
            fov_poly = sensors.get_camera_fov(state)

            # Record
            telemetry.append({
                "timestamp": round(current_time, 2),
                "pose": {"x": round(state.x, 2), "y": round(state.y, 2), "theta": round(state.theta, 3)},
                "battery": round(state.battery_level, 2),
                "gnss": {"lat": gnss_lat, "lon": gnss_lon},
                # "lidar": lidar_hits, # Omit to save space, or send count
                "lidar_count": len(lidar_hits),
                "camera_fov": fov_poly
            })

            current_time += dt

            if state.battery_level <= 0:
                break

        return {
            "mission_status": "completed" if current_idx >= len(path_points) else "timeout" if state.battery_level > 0 else "battery_empty",
            "path": path_points,
            "telemetry": telemetry
        }
