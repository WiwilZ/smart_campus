# 智慧校园 Frontend 第一阶段设计规格：基础设施与登录系统

## 1. 简介与目标
本项目旨在为智慧校园系统搭建基于 Next.js、HeroUI v3 和 Tailwind CSS v4 的新一代前端。为了逐步复刻 `vben-admin/web-naive` 的强大能力，第一阶段的核心目标是搭建坚实的基础设施和 1:1 还原登录系统架构。

## 2. 技术栈架构
- **核心框架**：Next.js (App Router 模式)
- **UI 组件库**：HeroUI v3 (原 NextUI，具有现代设计感且高度可定制)
- **样式引擎**：Tailwind CSS v4 (采用最新的 v4 版本带来性能飞跃)
- **状态管理**：Zustand (轻量级，支持 React Hook 无缝集成)
- **样式主题**：集成 `next-themes` 实现明暗模式（Dark Mode）切换。

## 3. 核心目录结构规范
所有第一阶段代码将在新建的 `frontend/` 目录中完成。
```text
frontend/
├── app/
│   ├── (auth)/
│   │   └── login/page.tsx     # 登录页入口
│   ├── (dashboard)/
│   │   └── page.tsx           # 登录后的重定向后台骨架页
│   ├── layout.tsx             # 全局根布局 (含 Provider)
│   └── globals.css            # 全局样式与 Tailwind v4 注入
├── components/
│   └── providers.tsx          # 统管 HeroUIProvider 和 next-themes
├── lib/
│   ├── http.ts                # 基于 fetch 的网络请求封装
│   └── utils.ts               # 通用工具函数 (包含 clsx, tailwind-merge)
├── store/
│   └── useUserStore.ts        # Zustand 用户状态管理
└── middleware.ts              # 核心服务端路由守卫
```

## 4. 鉴权与中间件机制
为了最大化 Next.js 的性能与体验，本项目放弃纯客户端单页应用的鉴权模式，转而采用**服务端 Middleware 混合鉴权**：
1. **状态存储**：用户的 Auth Token 在登录成功后必须同时保存在 Cookie 中（以支持服务端读取）和 Zustand Store 中（以支持客户端响应式渲染）。
2. **拦截逻辑**：`middleware.ts` 监听除 `/login` 和静态资源之外的所有页面访问。如果请求中不包含合法 Token 的 Cookie，则直接在服务端发起 302 重定向至 `/login`，避免页面的“闪屏”现象。
3. **安全与注销**：注销时通过 Server Action 或客户端同时清除 Cookie 与 Zustand 状态。

## 5. UI 复刻详细目标 (登录页)
1. **布局还原**：左右分屏结构，左侧展示品牌或插画背景，右侧展示登录表单。采用响应式设计，移动端自动隐藏左侧。
2. **组件映射**：原项目中基于 Naive UI 的 Input、Button、Checkbox 组件，将被一一对应的 HeroUI v3 组件所替代。
3. **主题切换**：登录页右上方需放置主题切换开关（明/暗模式切换），其样式与行为需与原项目一致。

## 6. 第一阶段成功标准
- 成功初始化 `frontend` 目录且 Next.js 服务可正常启动。
- HeroUI v3 与 Tailwind v4 配置完成并可正常渲染组件。
- 登录页界面还原度达到原项目的视觉标准。
- 鉴权 Middleware 能成功拦截未登录用户对 `(dashboard)` 的访问。
