<script setup lang="ts">
import type { DataTableColumns } from 'naive-ui';

import type { InspectionRealtimeRow } from '#/api';

import { h, onMounted, reactive, ref } from 'vue';

import { Page } from '@vben/common-ui';

import { NButton, NCard, NDataTable, NInput, NSelect, NTag } from 'naive-ui';

import { getInspectionRealtimeData } from '#/api';

const loading = ref(false);
const rows = ref<InspectionRealtimeRow[]>([]);
const filters = reactive({
  keyword: '',
  status: null as null | string,
});

const statusLabelMap: Record<InspectionRealtimeRow['status'], string> = {
  normal: '正常',
  offline: '离线',
  warning: '预警',
};
const statusTypeMap: Record<InspectionRealtimeRow['status'], 'error' | 'success' | 'warning'> = {
  normal: 'success',
  offline: 'error',
  warning: 'warning',
};
const statusOptions = [
  { label: '正常', value: 'normal' },
  { label: '预警', value: 'warning' },
  { label: '离线', value: 'offline' },
];

const columns: DataTableColumns<InspectionRealtimeRow> = [
  {
    key: 'pointName',
    minWidth: 220,
    title: '巡检点',
  },
  {
    key: 'metric',
    minWidth: 160,
    title: '检测指标',
  },
  {
    key: 'value',
    minWidth: 140,
    title: '实时值',
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
    key: 'time',
    minWidth: 160,
    title: '采集时间',
  },
];

async function loadData() {
  loading.value = true;
  try {
    const response = await getInspectionRealtimeData({
      keyword: filters.keyword || undefined,
      status: filters.status || undefined,
    });
    rows.value = response.items;
  } finally {
    loading.value = false;
  }
}

function resetFilters() {
  filters.keyword = '';
  filters.status = null;
  loadData();
}

onMounted(() => {
  loadData();
});
</script>

<template>
  <Page auto-content-height>
    <div class="space-y-4 p-1">
      <div class="grid grid-cols-1 gap-4 md:grid-cols-4">
        <NCard :bordered="false" class="shadow-sm">
          <div class="text-sm text-slate-500">在线点位</div>
          <div class="mt-3 text-3xl font-semibold text-slate-900">5</div>
        </NCard>
        <NCard :bordered="false" class="shadow-sm">
          <div class="text-sm text-slate-500">预警指标</div>
          <div class="mt-3 text-3xl font-semibold text-amber-500">2</div>
        </NCard>
        <NCard :bordered="false" class="shadow-sm">
          <div class="text-sm text-slate-500">采集频率</div>
          <div class="mt-3 text-3xl font-semibold text-slate-900">1 min</div>
        </NCard>
        <NCard :bordered="false" class="shadow-sm">
          <div class="text-sm text-slate-500">数据来源</div>
          <div class="mt-3 text-3xl font-semibold text-slate-900">Mock</div>
        </NCard>
      </div>

      <NCard :bordered="false" class="shadow-sm" title="实时数据筛选">
        <div class="grid grid-cols-1 gap-3 md:grid-cols-4">
          <NInput v-model:value="filters.keyword" clearable placeholder="搜索点位 / 指标 / 数值" />
          <NSelect v-model:value="filters.status" :options="statusOptions" clearable placeholder="请选择状态" />
          <div class="flex gap-3 md:col-span-2">
            <NButton type="primary" @click="loadData">搜索</NButton>
            <NButton @click="resetFilters">重置</NButton>
          </div>
        </div>
      </NCard>

      <NCard :bordered="false" class="shadow-sm" title="实时数据列表">
        <NDataTable
          :columns="columns"
          :data="rows"
          :loading="loading"
          :pagination="{ pageSize: 10 }"
          :row-key="(row: InspectionRealtimeRow) => row.id"
          scroll-x="900"
        />
      </NCard>
    </div>
  </Page>
</template>
