<script setup lang="ts">
import { ref } from 'vue';
import { NCard, NSelect } from 'naive-ui';

const props = defineProps<{
  robot: string;
}>();

const emit = defineEmits<{
  'update:robot': [value: string];
}>();

const robotOptions = [
  { label: 'Robot-1', value: 'Robot-1' },
  { label: 'Robot-2', value: 'Robot-2' },
  { label: 'Robot-3', value: 'Robot-3' },
  { label: 'Robot-4', value: 'Robot-4' },
  { label: 'Robot-5', value: 'Robot-5' },
];

function handleRobotChange(value: string) {
  emit('update:robot', value);
}
</script>

<template>
  <NCard size="small" title="机器人选择">
    <div class="flex gap-4">
      <NSelect
        :value="robot"
        :options="robotOptions"
        class="w-64"
        @update:value="handleRobotChange"
      />
    </div>
  </NCard>
</template>
