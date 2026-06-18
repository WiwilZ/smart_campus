<script setup lang="ts">
import type { DataTableColumns } from 'naive-ui';

import type { InspectionBatch } from '#/api';

import { h, onMounted, reactive, ref } from 'vue';

import { Page } from '@vben/common-ui';

import { NButton, NCard, NDataTable, NInput, NModal, NSelect, NTag } from 'naive-ui';

import { getInspectionBatches } from '#/api';

const loading = ref(false);
const rows = ref<InspectionBatch[]>([]);
const current = ref<InspectionBatch | null>(null);
const detailVisible = ref(false);
const filters = reactive({
  keyword: '',
  status: null as null | string,
});

const statusLabelMap: Record<InspectionBatch['status'], string> = {
  completed: '已完成',
  running: '执行中',
  unfinished: '未完成',
};
const statusTypeMap: Record<InspectionBatch['status'], 'error' | 'info' | 'success'> = {
  completed: 'success',
  running: 'info',
  unfinished: 'error',
};
const statusOptions = [
  { label: '已完成', value: 'completed' },
  { label: '执行中', value: 'running' },
  { label: '未完成', value: 'unfinished' },
];

const columns: DataTableColumns<InspectionBatch> = [
  {
    key: 'batchNo',
    title: '批次号',
    width: 100,
  },
  {
    key: 'type',
    minWidth: 120,
    title: '巡检类型',
  },
  {
    key: 'route',
    minWidth: 240,
    title: '路径',
  },
  {
    key: 'pointCount',
    title: '巡检点',
    width: 100,
  },
  {
    key: 'startedAt',
    minWidth: 160,
    title: '开始时间',
  },
  {
    key: 'finishedAt',
    minWidth: 160,
    title: '结束时间',
    render: (row) => row.finishedAt || '进行中',
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
    key: 'actions',
    title: '详情',
    width: 100,
    render: (row) =>
      h(
        NButton,
        {
          size: 'small',
          onClick: () => openDetail(row),
        },
        { default: () => '查看' },
      ),
  },
];

function openDetail(row: InspectionBatch) {
  current.value = row;
  detailVisible.value = true;
}

async function loadData() {
  loading.value = true;
  try {
    const response = await getInspectionBatches({
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
      <NCard :bordered="false" class="shadow-sm">
        <div class="flex justify-between items-start gap-4">
          <div class="flex flex-wrap gap-4">
            <NInput v-model:value="filters.keyword" clearable placeholder="搜索批次 / 类型 / 路径" style="width: 180px" />
            <NSelect v-model:value="filters.status" :options="statusOptions" clearable placeholder="请选择批次状态" style="width: 140px" />
          </div>
          <div class="flex items-center gap-3 whitespace-nowrap flex-shrink-0">
            <NButton type="primary" @click="loadData">查询</NButton>
            <NButton @click="resetFilters">重置</NButton>
          </div>
        </div>
      </NCard>

      <NCard :bordered="false" class="shadow-sm" title="巡检批次列表">
        <NDataTable
          :columns="columns"
          :data="rows"
          :loading="loading"
          :pagination="{ pageSize: 10 }"
          :row-key="(row: InspectionBatch) => row.id"
          scroll-x="1100"
        />
      </NCard>
    </div>

    <NModal v-model:show="detailVisible" preset="card" style="width: 560px" title="批次详情">
      <div class="space-y-3 text-sm">
        <div><span class="text-slate-500">批次号：</span>{{ current?.batchNo }}</div>
        <div><span class="text-slate-500">巡检类型：</span>{{ current?.type }}</div>
        <div><span class="text-slate-500">路径：</span>{{ current?.route }}</div>
        <div><span class="text-slate-500">巡检点：</span>{{ current?.pointCount }}</div>
        <div><span class="text-slate-500">开始时间：</span>{{ current?.startedAt }}</div>
        <div><span class="text-slate-500">结束时间：</span>{{ current?.finishedAt || '进行中' }}</div>
        <div v-if="current" class="flex items-center gap-2">
          <span class="text-slate-500">状态：</span>
          <NTag :type="statusTypeMap[current.status]">{{ statusLabelMap[current.status] }}</NTag>
        </div>
      </div>
    </NModal>
  </Page>
</template>
