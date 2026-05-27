import { requestClient } from '#/api/request';

export interface InspectionInspector {
  id: string;
  name: string;
  phone: string;
  shift: string;
  status: string;
  title: string;
}

export interface InspectionOption {
  label: string;
  value: string;
}

export interface InspectionPoint {
  area: string;
  code: string;
  description: string;
  deviceName: string;
  deviceType: string;
  id: string;
  inspectorName: string;
  lastInspectionTime: string;
  name: string;
  riskLevel: 'high' | 'low' | 'medium';
  status: 'normal' | 'offline' | 'warning';
}

export interface InspectionTask {
  checklist: string[];
  description: string;
  frequency: string;
  id: string;
  inspectorId: string;
  inspectorName: string;
  lastExecutionTime: string;
  plannedEnd: string;
  plannedStart: string;
  point?: InspectionPoint;
  pointId: string;
  pointName: string;
  priority: 'high' | 'low' | 'medium';
  status: 'completed' | 'in_progress' | 'paused' | 'pending' | 'scheduled';
  title: string;
}

export interface InspectionRecord {
  finishedAt: string;
  id: string;
  inspectorName: string;
  pointName: string;
  result: 'abnormal' | 'normal' | 'warning';
  summary: string;
  taskId: string;
  taskTitle: string;
}

export interface InspectionAlert {
  content: string;
  createdAt: string;
  id: string;
  level: 'high' | 'low' | 'medium';
  title: string;
}

export interface InspectionDashboardData {
  alerts: InspectionAlert[];
  recentRecords: InspectionRecord[];
  statusDistribution: Array<{
    label: string;
    type: 'error' | 'success' | 'warning';
    value: number;
  }>;
  summary: {
    activeTasks: number;
    completedTasks: number;
    offlinePoints: number;
    onDutyInspectors: number;
    pendingTasks: number;
    totalPoints: number;
    warningPoints: number;
  };
  upcomingTasks: InspectionTask[];
}

export interface InspectionPointsResponse {
  areaOptions: InspectionOption[];
  items: InspectionPoint[];
  stats: {
    normal: number;
    offline: number;
    warning: number;
  };
  statusOptions: InspectionOption[];
  total: number;
}

export interface InspectionTasksResponse {
  inspectorOptions: InspectionOption[];
  items: InspectionTask[];
  priorityOptions: InspectionOption[];
  statusOptions: InspectionOption[];
  summary: {
    completed: number;
    inProgress: number;
    paused: number;
    pending: number;
  };
  total: number;
}

export interface InspectionRecordsResponse {
  items: InspectionRecord[];
  resultOptions: InspectionOption[];
  total: number;
}

export interface InspectionDataRow {
  algorithm: string;
  detail: string;
  id: string;
  pointName: string;
  taskNo: string;
  time: string;
  value: string;
}

export interface InspectionDataResponse {
  algorithmOptions: InspectionOption[];
  items: InspectionDataRow[];
  pointOptions: InspectionOption[];
  total: number;
}

export interface InspectionRealtimeRow {
  id: string;
  metric: string;
  pointName: string;
  status: 'normal' | 'offline' | 'warning';
  time: string;
  value: string;
}

export interface InspectionRealtimeResponse {
  items: InspectionRealtimeRow[];
  statusOptions: InspectionOption[];
  total: number;
}

export interface InspectionAlertsResponse {
  items: InspectionAlert[];
  levelOptions: InspectionOption[];
  total: number;
}

export interface InspectionBatch {
  batchNo: string;
  finishedAt: string;
  id: string;
  pointCount: number;
  route: string;
  startedAt: string;
  status: 'completed' | 'running' | 'unfinished';
  type: string;
}

export interface InspectionBatchesResponse {
  items: InspectionBatch[];
  statusOptions: InspectionOption[];
  total: number;
}

export interface InspectionCommand {
  command: string;
  createdAt: string;
  id: string;
  operator: string;
  result: string;
  status: 'failed' | 'running' | 'success';
  target: string;
}

export interface InspectionCommandsResponse {
  items: InspectionCommand[];
  statusOptions: InspectionOption[];
  total: number;
}

export interface InspectionMetaData {
  inspectors: InspectionInspector[];
  pointOptions: InspectionOption[];
  priorityOptions: InspectionOption[];
  shiftOptions: InspectionOption[];
  statusOptions: InspectionOption[];
}

export interface InspectionSchedulePayload {
  executionTime: string;
  inspectorId: string;
  note?: string;
  reminderMinutes: number;
  shift: string;
}

export interface InspectionTaskPayload {
  checklist: string[];
  description: string;
  frequency: string;
  inspectorId: string;
  plannedEnd: string;
  plannedStart: string;
  pointId: string;
  priority: 'high' | 'low' | 'medium';
  status: 'completed' | 'in_progress' | 'paused' | 'pending' | 'scheduled';
  title: string;
}

export async function getInspectionDashboard() {
  return requestClient.get<InspectionDashboardData>('/inspection/dashboard');
}

export async function getInspectionMeta() {
  return requestClient.get<InspectionMetaData>('/inspection/meta');
}

export async function getInspectionPoints(params?: Record<string, any>) {
  return requestClient.get<InspectionPointsResponse>('/inspection/points', {
    params,
  });
}

export async function getInspectionTasks(params?: Record<string, any>) {
  return requestClient.get<InspectionTasksResponse>('/inspection/tasks', {
    params,
  });
}

export async function getInspectionRecords(params?: Record<string, any>) {
  return requestClient.get<InspectionRecordsResponse>('/inspection/records', {
    params,
  });
}

export async function getInspectionData(params?: Record<string, any>) {
  return requestClient.get<InspectionDataResponse>('/inspection/inspection-data', {
    params,
  });
}

export async function getInspectionRealtimeData(params?: Record<string, any>) {
  return requestClient.get<InspectionRealtimeResponse>('/inspection/realtime-data', {
    params,
  });
}

export async function getInspectionAlerts(params?: Record<string, any>) {
  return requestClient.get<InspectionAlertsResponse>('/inspection/alerts', {
    params,
  });
}

export async function getInspectionBatches(params?: Record<string, any>) {
  return requestClient.get<InspectionBatchesResponse>('/inspection/batches', {
    params,
  });
}

export async function getInspectionCommands(params?: Record<string, any>) {
  return requestClient.get<InspectionCommandsResponse>('/inspection/commands', {
    params,
  });
}

export async function getInspectionTaskDetail(taskId: string) {
  return requestClient.get<InspectionTask>(`/inspection/tasks/${taskId}`);
}

export async function updateInspectionTask(
  taskId: string,
  data: InspectionTaskPayload,
) {
  return requestClient.put<InspectionTask>(`/inspection/tasks/${taskId}`, data);
}

export async function scheduleInspectionTask(
  taskId: string,
  data: InspectionSchedulePayload,
) {
  return requestClient.post<{
    schedule: {
      createdAt: string;
      executionTime: string;
      id: string;
      inspectorId: string;
      inspectorName: string;
      note: string;
      reminderMinutes: number;
      shift: string;
      taskId: string;
      taskTitle: string;
    };
    task: InspectionTask;
  }>(`/inspection/tasks/${taskId}/schedule`, data);
}
