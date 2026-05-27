<script setup lang="ts">
import type { DataTableColumns } from 'naive-ui';

import type { InspectionCommand } from '#/api';

import { h, onMounted, reactive, ref } from 'vue';

import { Page } from '@vben/common-ui';

import { NButton, NCard, NDataTable, NInput, NModal, NSelect, NTag } from 'naive-ui';

import { getInspectionCommands } from '#/api';

const loading = ref(false);
const rows = ref<InspectionCommand[]>([]);
const current = ref<InspectionCommand | null>(null);
const detailVisible = ref(false);
const filters = reactive({
  keyword: '',
  status: null as null | string,
});

const statusLabelMap: Record<InspectionCommand['status'], string> = {
  failed: '失败',
  running: '执行中',
  success: '成功',
};
const statusTypeMap: Record<InspectionCommand['status'], 'error' | 'info' | 'success'> = {
  failed: 'error',
  running: 'info',
  success: 'success',
};
const statusOptions = [
  { label: '成功', value: 'success' },
  { label: '执行中', value: 'running' },
  { label: '失败', value: 'failed' },
];

const columns: DataTableColumns<InspectionCommand> = [
  {
    key: 'command',
    minWidth: 140,
    title: '命令',
  },
  {
    key: 'target',
    minWidth: 220,
    title: '目标设备',
  },
  {
    key: 'operator',
    minWidth: 100,
    title: '操作人',
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
    key: 'createdAt',
    minWidth: 160,
    title: '下发时间',
  },
  {
    key: 'result',
    minWidth: 220,
    title: '执行结果',
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

function openDetail(row: InspectionCommand) {
  current.value = row;
  detailVisible.value = true;
}

async function loadData() {
  loading.value = true;
  try {
    const response = await getInspectionCommands({
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
      <NCard :bordered="false" class="shadow-sm" title="命令筛选">
        <div class="grid grid-cols-1 gap-3 md:grid-cols-4">
          <NInput v-model:value="filters.keyword" clearable placeholder="搜索命令 / 设备 / 操作人" />
          <NSelect v-model:value="filters.status" :options="statusOptions" clearable placeholder="请选择命令状态" />
          <div class="flex gap-3 md:col-span-2">
            <NButton type="primary" @click="loadData">搜索</NButton>
            <NButton @click="resetFilters">重置</NButton>
          </div>
        </div>
      </NCard>

      <NCard :bordered="false" class="shadow-sm" title="命令列表">
        <NDataTable
          :columns="columns"
          :data="rows"
          :loading="loading"
          :pagination="{ pageSize: 10 }"
          :row-key="(row: InspectionCommand) => row.id"
          scroll-x="1100"
        />
      </NCard>
    </div>

    <NModal v-model:show="detailVisible" preset="card" style="width: 560px" title="命令详情">
      <div class="space-y-3 text-sm">
        <div><span class="text-slate-500">命令：</span>{{ current?.command }}</div>
        <div><span class="text-slate-500">目标设备：</span>{{ current?.target }}</div>
        <div><span class="text-slate-500">操作人：</span>{{ current?.operator }}</div>
        <div><span class="text-slate-500">下发时间：</span>{{ current?.createdAt }}</div>
        <div v-if="current" class="flex items-center gap-2">
          <span class="text-slate-500">状态：</span>
          <NTag :type="statusTypeMap[current.status]">{{ statusLabelMap[current.status] }}</NTag>
        </div>
        <div class="rounded-lg bg-slate-50 p-3 text-slate-600">{{ current?.result }}</div>
      </div>
    </NModal>
  </Page>
</template>
