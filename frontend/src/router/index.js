// src/router/index.js

import { createRouter, createWebHistory } from 'vue-router';
import LoginView from '../views/LoginView.vue';
import { useAuthStore } from '../stores/authStore';
import TickersView from '../views/TickersView.vue';
import EstadosTickersView from '../views/EstadosTickersView.vue';
import OrdenesView from '../views/OrdenesView.vue';
import AlertasView from '../views/AlertasView.vue';
import UsuariosView from '../views/UsuariosView.vue';
import TestToolsView from '../views/TestToolsView.vue';
import BitcoinBotView from '../views/BitcoinBotView.vue';
import EthBotView from '../views/EthBotView.vue';
import BnbBotView from '../views/BnbBotView.vue';
import ProfileView from '../views/ProfileView.vue';
import SubscriptionView from '../views/SubscriptionView.vue';
import BacktestView from '../views/BacktestView.vue';
import TradingAutomaticoView from '../views/TradingAutomaticoView.vue';
import BitcoinMainnetView from '../views/BitcoinMainnetView.vue';

const routes = [
  {
    path: '/',
    redirect: '/trading-automatico',
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
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
  {
    path: '/test-tools',
    name: 'TestTools',
    component: TestToolsView,
    meta: { requiresAuth: true },
  },
  {
    path: '/bitcoin-bot',
    name: 'BitcoinBot',
    component: BitcoinBotView,
    meta: { requiresAuth: true },
  },
  {
    path: '/eth-bot',
    name: 'EthBot',
    component: EthBotView,
    meta: { requiresAuth: true },
  },
  {
    path: '/bnb-bot',
    name: 'BnbBot',
    component: BnbBotView,
    meta: { requiresAuth: true },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: ProfileView,
    meta: { requiresAuth: true },
  },
  {
    path: '/subscription',
    name: 'Subscription',
    component: SubscriptionView,
    meta: { requiresAuth: true },
  },
  {
    path: '/backtest',
    name: 'Backtest',
    component: BacktestView,
    meta: { requiresAuth: true },
  },
  {
    path: '/trading-automatico',
    name: 'TradingAutomatico',
    component: TradingAutomaticoView,
    meta: { requiresAuth: true },
  },
  {
    path: '/bitcoin-30m-mainnet',
    name: 'Bitcoin30mMainnet',
    component: BitcoinMainnetView,
    meta: { requiresAuth: true },
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
    next('/trading-automatico'); // Redirigir a trading automático si no es admin
  } else {
    next();
  }
});

export default router;
