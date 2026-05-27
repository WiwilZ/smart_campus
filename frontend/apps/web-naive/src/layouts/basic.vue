<script lang="ts" setup>
import { computed, watch } from 'vue';
import { useRouter } from 'vue-router';

import { AuthenticationLoginExpiredModal } from '@vben/common-ui';
import { useWatermark } from '@vben/hooks';
import {
  BasicLayout,
  LockScreen,
  UserDropdown,
} from '@vben/layouts';
import { preferences } from '@vben/preferences';
import { useAccessStore, useUserStore } from '@vben/stores';

import { $t } from '#/locales';
import { useAuthStore } from '#/store';
import LoginForm from '#/views/_core/authentication/login.vue';
import { useRealtimeSessionState } from '#/views/realtime/transport/realtime-session';

const router = useRouter();
const userStore = useUserStore();
const authStore = useAuthStore();
const accessStore = useAccessStore();
const { connState } = useRealtimeSessionState();
const { destroyWatermark, updateWatermark } = useWatermark();
const backendNetworkText = computed(() => (connState.value === 'live' ? '网络已连接' : '网络未连接'));
const menus = computed(() => [
  {
    handler: () => {
      router.push({ name: 'Profile' });
    },
    icon: 'lucide:user',
    text: $t('page.auth.profile'),
  },
]);

const avatar = computed(() => {
  return userStore.userInfo?.avatar ?? preferences.app.defaultAvatar;
});

async function handleLogout() {
  await authStore.logout(false);
}

watch(
  () => ({
    enable: preferences.app.watermark,
    content: preferences.app.watermarkContent,
  }),
  async ({ enable, content }) => {
    if (enable) {
      await updateWatermark({
        content:
          content ||
          `${userStore.userInfo?.username} - ${userStore.userInfo?.realName}`,
      });
    } else {
      destroyWatermark();
    }
  },
  {
    immediate: true,
  },
);
</script>

<template>
  <BasicLayout @clear-preferences-and-logout="handleLogout">
    <template #header-right-90>
      <div class="backend-network-status" :data-live="connState === 'live'">
        {{ backendNetworkText }}
      </div>
    </template>
    <template #user-dropdown>
      <UserDropdown
        :avatar
        :menus
        :text="userStore.userInfo?.realName"
        description="巡检机器人"
        tag-text="Robot"
        @logout="handleLogout"
      />
    </template>
    <template #extra>
      <AuthenticationLoginExpiredModal
        v-model:open="accessStore.loginExpired"
        :avatar
      >
        <LoginForm />
      </AuthenticationLoginExpiredModal>
    </template>
    <template #lock-screen>
      <LockScreen :avatar @to-login="handleLogout" />
    </template>
  </BasicLayout>
</template>

<style lang="scss" scoped>
.backend-network-status {
  position: fixed;
  top: 10px;
  left: 50%;
  z-index: 10;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  color: #dc2626;
  font-size: 13px;
  background: hsl(var(--background));
  transform: translateX(-50%);
  white-space: nowrap;

  &[data-live='true'] {
    color: #16a34a;
    border-color: rgb(34 197 94 / 45%);
  }
}
</style>
