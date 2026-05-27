<script setup lang="ts">
import type { RecordableKey, RecordUiState } from '../composables/use-realtime-monitor';

import { computed } from 'vue';

import { NButton, NCard, NCheckbox, NCheckboxGroup, NSpace, NTag } from 'naive-ui';

const props = defineProps<{
  isRecording: boolean;
  lastRecordPaths: Record<string, string>;
  recordableOptions: Array<{ label: string; value: RecordableKey }>;
  recordBtnLabel: string;
  recordState: RecordUiState;
  recordTracks: RecordableKey[];
  running: boolean;
}>();

const emit = defineEmits<{
  discard: [];
  record: [];
  save: [];
  'update:recordTracks': [value: RecordableKey[]];
}>();

const pathEntries = computed(() => Object.entries(props.lastRecordPaths));

function onTracksUpdate(value: Array<number | string>) {
  emit('update:recordTracks', value as RecordableKey[]);
}
</script>

<template>
  <NCard class="record-card" size="small" title="录制">
    <template #header-extra>
      <div v-if="props.recordState === 'recording'" class="recording-indicator">
        <span class="recording-dot"></span>
        <span class="recording-text">录制中</span>
      </div>
    </template>

    <NCheckboxGroup
      class="record-track-group"
      :disabled="props.isRecording || !props.running"
      :value="props.recordTracks"
      @update:value="onTracksUpdate"
    >
      <NSpace :size="[12, 8]" :wrap-item="false">
        <NCheckbox
          v-for="option in props.recordableOptions"
          :key="option.value"
          :value="option.value"
        >
          {{ option.label }}
        </NCheckbox>
      </NSpace>
    </NCheckboxGroup>

    <div class="record-actions">
      <NButton
        v-if="props.recordState !== 'stopped'"
        block
        :disabled="!props.running"
        type="error"
        @click="emit('record')"
      >
        {{ props.recordBtnLabel }}
      </NButton>
      <NSpace v-else class="record-stop-actions" justify="space-between">
        <NButton class="stop-action" type="primary" @click="emit('save')">
          保存
        </NButton>
        <NButton class="stop-action" type="error" @click="emit('discard')">
          丢弃
        </NButton>
      </NSpace>
    </div>

    <div v-if="pathEntries.length > 0" class="record-paths">
      <div v-for="[name, path] in pathEntries" :key="name" class="record-path-row">
        <NTag size="small" type="info">{{ name }}</NTag>
        <span class="record-path" :title="path">{{ path }}</span>
      </div>
    </div>
  </NCard>
</template>

<style lang="scss" scoped>
.record-card {
  :deep(.n-card-header) {
    padding: 10px 12px 0;
  }

  :deep(.n-card__content) {
    padding: 10px 12px 12px;
  }
}

.recording-indicator {
  display: inline-flex;
  gap: 6px;
  align-items: center;
  font-size: 12px;
  color: rgb(239 68 68);
}

.recording-dot {
  width: 8px;
  height: 8px;
  background: rgb(239 68 68);
  border-radius: 50%;
  box-shadow: 0 0 6px rgb(239 68 68 / 60%);
  animation: recording-blink 1s ease-in-out infinite;
}

.recording-text {
  font-weight: 500;
  letter-spacing: 0.5px;
}

@keyframes recording-blink {
  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0.25;
  }
}

.record-actions {
  margin-top: 10px;
}

.record-stop-actions {
  display: flex;
  width: 100%;
}

.stop-action {
  flex: 1;
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
  color: rgb(100 116 139);
}
</style>
