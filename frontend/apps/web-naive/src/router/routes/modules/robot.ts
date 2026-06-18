import type { RouteRecordRaw } from 'vue-router';
import { BasicLayout } from '#/layouts';

const routes: RouteRecordRaw[] = [
  {
    component: BasicLayout,
    name: 'RobotManager',
    path: '/robot',
    meta: {
      icon: 'lucide:bot',
      order: 2,
      title: '机器人管理',
    },
    children: [
      {
        name: 'RobotControl',
        path: '',
        component: () => import('#/views/robot/index.vue'),
        meta: {
          title: '机器人管理',
          hideInMenu: true,
        },
      },
    ],
  },
];

export default routes;
