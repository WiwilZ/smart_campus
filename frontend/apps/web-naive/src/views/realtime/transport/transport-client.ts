export interface VideoRealtimeFrame {
  frame: VideoFrame;
  ptsUs: number;
}

export interface RealtimeTransportEvents {
  onClose?: (reason?: string) => void;
  onConnected?: () => void;
  onError?: (error: Error) => void;
  onVideoFrame?: (frame: VideoRealtimeFrame) => Promise<void> | void;
}

export class RealtimeTransportClient {
  private readonly events: RealtimeTransportEvents;
  private frameReader: null | ReadableStreamDefaultReader<VideoFrame> = null;
  private peer: null | RTCPeerConnection = null;
  private stopped = false;
  private websocket: null | WebSocket = null;

  constructor(events: RealtimeTransportEvents) {
    this.events = events;
  }

  close() {
    this.stopped = true;
    try {
      this.frameReader?.cancel();
    } catch {}
    try {
      this.websocket?.close();
    } catch {}
    try {
      this.peer?.close();
    } catch {}
    this.frameReader = null;
    this.websocket = null;
    this.peer = null;
  }

  async connect() {
    this.close();
    this.stopped = false;
    const peer = new RTCPeerConnection();
    this.peer = peer;
    peer.addTransceiver('video', { direction: 'recvonly' });

    peer.ontrack = (event) => {
      if (this.peer !== peer || event.track.kind !== 'video') {
        return;
      }
      this.startVideoProcessor(event.track);
    };

    peer.onconnectionstatechange = () => {
      if (this.peer !== peer) {
        return;
      }
      if (peer.connectionState === 'connected') {
        this.events.onConnected?.();
      } else if (['closed', 'disconnected', 'failed'].includes(peer.connectionState)) {
        this.events.onClose?.(`WebRTC: ${peer.connectionState}`);
      }
    };

    const socket = new WebSocket(this.websocketUrl());
    this.websocket = socket;
    await this.waitSocketOpen(socket);

    peer.onicecandidate = ({ candidate }) => {
      if (this.websocket !== socket || socket.readyState !== WebSocket.OPEN) {
        return;
      }
      socket.send(JSON.stringify(candidate
        ? {
            candidate: candidate.candidate,
            sdpMLineIndex: candidate.sdpMLineIndex,
            sdpMid: candidate.sdpMid,
            type: 'candidate',
          }
        : { candidate: null, type: 'candidate' }));
    };

    socket.addEventListener('message', async (event) => {
      if (this.websocket !== socket || this.peer !== peer) {
        return;
      }
      const payload = JSON.parse(event.data);
      if (payload.type === 'answer') {
        await peer.setRemoteDescription({ sdp: payload.sdp, type: 'answer' });
      } else if (payload.type === 'error') {
        this.events.onError?.(new Error(payload.message || '信令错误'));
      }
    });

    socket.addEventListener('close', () => {
      if (this.websocket === socket && !this.stopped) {
        this.events.onClose?.('WebSocket 已断开');
      }
    });

    const offer = await peer.createOffer();
    await peer.setLocalDescription(offer);
    socket.send(JSON.stringify({ sdp: peer.localDescription?.sdp, type: 'offer' }));
  }

  private async startVideoProcessor(track: MediaStreamTrack) {
    const Processor = (globalThis as any).MediaStreamTrackProcessor;
    if (Processor === undefined) {
      this.events.onError?.(new Error('当前浏览器不支持 MediaStreamTrackProcessor'));
      return;
    }
    const processor = new Processor({ track });
    const reader = processor.readable.getReader() as ReadableStreamDefaultReader<VideoFrame>;
    this.frameReader = reader;
    try {
      while (!this.stopped) {
        const result = await reader.read();
        if (result.done || !result.value) {
          break;
        }
        const frame = result.value;
        // await 形成帧背压，避免 VideoFrame 堆积导致 jitter。
        try {
          await this.events.onVideoFrame?.({
            frame,
            ptsUs: Math.max(0, Math.round(frame.timestamp || 0)),
          });
        } catch (error: any) {
          if (!this.stopped) {
            this.events.onError?.(new Error(error?.message || String(error)));
          }
        }
      }
    } catch (error: any) {
      if (!this.stopped) {
        this.events.onError?.(new Error(error?.message || String(error)));
      }
    }
  }

  private waitSocketOpen(socket: WebSocket) {
    return new Promise<void>((resolve, reject) => {
      if (socket.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }
      socket.addEventListener('open', () => resolve(), { once: true });
      socket.addEventListener('error', () => reject(new Error('WebSocket 连接失败')), { once: true });
    });
  }

  private websocketUrl() {
    const scheme = location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${scheme}//${location.host}/api/vision/ws`;
  }
}
