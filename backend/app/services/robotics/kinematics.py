import math
import numpy as np
from dataclasses import dataclass

@dataclass
class RobotState:
    x: float
    y: float
    theta: float  # radians
    v: float = 0.0
    phi: float = 0.0  # steering angle (Ackermann)
    battery_level: float = 100.0  # percentage

class Kinematics:
    def __init__(self, vehicle_type: str = 'differential', wheelbase: float = 1.0,
                 consumption_per_meter: float = 0.01):
        """
        vehicle_type: 'differential' or 'ackermann'
        wheelbase: Distance between axles (Ackermann) or wheel separation (Differential - though usually not needed for simple unicycle model)
        consumption_per_meter: Battery drain per meter traveled (%)
        """
        self.vehicle_type = vehicle_type
        self.wheelbase = wheelbase
        self.consumption_per_meter = consumption_per_meter

    def update(self, state: RobotState, control: dict, dt: float) -> RobotState:
        """
        Update robot state based on control inputs and time step.
        """
        new_state = RobotState(
            x=state.x,
            y=state.y,
            theta=state.theta,
            v=state.v,
            phi=state.phi,
            battery_level=state.battery_level
        )

        if self.vehicle_type == 'ackermann':
            # Control: v (velocity), phi (steering angle)
            v = control.get('v', 0.0)
            phi = control.get('phi', 0.0)

            # Limit steering angle? Let's assume input is valid.

            # Kinematic equations
            # x_dot = v * cos(theta)
            # y_dot = v * sin(theta)
            # theta_dot = (v / L) * tan(phi)

            dx = v * math.cos(new_state.theta) * dt
            dy = v * math.sin(new_state.theta) * dt
            dtheta = (v / self.wheelbase) * math.tan(phi) * dt

            new_state.x += dx
            new_state.y += dy
            new_state.theta += dtheta
            new_state.v = v
            new_state.phi = phi

            distance = math.sqrt(dx**2 + dy**2)

        elif self.vehicle_type == 'differential':
            # Control: v (linear velocity), omega (angular velocity)
            v = control.get('v', 0.0)
            omega = control.get('omega', 0.0)

            # Unicycle model
            # x_dot = v * cos(theta)
            # y_dot = v * sin(theta)
            # theta_dot = omega

            dx = v * math.cos(new_state.theta) * dt
            dy = v * math.sin(new_state.theta) * dt
            dtheta = omega * dt

            new_state.x += dx
            new_state.y += dy
            new_state.theta += dtheta
            new_state.v = v

            distance = math.sqrt(dx**2 + dy**2)

        else:
            raise ValueError(f"Unknown vehicle type: {self.vehicle_type}")

        # Normalize theta
        new_state.theta = math.atan2(math.sin(new_state.theta), math.cos(new_state.theta))

        # Battery consumption
        # Using simple distance based model
        consumption = distance * self.consumption_per_meter
        new_state.battery_level = max(0.0, new_state.battery_level - consumption)

        return new_state
