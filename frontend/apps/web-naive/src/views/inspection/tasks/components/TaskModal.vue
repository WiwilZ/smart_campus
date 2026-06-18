<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue';
import { NButton, NForm, NFormItem, NInput, NModal, NSelect } from 'naive-ui';
import type { InspectionTask, InspectionMetaData } from '#/api';

const props = defineProps<{
  show: boolean;
  editData?: InspectionTask | null;
  meta: InspectionMetaData | null;
}>();

const emit = defineEmits<{
  'update:show': [value: boolean];
  'save': [data: Partial<InspectionTask>];
}>();

const visible = computed({
  get: () => props.show,
  set: (val) => emit('update:show', val),
});

const formRef = ref();
const formData = reactive<Partial<InspectionTask>>({
  name: '',
  point: '',
  robot: '',
  description: '',
});

const selectedPoints = computed({
  get: () => formData.point ? formData.point.split(', ') : [],
  set: (val: string[]) => formData.point = val.join(', ')
});

const isEdit = computed(() => !!props.editData);

watch(
  () => props.show,
  (show) => {
    if (show) {
      if (props.editData) {
        Object.assign(formData, props.editData);
      } else {
        Object.assign(formData, {
          name: '', point: '', robot: '', description: '',
        });
      }
    }
  }
);

const handleSave = () => {
  emit('save', { ...formData });
  visible.value = false;
};
</script>

<template>
  <NModal v-model:show="visible" preset="card" style="width: 600px" :title="isEdit ? '编辑任务' : '新增任务'">
    <NForm ref="formRef" :model="formData" label-placement="left" label-width="100">
      <NFormItem label="任务名称" path="name">
        <NInput v-model:value="formData.name" placeholder="输入任务名称" />
      </NFormItem>
      <NFormItem label="巡检点位" path="point">
        <NSelect 
          v-model:value="selectedPoints" 
          :options="meta?.pointOptions || []" 
          placeholder="选择巡检点位" 
          multiple
          clearable
        />
      </NFormItem>
      <NFormItem label="执行机器人" path="robot">
        <NSelect 
          v-model:value="formData.robot" 
          :options="[{label: 'Robot-1', value: 'Robot-1'}, {label: 'Robot-2', value: 'Robot-2'}, {label: 'Robot-3', value: 'Robot-3'}, {label: 'Robot-4', value: 'Robot-4'}, {label: 'Robot-5', value: 'Robot-5'}]" 
          placeholder="选择执行机器人" 
          clearable
        />
      </NFormItem>
      <NFormItem label="说明" path="description">
        <NInput v-model:value="formData.description" type="textarea" placeholder="输入说明" />
      </NFormItem>
    </NForm>
    <template #footer>
      <div class="flex justify-end gap-2">
        <NButton @click="visible = false">取消</NButton>
        <NButton type="primary" @click="handleSave">保存</NButton>
      </div>
    </template>
  </NModal>
</template>
