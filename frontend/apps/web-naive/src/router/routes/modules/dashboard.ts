import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    name: 'InspectionDashboard',
    path: '/dashboard',
    component: () => import('#/views/dashboard/index.vue'),
    meta: {
      icon: 'lucide:layout-dashboard',
      order: 1,
      title: '巡检看板',
    },
  },
];

export default routes;
