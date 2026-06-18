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
  point: '',
  metric: '',
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
    title: '点位',
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
      point: filters.point || undefined,
      metric: filters.metric || undefined,
      status: filters.status || undefined,
    });
    rows.value = response.items;
  } finally {
    loading.value = false;
  }
}

function resetFilters() {
  filters.point = '';
  filters.metric = '';
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


      <NCard :bordered="false" class="shadow-sm">
        <div class="flex justify-between items-start gap-4">
          <div class="flex flex-wrap gap-4">
            <NInput v-model:value="filters.point" clearable placeholder="点位" style="width: 140px" />
            <NInput v-model:value="filters.metric" clearable placeholder="指标" style="width: 140px" />
            <NSelect v-model:value="filters.status" :options="statusOptions" clearable placeholder="状态" style="width: 140px" />
          </div>
          <div class="flex items-center gap-3 whitespace-nowrap flex-shrink-0">
            <NButton type="primary" @click="loadData">查询</NButton>
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
