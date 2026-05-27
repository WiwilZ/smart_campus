<script setup lang="ts">
import type {
  RealtimeVideoTile,
  TrackSlot,
} from '../composables/use-realtime-monitor';

import { NTag } from 'naive-ui';

const props = defineProps<{
  registerCanvas: (slot: TrackSlot, element: HTMLCanvasElement | null) => void;
  tiles: RealtimeVideoTile[];
}>();
</script>

<template>
  <section class="video-wall">
    <div v-for="tile in props.tiles" :key="tile.key" :data-live="tile.live" class="tile">
      <div class="tile-head">
        <span>{{ tile.title }}</span>
        <NTag :type="tile.live ? 'success' : 'error'" class="tile-tag" size="small">
          {{ tile.live ? '实时' : '未连接' }}
        </NTag>
      </div>
      <canvas
        :ref="(element) => props.registerCanvas(tile.key, element as HTMLCanvasElement | null)"
        height="720"
        width="1280"
      ></canvas>
    </div>
  </section>
</template>

<style lang="scss" scoped>
.video-wall {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  grid-auto-rows: max-content;
  align-items: start;
  gap: 12px;
  align-content: start;
  overflow-y: auto;
  padding: 4px 4px 8px 0;
}

.tile {
  position: relative;
  align-self: start;
  width: 100%;
  min-width: 0;
  overflow: hidden;
  background: #000;
  border: 1px solid rgb(244 63 94 / 50%);
  border-radius: 8px;

  &[data-live='true'] {
    border-color: rgb(16 185 129 / 50%);
  }
}

.tile::before {
  display: block;
  padding-top: 56.25%;
  content: '';
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

.tile canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #000;
}
</style>
