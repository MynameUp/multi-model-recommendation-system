import Vue from 'vue'
import Router from 'vue-router'
// 新增导入：问答历史页面组件
import UserQAHistory from '@/views/UserQAHistory.vue'


Vue.use(Router)

const commonRoutes = [
  {
    path: '/login',
    name: 'login',
    meta: { title: '登录' },
    component: () => import('../views/UserLogin.vue'),
  },
  {
    path: '/register',
    name: 'register',
    meta: { title: '注册' },
    component: () => import('../views/Register.vue'),
  },
  {
    path: '/404',
    name: '404',
    meta: { title: '404' },
    component: () => import('../components/ErrorPage.vue'),
  },
  {
    path: '/home',
    name: 'home',
    meta: { title: '首页' },
    redirect:'/allnews',
    children:[
      {
        path: '/allnews',
        name: 'allnews',
        component: () => import('../components/AllNews'),
      },
      {
        path: '/domesticnews/:id',
        name: 'domesticnews',
        component: () => import('../components/DomesticNews'),
      }
    ],
    component: () => import('../views/HomeView.vue'),
  },
  {
    path: '/user',
    name: 'user',
    meta: { title: '用户' },
    component: () => import('../views/UserDetail.vue'),
  },
  {
    path: '/message',
    name: 'message',
    meta: { title: '消息' },
    component: () => import('../views/UserMessage.vue'),
  },
  {
    path: '/recommend',
    name: 'recommend',
    meta: { title: '为你推荐' },
    component: () => import('../views/NewsRecommend.vue'),
  },
  {
    path: '/intelligent-recommend',
    name: 'intelligentRecommend',
    meta: { title: '智能推荐助手' },
    component: () => import('../views/IntelligentRecommend.vue'),
  },
  {
    path: '/eventhot',
    name: 'eventhot',
    meta: { title: '时事热点' },
    component: () => import('../views/CurrentEventHotSpot.vue'),
  },
  {
    path: '/newspage/:id',
    name: 'newspage',
    meta: { title: '详情' },
    component: () => import('../views/NewsDetail.vue'),
  },
  {
    path: '/history',
    name: 'history',
    meta: { title: '浏览记录' },
    component: () => import('../views/BrowsingHistory.vue'),
  },
  // 新增：问答历史路由
  {
    path: '/user/qa-history',
    name: 'UserQAHistory',
    component: UserQAHistory,
    meta: {
      title: '问答历史',
      requiresAuth: true  // 需要登录才能访问
    }
  },

  { path: '/', redirect: '/home' },
]

// 本地所有的页面 需要配合后台返回的数据生成页面
export const asyncRoutes = {
}

const createRouter = () => new Router({
  routes: commonRoutes,
  mode: 'history',
  // 修复：删掉未使用的参数 to, from, savedPosition
  scrollBehavior() {
    return { x: 0, y: 0 };
  }
});

const router = createRouter()

export function resetRouter() {
  const newRouter = createRouter()
  router.matcher = newRouter.matcher
}

export default router
