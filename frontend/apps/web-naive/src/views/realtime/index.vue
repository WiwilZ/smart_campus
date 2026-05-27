<script setup lang="ts">
import type { RecordableKey } from './composables/use-realtime-monitor';

import { Page } from '@vben/common-ui';

import { NButton, NCard, NTag } from 'naive-ui';

import { message } from '#/adapter/naive';

import RealtimeRecordPanel from './components/realtime-record-panel.vue';
import RealtimeVideoWall from './components/realtime-video-wall.vue';
import { useRealtimeMonitor } from './composables/use-realtime-monitor';

defineOptions({ name: 'RealtimeMonitor' });

const {
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
} = useRealtimeMonitor();

function onRecordTracksChange(value: RecordableKey[]) {
  recordTracks.value = value;
}

function moveMockCamera(action: string) {
  message.info(`云台${action}`);
}

function moveMockRobot(action: string) {
  message.info(`机器人${action}`);
}
</script>

<template>
  <Page auto-content-height>
    <div class="realtime-layout">
      <aside class="panel">
        <NCard size="small" title="视频流">
          <div class="fixed-profile">
            <div>
              <span class="label">配置</span>
              <span>{{ deviceInfo }}</span>
            </div>
            <div>
              <span class="label">流状态</span>
              <NTag
                :type="connText === '连接中' ? 'warning' : running ? 'success' : 'warning'"
                size="small"
              >
                {{ connText }}
              </NTag>
            </div>
          </div>
          <NButton
            block
            class="reconnect-button"
            :loading="reconnecting"
            type="primary"
            @click="onReconnectClick"
          >
            重新连接
          </NButton>
        </NCard>

        <RealtimeRecordPanel
          :is-recording="isRecording"
          :last-record-paths="lastRecordPaths"
          :record-btn-label="recordBtnLabel"
          :record-state="recordState"
          :record-tracks="recordTracks"
          :recordable-options="recordableOptions"
          :running="running"
          @discard="onDiscardClick"
          @record="onRecordClick"
          @save="onSaveClick"
          @update:record-tracks="onRecordTracksChange"
        />

        <NCard size="small" title="云台控制">
          <div class="space-y-3">
            <div class="grid grid-cols-3 gap-2">
              <span></span>
              <NButton @click="moveMockCamera('上移')">上</NButton>
              <span></span>
              <NButton @click="moveMockCamera('左移')">左</NButton>
              <NButton @click="moveMockCamera('回中')">中</NButton>
              <NButton @click="moveMockCamera('右移')">右</NButton>
              <span></span>
              <NButton @click="moveMockCamera('下移')">下</NButton>
              <span></span>
            </div>
            <div class="grid grid-cols-2 gap-2">
              <NButton @click="moveMockCamera('放大')">放大</NButton>
              <NButton @click="moveMockCamera('缩小')">缩小</NButton>
            </div>
          </div>
        </NCard>

        <NCard size="small" title="机器人运动控制">
          <div class="space-y-3">
            <div class="grid grid-cols-3 gap-2">
              <span></span>
              <NButton @click="moveMockRobot('前进')">前进</NButton>
              <span></span>
              <NButton @click="moveMockRobot('左转')">左转</NButton>
              <NButton @click="moveMockRobot('停止')">停止</NButton>
              <NButton @click="moveMockRobot('右转')">右转</NButton>
              <span></span>
              <NButton @click="moveMockRobot('后退')">后退</NButton>
              <span></span>
            </div>
          </div>
        </NCard>
      </aside>

      <RealtimeVideoWall :register-canvas="registerCanvas" :tiles="videoTiles" />
    </div>
  </Page>
</template>

<style lang="scss" scoped>
.realtime-layout {
  display: grid;
  grid-template-columns: 340px minmax(0, 1fr);
  gap: 12px;
  height: calc(100vh - 120px);
  min-height: 560px;
}

@media (max-width: 960px) {
  .realtime-layout {
    grid-template-columns: 1fr;
    height: auto;
  }
}

.panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
  padding-right: 4px;
}

.reconnect-button {
  margin-top: 12px;
}

.fixed-profile {
  display: grid;
  gap: 8px;
  color: #cbd5e1;
  font-size: 13px;

  > div {
    display: flex;
    justify-content: space-between;
    gap: 12px;
  }

  .label {
    color: #94a3b8;
    white-space: nowrap;
  }
}
</style>
