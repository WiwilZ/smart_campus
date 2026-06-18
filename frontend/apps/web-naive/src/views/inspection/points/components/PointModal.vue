<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue';
import { NButton, NForm, NFormItem, NInput, NModal } from 'naive-ui';
import type { InspectionPoint } from '#/api';

const props = defineProps<{
  show: boolean;
  editData?: InspectionPoint | null;
}>();

const emit = defineEmits<{
  'update:show': [value: boolean];
  'save': [data: Partial<InspectionPoint>];
}>();

const visible = computed({
  get: () => props.show,
  set: (val) => emit('update:show', val),
});

const formRef = ref();
const formData = reactive<Partial<InspectionPoint>>({
  name: '',
  coordinates: '[0, 0]',
  description: '',
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
          name: '',
          coordinates: '[0, 0]',
          description: '',
        });
      }
    }
  }
);

const handleMapClick = (e: MouseEvent) => {
  const rect = (e.target as HTMLElement).getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;
  formData.coordinates = `[${x.toFixed(2)}, ${y.toFixed(2)}]`;
};

const handleSave = () => {
  emit('save', { ...formData });
  visible.value = false;
};
</script>

<template>
  <NModal v-model:show="visible" preset="card" style="width: 600px" :title="isEdit ? '编辑点位' : '新增点位'">
    <NForm ref="formRef" :model="formData" label-placement="left" label-width="100">
      <NFormItem label="名称" path="name">
        <NInput v-model:value="formData.name" placeholder="输入名称" />
      </NFormItem>
      <NFormItem label="坐标">
        <div class="flex flex-col gap-2 w-full">
          <NInput v-model:value="formData.coordinates" readonly placeholder="点击地图获取坐标" />
          <div 
            class="w-full h-[200px] bg-slate-100 rounded relative cursor-crosshair flex items-center justify-center text-slate-400 overflow-hidden"
            @click="handleMapClick"
          >
            地图区域
            <div 
              v-if="formData.coordinates !== '[0, 0]'"
              class="absolute w-3 h-3 bg-red-500 rounded-full transform -translate-x-1/2 -translate-y-1/2"
              :style="{ left: JSON.parse(formData.coordinates || '[0,0]')[0] + 'px', top: JSON.parse(formData.coordinates || '[0,0]')[1] + 'px' }"
            ></div>
          </div>
        </div>
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
