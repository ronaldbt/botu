// src/router/index.js

import { createRouter, createWebHistory } from 'vue-router';
import LoginView from '../views/LoginView.vue';
import DashboardView from '../views/DashboardView.vue';
import { useAuthStore } from '../stores/authStore';
import TickersView from '../views/TickersView.vue';
import EstadosTickersView from '../views/EstadosTickersView.vue';
import OrdenesView from '../views/OrdenesView.vue';
import AlertasView from '../views/AlertasView.vue';
import UsuariosView from '../views/UsuariosView.vue';

const routes = [
  {
    path: '/',
    redirect: '/dashboard',
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: DashboardView,
    meta: { requiresAuth: true },
  },
  {
    path: '/tickers',
    name: 'Tickers',
    component: TickersView,
    meta: { requiresAuth: true },
  },
  {
    path: '/estados-tickers',
    name: 'EstadosTickers',
    component: EstadosTickersView,
    meta: { requiresAuth: true },  // protegida con auth como las otras
  },
  {
    path: '/ordenes',
    name: 'Ordenes',
    component: OrdenesView,
    meta: { requiresAuth: true },
  },
  {
    path: '/alertas',
    name: 'Alertas',
    component: AlertasView,
    meta: { requiresAuth: true },
  },
  {
    path: '/usuarios',
    name: 'Usuarios',
    component: UsuariosView,
    meta: { requiresAuth: true, requiresAdmin: true },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login');
  } else if (to.meta.requiresAdmin && !authStore.user?.is_admin) {
    next('/dashboard'); // Redirigir a dashboard si no es admin
  } else {
    next();
  }
});

export default router;
