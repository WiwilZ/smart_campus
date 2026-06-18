<script setup lang="ts">
import type { DataTableColumns } from 'naive-ui';

import type { InspectionAlert } from '#/api';

import { h, onMounted, reactive, ref } from 'vue';

import { Page } from '@vben/common-ui';

import { NButton, NCard, NDataTable, NDatePicker, NImage, NInput, NModal, NSelect, NTag } from 'naive-ui';

import { getInspectionAlerts } from '#/api';

const loading = ref(false);
const rows = ref<InspectionAlert[]>([]);
const filters = reactive({
  content: '',
  location: '',
  time: null as null | string,
});

const columns: DataTableColumns<InspectionAlert> = [
  {
    key: 'description',
    minWidth: 180,
    title: '描述',
  },
  {
    key: 'location',
    minWidth: 120,
    title: '地点',
  },
  {
    key: 'image',
    minWidth: 160,
    title: '图片',
    render: (row) =>
      row.image
        ? h(NImage, { src: row.image, width: 100, height: 75, objectFit: 'cover', class: 'rounded-md' })
        : '暂无图片',
  },
  {
    key: 'time',
    minWidth: 160,
    title: '时间',
  },
];

async function loadData() {
  loading.value = true;
  try {
    const response = await getInspectionAlerts({
      content: filters.content || undefined,
      location: filters.location || undefined,
      time: filters.time || undefined,
    });
    rows.value = response.items;
  } finally {
    loading.value = false;
  }
}

function resetFilters() {
  filters.content = '';
  filters.location = '';
  filters.time = null;
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
            <NInput v-model:value="filters.content" clearable placeholder="内容" style="width: 140px" />
            <NInput v-model:value="filters.location" clearable placeholder="地点" style="width: 140px" />
            <NDatePicker v-model:formatted-value="filters.time" value-format="yyyy-MM-dd" type="date" clearable placeholder="时间" style="width: 140px" />
          </div>
          <div class="flex items-center gap-3 whitespace-nowrap flex-shrink-0">
            <NButton type="primary" @click="loadData">查询</NButton>
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
  </Page>
</template>
