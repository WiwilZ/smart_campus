import { defineConfig } from '@vben/vite-config';

export default defineConfig(async () => {
  return {
    application: {},
    vite: {
      server: {
        proxy: {
          '/api': {
            changeOrigin: true,
            // 后端由 /mnt/SSD/vision/web (FastAPI) 统一承担 /api/*（含认证、用户、视觉 HTTP 与 /api/vision/ws WebSocket）。
            // 不再 rewrite，因为 FastAPI 内部路由自身就以 /api 开头。
            target: 'http://localhost:8080',
            ws: true,
          },
        },
      },
    },
  };
});
