// 数据库服务层 - API客户端
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

// 封装API请求
async function apiRequest(endpoint: string, options: RequestInit = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  try {
    const response = await fetch(url, config);
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.message || '请求失败');
    }
    
    return data;
  } catch (error) {
    console.error('API请求失败:', error);
    throw error;
  }
}

// 用户相关操作
export const userService = {
  // 获取所有用户
  async getAllUsers() {
    try {
      const data = await apiRequest('/users');
      return data;
    } catch (error) {
      console.error('获取用户失败:', error);
      return [];
    }
  },

  // 根据用户名获取用户
  async getUserByUsername(username: string) {
    try {
      const data = await apiRequest(`/users/username/${username}`);
      return data;
    } catch (error) {
      console.error('获取用户失败:', error);
      return null;
    }
  },

  // 创建用户
  async createUser(user: { username: string; password: string; email?: string; role?: string }) {
    try {
      const data = await apiRequest('/auth/register', {
        method: 'POST',
        body: JSON.stringify(user)
      });
      return data.id;
    } catch (error) {
      console.error('创建用户失败:', error);
      throw error;
    }
  }
};

// 设备相关操作
export const deviceService = {
  // 获取所有设备
  async getAllDevices() {
    try {
      const data = await apiRequest('/devices');
      return data;
    } catch (error) {
      console.error('获取设备失败:', error);
      return [];
    }
  },

  // 添加设备
  async addDevice(device: { name: string; type: string; ip_address?: string; mac_address?: string; location?: string; description?: string }) {
    try {
      const data = await apiRequest('/devices', {
        method: 'POST',
        body: JSON.stringify(device)
      });
      return data.id;
    } catch (error) {
      console.error('添加设备失败:', error);
      throw error;
    }
  },

  // 更新设备状态
  async updateDeviceStatus(deviceId: string, status: string) {
    try {
      const data = await apiRequest(`/devices/${deviceId}/status`, {
        method: 'PUT',
        body: JSON.stringify({ status })
      });
      return data.success;
    } catch (error) {
      console.error('更新设备状态失败:', error);
      return false;
    }
  }
};

// 链路相关操作
export const linkService = {
  // 获取所有链路
  async getAllLinks() {
    try {
      const data = await apiRequest('/links');
      return data;
    } catch (error) {
      console.error('获取链路失败:', error);
      return [];
    }
  },

  // 添加链路
  async addLink(link: { source_device_id: string; target_device_id: string; bandwidth?: number; latency?: number; description?: string }) {
    try {
      const data = await apiRequest('/links', {
        method: 'POST',
        body: JSON.stringify(link)
      });
      return data.id;
    } catch (error) {
      console.error('添加链路失败:', error);
      throw error;
    }
  }
};

// 黑名单相关操作
export const blacklistService = {
  // 获取所有黑名单记录
  async getAllBlacklist() {
    try {
      const data = await apiRequest('/blacklist');
      return data;
    } catch (error) {
      console.error('获取黑名单失败:', error);
      return [];
    }
  },

  // 添加黑名单记录
  async addBlacklist(blacklist: { ip_address: string; reason?: string; blocked_by?: string }) {
    try {
      const data = await apiRequest('/blacklist', {
        method: 'POST',
        body: JSON.stringify(blacklist)
      });
      return data.id;
    } catch (error) {
      console.error('添加黑名单失败:', error);
      throw error;
    }
  },

  // 移除黑名单记录
  async removeBlacklist(id: string) {
    try {
      const data = await apiRequest(`/blacklist/${id}`, {
        method: 'DELETE'
      });
      return data.success;
    } catch (error) {
      console.error('移除黑名单失败:', error);
      return false;
    }
  }
};