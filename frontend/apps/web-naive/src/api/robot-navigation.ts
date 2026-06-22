import { requestClient } from '#/api/request';

export interface RobotNavigationRect {
  height: number;
  width: number;
  x: number;
  y: number;
}

export interface RobotNavigationMapData {
  costmapZones: RobotNavigationRect[];
  legend: Record<string, string>;
  obstacles: RobotNavigationRect[];
  robot: string;
  worldSize: number;
}

export async function getRobotNavigationMap(robot: string) {
  return requestClient.get<RobotNavigationMapData>('/robot/navigation/map', {
    params: { robot },
  });
}
