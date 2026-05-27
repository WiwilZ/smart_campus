<script setup lang="ts">
import { NCard, NSelect } from 'naive-ui';

const props = defineProps<{
  disabled: boolean;
  format: string;
  formatOptions: Array<{ label: string; value: string }>;
  fps: string;
  fpsOptions: Array<{ label: string; value: string }>;
  resolution: string;
  resolutionOptions: Array<{ label: string; value: string }>;
  title: string;
}>();

const emit = defineEmits<{
  formatChange: [];
  resolutionChange: [];
  'update:format': [value: string];
  'update:fps': [value: string];
  'update:resolution': [value: string];
}>();

function onFormatUpdate(value: null | string) {
  emit('update:format', value ?? '');
  emit('formatChange');
}

function onResolutionUpdate(value: null | string) {
  emit('update:resolution', value ?? '');
  emit('resolutionChange');
}

function onFpsUpdate(value: null | string) {
  emit('update:fps', value ?? '');
}
</script>

<template>
  <NCard :title="props.title" class="config-card" size="small">
    <div class="field-row">
      <label>格式</label>
      <NSelect
        :disabled="props.disabled"
        :options="props.formatOptions"
        :value="props.format"
        @update:value="onFormatUpdate"
      />
    </div>
    <div class="field-row">
      <label>分辨率</label>
      <NSelect
        :disabled="props.disabled"
        :options="props.resolutionOptions"
        :value="props.resolution"
        @update:value="onResolutionUpdate"
      />
    </div>
    <div class="field-row">
      <label>帧率</label>
      <NSelect
        :disabled="props.disabled"
        :options="props.fpsOptions"
        :value="props.fps"
        @update:value="onFpsUpdate"
      />
    </div>
  </NCard>
</template>

<style lang="scss" scoped>
.config-card {
  :deep(.n-card-header) {
    padding: 10px 12px 0;
  }

  :deep(.n-card__content) {
    padding: 10px 12px 12px;
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
    color: rgb(100 116 139);
  }
}
</style>
