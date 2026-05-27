<script setup lang="ts">
import type { InspectionAlert, InspectionDashboardData, InspectionTask } from '#/api';

import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';

import { NButton, NCard, NEmpty, NProgress, NSkeleton, NTag } from 'naive-ui';

import { getInspectionDashboard } from '#/api';

const router = useRouter();
const loading = ref(true);
const dashboard = ref<InspectionDashboardData | null>(null);

const alertTypeMap: Record<InspectionAlert['level'], 'error' | 'success' | 'warning'> = {
  high: 'error',
  low: 'success',
  medium: 'warning',
};
const alertLabelMap: Record<InspectionAlert['level'], string> = {
  high: '紧急',
  low: '提示',
  medium: '关注',
};
const priorityLabelMap: Record<InspectionTask['priority'], string> = {
  high: '高',
  low: '低',
  medium: '中',
};
const priorityTypeMap: Record<InspectionTask['priority'], 'error' | 'info' | 'warning'> = {
  high: 'error',
  low: 'info',
  medium: 'warning',
};
const statusLabelMap: Record<InspectionTask['status'], string> = {
  completed: '已完成',
  in_progress: '执行中',
  paused: '已暂停',
  pending: '待处理',
  scheduled: '已排班',
};
const statusTypeMap: Record<InspectionTask['status'], 'default' | 'error' | 'info' | 'success' | 'warning'> = {
  completed: 'success',
  in_progress: 'warning',
  paused: 'default',
  pending: 'info',
  scheduled: 'success',
};
const robotInfo = [
  { label: '剩余电量', value: '86%' },
  { label: '内存占用', value: '12 GB / 30GB' },
  { label: '硬盘占用', value: '80%' },
  { label: '当前位置', value: '学府广场' },
];
const campusZones = [
  {
    content: '人流密度、广场照明、公共广播、异常聚集',
    metric: '126 人/小时',
    name: '学府广场',
    status: '巡检中',
    type: 'info',
  },
  {
    content: '入口拥堵、消防门、疏散标识、视频链路',
    metric: '拥堵指数 72%',
    name: '体育运动中心',
    status: '预警',
    type: 'warning',
  },
  {
    content: '阅览区温湿度、门禁闸机、人流密度、消防通道',
    metric: '24.6 ℃ / 51%',
    name: '文理图书馆',
    status: '正常',
    type: 'success',
  },
  {
    content: '水位、护栏、警示牌、夜间补光',
    metric: '水位 0.82 m',
    name: '听荷池',
    status: '待复核',
    type: 'warning',
  },
  {
    content: '燃气报警、后厨温度、排烟系统、后勤通道',
    metric: '燃气 0 ppm',
    name: '东三食堂',
    status: '正常',
    type: 'success',
  },
  {
    content: '消防通道、电瓶车停放、楼栋照明、夜间噪声',
    metric: '通道无遮挡',
    name: '北园学生宿舍',
    status: '正常',
    type: 'success',
  },
  {
    content: '视频终端、车道占用、充电桩、网络网关',
    metric: '视频离线',
    name: '东区停车场',
    status: '离线',
    type: 'error',
  },
] as const;

const summaryCards = computed(() => {
  const summary = dashboard.value?.summary;
  if (!summary) {
    return [];
  }
  return [
    {
      description: '在线巡检点总量',
      title: '巡检点位',
      value: `${summary.totalPoints}`,
    },
    {
      description: '待处理或已排班任务',
      title: '待执行任务',
      value: `${summary.pendingTasks}`,
    },
    {
      description: '当前执行中的任务数',
      title: '执行中任务',
      value: `${summary.activeTasks}`,
    },
    {
      description: '当前值班人员数量',
      title: '值班人员',
      value: `${summary.onDutyInspectors}`,
    },
  ];
});

function progressPercent(value: number) {
  const total = dashboard.value?.summary.totalPoints || 1;
  return Math.round((value / total) * 100);
}

function goTo(path: string) {
  router.push(path).catch((error) => console.error('navigation failed', error));
}

async function loadDashboard() {
  loading.value = true;
  try {
    dashboard.value = await getInspectionDashboard();
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadDashboard();
});
</script>

<template>
  <Page auto-content-height>
    <div class="space-y-4 p-1">
      <div class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <NCard v-for="item in summaryCards" :key="item.title" :bordered="false" class="shadow-sm">
          <div class="text-sm text-slate-500">{{ item.title }}</div>
          <div class="mt-3 text-3xl font-semibold text-slate-900">{{ item.value }}</div>
          <div class="mt-2 text-xs text-slate-400">{{ item.description }}</div>
        </NCard>
      </div>

      <div class="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <NCard :bordered="false" class="shadow-sm" title="机器人信息">
          <div class="space-y-3">
            <div
              v-for="item in robotInfo"
              :key="item.label"
              class="flex items-center justify-between gap-4 rounded-lg bg-slate-50 px-4 py-3 text-sm"
            >
              <span class="text-slate-500">{{ item.label }}</span>
              <span class="text-right font-medium text-slate-900">{{ item.value }}</span>
            </div>
          </div>
        </NCard>

        <NCard :bordered="false" class="shadow-sm xl:col-span-2" title="校园巡检">
          <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            <div v-for="(zone, index) in campusZones" :key="zone.name" class="rounded-2xl border border-slate-200 p-4">
              <div class="flex items-start justify-between gap-3">
                <div>
                  <div class="text-xs text-slate-400">巡检点 {{ index + 1 }}</div>
                  <div class="mt-1 text-base font-semibold text-slate-900">{{ zone.name }}</div>
                </div>
                <NTag :type="zone.type" size="small">{{ zone.status }}</NTag>
              </div>
              <div class="my-4 h-2 rounded-full bg-slate-100">
                <div
                  class="h-2 rounded-full"
                  :class="{
                    'bg-emerald-500': zone.type === 'success',
                    'bg-red-500': zone.type === 'error',
                    'bg-sky-500': zone.type === 'info',
                    'bg-amber-500': zone.type === 'warning',
                  }"
                  :style="{ width: zone.type === 'error' ? '35%' : zone.type === 'warning' ? '68%' : '88%' }"
                ></div>
              </div>
              <div class="text-sm text-slate-600">{{ zone.content }}</div>
              <div class="mt-3 rounded-lg bg-slate-50 px-3 py-2 text-sm font-medium text-slate-800">
                当前指标：{{ zone.metric }}
              </div>
            </div>
          </div>
        </NCard>
      </div>

      <div class="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <NCard :bordered="false" class="shadow-sm xl:col-span-1" title="点位态势">
          <div v-if="loading" class="space-y-3">
            <NSkeleton :repeat="3" text />
          </div>
          <div v-else class="space-y-4">
            <div
              v-for="item in dashboard?.statusDistribution ?? []"
              :key="item.label"
              class="rounded-xl bg-slate-50 p-4"
            >
              <div class="mb-2 flex items-center justify-between text-sm text-slate-600">
                <span>{{ item.label }}</span>
                <span>{{ item.value }}</span>
              </div>
              <NProgress
                :color="item.type === 'success' ? '#18a058' : item.type === 'warning' ? '#f0a020' : '#d03050'"
                :percentage="progressPercent(item.value)"
                :show-indicator="false"
                processing
                type="line"
              />
            </div>
            <div class="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">
              当前离线点位 {{ dashboard?.summary.offlinePoints ?? 0 }} 个，预警点位
              {{ dashboard?.summary.warningPoints ?? 0 }} 个。
            </div>
          </div>
        </NCard>

        <NCard :bordered="false" class="shadow-sm xl:col-span-2" title="待执行任务">
          <template #header-extra>
            <NButton text type="primary" @click="goTo('/inspection/tasks')">查看全部</NButton>
          </template>
          <div v-if="loading" class="space-y-3">
            <NSkeleton :repeat="4" text />
          </div>
          <div v-else-if="dashboard?.upcomingTasks.length" class="space-y-3">
            <div
              v-for="task in dashboard?.upcomingTasks"
              :key="task.id"
              class="flex flex-col gap-3 rounded-xl border border-slate-200 p-4 transition hover:border-primary md:flex-row md:items-center md:justify-between"
            >
              <div>
                <div class="flex flex-wrap items-center gap-2">
                  <div class="text-base font-medium text-slate-900">{{ task.title }}</div>
                  <NTag :type="priorityTypeMap[task.priority]" size="small">
                    {{ priorityLabelMap[task.priority] }}优先级
                  </NTag>
                  <NTag :type="statusTypeMap[task.status]" size="small">
                    {{ statusLabelMap[task.status] }}
                  </NTag>
                </div>
                <div class="mt-2 text-sm text-slate-500">
                  {{ task.pointName }} · {{ task.inspectorName }} · {{ task.plannedStart }}
                </div>
              </div>
              <NButton ghost type="primary" @click="goTo(`/inspection/tasks/${task.id}`)">
                编辑任务
              </NButton>
            </div>
          </div>
          <NEmpty v-else description="暂无待执行任务" />
        </NCard>
      </div>

      <div class="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <NCard :bordered="false" class="shadow-sm" title="最新巡检记录">
          <div v-if="loading" class="space-y-3">
            <NSkeleton :repeat="4" text />
          </div>
          <div v-else-if="dashboard?.recentRecords.length" class="space-y-3">
            <div
              v-for="record in dashboard?.recentRecords"
              :key="record.id"
              class="rounded-xl bg-slate-50 p-4"
            >
              <div class="flex items-center justify-between gap-3">
                <div class="font-medium text-slate-900">{{ record.taskTitle }}</div>
                <div class="text-xs text-slate-400">{{ record.finishedAt }}</div>
              </div>
              <div class="mt-1 text-sm text-slate-500">
                {{ record.pointName }} · {{ record.inspectorName }}
              </div>
              <div class="mt-2 text-sm text-slate-600">{{ record.summary }}</div>
            </div>
          </div>
          <NEmpty v-else description="暂无巡检记录" />
        </NCard>

        <NCard :bordered="false" class="shadow-sm" title="告警与关注事项">
          <template #header-extra>
            <NButton text type="primary" @click="goTo('/inspection/alerts')">查看告警</NButton>
          </template>
          <div v-if="loading" class="space-y-3">
            <NSkeleton :repeat="4" text />
          </div>
          <div v-else-if="dashboard?.alerts.length" class="space-y-3">
            <div
              v-for="alert in dashboard?.alerts"
              :key="alert.id"
              class="rounded-xl border border-slate-200 p-4"
            >
              <div class="flex items-center justify-between gap-2">
                <div class="font-medium text-slate-900">{{ alert.title }}</div>
                <NTag :type="alertTypeMap[alert.level]" size="small">
                  {{ alertLabelMap[alert.level] }}
                </NTag>
              </div>
              <div class="mt-2 text-sm text-slate-600">{{ alert.content }}</div>
              <div class="mt-2 text-xs text-slate-400">{{ alert.createdAt }}</div>
            </div>
          </div>
          <NEmpty v-else description="暂无告警信息" />
        </NCard>
      </div>
    </div>
  </Page>
</template>
