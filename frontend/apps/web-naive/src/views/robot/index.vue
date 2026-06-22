<script setup lang="ts">
import { ref } from 'vue';
import { Page } from '@vben/common-ui';
import { NGrid, NGridItem } from 'naive-ui';
import RobotSelector from './components/RobotSelector.vue';
import MotionControl from './components/MotionControl.vue';
import MapControl from './components/MapControl.vue';
import VideoViewer from './components/VideoViewer.vue';

const selectedRobot = ref<string>('Robot-1');
</script>

<template>
  <Page auto-content-height>
    <div class="p-4">
      <NGrid :cols="24" :x-gap="16" :y-gap="16">
        <!-- 左侧：机器人选择、控制 -->
        <NGridItem :span="6" class="space-y-4">
          <RobotSelector v-model:robot="selectedRobot" />
          <MotionControl :robot="selectedRobot" />
        </NGridItem>
        
        <!-- 中间：地图与导航 -->
        <NGridItem :span="10">
          <MapControl :robot="selectedRobot" />
        </NGridItem>
        
        <!-- 右侧：实时画面 -->
        <NGridItem :span="8">
          <VideoViewer :robot="selectedRobot" />
        </NGridItem>
      </NGrid>
    </div>
  </Page>
</template>
