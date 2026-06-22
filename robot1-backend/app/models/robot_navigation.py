from pydantic import BaseModel


class RobotNavigationGoal(BaseModel):
    robot: str
    x: float
    y: float
    yaw: float = 0.0


class RobotInitialPose(BaseModel):
    robot: str
    x: float
    y: float
    yaw: float = 0.0


class RobotNavigationClear(BaseModel):
    robot: str
