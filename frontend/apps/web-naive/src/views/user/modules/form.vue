<script lang="ts" setup>
import type { SystemUserApi } from '#/api/system/user';

import { computed, nextTick, ref } from 'vue';

import { useVbenDrawer } from '@vben/common-ui';

import { useVbenForm } from '#/adapter/form';
import { createUser, updateUser } from '#/api';

import { useFormSchema } from '../data';

const emit = defineEmits<{
  success: [];
}>();

const currentUser = ref<null | SystemUserApi.SystemUser>(null);
const editingId = ref('');

const [Form, formApi] = useVbenForm({
  schema: useFormSchema(),
  showDefaultActions: false,
});

const [Drawer, drawerApi] = useVbenDrawer({
  async onConfirm() {
    const { valid } = await formApi.validate();
    if (!valid) {
      return;
    }
    const values = await formApi.getValues<SystemUserApi.UserPayload>();
    drawerApi.lock();
    (editingId.value ? updateUser(editingId.value, values) : createUser(values))
      .then(() => {
        emit('success');
        drawerApi.close();
      })
      .catch(() => {
        drawerApi.unlock();
      });
  },
  async onOpenChange(isOpen) {
    if (!isOpen) {
      return;
    }

    const data = drawerApi.getData<SystemUserApi.SystemUser>();
    currentUser.value = data ?? null;
    editingId.value = data?.id ?? '';
    formApi.resetForm();
    await nextTick();

    if (data) {
      formApi.setValues({
        realName: data.realName,
        remark: data.remark,
        role: data.role,
        status: data.status,
        username: data.username,
      });
      return;
    }

    formApi.setValues({
      realName: '',
      remark: '',
      role: 'user',
      status: 1,
      username: '',
    });
  },
});

const drawerTitle = computed(() =>
  currentUser.value ? '编辑用户' : '新增用户',
);
</script>

<template>
  <Drawer :title="drawerTitle">
    <Form />
  </Drawer>
</template>
