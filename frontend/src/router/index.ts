import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";
import AuthPage from "../pages/AuthPage.vue";
import MainLayout from "../layouts/MainLayout.vue";
import ImageRepairPage from "../pages/ImageRepairPage.vue";
import OcrProcessingPage from "../pages/OcrProcessingPage.vue";
import TextCompletionPage from "../pages/TextCompletionPage.vue";
import ProfilePage from "../pages/ProfilePage.vue";
import BatchProcessingPage from "../pages/BatchProcessingPage.vue";
import DashboardPage from "../pages/DashboardPage.vue";
import PipelinePage from "../pages/PipelinePage.vue";
import RepairComparisonPage from "../pages/RepairComparisonPage.vue";
import ImageEnhancePage from "../pages/ImageEnhancePage.vue";
import UserGuidePage from "../pages/UserGuidePage.vue";

const routes: RouteRecordRaw[] = [
  {
    path: "/auth",
    name: "auth",
    component: AuthPage,
  },
  // 默认跳转到登录页
  {
    path: "/",
    redirect: "/auth",
  },
  {
    path: "/app",
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: "",
        redirect: "/app/image-repair",
      },
      {
        path: "image-repair",
        name: "image-repair",
        component: ImageRepairPage,
      },
      {
        path: "image-enhance",
        name: "image-enhance",
        component: ImageEnhancePage,
      },
      {
        path: "ocr-processing",
        name: "ocr-processing",
        component: OcrProcessingPage,
      },
      {
        path: "text-completion",
        name: "text-completion",
        component: TextCompletionPage,
      },
      {
        path: "batch-processing",
        name: "batch-processing",
        component: BatchProcessingPage,
      },

      {
        path: "dashboard",
        name: "dashboard",
        component: DashboardPage,
      },
      {
        path: "user-guide",
        name: "user-guide",
        component: UserGuidePage,
      },
      {
        path: "profile",
        name: "profile",
        component: ProfilePage,
        redirect: "/app/profile/info",
        children: [
          {
            path: "info",
            name: "profile-info",
            component: ProfilePage,
          },
          {
            path: "files",
            name: "profile-files",
            component: ProfilePage,
          },
        ],
      },
      {
        path: "repair-comparison",
        name: "repair-comparison",
        component: RepairComparisonPage,
      },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  if (to.meta.requiresAuth) {
    const token = localStorage.getItem("token");
    
    // 如果没有 token，跳转到登录页
    if (!token) {
      return { path: "/auth" };
    }
    
    // 检查 token 格式是否有效
    const tokenParts = token.split('.');
    if (tokenParts.length !== 3) {
      localStorage.removeItem("token");
      return { path: "/auth" };
    }
    
    // 现在 token 默认 100 年过期，所以不再检查过期时间
    // 只需验证格式即可
  }
  return true;
});

export default router;

