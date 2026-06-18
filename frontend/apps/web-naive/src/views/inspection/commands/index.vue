<script setup lang="ts">
import type { DataTableColumns } from 'naive-ui';

import type { InspectionCommand } from '#/api';

import { h, onMounted, reactive, ref } from 'vue';

import { Page } from '@vben/common-ui';

import { NButton, NCard, NDataTable, NInput, NModal, NSelect, NTag } from 'naive-ui';

import { getInspectionCommands } from '#/api';

const loading = ref(false);
const rows = ref<InspectionCommand[]>([]);
const filters = reactive({
  command: '',
  robot: '',
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
    title: '机器人',
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
];



async function loadData() {
  loading.value = true;
  try {
    const response = await getInspectionCommands({
      command: filters.command || undefined,
      robot: filters.robot || undefined,
      status: filters.status || undefined,
    });
    rows.value = response.items;
  } finally {
    loading.value = false;
  }
}

function resetFilters() {
  filters.command = '';
  filters.robot = '';
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
            <NInput v-model:value="filters.command" clearable placeholder="命令" style="width: 140px" />
            <NInput v-model:value="filters.robot" clearable placeholder="执行机器人" style="width: 140px" />
            <NSelect v-model:value="filters.status" :options="statusOptions" clearable placeholder="状态" style="width: 140px" />
          </div>
          <div class="flex items-center gap-3 whitespace-nowrap flex-shrink-0">
            <NButton type="primary" @click="loadData">查询</NButton>
            <NButton @click="resetFilters">重置</NButton>
          </div>
        </div>
      </NCard>

      <NCard :bordered="false" class="shadow-sm" title="命令数据列表">
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
  </Page>
</template>
