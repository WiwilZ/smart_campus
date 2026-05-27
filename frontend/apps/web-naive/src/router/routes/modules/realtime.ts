import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    name: 'RealtimeMonitor',
    path: '/realtime',
    component: () => import('#/views/realtime/index.vue'),
    meta: {
      icon: 'lucide:camera',
      order: 1,
      title: '实时监控',
    },
  },
];

export default routes;
