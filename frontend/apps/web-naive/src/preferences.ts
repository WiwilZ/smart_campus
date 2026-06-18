import { defineOverridesPreferences } from '@vben/preferences';

/**
 * @description 项目配置文件
 * 只需要覆盖项目中的一部分配置，不需要的配置不用覆盖，会自动使用默认配置
 * !!! 更改配置后请清空缓存，否则可能不生效
 */
export const overridesPreferences = defineOverridesPreferences({
  // overrides
  app: {
    authPageLayout: 'panel-center',
    defaultHomePath: '/dashboard',
    enableCheckUpdates: false,
    enablePreferences: false,
    name: '智慧校园',
  },
  copyright: {
    companyName: 'scu-201',
    companySiteLink: '',
    date: '2026',
  },
  logo: {
    source: '/logo.png',
  },
  theme: {
    mode: 'light',
    semiDarkHeader: false,
    semiDarkSidebar: false,
    semiDarkSidebarSub: false,
  },
  widget: {
    globalSearch: false,
    languageToggle: false,
    themeToggle: false,
    timezone: false,
  },
});
