<script setup lang="ts">
import type { DataTableColumns } from 'naive-ui';

import type { InspectionPoint, InspectionPointsResponse } from '#/api';

import { computed, h, onMounted, reactive, ref } from 'vue';
import PointModal from './components/PointModal.vue';

import { Page } from '@vben/common-ui';

import {
  NButton,
  NCard,
  NDataTable,
  NInput,
  NPopconfirm,
} from 'naive-ui';
import { message } from '#/adapter/naive';

import { getInspectionPoints } from '#/api';

const loading = ref(false);
const points = ref<InspectionPoint[]>([]);
const filters = reactive({
  name: '',
  description: '',
});

const showModal = ref(false);
const editingPoint = ref<InspectionPoint | null>(null);

const handleAdd = () => {
  editingPoint.value = null;
  showModal.value = true;
};

const handleEdit = (row: InspectionPoint) => {
  editingPoint.value = row;
  showModal.value = true;
};

import { createInspectionPoint, updateInspectionPoint, deleteInspectionPoint } from '#/api/inspection';

const handleDelete = async (row: InspectionPoint) => {
  try {
    await deleteInspectionPoint(row.id);
    message.success('删除成功');
    loadPoints();
  } catch (error) {
    message.error('删除失败');
  }
};

const handleSavePoint = async (data: Partial<InspectionPoint>) => {
  try {
    if (editingPoint.value) {
      await updateInspectionPoint(editingPoint.value.id, data);
      message.success('修改成功');
    } else {
      await createInspectionPoint(data);
      message.success('新增成功');
    }
    loadPoints();
  } catch (error) {
    message.error('操作失败');
  }
};

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



const columns: DataTableColumns<InspectionPoint> = [
  { key: 'name', title: '名称' },
  { key: 'coordinates', title: '坐标', width: 150 },
  { key: 'description', title: '说明', minWidth: 200 },
  { key: 'creatorName', title: '创建人', width: 100 },
  { key: 'createTime', title: '创建时间', width: 160 },
  { key: 'modifierName', title: '修改人', width: 100 },
  { key: 'modifyTime', title: '修改时间', width: 160 },
  {
    key: 'actions',
    title: '操作',
    width: 140,
    render: (row) =>
      h('div', { class: 'flex gap-2' }, [
        h(
          NButton,
          { size: 'small', type: 'primary', ghost: true, onClick: () => handleEdit(row) },
          { default: () => '编辑' }
        ),
        h(
          NPopconfirm,
          { onPositiveClick: () => handleDelete(row) },
          {
            default: () => '确认删除该点位吗？',
            trigger: () => h(NButton, { size: 'small', type: 'error', ghost: true }, { default: () => '删除' })
          }
        )
      ]),
  },
];

async function loadPoints() {
  loading.value = true;
  try {
    const response = await getInspectionPoints({
      keyword: filters.keyword || undefined,
    });
    points.value = response.items;
  } finally {
    loading.value = false;
  }
}

function resetFilters() {
  filters.name = '';
  filters.description = '';
  loadPoints();
}

onMounted(() => {
  loadPoints();
});
</script>

<template>
  <Page auto-content-height>
    <div class="space-y-4 p-1">
      <NCard :bordered="false" class="shadow-sm">
        <div class="flex justify-between items-start gap-4">
          <div class="flex flex-wrap gap-4">
            <NInput v-model:value="filters.name" clearable placeholder="名称" style="width: 140px" />
            <NInput v-model:value="filters.description" clearable placeholder="说明" style="width: 140px" />
          </div>
          <div class="flex items-center gap-3 whitespace-nowrap flex-shrink-0">
            <NButton type="primary" @click="loadPoints">查询</NButton>
            <NButton @click="resetFilters">重置</NButton>
          </div>
        </div>
      </NCard>



      <NCard :bordered="false" class="shadow-sm" title="巡检点位列表">
        <template #header-extra>
          <NButton type="primary" @click="handleAdd">新增</NButton>
        </template>
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
    
    <PointModal v-model:show="showModal" :edit-data="editingPoint" @save="handleSavePoint" />
  </Page>
</template>
