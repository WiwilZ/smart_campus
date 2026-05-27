<script setup lang="ts">
import type { InspectionMetaData, InspectionTaskPayload } from '#/api';

import { computed, onMounted, reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';

import {
  NAlert,
  NButton,
  NCard,
  NForm,
  NFormItem,
  NInput,
  NSelect,
  NSpin,
} from 'naive-ui';

import { message } from '#/adapter/naive';
import { getInspectionMeta, getInspectionTaskDetail, updateInspectionTask } from '#/api';

const route = useRoute();
const router = useRouter();
const taskId = computed(() => String(route.params.id || ''));
const loading = ref(true);
const saving = ref(false);
const meta = ref<InspectionMetaData | null>(null);
const checklistText = ref('');
const form = reactive<InspectionTaskPayload>({
  checklist: [],
  description: '',
  frequency: '',
  inspectorId: '',
  plannedEnd: '',
  plannedStart: '',
  pointId: '',
  priority: 'medium',
  status: 'pending',
  title: '',
});

const inspectorOptions = computed(
  () => meta.value?.inspectors.map((item) => ({ label: item.name, value: item.id })) ?? [],
);

const currentPoint = computed(() => {
  return meta.value?.pointOptions.find((item) => item.value === form.pointId)?.label || '未选择点位';
});

async function loadDetail() {
  loading.value = true;
  try {
    const [detail, metaData] = await Promise.all([
      getInspectionTaskDetail(taskId.value),
      getInspectionMeta(),
    ]);
    meta.value = metaData;
    form.title = detail.title;
    form.pointId = detail.pointId;
    form.inspectorId = detail.inspectorId;
    form.frequency = detail.frequency;
    form.priority = detail.priority;
    form.status = detail.status;
    form.plannedStart = detail.plannedStart;
    form.plannedEnd = detail.plannedEnd;
    form.description = detail.description;
    checklistText.value = detail.checklist.join('\n');
  } finally {
    loading.value = false;
  }
}

async function onSubmit() {
  const checklist = checklistText.value
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean);
  if (checklist.length === 0) {
    message.error('请至少填写一条巡检项');
    return;
  }
  saving.value = true;
  try {
    await updateInspectionTask(taskId.value, {
      ...form,
      checklist,
    });
    message.success('任务已保存');
    router.push('/inspection/tasks').catch((error) => {
      console.error('navigation failed', error);
    });
  } finally {
    saving.value = false;
  }
}

function goBack() {
  router.push('/inspection/tasks').catch((error) => {
    console.error('navigation failed', error);
  });
}

onMounted(() => {
  loadDetail();
});
</script>

<template>
  <Page auto-content-height>
    <NSpin :show="loading">
      <div class="space-y-4 p-1">
        <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <div class="text-2xl font-semibold text-slate-900">任务编辑</div>
            <div class="mt-1 text-sm text-slate-500">编辑任务基础信息、巡检项和计划时间。</div>
          </div>
          <div class="flex gap-3">
            <NButton @click="goBack">返回列表</NButton>
            <NButton :loading="saving" type="primary" @click="onSubmit">保存任务</NButton>
          </div>
        </div>

        <NAlert :show-icon="false" type="info">
          当前任务关联点位：{{ currentPoint }}。
        </NAlert>

        <NCard :bordered="false" class="shadow-sm">
          <NForm label-placement="top">
            <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
              <NFormItem label="任务标题">
                <NInput v-model:value="form.title" placeholder="请输入任务标题" />
              </NFormItem>
              <NFormItem label="巡检点位">
                <NSelect v-model:value="form.pointId" :options="meta?.pointOptions ?? []" />
              </NFormItem>
              <NFormItem label="巡检人员">
                <NSelect v-model:value="form.inspectorId" :options="inspectorOptions" />
              </NFormItem>
              <NFormItem label="巡检频次">
                <NInput v-model:value="form.frequency" placeholder="例如：每日 08:00 / 16:00" />
              </NFormItem>
              <NFormItem label="优先级">
                <NSelect v-model:value="form.priority" :options="meta?.priorityOptions ?? []" />
              </NFormItem>
              <NFormItem label="任务状态">
                <NSelect v-model:value="form.status" :options="meta?.statusOptions ?? []" />
              </NFormItem>
              <NFormItem label="计划开始">
                <NInput v-model:value="form.plannedStart" placeholder="YYYY-MM-DD HH:mm" />
              </NFormItem>
              <NFormItem label="计划结束">
                <NInput v-model:value="form.plannedEnd" placeholder="YYYY-MM-DD HH:mm" />
              </NFormItem>
            </div>

            <NFormItem label="任务说明">
              <NInput v-model:value="form.description" placeholder="请输入任务说明" type="textarea" />
            </NFormItem>
            <NFormItem label="巡检项（每行一项）">
              <NInput
                v-model:value="checklistText"
                :autosize="{ minRows: 5 }"
                placeholder="例如：\n检查门禁状态\n核对表计读数\n确认告警灯状态"
                type="textarea"
              />
            </NFormItem>
          </NForm>
        </NCard>
      </div>
    </NSpin>
  </Page>
</template>
