<script lang="ts" setup>
import type { SelectProps } from 'ant-design-vue';

import { computed, onBeforeUnmount, onMounted, reactive, ref, shallowRef, watch } from 'vue';

import { Page } from '@vben/common-ui';

import {
  Button,
  Card,
  Checkbox,
  message,
  Select,
  Space,
  Tag,
} from 'ant-design-vue';

import { requestClient } from '#/api/request';

defineOptions({ name: 'RealSenseMonitor' });

// ───────────────────────── Types ─────────────────────────

interface StreamProfile {
  stream: string;
  stream_index: number;
  format: string;
  width: number;
  height: number;
  fps: number;
}

interface StreamsData {
  device: { name: string; serial: string } | null;
  rgb: StreamProfile[];
  ir1: StreamProfile[];
  ir2: StreamProfile[];
  depth: StreamProfile[];
}

interface HealthData {
  running: boolean;
  starting: boolean;
  recording: 'not_recording' | 'started' | 'recording' | 'stopped';
  record_tracks: string[];
  record_paths: Record<string, string>;
  error: string | null;
  rgb_profile: StreamProfile | null;
  ir1_profile: StreamProfile | null;
  ir2_profile: StreamProfile | null;
  depth_profile: StreamProfile | null;
  frames: Record<string, number[] | null>;
}

type BucketKey = 'rgb' | 'ir1' | 'ir2' | 'depth';
type RecordableKey = 'rgb' | 'seg' | 'depth' | 'ir1' | 'ir2';
type ConnState = 'idle' | 'connecting' | 'live' | 'error';
type RecordUiState = 'idle' | 'recording' | 'stopped';

interface BucketForm {
  format: string;
  resolution: string; // "WxH"
  fps: string; // 字符串，和 a-select option value 保持一致
}

// ───────────────────────── Reactive state ─────────────────────────

const deviceInfo = ref<string>('尚未连接');
const connState = ref<ConnState>('idle');
const connText = ref<string>('未连接');

const running = ref<boolean>(false);
const applying = ref<boolean>(false);

const recordState = ref<RecordUiState>('idle');
const recordTracks = ref<RecordableKey[]>(['rgb', 'seg', 'depth', 'ir1', 'ir2']);
const lastRecordPaths = ref<Record<string, string>>({});
const backendError = ref<string | null>(null);

const recordableOptions: { label: string; value: RecordableKey }[] = [
  { label: 'RGB', value: 'rgb' },
  { label: 'Segmentation', value: 'seg' },
  { label: 'Depth', value: 'depth' },
  { label: 'IR1', value: 'ir1' },
  { label: 'IR2', value: 'ir2' },
];

const profiles = reactive<Record<BucketKey, StreamProfile[]>>({
  rgb: [],
  ir1: [],
  ir2: [],
  depth: [],
});

const forms = reactive<Record<BucketKey, BucketForm>>({
  rgb: { format: '', resolution: '', fps: '' },
  ir1: { format: '', resolution: '', fps: '' },
  ir2: { format: '', resolution: '', fps: '' },
  depth: { format: '', resolution: '', fps: '' },
});

// ───────────────────────── Video refs & WebRTC ─────────────────────────

const videoRgb = ref<HTMLVideoElement | null>(null);
const videoSeg = ref<HTMLVideoElement | null>(null);
const videoIr1 = ref<HTMLVideoElement | null>(null);
const videoIr2 = ref<HTMLVideoElement | null>(null);
const videoDepth = ref<HTMLVideoElement | null>(null);

// 后端 WEBRTC_TRACK_ORDER 固定为 rgb / ir1 / ir2 / depth / seg，前端按此顺序绑定
const TRACK_ORDER = ['rgb', 'ir1', 'ir2', 'depth', 'seg'] as const;
type TrackSlot = (typeof TRACK_ORDER)[number];

function tileRef(slot: TrackSlot): HTMLVideoElement | null {
  switch (slot) {
    case 'rgb':
      return videoRgb.value;
    case 'seg':
      return videoSeg.value;
    case 'ir1':
      return videoIr1.value;
    case 'ir2':
      return videoIr2.value;
    case 'depth':
      return videoDepth.value;
    default:
      return null;
  }
}

const tileLive = reactive<Record<TrackSlot, boolean>>({
  rgb: false,
  ir1: false,
  ir2: false,
  depth: false,
  seg: false,
});

const pc = shallowRef<RTCPeerConnection | null>(null);
const ws = shallowRef<WebSocket | null>(null);
let trackIndex = 0;
let webrtcStarted = false;

// ───────────────────────── Profile cascading options ─────────────────────────

function uniqueSorted<T>(values: T[], cmp: (a: T, b: T) => number): T[] {
  return [...new Set(values)].sort(cmp);
}

function filteredPool(bucket: BucketKey): StreamProfile[] {
  // IR1 / IR2 分别固定到 stream_index=1 / 2
  const pool = profiles[bucket];
  if (bucket === 'ir1') return pool.filter((p) => p.stream_index === 1);
  if (bucket === 'ir2') return pool.filter((p) => p.stream_index === 2);
  return pool;
}

function formatOptions(bucket: BucketKey): SelectProps['options'] {
  const pool = filteredPool(bucket);
  return uniqueSorted(
    pool.map((p) => p.format),
    (a, b) => a.localeCompare(b),
  ).map((v) => ({ label: v, value: v }));
}

function resolutionOptions(bucket: BucketKey): SelectProps['options'] {
  const form = forms[bucket];
  const pool = filteredPool(bucket).filter((p) => p.format === form.format);
  return uniqueSorted(
    pool.map((p) => `${p.width}x${p.height}`),
    (a, b) => {
      const [aw, ah] = a.split('x').map(Number);
      const [bw, bh] = b.split('x').map(Number);
      return aw * ah - bw * bh;
    },
  ).map((v) => ({ label: v, value: v }));
}

function fpsOptions(bucket: BucketKey): SelectProps['options'] {
  const form = forms[bucket];
  const [w, h] = (form.resolution || '0x0').split('x').map(Number);
  const pool = filteredPool(bucket).filter(
    (p) => p.format === form.format && p.width === w && p.height === h,
  );
  return uniqueSorted(
    pool.map((p) => p.fps),
    (a, b) => a - b,
  ).map((v) => ({ label: `${v} fps`, value: String(v) }));
}

function getSelection(bucket: BucketKey): StreamProfile | null {
  const form = forms[bucket];
  if (!form.format || !form.resolution || !form.fps) return null;
  const [w, h] = form.resolution.split('x').map(Number);
  const fps = Number(form.fps);
  return (
    filteredPool(bucket).find(
      (p) => p.format === form.format && p.width === w && p.height === h && p.fps === fps,
    ) ?? null
  );
}

// 级联：format 变了要重置 resolution + fps；resolution 变了重置 fps
function onFormatChange(bucket: BucketKey) {
  const opts = resolutionOptions(bucket) ?? [];
  const first = (opts[0]?.value as string) ?? '';
  forms[bucket].resolution = first;
  onResolutionChange(bucket);
}

function onResolutionChange(bucket: BucketKey) {
  const opts = fpsOptions(bucket) ?? [];
  const first = (opts[0]?.value as string) ?? '';
  forms[bucket].fps = first;
}

// 给一组偏好挑一个作为默认值
function pickPreferred(
  bucket: BucketKey,
  prefer: Partial<StreamProfile>[],
): void {
  const pool = profiles[bucket];
  for (const want of prefer) {
    const match = pool.find(
      (p) =>
        (!want.format || p.format === want.format) &&
        (!want.width || p.width === want.width) &&
        (!want.height || p.height === want.height) &&
        (!want.fps || p.fps === want.fps) &&
        (want.stream_index === undefined || p.stream_index === want.stream_index),
    );
    if (!match) continue;
    forms[bucket].format = match.format;
    forms[bucket].resolution = `${match.width}x${match.height}`;
    forms[bucket].fps = String(match.fps);
    return;
  }
  // 没匹配则回退第一条可用 profile
  const pool2 = filteredPool(bucket);
  if (pool2.length > 0) {
    const first = pool2[0];
    forms[bucket].format = first.format;
    forms[bucket].resolution = `${first.width}x${first.height}`;
    forms[bucket].fps = String(first.fps);
  }
}

// ───────────────────────── 按钮 / 状态派生 ─────────────────────────

const isRecording = computed(
  () => recordState.value === 'recording' || recordState.value === 'stopped',
);

const configDisabled = computed(() => applying.value || isRecording.value);

const startBtnLabel = computed(() => {
  if (applying.value) return running.value ? '应用中…' : '启动中…';
  return running.value ? '应用配置' : '开始';
});

const recordBtnLabel = computed(() =>
  recordState.value === 'recording' ? '结束录制' : '开始录制',
);

// ───────────────────────── HTTP 调用 ─────────────────────────

async function callApi<T>(
  path: string,
  options?: { method?: 'GET' | 'POST'; data?: unknown },
): Promise<T | null> {
  try {
    if ((options?.method ?? 'GET') === 'GET') {
      return await requestClient.get<T>(path);
    }
    return await requestClient.post<T>(path, options?.data ?? {});
  } catch (error) {
    // 请求拦截器已弹过 message，这里只返回 null
    console.error(`[vision] ${path} 失败`, error);
    return null;
  }
}

async function loadStreams(): Promise<boolean> {
  const data = await callApi<StreamsData>('/vision/streams');
  if (!data) return false;
  deviceInfo.value = data.device
    ? `${data.device.name} · SN ${data.device.serial}`
    : '未检测到设备';
  console.info('[vision] stream device:', deviceInfo.value);
  profiles.rgb = data.rgb || [];
  profiles.ir1 = data.ir1 || [];
  profiles.ir2 = data.ir2 || [];
  profiles.depth = data.depth || [];

  if (profiles.rgb.length === 0) message.warning('未发现 RGB 流配置');
  if (profiles.ir1.length === 0) message.warning('未发现红外 1 流配置');
  if (profiles.ir2.length === 0) message.warning('未发现红外 2 流配置');
  if (profiles.depth.length === 0) message.warning('未发现深度流配置');

  pickPreferred('rgb', [
    { format: 'rgb8', width: 640, height: 480, fps: 30 },
    { format: 'rgb8', width: 640, height: 480 },
    { format: 'rgb8' },
  ]);
  pickPreferred('ir1', [
    { stream_index: 1, format: 'y8', width: 640, height: 480, fps: 30 },
    { stream_index: 1, format: 'y8', width: 640, height: 480 },
    { stream_index: 1, format: 'y8' },
    { stream_index: 1 },
  ]);
  pickPreferred('ir2', [
    { stream_index: 2, format: 'y8', width: 640, height: 480, fps: 30 },
    { stream_index: 2, format: 'y8', width: 640, height: 480 },
    { stream_index: 2, format: 'y8' },
    { stream_index: 2 },
  ]);
  pickPreferred('depth', [
    { format: 'z16', width: 640, height: 480, fps: 30 },
    { format: 'z16', width: 640, height: 480 },
    { format: 'z16' },
  ]);
  return true;
}

async function onApplyClick() {
  const rgb = getSelection('rgb');
  const ir1 = getSelection('ir1');
  const ir2 = getSelection('ir2');
  const depth = getSelection('depth');
  if (!rgb) return message.warning('请选择 RGB 参数');
  if (!ir1) return message.warning('请选择 IR1 参数');
  if (!ir2) return message.warning('请选择 IR2 参数');
  if (!depth) return message.warning('请选择深度参数');

  applying.value = true;
  setConnState('connecting');
  try {
    const resp = await callApi<{
      running: boolean;
      rgb_profile: StreamProfile;
      ir1_profile: StreamProfile;
      ir2_profile: StreamProfile;
      depth_profile: StreamProfile;
    }>('/vision/start', {
      method: 'POST',
      data: { rgb, ir1, ir2, depth },
    });
    if (!resp) {
      setConnState(running.value ? 'live' : 'idle');
      return;
    }
    running.value = true;
    if (!webrtcStarted) {
      webrtcStarted = true;
      await startWebRTC();
    }
  } finally {
    applying.value = false;
  }
}

// 录制
async function onRecordClick() {
  if (recordState.value === 'idle') {
    const tracks = [...recordTracks.value];
    if (tracks.length === 0) {
      message.warning('请至少勾选一个录制轨道');
      return;
    }
    const resp = await callApi<{ paths: Record<string, string>; tracks: string[] }>(
      '/vision/record/start',
      { method: 'POST', data: { tracks } },
    );
    if (!resp) return;
    lastRecordPaths.value = resp.paths || {};
    recordState.value = 'recording';
  } else if (recordState.value === 'recording') {
    const resp = await callApi<{ paths: Record<string, string> }>(
      '/vision/record/stop',
      { method: 'POST' },
    );
    if (!resp) return;
    lastRecordPaths.value = resp.paths || lastRecordPaths.value;
    recordState.value = 'stopped';
  }
}

async function onSaveClick() {
  const resp = await callApi<{ paths: Record<string, string> }>(
    '/vision/record/commit',
    { method: 'POST' },
  );
  if (!resp) return;
  recordState.value = 'idle';
  lastRecordPaths.value = {};
}

async function onDiscardClick() {
  const paths = Object.values(lastRecordPaths.value);
  if (paths.length === 0) {
    recordState.value = 'idle';
    lastRecordPaths.value = {};
    return;
  }
  const resp = await callApi<{ paths: string[]; errors: string[] }>(
    '/vision/record/discard',
    { method: 'POST', data: { paths } },
  );
  if (!resp) return;
  recordState.value = 'idle';
  lastRecordPaths.value = {};
}

// ───────────────────────── WebRTC ─────────────────────────

function setConnState(kind: ConnState, text?: string) {
  connState.value = kind;
  const labels: Record<ConnState, string> = {
    idle: '未连接',
    connecting: '连接中',
    live: '已连接',
    error: '异常',
  };
  connText.value = text || labels[kind];
  console.info('[vision] connection state:', connState.value, connText.value);
}

function setTileLive(slot: TrackSlot, live: boolean) {
  tileLive[slot] = live;
}

// 后端 ws status 推送的 error，只弹一次，不在页面常驻显示
watch(backendError, (err) => {
  if (err) message.error(err);
});

async function startWebRTC() {
  try {
    const peer = new RTCPeerConnection();
    pc.value = peer;
    trackIndex = 0;

    peer.ontrack = (event) => {
      const slot = TRACK_ORDER[trackIndex];
      trackIndex += 1;
      if (!slot) return;
      const videoEl = tileRef(slot);
      if (!videoEl) return;
      videoEl.srcObject = new MediaStream([event.track]);
      const onMeta = () => {
        setTileLive(slot, true);
        // 把真实视频宽高比写进 tile 的 CSS 变量，tile 会按这个比例自适应
        const w = videoEl.videoWidth;
        const h = videoEl.videoHeight;
        const tileEl = videoEl.parentElement as HTMLElement | null;
        if (tileEl && w > 0 && h > 0) {
          tileEl.style.setProperty('--tile-aspect', `${w} / ${h}`);
        }
      };
      videoEl.addEventListener('loadedmetadata', onMeta, { once: true });
      videoEl.play().catch((err) => console.error('video play failed', err));
    };
    peer.onconnectionstatechange = () => {
      const st = peer.connectionState;
      if (st === 'connected') setConnState('live');
      else if (['failed', 'disconnected', 'closed'].includes(st)) {
        setConnState('error', `WebRTC: ${st}`);
        for (const slot of TRACK_ORDER) setTileLive(slot, false);
      }
    };

    // 5 个 recvonly transceiver，对应 rgb / ir1 / ir2 / depth / seg
    for (let i = 0; i < TRACK_ORDER.length; i += 1) {
      peer.addTransceiver('video', { direction: 'recvonly' });
    }

    const wsScheme = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const socket = new WebSocket(`${wsScheme}//${location.host}/api/vision/ws`);
    ws.value = socket;

    const pendingOut: unknown[] = [];
    function sendSignal(msg: unknown) {
      if (socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify(msg));
      else if (socket.readyState === WebSocket.CONNECTING) pendingOut.push(msg);
    }

    peer.onicecandidate = ({ candidate }) => {
      sendSignal(
        candidate
          ? {
              type: 'candidate',
              candidate: candidate.candidate,
              sdpMid: candidate.sdpMid,
              sdpMLineIndex: candidate.sdpMLineIndex,
            }
          : { type: 'candidate', candidate: null },
      );
    };

    socket.addEventListener('message', async (ev) => {
      let msg: any;
      try {
        msg = JSON.parse(ev.data);
      } catch {
        return;
      }
      try {
        if (msg.type === 'answer') {
          await peer.setRemoteDescription({ type: 'answer', sdp: msg.sdp });
        } else if (msg.type === 'status') {
          syncStatusFromServer(msg);
        } else if (msg.type === 'error') {
          message.error(`信令错误：${msg.message}`);
        }
      } catch (error: any) {
        message.error(`信令处理失败：${error?.message || error}`);
      }
    });

    socket.addEventListener('close', () => {
      if (peer.connectionState !== 'connected' && peer.connectionState !== 'closed') {
        setConnState('error', 'WebSocket 已断开');
      }
    });

    await new Promise<void>((resolve, reject) => {
      if (socket.readyState === WebSocket.OPEN) return resolve();
      socket.addEventListener('open', () => resolve(), { once: true });
      socket.addEventListener(
        'error',
        () => reject(new Error('WebSocket 连接失败')),
        { once: true },
      );
    });

    while (pendingOut.length > 0) socket.send(JSON.stringify(pendingOut.shift()));

    const offer = await peer.createOffer();
    await peer.setLocalDescription(offer);
    socket.send(JSON.stringify({ type: 'offer', sdp: peer.localDescription?.sdp }));
  } catch (error: any) {
    const detail = error?.message || String(error);
    setConnState('error', `WebRTC 启动失败：${detail}`);
    message.error(`WebRTC 启动失败：${detail}`);
  }
}

function syncStatusFromServer(msg: any) {
  running.value = Boolean(msg.running);
  backendError.value = msg.error ?? null;

  // 后端 recording: not_recording / started / recording / stopped
  const srv = msg.recording as string;
  if (srv === 'started' || srv === 'recording') {
    recordState.value = 'recording';
    if (msg.record_paths) lastRecordPaths.value = msg.record_paths;
  } else if (srv === 'stopped') {
    recordState.value = 'stopped';
    if (msg.record_paths) lastRecordPaths.value = msg.record_paths;
  } else {
    recordState.value = 'idle';
    if (!msg.record_paths || Object.keys(msg.record_paths).length === 0) {
      lastRecordPaths.value = {};
    }
  }
}

// ───────────────────────── Init / teardown ─────────────────────────

onMounted(async () => {
  // 先看看后端当前是否已在运行，运行中就直接上 WebRTC
  const health = await callApi<HealthData>('/vision/health');
  if (health?.running) {
    running.value = true;
    await loadStreams();
    webrtcStarted = true;
    await startWebRTC();
  } else {
    await loadStreams();
  }
});

onBeforeUnmount(() => {
  try {
    ws.value?.close();
  } catch {
    // ignore
  }
  try {
    pc.value?.close();
  } catch {
    // ignore
  }
});
</script>

<template>
  <Page>
    <div class="realsense-layout">
      <!-- 左侧：录制 + 配置 + 开始 -->
      <aside class="panel">
        <Card size="small" class="panel-card" title="录制">
          <Checkbox.Group
            v-model:value="recordTracks"
            :options="recordableOptions"
            :disabled="isRecording || !running"
          />

          <div class="record-actions">
            <Button
              v-if="recordState !== 'stopped'"
              type="primary"
              danger
              :disabled="!running"
              block
              @click="onRecordClick"
            >
              {{ recordBtnLabel }}
            </Button>
            <Space v-else style="width: 100%">
              <Button type="primary" @click="onSaveClick">保存</Button>
              <Button danger @click="onDiscardClick">丢弃</Button>
            </Space>
          </div>

          <div v-if="Object.keys(lastRecordPaths).length > 0" class="record-paths">
            <div
              v-for="(path, name) in lastRecordPaths"
              :key="name"
              class="record-path-row"
            >
              <Tag color="geekblue">{{ name }}</Tag>
              <span class="record-path" :title="path">{{ path }}</span>
            </div>
          </div>
        </Card>

        <Card size="small" class="panel-card" title="RGB 相机">
          <div class="field-row">
            <label>格式</label>
            <Select
              v-model:value="forms.rgb.format"
              :options="formatOptions('rgb')"
              :disabled="configDisabled"
              @change="onFormatChange('rgb')"
            />
          </div>
          <div class="field-row">
            <label>分辨率</label>
            <Select
              v-model:value="forms.rgb.resolution"
              :options="resolutionOptions('rgb')"
              :disabled="configDisabled"
              @change="onResolutionChange('rgb')"
            />
          </div>
          <div class="field-row">
            <label>帧率</label>
            <Select
              v-model:value="forms.rgb.fps"
              :options="fpsOptions('rgb')"
              :disabled="configDisabled"
            />
          </div>
        </Card>

        <Card size="small" class="panel-card" title="红外 1">
          <div class="field-row">
            <label>格式</label>
            <Select
              v-model:value="forms.ir1.format"
              :options="formatOptions('ir1')"
              :disabled="configDisabled"
              @change="onFormatChange('ir1')"
            />
          </div>
          <div class="field-row">
            <label>分辨率</label>
            <Select
              v-model:value="forms.ir1.resolution"
              :options="resolutionOptions('ir1')"
              :disabled="configDisabled"
              @change="onResolutionChange('ir1')"
            />
          </div>
          <div class="field-row">
            <label>帧率</label>
            <Select
              v-model:value="forms.ir1.fps"
              :options="fpsOptions('ir1')"
              :disabled="configDisabled"
            />
          </div>
        </Card>

        <Card size="small" class="panel-card" title="红外 2">
          <div class="field-row">
            <label>格式</label>
            <Select
              v-model:value="forms.ir2.format"
              :options="formatOptions('ir2')"
              :disabled="configDisabled"
              @change="onFormatChange('ir2')"
            />
          </div>
          <div class="field-row">
            <label>分辨率</label>
            <Select
              v-model:value="forms.ir2.resolution"
              :options="resolutionOptions('ir2')"
              :disabled="configDisabled"
              @change="onResolutionChange('ir2')"
            />
          </div>
          <div class="field-row">
            <label>帧率</label>
            <Select
              v-model:value="forms.ir2.fps"
              :options="fpsOptions('ir2')"
              :disabled="configDisabled"
            />
          </div>
        </Card>

        <Card size="small" class="panel-card" title="深度">
          <div class="field-row">
            <label>格式</label>
            <Select
              v-model:value="forms.depth.format"
              :options="formatOptions('depth')"
              :disabled="configDisabled"
              @change="onFormatChange('depth')"
            />
          </div>
          <div class="field-row">
            <label>分辨率</label>
            <Select
              v-model:value="forms.depth.resolution"
              :options="resolutionOptions('depth')"
              :disabled="configDisabled"
              @change="onResolutionChange('depth')"
            />
          </div>
          <div class="field-row">
            <label>帧率</label>
            <Select
              v-model:value="forms.depth.fps"
              :options="fpsOptions('depth')"
              :disabled="configDisabled"
            />
          </div>
        </Card>

        <Card size="small" class="panel-card" title="开始">
          <Button
            type="primary"
            block
            :loading="applying"
            :disabled="isRecording"
            @click="onApplyClick"
          >
            {{ startBtnLabel }}
          </Button>
        </Card>
      </aside>

      <!-- 右侧：响应式视频墙（3/2/1 列），5 路 -->
      <section class="video-wall">
        <div class="tile" :data-live="tileLive.rgb">
          <div class="tile-head">
            <span>RGB</span>
            <Tag :color="tileLive.rgb ? 'green' : 'red'" class="tile-tag">
              {{ tileLive.rgb ? '实时' : '未连接' }}
            </Tag>
          </div>
          <video ref="videoRgb" autoplay playsinline muted></video>
        </div>
        <div class="tile" :data-live="tileLive.seg">
          <div class="tile-head">
            <span>Segmentation</span>
            <Tag :color="tileLive.seg ? 'green' : 'red'" class="tile-tag">
              {{ tileLive.seg ? '实时' : '未连接' }}
            </Tag>
          </div>
          <video ref="videoSeg" autoplay playsinline muted></video>
        </div>
        <div class="tile" :data-live="tileLive.ir1">
          <div class="tile-head">
            <span>IR 1</span>
            <Tag :color="tileLive.ir1 ? 'green' : 'red'" class="tile-tag">
              {{ tileLive.ir1 ? '实时' : '未连接' }}
            </Tag>
          </div>
          <video ref="videoIr1" autoplay playsinline muted></video>
        </div>
        <div class="tile" :data-live="tileLive.ir2">
          <div class="tile-head">
            <span>IR 2</span>
            <Tag :color="tileLive.ir2 ? 'green' : 'red'" class="tile-tag">
              {{ tileLive.ir2 ? '实时' : '未连接' }}
            </Tag>
          </div>
          <video ref="videoIr2" autoplay playsinline muted></video>
        </div>
        <div class="tile" :data-live="tileLive.depth">
          <div class="tile-head">
            <span>Depth</span>
            <Tag :color="tileLive.depth ? 'green' : 'red'" class="tile-tag">
              {{ tileLive.depth ? '实时' : '未连接' }}
            </Tag>
          </div>
          <video ref="videoDepth" autoplay playsinline muted></video>
        </div>
      </section>
    </div>
  </Page>
</template>

<style lang="scss" scoped>
.realsense-layout {
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: 12px;
  height: calc(100vh - 120px);
  min-height: 560px;
}

.panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
  padding-right: 4px;
}

.panel-card {
  :deep(.ant-card-head) {
    min-height: 36px;
    padding: 0 12px;
  }

  :deep(.ant-card-head-title) {
    padding: 8px 0;
    font-size: 13px;
  }

  :deep(.ant-card-body) {
    padding: 10px 12px;
  }
}

.field-row {
  display: grid;
  grid-template-columns: 64px 1fr;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;

  &:last-child {
    margin-bottom: 0;
  }

  label {
    font-size: 12px;
    color: var(--ant-color-text-secondary, #94a3b8);
  }
}

.record-actions {
  margin-top: 10px;
}

.record-paths {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 10px;
  font-size: 11px;
}

.record-path-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.record-path {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--ant-color-text-secondary, #94a3b8);
}

.video-wall {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  align-content: start;
  overflow-y: auto;
  padding-right: 4px;
}

@media (max-width: 1399px) {
  .video-wall {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 899px) {
  .video-wall {
    grid-template-columns: 1fr;
  }
}

.tile {
  position: relative;
  width: 100%;
  min-width: 0;
  overflow: hidden;
  background: #000;
  border: 1px solid rgb(244 63 94 / 50%);
  border-radius: 8px;
  aspect-ratio: var(--tile-aspect, 4 / 3);

  &[data-live='true'] {
    border-color: rgb(16 185 129 / 50%);
  }

  &[data-live='false'] {
    aspect-ratio: 4 / 3;
  }
}

.tile-head {
  position: absolute;
  inset: 8px 8px auto 8px;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #cbd5f5;
  font-size: 12px;
  text-shadow: 0 1px 2px rgb(0 0 0 / 60%);
  pointer-events: none;
}

.tile[data-live='false'] .tile-head {
  color: #fecaca;
}

.tile-tag {
  pointer-events: auto;
}

.tile video {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #000;
}
</style>
