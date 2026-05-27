<script lang="ts" setup>
import type {
  OnActionClickParams,
  VxeTableGridOptions,
} from '#/adapter/vxe-table';
import type { SystemUserApi } from '#/api';

import { Page, useVbenDrawer } from '@vben/common-ui';
import { Plus } from '@vben/icons';

import { NButton } from 'naive-ui';

import { dialog, message } from '#/adapter/naive';
import { useVbenVxeGrid } from '#/adapter/vxe-table';
import { deleteUser, getUserList, updateUser } from '#/api';

import { useColumns, useGridFormSchema } from './data';
import Form from './modules/form.vue';

defineOptions({ name: 'UserManagement' });

const [FormDrawer, formDrawerApi] = useVbenDrawer({
  connectedComponent: Form,
  destroyOnClose: true,
});

const [Grid, gridApi] = useVbenVxeGrid({
  formOptions: {
    schema: useGridFormSchema(),
    submitOnChange: true,
  },
  gridOptions: {
    columns: useColumns(onActionClick, onStatusChange),
    height: 'auto',
    keepSource: true,
    proxyConfig: {
      ajax: {
        query: async ({ page }, formValues) => {
          return await getUserList({
            page: page.currentPage,
            pageSize: page.pageSize,
            ...formValues,
          });
        },
      },
    },
    rowConfig: {
      keyField: 'id',
    },
    toolbarConfig: {
      custom: true,
      export: false,
      refresh: true,
      search: true,
      zoom: true,
    },
  } as VxeTableGridOptions<SystemUserApi.SystemUser>,
});

function confirmAction(content: string, title: string) {
  return new Promise<boolean>((resolve, reject) => {
    let settled = false;
    const settle = (callback: () => void) => {
      if (settled) {
        return;
      }
      settled = true;
      callback();
    };

    dialog.warning({
      content,
      negativeText: '取消',
      onClose: () => settle(() => reject(new Error('已取消'))),
      onNegativeClick: () => settle(() => reject(new Error('已取消'))),
      onPositiveClick: () => settle(() => resolve(true)),
      positiveText: '确认',
      title,
    });
  });
}

function onActionClick(event: OnActionClickParams<SystemUserApi.SystemUser>) {
  switch (event.code) {
    case 'delete': {
      onDelete(event.row);
      break;
    }
    case 'edit': {
      onEdit(event.row);
      break;
    }
  }
}

async function onStatusChange(
  newStatus: number,
  row: SystemUserApi.SystemUser,
) {
  const labels: Record<string, string> = {
    0: '禁用',
    1: '启用',
  };

  try {
    await confirmAction(
      `你要将 ${row.username} 的状态切换为【${labels[newStatus.toString()]}】吗？`,
      '切换状态',
    );
    await updateUser(row.id, { status: newStatus as 0 | 1 });
    return true;
  } catch {
    return false;
  }
}

function onCreate() {
  formDrawerApi.setData(undefined).open();
}

function onDelete(row: SystemUserApi.SystemUser) {
  confirmAction(`你确定要删除用户 ${row.username} 吗？`, '删除用户')
    .then(async () => {
      const loading = message.loading(`正在删除 ${row.username}...`, {
        duration: 0,
      });
      try {
        await deleteUser(row.id);
        loading.destroy();
        message.success(`已删除 ${row.username}`);
        onRefresh();
      } catch {
        loading.destroy();
      }
    })
    .catch(() => undefined);
}

function onEdit(row: SystemUserApi.SystemUser) {
  formDrawerApi.setData(row).open();
}

function onRefresh() {
  gridApi.query();
}
</script>

<template>
  <Page auto-content-height>
    <FormDrawer @success="onRefresh" />
    <Grid table-title="用户列表">
      <template #toolbar-tools>
        <NButton type="primary" @click="onCreate">
          <Plus class="size-5" />
          新增用户
        </NButton>
      </template>
    </Grid>
  </Page>
</template>
