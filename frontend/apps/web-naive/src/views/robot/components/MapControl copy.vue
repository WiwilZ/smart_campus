<script setup lang="ts">
import { ref } from 'vue';
import { NCard, NButton, NInput } from 'naive-ui';
import { message } from '#/adapter/naive';

const mapContainer = ref<HTMLDivElement>();
const robotPos = ref({ x: 50, y: 50 });
const targetPos = ref<{ x: number, y: number } | null>(null);

const calibX = ref('');
const calibY = ref('');

function handleMapClick(e: MouseEvent) {
  if (!mapContainer.value) return;
  const rect = mapContainer.value.getBoundingClientRect();
  const x = ((e.clientX - rect.left) / rect.width) * 100;
  const y = ((e.clientY - rect.top) / rect.height) * 100;
  targetPos.value = { x, y };
}

function setTarget() {
  if (!targetPos.value) return;
  message.success(`已下发目标坐标: [${targetPos.value.x.toFixed(1)}, ${targetPos.value.y.toFixed(1)}]`);
}

function calibrate() {
  const x = parseFloat(calibX.value);
  const y = parseFloat(calibY.value);
  if (!isNaN(x) && !isNaN(y)) {
    robotPos.value = { x, y };
    targetPos.value = null;
    message.success(`已校准位置为 [${x}, ${y}]`);
  } else {
    message.error('请输入有效的坐标');
  }
}
</script>

<template>
  <NCard size="small" title="地图与导航">
    <template #header-extra>
      <div class="flex gap-2 items-center">
        <NInput v-model:value="calibX" placeholder="X" size="small" style="width: 60px" />
        <NInput v-model:value="calibY" placeholder="Y" size="small" style="width: 60px" />
        <NButton size="small" @click="calibrate">位置校准</NButton>
        <NButton size="small" type="primary" :disabled="!targetPos" @click="setTarget">导航至目标</NButton>
      </div>
    </template>
    <div 
      ref="mapContainer"
      class="relative h-[400px] w-full bg-slate-100 overflow-hidden cursor-crosshair rounded-md border border-slate-200"
      @click="handleMapClick"
    >
      <div class="absolute inset-0 opacity-10" style="background-image: radial-gradient(#000 1px, transparent 1px); background-size: 20px 20px;"></div>
      
      <!-- Robot Marker -->
      <div 
        class="absolute w-4 h-4 bg-blue-500 rounded-full shadow-lg transition-all duration-300 transform -translate-x-1/2 -translate-y-1/2 z-10"
        :style="{ left: robotPos.x + '%', top: robotPos.y + '%' }"
      >
        <div class="absolute inset-0 bg-blue-500 rounded-full animate-ping opacity-50"></div>
      </div>
      
      <!-- Target Marker -->
      <div 
        v-if="targetPos"
        class="absolute w-4 h-4 border-2 border-red-500 rounded-full transform -translate-x-1/2 -translate-y-1/2"
        :style="{ left: targetPos.x + '%', top: targetPos.y + '%' }"
      >
        <div class="absolute top-1/2 left-1/2 w-1 h-1 bg-red-500 rounded-full transform -translate-x-1/2 -translate-y-1/2"></div>
      </div>
    </div>
    <div class="mt-2 text-xs text-slate-500 flex justify-between">
      <span>当前: [{{ robotPos.x.toFixed(1) }}, {{ robotPos.y.toFixed(1) }}]</span>
      <span v-if="targetPos">目标: [{{ targetPos.x.toFixed(1) }}, {{ targetPos.y.toFixed(1) }}]</span>
      <span v-else>点击地图设置目标点</span>
    </div>
  </NCard>
</template>
