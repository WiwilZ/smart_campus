<script setup lang="ts">
import type { DataTableColumns } from 'naive-ui';

import type { InspectionAlert } from '#/api';

import { h, onMounted, reactive, ref } from 'vue';

import { Page } from '@vben/common-ui';

import { NButton, NCard, NDataTable, NInput, NModal, NSelect, NTag } from 'naive-ui';

import { getInspectionAlerts } from '#/api';

const loading = ref(false);
const rows = ref<InspectionAlert[]>([]);
const current = ref<InspectionAlert | null>(null);
const detailVisible = ref(false);
const filters = reactive({
  keyword: '',
  level: null as null | string,
});

const levelLabelMap: Record<InspectionAlert['level'], string> = {
  high: '1级告警',
  low: '提示',
  medium: '2级告警',
};
const levelTypeMap: Record<InspectionAlert['level'], 'error' | 'success' | 'warning'> = {
  high: 'error',
  low: 'success',
  medium: 'warning',
};
const levelOptions = [
  { label: '1级告警', value: 'high' },
  { label: '2级告警', value: 'medium' },
  { label: '提示', value: 'low' },
];

const columns: DataTableColumns<InspectionAlert> = [
  {
    key: 'title',
    minWidth: 220,
    title: '算法 - 检测项',
  },
  {
    key: 'level',
    minWidth: 160,
    title: '告警等级 - 巡检值',
    render: (row) =>
      h(
        NTag,
        { bordered: false, type: levelTypeMap[row.level] },
        { default: () => levelLabelMap[row.level] },
      ),
  },
  {
    key: 'createdAt',
    minWidth: 160,
    title: '告警时间',
  },
  {
    key: 'content',
    minWidth: 320,
    title: '告警内容',
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

function openDetail(row: InspectionAlert) {
  current.value = row;
  detailVisible.value = true;
}

async function loadData() {
  loading.value = true;
  try {
    const response = await getInspectionAlerts({
      keyword: filters.keyword || undefined,
      level: filters.level || undefined,
    });
    rows.value = response.items;
  } finally {
    loading.value = false;
  }
}

function resetFilters() {
  filters.keyword = '';
  filters.level = null;
  loadData();
}

onMounted(() => {
  loadData();
});
</script>

<template>
  <Page auto-content-height>
    <div class="space-y-4 p-1">
      <NCard :bordered="false" class="shadow-sm" title="告警数据筛选">
        <div class="grid grid-cols-1 gap-3 md:grid-cols-4">
          <NInput v-model:value="filters.keyword" clearable placeholder="搜索告警标题 / 内容" />
          <NSelect v-model:value="filters.level" :options="levelOptions" clearable placeholder="请选择告警等级" />
          <div class="flex gap-3 md:col-span-2">
            <NButton type="primary" @click="loadData">搜索</NButton>
            <NButton @click="resetFilters">重置</NButton>
          </div>
        </div>
      </NCard>

      <NCard :bordered="false" class="shadow-sm" title="告警数据列表">
        <NDataTable
          :columns="columns"
          :data="rows"
          :loading="loading"
          :pagination="{ pageSize: 10 }"
          :row-key="(row: InspectionAlert) => row.id"
          scroll-x="1000"
        />
      </NCard>
    </div>

    <NModal v-model:show="detailVisible" preset="card" style="width: 560px" title="告警详情">
      <div class="space-y-3 text-sm">
        <div class="flex items-center gap-2">
          <span class="text-slate-500">等级：</span>
          <NTag v-if="current" :type="levelTypeMap[current.level]">{{ levelLabelMap[current.level] }}</NTag>
        </div>
        <div><span class="text-slate-500">标题：</span>{{ current?.title }}</div>
        <div><span class="text-slate-500">时间：</span>{{ current?.createdAt }}</div>
        <div class="rounded-lg bg-slate-50 p-3 text-slate-600">{{ current?.content }}</div>
      </div>
    </NModal>
  </Page>
</template>
