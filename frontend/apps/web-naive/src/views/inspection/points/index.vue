<script setup lang="ts">
import type { DataTableColumns } from 'naive-ui';

import type { InspectionPoint, InspectionPointsResponse } from '#/api';

import { computed, h, onMounted, reactive, ref } from 'vue';

import { Page } from '@vben/common-ui';

import {
  NButton,
  NCard,
  NDataTable,
  NInput,
  NSelect,
  NTag,
} from 'naive-ui';

import { getInspectionPoints } from '#/api';

const loading = ref(false);
const points = ref<InspectionPoint[]>([]);
const areaOptions = ref<InspectionPointsResponse['areaOptions']>([]);
const statusOptions = ref<InspectionPointsResponse['statusOptions']>([]);
const stats = ref({ normal: 0, offline: 0, warning: 0 });
const filters = reactive({
  area: null as null | string,
  keyword: '',
  status: null as null | string,
});

const statusLabelMap: Record<InspectionPoint['status'], string> = {
  normal: '正常',
  offline: '离线',
  warning: '预警',
};
const statusTypeMap: Record<InspectionPoint['status'], 'error' | 'success' | 'warning'> = {
  normal: 'success',
  offline: 'error',
  warning: 'warning',
};
const riskLabelMap: Record<InspectionPoint['riskLevel'], string> = {
  high: '高风险',
  low: '低风险',
  medium: '中风险',
};
const riskTypeMap: Record<InspectionPoint['riskLevel'], 'error' | 'info' | 'warning'> = {
  high: 'error',
  low: 'info',
  medium: 'warning',
};

const summaryCards = computed(() => [
  { title: '正常点位', value: stats.value.normal },
  { title: '预警点位', value: stats.value.warning },
  { title: '离线点位', value: stats.value.offline },
  { title: '当前结果数', value: points.value.length },
]);

const columns: DataTableColumns<InspectionPoint> = [
  {
    key: 'code',
    title: '点位编号',
    width: 100,
  },
  {
    key: 'name',
    title: '点位名称',
  },
  {
    key: 'area',
    title: '所属区域',
    width: 120,
  },
  {
    key: 'deviceName',
    title: '设备名称',
    minWidth: 180,
  },
  {
    key: 'deviceType',
    title: '设备类型',
    width: 120,
  },
  {
    key: 'status',
    title: '状态',
    width: 100,
    render: (row) =>
      h(
        NTag,
        { bordered: false, type: statusTypeMap[row.status] },
        { default: () => statusLabelMap[row.status] },
      ),
  },
  {
    key: 'riskLevel',
    title: '风险等级',
    width: 100,
    render: (row) =>
      h(
        NTag,
        { bordered: false, type: riskTypeMap[row.riskLevel] },
        { default: () => riskLabelMap[row.riskLevel] },
      ),
  },
  {
    key: 'inspectorName',
    title: '责任人',
    width: 100,
  },
  {
    key: 'lastInspectionTime',
    title: '最近巡检',
    width: 150,
  },
  {
    key: 'description',
    title: '说明',
    minWidth: 220,
  },
];

async function loadPoints() {
  loading.value = true;
  try {
    const response = await getInspectionPoints({
      area: filters.area || undefined,
      keyword: filters.keyword || undefined,
      status: filters.status || undefined,
    });
    areaOptions.value = response.areaOptions;
    points.value = response.items;
    stats.value = response.stats;
    statusOptions.value = response.statusOptions;
  } finally {
    loading.value = false;
  }
}

function resetFilters() {
  filters.area = null;
  filters.keyword = '';
  filters.status = null;
  loadPoints();
}

onMounted(() => {
  loadPoints();
});
</script>

<template>
  <Page auto-content-height>
    <div class="space-y-4 p-1">
      <NCard :bordered="false" class="shadow-sm" title="点位筛选">
        <div class="grid grid-cols-1 gap-3 md:grid-cols-4">
          <NInput v-model:value="filters.keyword" clearable placeholder="搜索点位名称 / 编号 / 设备" />
          <NSelect v-model:value="filters.area" :options="areaOptions" clearable placeholder="筛选区域" />
          <NSelect v-model:value="filters.status" :options="statusOptions" clearable placeholder="筛选状态" />
          <div class="flex gap-3">
            <NButton type="primary" @click="loadPoints">查询</NButton>
            <NButton @click="resetFilters">重置</NButton>
          </div>
        </div>
      </NCard>

      <div class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <NCard v-for="item in summaryCards" :key="item.title" :bordered="false" class="shadow-sm">
          <div class="text-sm text-slate-500">{{ item.title }}</div>
          <div class="mt-3 text-3xl font-semibold text-slate-900">{{ item.value }}</div>
        </NCard>
      </div>

      <NCard :bordered="false" class="shadow-sm" title="巡检点位列表">
        <NDataTable
          :columns="columns"
          :data="points"
          :loading="loading"
          :pagination="{ pageSize: 10 }"
          :row-key="(row: InspectionPoint) => row.id"
          scroll-x="1400"
        />
      </NCard>
    </div>
  </Page>
</template>
