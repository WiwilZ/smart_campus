<script setup lang="ts">
import { ref } from 'vue';
import { NCard, NButton } from 'naive-ui';
import { message } from '#/adapter/naive';

function moveRobot(action: string) {
  message.info(`机器人${action}`);
}

function moveCamera(action: string) {
  message.info(`云台${action}`);
}
</script>

<template>
  <div class="space-y-4">
    <NCard size="small" title="云台控制">
      <div class="space-y-3">
        <div class="grid grid-cols-3 gap-2 w-48 mx-auto">
          <span></span>
          <NButton @click="moveCamera('上移')">上</NButton>
          <span></span>
          <NButton @click="moveCamera('左移')">左</NButton>
          <NButton @click="moveCamera('回中')">中</NButton>
          <NButton @click="moveCamera('右移')">右</NButton>
          <span></span>
          <NButton @click="moveCamera('下移')">下</NButton>
          <span></span>
        </div>
        <div class="grid grid-cols-2 gap-2 w-48 mx-auto">
          <NButton @click="moveCamera('放大')">放大</NButton>
          <NButton @click="moveCamera('缩小')">缩小</NButton>
        </div>
      </div>
    </NCard>
    
    <NCard size="small" title="机器人控制">
      <div class="grid grid-cols-3 gap-2 w-48 mx-auto">
        <span></span>
        <NButton @click="moveRobot('前进')">前进</NButton>
        <span></span>
        <NButton @click="moveRobot('左转')">左转</NButton>
        <NButton @click="moveRobot('停止')">停止</NButton>
        <NButton @click="moveRobot('右转')">右转</NButton>
        <span></span>
        <NButton @click="moveRobot('后退')">后退</NButton>
        <span></span>
      </div>
    </NCard>
  </div>
</template>
