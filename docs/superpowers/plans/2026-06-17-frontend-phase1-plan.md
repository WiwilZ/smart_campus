# 智慧校园 Frontend 第一阶段（基础设施与登录） 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 初始化 Next.js 项目，配置 HeroUI v3 与 Tailwind v4，搭建全局状态与中间件鉴权，并还原基础的登录页面布局。

**架构：** 采用 Next.js App Router 混合渲染架构，由服务端 Middleware 负责路由级鉴权（无 Cookie 时重定向至登录页）。客户端使用 Zustand 响应式存储用户信息，样式底层依赖 Tailwind CSS v4 配合 HeroUI v3。

**技术栈：** Next.js 15, Tailwind CSS v4, HeroUI v3, Zustand, js-cookie

---

### 任务 1：初始化 Next.js 项目与核心依赖

**文件：**
- 创建：`frontend/package.json`

- [ ] **步骤 1：创建项目骨架**
运行：`npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir=false --import-alias="@/*"`
预期：生成 `frontend` 目录及基础模板。

- [ ] **步骤 2：安装依赖**
运行：`cd frontend && npm install @heroui/react framer-motion zustand js-cookie next-themes && npm install -D @types/js-cookie`
预期：依赖安装成功。

- [ ] **步骤 3：Commit**
```bash
git add frontend/
git commit -m "chore: init next.js project with dependencies"
```

### 任务 2：配置 Tailwind v4 与 HeroUI Providers

**文件：**
- 修改：`frontend/app/globals.css`
- 修改：`frontend/tailwind.config.ts`
- 创建：`frontend/components/providers.tsx`
- 修改：`frontend/app/layout.tsx`

- [ ] **步骤 1：配置 Tailwind 和 HeroUI**
```typescript
// frontend/tailwind.config.ts
import { heroui } from "@heroui/react";
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./node_modules/@heroui/theme/dist/**/*.{js,ts,jsx,tsx}"
  ],
  theme: {
    extend: {},
  },
  darkMode: "class",
  plugins: [heroui()],
};
export default config;
```

- [ ] **步骤 2：创建 Providers 组件**
```tsx
// frontend/components/providers.tsx
"use client";

import { HeroUIProvider } from "@heroui/react";
import { ThemeProvider as NextThemesProvider } from "next-themes";
import { useRouter } from "next/navigation";

export function Providers({ children }: { children: React.ReactNode }) {
  const router = useRouter();

  return (
    <HeroUIProvider navigate={router.push}>
      <NextThemesProvider attribute="class" defaultTheme="system">
        {children}
      </NextThemesProvider>
    </HeroUIProvider>
  );
}
```

- [ ] **步骤 3：注入 Layout 和全局样式**
```tsx
// frontend/app/layout.tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "智慧校园",
  description: "基于 Next.js 的智慧校园管理系统",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
```
*（确保 `frontend/app/globals.css` 仅保留基本的 Tailwind 指令 `@tailwind base; @tailwind components; @tailwind utilities;`）*

- [ ] **步骤 4：Commit**
```bash
git add frontend/
git commit -m "feat: configure tailwind v4, heroui and providers"
```

### 任务 3：封装 Zustand 状态管理与 Cookie 工具

**文件：**
- 创建：`frontend/store/useUserStore.ts`
- 创建：`frontend/lib/utils.ts`

- [ ] **步骤 1：创建 Zustand Store**
```typescript
// frontend/store/useUserStore.ts
import { create } from 'zustand';
import Cookies from 'js-cookie';

interface UserInfo {
  id: string;
  username: string;
  role: string;
}

interface UserState {
  token: string | null;
  userInfo: UserInfo | null;
  setToken: (token: string) => void;
  setUserInfo: (info: UserInfo) => void;
  logout: () => void;
}

export const useUserStore = create<UserState>((set) => ({
  token: typeof window !== 'undefined' ? Cookies.get('token') || null : null,
  userInfo: null,
  setToken: (token) => {
    Cookies.set('token', token, { expires: 7 });
    set({ token });
  },
  setUserInfo: (info) => set({ userInfo: info }),
  logout: () => {
    Cookies.remove('token');
    set({ token: null, userInfo: null });
  },
}));
```

- [ ] **步骤 2：创建 Utils 辅助**
```typescript
// frontend/lib/utils.ts
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

- [ ] **步骤 3：Commit**
```bash
git add frontend/store/ frontend/lib/
git commit -m "feat: setup zustand store and base utils"
```

### 任务 4：配置服务端鉴权 Middleware

**文件：**
- 创建：`frontend/middleware.ts`
- 创建：`frontend/app/(dashboard)/page.tsx`

- [ ] **步骤 1：创建 Dashboard 骨架（测试拦截用）**
```tsx
// frontend/app/(dashboard)/page.tsx
export default function DashboardPage() {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold">工作台 (需登录)</h1>
    </div>
  );
}
```

- [ ] **步骤 2：编写 Middleware**
```typescript
// frontend/middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('token')?.value;
  const isAuthPage = request.nextUrl.pathname.startsWith('/login');

  if (!token && !isAuthPage) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  if (token && isAuthPage) {
    return NextResponse.redirect(new URL('/', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
```

- [ ] **步骤 3：Commit**
```bash
git add frontend/middleware.ts frontend/app/(dashboard)/
git commit -m "feat: add auth middleware and dashboard skeleton"
```

### 任务 5：还原登录页布局与逻辑

**文件：**
- 创建：`frontend/app/(auth)/login/page.tsx`

- [ ] **步骤 1：开发登录页 UI**
```tsx
// frontend/app/(auth)/login/page.tsx
"use client";

import { useState } from "react";
import { Button, Input, Checkbox } from "@heroui/react";
import { useUserStore } from "@/store/useUserStore";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const setToken = useUserStore((state) => state.setToken);
  const router = useRouter();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    // 模拟登录逻辑
    if (username && password) {
      setToken("mock_jwt_token_" + Date.now());
      router.push("/");
    }
  };

  return (
    <div className="flex h-screen w-full bg-default-50">
      {/* 左侧品牌区 */}
      <div className="hidden lg:flex flex-1 flex-col justify-center items-center bg-primary text-white">
        <h1 className="text-5xl font-bold mb-4">智慧校园</h1>
        <p className="text-xl opacity-80">构建未来的教育基础设施</p>
      </div>

      {/* 右侧表单区 */}
      <div className="flex-1 flex flex-col justify-center items-center p-8">
        <div className="w-full max-w-sm">
          <div className="mb-10 text-center">
            <h2 className="text-3xl font-bold text-default-900">登录账号</h2>
            <p className="text-default-500 mt-2">欢迎回来，请输入您的账号密码</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-6">
            <Input
              isRequired
              label="账号"
              placeholder="请输入用户名"
              value={username}
              onValueChange={setUsername}
            />
            <Input
              isRequired
              label="密码"
              placeholder="请输入密码"
              type="password"
              value={password}
              onValueChange={setPassword}
            />
            
            <div className="flex items-center justify-between">
              <Checkbox size="sm">记住我</Checkbox>
              <a href="#" className="text-sm text-primary">忘记密码？</a>
            </div>

            <Button color="primary" type="submit" fullWidth size="lg">
              登 录
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **步骤 2：Commit**
```bash
git add frontend/app/(auth)/login/
git commit -m "feat: implement login page UI and mock auth flow"
```
