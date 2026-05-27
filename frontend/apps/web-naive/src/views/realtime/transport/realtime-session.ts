import type { VideoRealtimeFrame } from './transport-client';

import { ref } from 'vue';

import { getVisionHealth, startVisionPipeline } from '#/api/vision';

import { RealtimeTransportClient } from './transport-client';

export type RealtimeSessionState = 'connecting' | 'error' | 'idle' | 'live';

// handler 不需要也不应该 close 这个 frame，session 会在广播后统一 close。
type FrameHandler = (frame: VideoRealtimeFrame) => Promise<void> | void;

const frameHandlers = new Set<FrameHandler>();
const connState = ref<RealtimeSessionState>('idle');
const connText = ref('未连接');
let client: null | RealtimeTransportClient = null;
let reconnectTimer: null | ReturnType<typeof setTimeout> = null;
let startPromise: null | Promise<void> = null;
let activeSessionToken = 0;
let nextSessionToken = 0;
let shouldAutoReconnect = false;

function setConnState(kind: RealtimeSessionState, text?: string) {
  connState.value = kind;
  const labels: Record<RealtimeSessionState, string> = {
    connecting: '连接中',
    error: '异常',
    idle: '未连接',
    live: '已连接',
  };
  connText.value = text || labels[kind];
}

export function subscribeRealtimeFrames(handler: FrameHandler) {
  frameHandlers.add(handler);
  return () => {
    frameHandlers.delete(handler);
  };
}

export function useRealtimeSessionState() {
  return {
    connState,
    connText,
  };
}

export async function ensureRealtimeSessionStarted() {
  shouldAutoReconnect = true;
  if (client) {
    return;
  }
  if (startPromise) {
    return startPromise;
  }
  startPromise = startRealtimeSession();
  try {
    await startPromise;
  } finally {
    startPromise = null;
  }
}

export function stopRealtimeSession() {
  shouldAutoReconnect = false;
  activeSessionToken = 0;
  startPromise = null;
  clearReconnectTimer();
  const currentClient = client;
  client = null;
  currentClient?.close();
  setConnState('idle');
}

export async function restartRealtimeSession() {
  stopRealtimeSession();
  await ensureRealtimeSessionStarted();
}

function clearReconnectTimer() {
  if (!reconnectTimer) {
    return;
  }
  clearTimeout(reconnectTimer);
  reconnectTimer = null;
}

function scheduleReconnect(token: number) {
  if (!shouldAutoReconnect || token !== activeSessionToken || reconnectTimer) {
    return;
  }
  reconnectTimer = setTimeout(async () => {
    reconnectTimer = null;
    if (!shouldAutoReconnect || token !== activeSessionToken || client) {
      return;
    }
    try {
      await ensureRealtimeSessionStarted();
    } catch (error) {
      console.error('[vision] realtime auto reconnect failed', error);
      scheduleReconnect(activeSessionToken);
    }
  }, 2000);
}

async function startRealtimeSession() {
  nextSessionToken += 1;
  const token = nextSessionToken;
  activeSessionToken = token;
  setConnState('connecting');
  const health = await getVisionHealth();
  if (token !== activeSessionToken) {
    return;
  }
  if (!health.running) {
    await startVisionPipeline();
    if (token !== activeSessionToken) {
      return;
    }
  }
  const nextClient = new RealtimeTransportClient({
    onClose(reason) {
      if (client === nextClient) {
        client = null;
        setConnState('error', reason || '连接已断开');
        scheduleReconnect(token);
      }
    },
    onConnected() {
      if (client === nextClient) {
        setConnState('live');
      }
    },
    onError(error) {
      if (client === nextClient) {
        setConnState('error', error.message);
        scheduleReconnect(token);
      }
      console.error('[vision] realtime session error', error);
    },
    async onVideoFrame(frame) {
      try {
        if (frameHandlers.size === 0) {
          return;
        }
        const handlers = [...frameHandlers];
        await Promise.all(handlers.map((h) => Promise.resolve(h(frame))));
      } finally {
        frame.frame.close();
      }
    },
  });
  if (token !== activeSessionToken) {
    nextClient.close();
    return;
  }
  client = nextClient;
  try {
    await nextClient.connect();
  } catch (error: any) {
    if (client === nextClient) {
      client = null;
    }
    nextClient.close();
    setConnState('error', `WebRTC 启动失败：${error?.message || error}`);
    scheduleReconnect(token);
    throw error;
  }
}
