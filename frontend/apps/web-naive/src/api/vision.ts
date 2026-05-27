import { requestClient } from './request';

export type VisionTrack = 'depth' | 'ir1' | 'ir2' | 'rgb';

export interface StreamProfile {
  stream: string;
  stream_index: number;
  format: string;
  width: number;
  height: number;
  fps: number;
}

export interface VisionStreamsData {
  device: null | { name: string; serial: string };
  rgb: StreamProfile[];
  ir1: StreamProfile[];
  ir2: StreamProfile[];
  depth: StreamProfile[];
}

export interface VisionHealthData {
  running: boolean;
  starting: boolean;
  recording: 'not_recording' | 'recording' | 'started' | 'stopped' | 'stopping';
  record_tracks: string[];
  record_paths: Record<string, string>;
  error: null | string;
  rgb_profile: null | StreamProfile;
  ir1_profile: null | StreamProfile;
  ir2_profile: null | StreamProfile;
  depth_profile: null | StreamProfile;
  frames: Record<string, null | number[]>;
}

export interface VisionStartResponse {
  running: boolean;
  rgb_profile: StreamProfile;
  ir1_profile: StreamProfile;
  ir2_profile: StreamProfile;
  depth_profile: StreamProfile;
}

export interface VisionRecordStartResponse {
  paths: Record<string, string>;
  tracks: string[];
}

export interface VisionRecordStopResponse {
  paths: Record<string, string>;
}

export interface VisionRecordDiscardResponse {
  errors: string[];
  paths: string[];
}

export async function getVisionHealth() {
  return requestClient.get<VisionHealthData>('/vision/health');
}

export async function getVisionStreams() {
  return requestClient.get<VisionStreamsData>('/vision/streams');
}

export async function startVisionPipeline() {
  return requestClient.post<VisionStartResponse>('/vision/start');
}

export async function startVisionRecord(data: { tracks: string[] }) {
  return requestClient.post<VisionRecordStartResponse>('/vision/record/start', data);
}

export async function stopVisionRecord() {
  return requestClient.post<VisionRecordStopResponse>('/vision/record/stop');
}

export async function commitVisionRecord() {
  return requestClient.post<VisionRecordStopResponse>('/vision/record/commit');
}

export async function discardVisionRecord(data: { paths: string[] }) {
  return requestClient.post<VisionRecordDiscardResponse>('/vision/record/discard', data);
}
