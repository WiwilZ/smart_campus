import type { RouteRecordRaw } from 'vue-router';

import { BasicLayout } from '#/layouts';

const routes: RouteRecordRaw[] = [
  {
    name: 'InspectionCenter',
    path: '/inspection',
    component: BasicLayout,
    redirect: '/inspection/points',
    meta: {
      icon: 'lucide:clipboard-list',
      order: 2,
      title: '巡检管理',
    },
    children: [
      {
        name: 'InspectionPoints',
        path: 'points',
        component: () => import('#/views/inspection/points/index.vue'),
        meta: {
          title: '巡检点位',
        },
      },
      {
        name: 'InspectionTasks',
        path: 'tasks',
        component: () => import('#/views/inspection/tasks/index.vue'),
        meta: {
          title: '巡检任务',
        },
      },
      {
        name: 'InspectionTaskEdit',
        path: 'tasks/:id',
        component: () => import('#/views/inspection/tasks/edit.vue'),
        meta: {
          hideInMenu: true,
          title: '任务编辑',
        },
      },

      {
        name: 'InspectionRealtimeData',
        path: 'realtime-data',
        component: () => import('#/views/inspection/reports/index.vue'),
        meta: {
          title: '实时数据',
        },
      },
      {
        name: 'InspectionAlerts',
        path: 'alerts',
        component: () => import('#/views/inspection/alerts/index.vue'),
        meta: {
          title: '告警数据',
        },
      },

      {
        name: 'InspectionCommands',
        path: 'commands',
        component: () => import('#/views/inspection/commands/index.vue'),
        meta: {
          title: '命令数据',
        },
      },
    ],
  },
];

export default routes;
