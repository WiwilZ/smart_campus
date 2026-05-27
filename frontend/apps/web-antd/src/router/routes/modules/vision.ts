import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    name: 'RealSenseMonitor',
    path: '/realsense',
    component: () => import('#/views/realsense/index.vue'),
    meta: {
      icon: 'lucide:camera',
      order: 5,
      title: 'RealSense 监控',
    },
  },
];

export default routes;
