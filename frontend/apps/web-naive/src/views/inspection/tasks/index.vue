<script setup lang="ts">
import type { DataTableColumns } from 'naive-ui';

import type { InspectionMetaData, InspectionTask, InspectionTasksResponse } from '#/api';

import { computed, h, onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';

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
const filters = reactive({
  inspectorId: null as null | string,
  keyword: '',
  priority: null as null | string,
  status: null as null | string,
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
  in_progress: '执行中',
  paused: '已暂停',
  pending: '待处理',
  scheduled: '已排班',
};
const statusTypeMap: Record<InspectionTask['status'], 'default' | 'error' | 'info' | 'success' | 'warning'> = {
  completed: 'success',
  in_progress: 'warning',
  paused: 'default',
  pending: 'info',
  scheduled: 'success',
};

const summaryCards = computed(() => [
  { title: '待执行', value: summary.value.pending },
  { title: '执行中', value: summary.value.inProgress },
  { title: '已完成', value: summary.value.completed },
  { title: '已暂停', value: summary.value.paused },
]);

function openEdit(task: InspectionTask) {
  router.push(`/inspection/tasks/${task.id}`).catch((error) => {
    console.error('navigation failed', error);
  });
}

function openSchedule(task: InspectionTask) {
  currentTask.value = task;
  scheduleForm.executionTime = task.plannedStart.replace(' ', 'T');
  scheduleForm.inspectorId = task.inspectorId;
  scheduleForm.note = '';
  scheduleForm.reminderMinutes = 15;
  scheduleForm.shift = 'morning';
  scheduleVisible.value = true;
}

const columns: DataTableColumns<InspectionTask> = [
  {
    key: 'title',
    title: '任务名称',
    minWidth: 180,
  },
  {
    key: 'pointName',
    title: '巡检点位',
    width: 140,
  },
  {
    key: 'inspectorName',
    title: '巡检人员',
    width: 100,
  },
  {
    key: 'frequency',
    title: '频次',
    width: 140,
  },
  {
    key: 'priority',
    title: '优先级',
    width: 100,
    render: (row) =>
      h(
        NTag,
        { bordered: false, type: priorityTypeMap[row.priority] },
        { default: () => `${priorityLabelMap[row.priority]}优先` },
      ),
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
    key: 'plannedStart',
    title: '计划开始',
    width: 150,
  },
  {
    key: 'plannedEnd',
    title: '计划结束',
    width: 150,
  },
  {
    key: 'actions',
    title: '操作',
    width: 180,
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
          NButton,
          {
            size: 'small',
            type: 'warning',
            ghost: true,
            onClick: () => openSchedule(row),
          },
          { default: () => '排班' },
        ),
      ]),
  },
];

async function loadTasks() {
  loading.value = true;
  try {
    const [tasksResponse, metaResponse] = await Promise.all([
      getInspectionTasks({
        inspectorId: filters.inspectorId || undefined,
        keyword: filters.keyword || undefined,
        priority: filters.priority || undefined,
        status: filters.status || undefined,
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
  filters.inspectorId = null;
  filters.keyword = '';
  filters.priority = null;
  filters.status = null;
  loadTasks();
}

async function submitSchedule() {
  if (!currentTask.value) {
    return;
  }
  if (!scheduleForm.executionTime) {
    message.error('请选择执行时间');
    return;
  }
  scheduling.value = true;
  try {
    await scheduleInspectionTask(currentTask.value.id, {
      executionTime: scheduleForm.executionTime,
      inspectorId: scheduleForm.inspectorId,
      note: scheduleForm.note,
      reminderMinutes: scheduleForm.reminderMinutes,
      shift: scheduleForm.shift,
    });
    message.success('排班已更新');
    scheduleVisible.value = false;
    await loadTasks();
  } finally {
    scheduling.value = false;
  }
}

onMounted(() => {
  loadTasks();
});
</script>

<template>
  <Page auto-content-height>
    <div class="space-y-4 p-1">
      <NCard :bordered="false" class="shadow-sm" title="任务筛选">
        <div class="grid grid-cols-1 gap-3 md:grid-cols-5">
          <NInput v-model:value="filters.keyword" clearable placeholder="搜索任务名称 / 点位 / ID" />
          <NSelect
            v-model:value="filters.status"
            :options="meta?.statusOptions ?? []"
            clearable
            placeholder="筛选状态"
          />
          <NSelect
            v-model:value="filters.priority"
            :options="meta?.priorityOptions ?? []"
            clearable
            placeholder="筛选优先级"
          />
          <NSelect
            v-model:value="filters.inspectorId"
            :options="meta?.inspectors.map((item) => ({ label: item.name, value: item.id })) ?? []"
            clearable
            placeholder="筛选巡检人员"
          />
          <div class="flex gap-3">
            <NButton type="primary" @click="loadTasks">查询</NButton>
            <NButton @click="resetFilters">重置</NButton>
          </div>
        </div>
      </NCard>

      <div class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <NCard v-for="item in summaryCards" :key="item.title" :bordered="false" class="shadow-sm">
          <div class="text-sm text-slate-500">{{ item.title }}</div>
          <div class="mt-3 text-3xl font-semibold text-slate-900">{{ item.value }}</div>
        </NCard>
      </div>

      <NCard :bordered="false" class="shadow-sm" title="巡检任务列表">
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

    <NModal v-model:show="scheduleVisible" preset="card" style="width: 560px" title="任务排班">
      <div class="space-y-4">
        <div class="rounded-xl bg-slate-50 p-4 text-sm text-slate-600">
          <div class="font-medium text-slate-900">{{ currentTask?.title }}</div>
          <div class="mt-1">{{ currentTask?.pointName }} · {{ currentTask?.inspectorName }}</div>
        </div>
        <NForm label-placement="top">
          <NFormItem label="巡检人员">
            <NSelect
              v-model:value="scheduleForm.inspectorId"
              :options="meta?.inspectors.map((item) => ({ label: item.name, value: item.id })) ?? []"
            />
          </NFormItem>
          <NFormItem label="执行时间">
            <input
              v-model="scheduleForm.executionTime"
              class="h-10 w-full rounded-md border border-slate-200 px-3 outline-none transition focus:border-primary"
              type="datetime-local"
            />
          </NFormItem>
          <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
            <NFormItem label="班次">
              <NSelect v-model:value="scheduleForm.shift" :options="meta?.shiftOptions ?? []" />
            </NFormItem>
            <NFormItem label="提前提醒（分钟）">
              <NInputNumber v-model:value="scheduleForm.reminderMinutes" :min="5" class="w-full" />
            </NFormItem>
          </div>
          <NFormItem label="备注">
            <NInput v-model:value="scheduleForm.note" placeholder="排班备注" type="textarea" />
          </NFormItem>
        </NForm>
      </div>
      <template #footer>
        <div class="flex justify-end gap-3">
          <NButton @click="scheduleVisible = false">取消</NButton>
          <NButton :loading="scheduling" type="primary" @click="submitSchedule">保存排班</NButton>
        </div>
      </template>
    </NModal>
  </Page>
</template>
