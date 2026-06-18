<script setup lang="ts">
import type { DataTableColumns } from 'naive-ui';

import type { InspectionDataRow, InspectionDataResponse } from '#/api';

import { h, onMounted, reactive, ref } from 'vue';

import { Page } from '@vben/common-ui';

import { NButton, NCard, NDataTable, NInput, NModal, NSelect } from 'naive-ui';

import { getInspectionData } from '#/api';

const loading = ref(false);
const rows = ref<InspectionDataRow[]>([]);
const pointOptions = ref<InspectionDataResponse['pointOptions']>([]);
const algorithmOptions = ref<InspectionDataResponse['algorithmOptions']>([]);
const current = ref<InspectionDataRow | null>(null);
const detailVisible = ref(false);
const filters = reactive({
  algorithm: null as null | string,
  keyword: '',
  pointName: null as null | string,
});

const columns: DataTableColumns<InspectionDataRow> = [
  {
    key: 'algorithm',
    minWidth: 220,
    title: '检测项 - 算法',
  },
  {
    key: 'taskNo',
    minWidth: 140,
    title: '任务类型 - 任务号',
  },
  {
    key: 'pointName',
    minWidth: 220,
    title: '巡检点',
  },
  {
    key: 'value',
    minWidth: 140,
    title: '巡检值',
  },
  {
    key: 'time',
    minWidth: 160,
    title: '巡检时间',
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

function openDetail(row: InspectionDataRow) {
  current.value = row;
  detailVisible.value = true;
}

async function loadData() {
  loading.value = true;
  try {
    const response = await getInspectionData({
      algorithm: filters.algorithm || undefined,
      keyword: filters.keyword || undefined,
      pointName: filters.pointName || undefined,
    });
    rows.value = response.items;
    pointOptions.value = response.pointOptions;
    algorithmOptions.value = response.algorithmOptions;
  } finally {
    loading.value = false;
  }
}

function resetFilters() {
  filters.algorithm = null;
  filters.keyword = '';
  filters.pointName = null;
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
            <NInput v-model:value="filters.keyword" clearable placeholder="搜索任务/点位/值" style="width: 160px" />
            <NSelect v-model:value="filters.pointName" :options="pointOptions" clearable placeholder="请选择巡检点" style="width: 140px" />
            <NSelect
              v-model:value="filters.algorithm"
              :options="algorithmOptions"
              clearable
              placeholder="请选择检测项"
              style="width: 140px"
            />
          </div>
          <div class="flex items-center gap-3 whitespace-nowrap flex-shrink-0">
            <NButton type="primary" @click="loadData">查询</NButton>
            <NButton @click="resetFilters">重置</NButton>
          </div>
        </div>
      </NCard>

      <NCard :bordered="false" class="shadow-sm" title="巡检数据列表">
        <NDataTable
          :columns="columns"
          :data="rows"
          :loading="loading"
          :pagination="{ pageSize: 10 }"
          :row-key="(row: InspectionDataRow) => row.id"
          scroll-x="1000"
        />
      </NCard>
    </div>

    <NModal v-model:show="detailVisible" preset="card" style="width: 560px" title="巡检详情">
      <div class="space-y-3 text-sm">
        <div><span class="text-slate-500">检测项：</span>{{ current?.algorithm }}</div>
        <div><span class="text-slate-500">任务：</span>{{ current?.taskNo }}</div>
        <div><span class="text-slate-500">巡检点：</span>{{ current?.pointName }}</div>
        <div><span class="text-slate-500">巡检值：</span>{{ current?.value }}</div>
        <div><span class="text-slate-500">巡检时间：</span>{{ current?.time }}</div>
        <div class="rounded-lg bg-slate-50 p-3 text-slate-600">{{ current?.detail }}</div>
      </div>
    </NModal>
  </Page>
</template>
