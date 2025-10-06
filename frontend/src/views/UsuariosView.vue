<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 p-4 md:p-6">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="mb-6 md:mb-8">
        <div class="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
          <div>
            <h1 class="text-2xl md:text-4xl font-bold text-slate-900 mb-2">
              Gestión de Usuarios
            </h1>
            <p class="text-slate-600 text-sm md:text-base">Administra usuarios del sistema</p>
          </div>
          <button 
            @click="showCreateModal = true"
            class="bg-slate-700 hover:bg-slate-800 text-white px-4 md:px-6 py-2 md:py-3 rounded-lg transition-all duration-200 text-sm md:text-base border border-slate-600"
          >
            <svg class="w-4 h-4 md:w-5 md:h-5 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
            </svg>
            Nuevo Usuario
          </button>
        </div>
      </div>

      <!-- Stats Cards -->
      <div class="grid grid-cols-2 md:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 mb-6 md:mb-8">
        <div class="bg-white rounded-lg p-4 md:p-6 shadow-sm border border-slate-200">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-slate-500 text-xs md:text-sm font-medium">Total Usuarios</p>
              <p class="text-xl md:text-3xl font-bold text-slate-900 mt-1 md:mt-2">{{ usuarios.length }}</p>
            </div>
            <div class="w-8 h-8 md:w-12 md:h-12 bg-slate-100 rounded-lg flex items-center justify-center">
              <svg class="w-4 h-4 md:w-6 md:h-6 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"></path>
              </svg>
            </div>
          </div>
        </div>
        
        <div class="bg-white rounded-lg p-4 md:p-6 shadow-sm border border-slate-200">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-slate-500 text-xs md:text-sm font-medium">Administradores</p>
              <p class="text-xl md:text-3xl font-bold text-slate-900 mt-1 md:mt-2">{{ usuarios.filter(u => u.is_admin).length }}</p>
            </div>
            <div class="w-8 h-8 md:w-12 md:h-12 bg-slate-100 rounded-lg flex items-center justify-center">
              <svg class="w-4 h-4 md:w-6 md:h-6 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path>
              </svg>
            </div>
          </div>
        </div>
        
        <div class="bg-white rounded-lg p-4 md:p-6 shadow-sm border border-slate-200">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-slate-500 text-xs md:text-sm font-medium">Usuarios Activos</p>
              <p class="text-xl md:text-3xl font-bold text-slate-900 mt-1 md:mt-2">{{ usuarios.filter(u => u.is_active).length }}</p>
            </div>
            <div class="w-8 h-8 md:w-12 md:h-12 bg-slate-100 rounded-lg flex items-center justify-center">
              <svg class="w-4 h-4 md:w-6 md:h-6 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
              </svg>
            </div>
          </div>
        </div>
        
        <div class="bg-white rounded-lg p-4 md:p-6 shadow-sm border border-slate-200">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-slate-500 text-xs md:text-sm font-medium">Telegram Suscritos</p>
              <p class="text-xl md:text-3xl font-bold text-slate-900 mt-1 md:mt-2">{{ usuarios.filter(u => u.telegram_subscribed).length }}</p>
            </div>
            <div class="w-8 h-8 md:w-12 md:h-12 bg-slate-100 rounded-lg flex items-center justify-center">
              <svg class="w-4 h-4 md:w-6 md:h-6 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
              </svg>
            </div>
          </div>
        </div>
      </div>

      <!-- Users Table -->
      <div class="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
        <div class="px-6 py-4 border-b border-slate-200 bg-slate-50">
          <h2 class="text-lg font-semibold text-slate-900">Lista de Usuarios</h2>
        </div>
        
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-gradient-to-r from-slate-50 to-slate-100 border-b border-slate-200">
              <tr>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Usuario</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Rol</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Estado</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Telegram</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Fecha Creación</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-200">
              <tr
                v-for="usuario in usuarios"
                :key="usuario.id"
                class="hover:bg-slate-50 transition-colors duration-200"
              >
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex items-center">
                    <div class="w-8 h-8 rounded-lg bg-slate-600 flex items-center justify-center text-white text-sm font-bold mr-3">
                      {{ usuario.username.charAt(0).toUpperCase() }}
                    </div>
                    <span class="text-sm font-semibold text-slate-900">{{ usuario.username }}</span>
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium"
                        :class="usuario.is_admin 
                          ? 'bg-amber-100 text-amber-800' 
                          : 'bg-slate-100 text-slate-800'">
                    <div class="w-2 h-2 rounded-full mr-2"
                         :class="usuario.is_admin ? 'bg-amber-400' : 'bg-slate-400'"></div>
                    {{ usuario.is_admin ? 'Administrador' : 'Usuario' }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex items-center space-x-2">
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium"
                          :class="getStatusClass(usuario)">
                      <div class="w-2 h-2 rounded-full mr-2"
                           :class="getStatusDotClass(usuario)"></div>
                      {{ getStatusText(usuario) }}
                    </span>
                    <!-- Quick action buttons -->
                    <div class="flex space-x-1">
                      <button
                        v-if="!usuario.is_active"
                        @click="toggleUserStatus(usuario, 'active')"
                        title="Activar usuario"
                        class="w-6 h-6 flex items-center justify-center rounded-full bg-green-100 hover:bg-green-200 text-green-600 transition-colors"
                      >
                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                        </svg>
                      </button>
                      <button
                        v-if="usuario.is_active && usuario.subscription_status !== 'suspended'"
                        @click="toggleUserStatus(usuario, 'suspended')"
                        title="Suspender usuario"
                        class="w-6 h-6 flex items-center justify-center rounded-full bg-yellow-100 hover:bg-yellow-200 text-yellow-600 transition-colors"
                      >
                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                      </button>
                      <button
                        v-if="usuario.is_active"
                        @click="toggleUserStatus(usuario, 'inactive')"
                        title="Desactivar usuario"
                        class="w-6 h-6 flex items-center justify-center rounded-full bg-red-100 hover:bg-red-200 text-red-600 transition-colors"
                      >
                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                      </button>
                    </div>
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex items-center space-x-2">
                    <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
                          :class="usuario.telegram_subscribed 
                            ? 'bg-blue-100 text-blue-800' 
                            : 'bg-gray-100 text-gray-600'">
                      <div class="w-2 h-2 rounded-full mr-1"
                           :class="usuario.telegram_subscribed ? 'bg-blue-400' : 'bg-gray-400'"></div>
                      {{ usuario.telegram_subscribed ? 'Conectado' : 'No conectado' }}
                    </span>
                    <span v-if="usuario.subscription_status" 
                          class="text-xs text-slate-500">
                      ({{ usuario.subscription_status }})
                    </span>
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                  {{ formatDate(usuario.created_at) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">
                  <div class="flex items-center space-x-2">
                    <button 
                      @click="editUser(usuario)"
                      class="text-slate-600 hover:text-slate-900 transition-colors duration-200"
                      title="Editar usuario"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                      </svg>
                    </button>
                    <button 
                      @click="deleteUser(usuario)"
                      class="text-red-600 hover:text-red-900 transition-colors duration-200"
                      title="Eliminar usuario"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                      </svg>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        
        <div v-if="usuarios.length === 0" class="text-center py-12">
          <div class="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center mx-auto mb-4">
            <svg class="w-6 h-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"></path>
            </svg>
          </div>
          <h3 class="text-base font-semibold text-slate-900 mb-2">No hay usuarios</h3>
          <p class="text-slate-500 text-sm">No se encontraron usuarios en el sistema.</p>
        </div>
      </div>
    </div>

    <!-- Create/Edit User Modal -->
    <div v-if="showCreateModal || showEditModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div class="px-6 py-4 border-b border-slate-200">
          <h3 class="text-lg font-semibold text-slate-900">
            {{ showCreateModal ? 'Crear Usuario' : 'Editar Usuario' }}
          </h3>
        </div>
        
        <form @submit.prevent="saveUser" class="p-6 space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">Nombre de Usuario</label>
            <input
              v-model="userForm.username"
              type="text"
              required
              class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-500 focus:border-transparent"
              placeholder="Ingresa el nombre de usuario"
            />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">Contraseña</label>
            <input
              v-model="userForm.password"
              type="password"
              :required="showCreateModal"
              class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-500 focus:border-transparent"
              placeholder="Ingresa la contraseña"
            />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">Confirmar Contraseña</label>
            <input
              v-model="userForm.confirmPassword"
              type="password"
              :required="showCreateModal"
              class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-500 focus:border-transparent"
              placeholder="Confirma la contraseña"
            />
          </div>
          
          <div class="flex items-center space-x-4">
            <label class="flex items-center">
              <input
                v-model="userForm.is_admin"
                type="checkbox"
                class="w-4 h-4 text-slate-600 bg-slate-100 border-slate-300 rounded focus:ring-slate-500 focus:ring-2"
              />
              <span class="ml-2 text-sm text-slate-700">Administrador</span>
            </label>
            
            <label class="flex items-center">
              <input
                v-model="userForm.is_active"
                type="checkbox"
                class="w-4 h-4 text-slate-600 bg-slate-100 border-slate-300 rounded focus:ring-slate-500 focus:ring-2"
              />
              <span class="ml-2 text-sm text-slate-700">Activo</span>
            </label>
          </div>
          
          <div class="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              @click="closeModal"
              class="px-4 py-2 text-slate-600 hover:text-slate-800 transition-colors duration-200"
            >
              Cancelar
            </button>
            <button
              type="submit"
              class="px-4 py-2 bg-slate-700 hover:bg-slate-800 text-white rounded-lg transition-colors duration-200"
            >
              {{ showCreateModal ? 'Crear' : 'Actualizar' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import apiClient from '@/config/api';
import { useAuthStore } from '../stores/authStore';

const authStore = useAuthStore();
const usuarios = ref([]);
const showCreateModal = ref(false);
const showEditModal = ref(false);
const userForm = ref({
  id: null,
  username: '',
  password: '',
  confirmPassword: '',
  is_admin: false,
  is_active: true
});

const ultimoUsuario = computed(() => {
  if (usuarios.value.length === 0) return 'N/A';
  const ultimo = usuarios.value[usuarios.value.length - 1];
  return ultimo.username;
});

const fetchUsuarios = async () => {
  try {
    console.log('Fetching usuarios...');
    console.log('Auth token:', authStore.token ? 'Present' : 'Missing');
    console.log('User:', authStore.user);
    console.log('Is admin:', authStore.isAdmin);
    
    const response = await apiClient.get('/users/', {
      headers: {
        Authorization: `Bearer ${authStore.token}`,
      },
    });
    usuarios.value = response.data;
    console.log('Usuarios loaded:', usuarios.value.length);
  } catch (err) {
    console.error('Error fetching usuarios:', err);
    console.error('Response status:', err.response?.status);
    console.error('Response data:', err.response?.data);
    
    if (err.response?.status === 401) {
      alert('Tu sesión ha expirado. Por favor, inicia sesión nuevamente.');
      authStore.clearAuthData();
      // Optionally redirect to login
      window.location.href = '/login';
    }
  }
};

const saveUser = async () => {
  if (userForm.value.password !== userForm.value.confirmPassword) {
    alert('Las contraseñas no coinciden');
    return;
  }

  try {
    const userData = {
      username: userForm.value.username,
      is_admin: userForm.value.is_admin,
      is_active: userForm.value.is_active
    };

    if (userForm.value.password) {
      userData.password = userForm.value.password;
    }

    if (showCreateModal.value) {
      await apiClient.post('/users/', userData, {
        headers: {
          Authorization: `Bearer ${authStore.token}`,
        },
      });
    } else {
      await apiClient.put(`/users/${userForm.value.id}`, userData, {
        headers: {
          Authorization: `Bearer ${authStore.token}`,
        },
      });
    }

    await fetchUsuarios();
    closeModal();
  } catch (err) {
    console.error('Error saving user:', err);
    alert('Error al guardar el usuario');
  }
};

const editUser = (usuario) => {
  userForm.value = {
    id: usuario.id,
    username: usuario.username,
    password: '',
    confirmPassword: '',
    is_admin: usuario.is_admin,
    is_active: usuario.is_active
  };
  showEditModal.value = true;
};

const deleteUser = async (usuario) => {
  if (!confirm(`¿Estás seguro de que quieres eliminar al usuario ${usuario.username}?`)) {
    return;
  }

  try {
    await apiClient.delete(`/users/${usuario.id}`, {
      headers: {
        Authorization: `Bearer ${authStore.token}`,
      },
    });
    await fetchUsuarios();
  } catch (err) {
    console.error('Error deleting user:', err);
    alert('Error al eliminar el usuario');
  }
};

const closeModal = () => {
  showCreateModal.value = false;
  showEditModal.value = false;
  userForm.value = {
    id: null,
    username: '',
    password: '',
    confirmPassword: '',
    is_admin: false,
    is_active: true
  };
};

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('es-ES');
};

// Status management functions
const getStatusText = (usuario) => {
  if (!usuario.is_active) return 'Inactivo';
  if (usuario.subscription_status === 'suspended') return 'Suspendido';
  return 'Activo';
};

const getStatusClass = (usuario) => {
  if (!usuario.is_active) return 'bg-red-100 text-red-800';
  if (usuario.subscription_status === 'suspended') return 'bg-yellow-100 text-yellow-800';
  return 'bg-green-100 text-green-800';
};

const getStatusDotClass = (usuario) => {
  if (!usuario.is_active) return 'bg-red-400';
  if (usuario.subscription_status === 'suspended') return 'bg-yellow-400';
  return 'bg-green-400';
};

const toggleUserStatus = async (usuario, newStatus) => {
  try {
    const updateData = {};
    
    switch (newStatus) {
      case 'active':
        updateData.is_active = true;
        updateData.subscription_status = 'active';
        break;
      case 'suspended':
        updateData.is_active = true;
        updateData.subscription_status = 'suspended';
        break;
      case 'inactive':
        updateData.is_active = false;
        updateData.subscription_status = 'inactive';
        break;
    }
    
    await apiClient.put(`/users/${usuario.id}`, updateData, {
      headers: {
        Authorization: `Bearer ${authStore.token}`,
      },
    });
    
    await fetchUsuarios();
  } catch (err) {
    console.error('Error updating user status:', err);
    alert('Error al actualizar el estado del usuario');
  }
};

onMounted(() => {
  fetchUsuarios();
});
</script>
