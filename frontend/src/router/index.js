import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '风险仪表盘' },
  },
  {
    path: '/websites',
    name: 'Websites',
    component: () => import('@/views/Websites.vue'),
    meta: { title: '巡检管理' },
  },
  {
    path: '/leaks',
    name: 'Leaks',
    component: () => import('@/views/Leaks.vue'),
    meta: { title: '泄露记录' },
  },
  {
    path: '/alerts',
    name: 'Alerts',
    component: () => import('@/views/Alerts.vue'),
    meta: { title: '告警中心' },
  },
  {
    path: '/rules',
    name: 'Rules',
    component: () => import('@/views/Rules.vue'),
    meta: { title: '规则管理' },
  },
  {
    path: '/reports',
    name: 'Reports',
    component: () => import('@/views/Reports.vue'),
    meta: { title: '报表中心' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _, next) => {
  if (to.meta.title) document.title = `${to.meta.title} - 敏感信息巡检平台`
  next()
})

export default router
