<script setup lang="ts">
import type { DataTableColumns } from 'naive-ui';

import type { InspectionMetaData, InspectionTask, InspectionTasksResponse } from '#/api';

import { computed, h, onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import TaskModal from './components/TaskModal.vue';

import { Page } from '@vben/common-ui';

import {
  NButton,
  NCard,
  NDataTable,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NModal,
  NSelect,
  NTag,
  NPopconfirm,
} from 'naive-ui';

import { message } from '#/adapter/naive';
import { getInspectionMeta, getInspectionTasks, scheduleInspectionTask } from '#/api';

const router = useRouter();
const loading = ref(false);
const scheduling = ref(false);
const scheduleVisible = ref(false);
const tasks = ref<InspectionTask[]>([]);
const meta = ref<InspectionMetaData | null>(null);
const summary = ref<InspectionTasksResponse['summary']>({
  completed: 0,
  inProgress: 0,
  paused: 0,
  pending: 0,
});
const currentTask = ref<InspectionTask | null>(null);

const showModal = ref(false);
const editingTask = ref<InspectionTask | null>(null);

const handleAdd = () => {
  editingTask.value = null;
  showModal.value = true;
};

import { createInspectionTask, updateInspectionTaskDetail, deleteInspectionTask } from '#/api/inspection';

const handleDelete = async (row: InspectionTask) => {
  try {
    await deleteInspectionTask(row.id);
    message.success('删除成功');
    loadTasks();
  } catch (error) {
    message.error('删除失败');
  }
};

const handleSaveTask = async (data: Partial<InspectionTask>) => {
  try {
    if (editingTask.value) {
      await updateInspectionTaskDetail(editingTask.value.id, data);
      message.success('修改成功');
    } else {
      await createInspectionTask(data);
      message.success('新增成功');
    }
    loadTasks();
  } catch (error) {
    message.error('操作失败');
  }
};
const filters = reactive({
  name: '',
  point: '',
  robot: '',
  status: null as null | string,
  description: '',
});
const scheduleForm = reactive({
  executionTime: '',
  inspectorId: '',
  note: '',
  reminderMinutes: 15,
  shift: 'morning',
});

const priorityLabelMap: Record<InspectionTask['priority'], string> = {
  high: '高',
  low: '低',
  medium: '中',
};
const priorityTypeMap: Record<InspectionTask['priority'], 'error' | 'info' | 'warning'> = {
  high: 'error',
  low: 'info',
  medium: 'warning',
};
const statusLabelMap: Record<InspectionTask['status'], string> = {
  completed: '已完成',
  error: '执行出错',
  in_progress: '执行中',
  pending: '待执行',
};
const statusTypeMap: Record<InspectionTask['status'], 'default' | 'error' | 'info' | 'success' | 'warning'> = {
  completed: 'success',
  error: 'error',
  in_progress: 'warning',
  pending: 'info',
};

const summaryCards = computed(() => [
  { title: '待执行', value: tasks.value.filter(t => t.status === 'pending').length },
  { title: '执行中', value: tasks.value.filter(t => t.status === 'in_progress').length },
  { title: '执行成功', value: tasks.value.filter(t => t.status === 'completed').length },
]);

function openEdit(task: InspectionTask) {
  editingTask.value = task;
  showModal.value = true;
}

const columns: DataTableColumns<InspectionTask> = [
  { key: 'name', title: '名称', minWidth: 150 },
  { key: 'point', title: '点位', minWidth: 200 },
  { key: 'robot', title: '执行机器人', width: 140 },
  {
    key: 'status',
    title: '状态',
    width: 100,
    render: (row) => {
      const statusMap: Record<string, { label: string, type: 'default' | 'error' | 'success' | 'warning' | 'info' }> = {
        pending: { label: '待执行', type: 'info' },
        in_progress: { label: '执行中', type: 'warning' },
        completed: { label: '执行成功', type: 'success' },
        error: { label: '执行失败', type: 'error' }
      };
      const mapObj = statusMap[row.status] || { label: row.status, type: 'default' };
      return h(NTag, { type: mapObj.type, bordered: false }, { default: () => mapObj.label });
    }
  },
  { key: 'startTime', title: '执行开始时间', width: 160 },
  { key: 'endTime', title: '执行结束时间', width: 160 },
  { key: 'description', title: '说明', minWidth: 150 },
  { key: 'creatorName', title: '创建人', width: 100 },
  { key: 'createTime', title: '创建时间', width: 160 },
  { key: 'modifierName', title: '修改人', width: 100 },
  { key: 'modifyTime', title: '修改时间', width: 160 },
  {
    key: 'actions',
    title: '操作',
    width: 180,
    fixed: 'right',
    render: (row) =>
      h('div', { class: 'flex gap-2' }, [
        h(
          NButton,
          {
            size: 'small',
            type: 'primary',
            ghost: true,
            onClick: () => openEdit(row),
          },
          { default: () => '编辑' },
        ),
        h(
          NPopconfirm,
          { onPositiveClick: () => handleDelete(row) },
          {
            default: () => '确认删除该任务吗？',
            trigger: () => h(NButton, { size: 'small', type: 'error', ghost: true }, { default: () => '删除' })
          }
        )
      ]),
  },
];

async function loadTasks() {
  loading.value = true;
  try {
    const [tasksResponse, metaResponse] = await Promise.all([
      getInspectionTasks({
        name: filters.name || undefined,
        point: filters.point || undefined,
        robot: filters.robot || undefined,
        status: filters.status || undefined,
        description: filters.description || undefined,
      }),
      meta.value ? Promise.resolve(meta.value) : getInspectionMeta(),
    ]);
    tasks.value = tasksResponse.items;
    summary.value = tasksResponse.summary;
    meta.value = metaResponse;
  } finally {
    loading.value = false;
  }
}

function resetFilters() {
  filters.name = '';
  filters.point = '';
  filters.robot = '';
  filters.status = null;
  filters.description = '';
  loadTasks();
}

onMounted(() => {
  loadTasks();
});
</script>

<template>
  <Page auto-content-height>
    <div class="space-y-4 p-1">
      <NCard :bordered="false" class="shadow-sm">
        <div class="flex justify-between items-start gap-4">
          <div class="flex flex-wrap gap-4">
            <NInput v-model:value="filters.name" clearable placeholder="名称" style="width: 140px" />
            <NInput v-model:value="filters.point" clearable placeholder="点位" style="width: 140px" />
            <NInput v-model:value="filters.robot" clearable placeholder="执行机器人" style="width: 140px" />
            <NSelect v-model:value="filters.status" :options="meta?.statusOptions ?? []" clearable placeholder="状态" style="width: 140px" />
            <NInput v-model:value="filters.description" clearable placeholder="说明" style="width: 140px" />
          </div>
          <div class="flex items-center gap-3 whitespace-nowrap flex-shrink-0">
            <NButton type="primary" @click="loadTasks">查询</NButton>
            <NButton @click="resetFilters">重置</NButton>
          </div>
        </div>
      </NCard>



      <NCard :bordered="false" class="shadow-sm" title="巡检任务列表">
        <template #header-extra>
          <NButton type="primary" @click="handleAdd">新增</NButton>
        </template>
        <NDataTable
          :columns="columns"
          :data="tasks"
          :loading="loading"
          :pagination="{ pageSize: 10 }"
          :row-key="(row: InspectionTask) => row.id"
          scroll-x="1400"
        />
      </NCard>
    </div>

    <TaskModal v-model:show="showModal" :edit-data="editingTask" :meta="meta" @save="handleSaveTask" />
  </Page>
</template>
