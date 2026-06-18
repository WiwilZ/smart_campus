<script setup lang="ts">
import { NCard } from 'naive-ui';
import { useRealtimeMonitor } from '../../realtime/composables/use-realtime-monitor';

const { registerCanvas } = useRealtimeMonitor();
</script>

<template>
  <NCard size="small" title="实时视频流" class="h-full">
    <div class="w-full h-full min-h-[300px] bg-black rounded-md flex items-center justify-center text-white overflow-hidden relative">
      <!-- 实时视频流 -->
      <canvas 
        :ref="(element) => registerCanvas('rgb', element as HTMLCanvasElement | null)" 
        width="1280" 
        height="720" 
        class="w-full h-full object-contain absolute inset-0 bg-black"
      ></canvas>
      
      <!-- OSD 覆盖层 -->
      <div class="absolute inset-0 pointer-events-none p-4 flex flex-col justify-between">
        <div class="flex justify-between text-green-400 text-xs font-mono drop-shadow-md">
          <span>REC 00:15:32</span>
          <span>1080P 30FPS</span>
        </div>
        <div class="self-center flex flex-col items-center opacity-50">
          <div class="w-32 h-32 border border-green-500 rounded-full relative">
            <div class="absolute top-1/2 left-0 w-full h-[1px] bg-green-500"></div>
            <div class="absolute top-0 left-1/2 w-[1px] h-full bg-green-500"></div>
          </div>
        </div>
        <div class="flex justify-between text-green-400 text-xs font-mono drop-shadow-md">
          <span>RGB SENSOR</span>
          <span>PTZ: 0° 0°</span>
        </div>
      </div>
    </div>
  </NCard>
</template>
