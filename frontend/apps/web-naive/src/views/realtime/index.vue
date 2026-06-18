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
