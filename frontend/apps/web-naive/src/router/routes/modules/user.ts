import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    name: 'UserManagement',
    path: '/user',
    component: () => import('#/views/user/list.vue'),
    meta: {
      icon: 'mdi:account-group',
      order: 2,
      title: '用户管理',
    },
  },
];

export default routes;
