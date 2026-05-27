import type { VideoRealtimeFrame } from '../transport/transport-client';
import type { UvRegion } from '../webgpu/colormap-pipelines';

import type { VisionHealthData, VisionTrack } from '#/api/vision';

import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';

import { message } from '#/adapter/naive';
import {
  commitVisionRecord,
  discardVisionRecord,
  getVisionHealth,
  startVisionRecord,
  stopVisionRecord,
} from '#/api/vision';

import {
  ensureRealtimeSessionStarted,
  restartRealtimeSession,
  subscribeRealtimeFrames,
  useRealtimeSessionState,
} from '../transport/realtime-session';
import { WebGpuRealtimeRenderer } from '../webgpu/colormap-pipelines';

export type ConnState = 'connecting' | 'error' | 'idle' | 'live';
export type RecordUiState = 'idle' | 'recording' | 'stopped';
export type RecordableKey = VisionTrack;
export type TrackSlot = VisionTrack;

export interface RealtimeVideoTile {
  key: TrackSlot;
  live: boolean;
  title: string;
}

const TRACK_ORDER: TrackSlot[] = ['rgb', 'depth', 'ir1', 'ir2'];
const TRACK_TITLES: Record<TrackSlot, string> = {
  depth: 'Depth',
  ir1: 'IR 1',
  ir2: 'IR 2',
  rgb: 'RGB',
};
// 与后端 MOSAIC_LAYOUT 一一对应：rgb 左上、depth 右上、ir1 左下、ir2 右下。
const TRACK_REGIONS: Record<TrackSlot, UvRegion> = {
  depth: { offsetU: 0.5, offsetV: 0, scaleU: 0.5, scaleV: 0.5 },
  ir1: { offsetU: 0, offsetV: 0.5, scaleU: 0.5, scaleV: 0.5 },
  ir2: { offsetU: 0.5, offsetV: 0.5, scaleU: 0.5, scaleV: 0.5 },
  rgb: { offsetU: 0, offsetV: 0, scaleU: 0.5, scaleV: 0.5 },
};
export function useRealtimeMonitor() {
  const { connState, connText } = useRealtimeSessionState();
  const backendError = ref<null | string>(null);
  const deviceInfo = ref('1280×720 @ 30fps');
  const lastRecordPaths = ref<Record<string, string>>({});
  const recordState = ref<RecordUiState>('idle');
  const recordTracks = ref<RecordableKey[]>(['rgb', 'ir1', 'ir2', 'depth']);
  const reconnecting = ref(false);
  const running = computed(() => connState.value === 'connecting' || connState.value === 'live');

  const renderers = new Map<TrackSlot, WebGpuRealtimeRenderer>();
  const rendererTokens = new Map<TrackSlot, number>();
  let unsubscribeFrames: (() => void) | null = null;

  const tileLive = reactive<Record<TrackSlot, boolean>>({
    depth: false,
    ir1: false,
    ir2: false,
    rgb: false,
  });

  const isRecording = computed(
    () => recordState.value === 'recording' || recordState.value === 'stopped',
  );
  const recordBtnLabel = computed(() =>
    recordState.value === 'recording' ? '结束录制' : '开始录制',
  );
  const videoTiles = computed<RealtimeVideoTile[]>(() =>
    TRACK_ORDER.map((slot) => ({ key: slot, live: tileLive[slot], title: TRACK_TITLES[slot] })),
  );

  const recordableOptions: Array<{ label: string; value: RecordableKey }> = [
    { label: 'RGB', value: 'rgb' },
    { label: 'IR1', value: 'ir1' },
    { label: 'IR2', value: 'ir2' },
    { label: 'Depth', value: 'depth' },
  ];

  async function onDiscardClick() {
    const paths = Object.values(lastRecordPaths.value);
    if (paths.length === 0) {
      resetRecordState();
      return;
    }
    const response = await requestOrNull(() => discardVisionRecord({ paths }));
    if (!response) {
      return;
    }
    resetRecordState();
  }

  async function onRecordClick() {
    if (recordState.value === 'idle') {
      const tracks = [...recordTracks.value];
      if (tracks.length === 0) {
        message.warning('请至少勾选一个录制轨道');
        return;
      }
      const response = await requestOrNull(() => startVisionRecord({ tracks }));
      if (!response) {
        return;
      }
      lastRecordPaths.value = response.paths || {};
      recordState.value = 'recording';
      return;
    }

    if (recordState.value === 'recording') {
      const response = await requestOrNull(() => stopVisionRecord());
      if (!response) {
        return;
      }
      lastRecordPaths.value = response.paths || lastRecordPaths.value;
      recordState.value = 'stopped';
    }
  }

  async function onSaveClick() {
    const response = await requestOrNull(() => commitVisionRecord());
    if (!response) {
      return;
    }
    resetRecordState();
  }

  async function onReconnectClick() {
    if (reconnecting.value) {
      return;
    }
    reconnecting.value = true;
    setAllTilesLive(false);
    try {
      await restartRealtimeSession();
    } catch (error) {
      console.error('[vision] reconnect failed', error);
      message.error('视频流重新连接失败');
    } finally {
      reconnecting.value = false;
    }
  }

  async function registerCanvas(slot: TrackSlot, canvas: HTMLCanvasElement | null) {
    const token = (rendererTokens.get(slot) || 0) + 1;
    rendererTokens.set(slot, token);
    renderers.get(slot)?.dispose();
    renderers.delete(slot);
    if (!canvas) {
      return;
    }
    try {
      const renderer = await WebGpuRealtimeRenderer.create(canvas, TRACK_REGIONS[slot]);
      if (rendererTokens.get(slot) !== token) {
        renderer.dispose();
        return;
      }
      renderers.set(slot, renderer);
    } catch (error: any) {
      message.error(`初始化 ${TRACK_TITLES[slot]} 渲染失败：${error?.message || error}`);
    }
  }

  function resetRecordState() {
    recordState.value = 'idle';
    lastRecordPaths.value = {};
  }

  function renderMosaicFrame(frame: VideoRealtimeFrame) {
    if (renderers.size === 0) {
      return;
    }
    for (const [slot, renderer] of renderers) {
      renderer.renderVideo(frame);
      tileLive[slot] = true;
    }
  }

  function setAllTilesLive(live: boolean) {
    for (const slot of TRACK_ORDER) {
      tileLive[slot] = live;
    }
  }

  function syncStatusFromServer(payload: VisionHealthData) {
    backendError.value = payload.error ?? null;

    if (payload.recording === 'started' || payload.recording === 'recording') {
      recordState.value = 'recording';
      lastRecordPaths.value = payload.record_paths || {};
      return;
    }
    if (payload.recording === 'stopped' || payload.recording === 'stopping') {
      recordState.value = 'stopped';
      lastRecordPaths.value = payload.record_paths || {};
      return;
    }
    resetRecordState();
  }

  async function requestOrNull<T>(request: () => Promise<T>): Promise<null | T> {
    try {
      return await request();
    } catch (error) {
      console.error('[vision] request failed', error);
      message.error('视觉服务请求失败');
      return null;
    }
  }

  // 连接状态脱离“live”时立刻重置各 tile 为离线。
  const stopWatchConn = watch(connState, (value) => {
    if (value !== 'live') {
      setAllTilesLive(false);
    }
  });

  onMounted(async () => {
    unsubscribeFrames = subscribeRealtimeFrames(renderMosaicFrame);
    const health = await requestOrNull(() => getVisionHealth());
    if (health) {
      syncStatusFromServer(health);
    }
    await requestOrNull(() => ensureRealtimeSessionStarted());
  });

  onBeforeUnmount(() => {
    unsubscribeFrames?.();
    unsubscribeFrames = null;
    stopWatchConn();
    setAllTilesLive(false);
    for (const renderer of renderers.values()) {
      renderer.dispose();
    }
    renderers.clear();
    rendererTokens.clear();
  });

  return {
    backendError,
    connState,
    connText,
    deviceInfo,
    isRecording,
    lastRecordPaths,
    onDiscardClick,
    onRecordClick,
    onReconnectClick,
    onSaveClick,
    recordBtnLabel,
    recordState,
    recordTracks,
    recordableOptions,
    reconnecting,
    registerCanvas,
    running,
    videoTiles,
  };
}
