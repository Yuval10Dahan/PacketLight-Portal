import axios from 'axios';

const API_BASE_URL = '/api';

export const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
});

/**
 * Fetch dashboard statistics for a specific folder
 * @param {number} folderId - The ALM folder ID
 * @returns {Promise} Dashboard stats data
 */
export const getDashboardStats = async (folderId) => {
    const response = await api.get(`/dashboard/stats/${folderId}`);
    return response.data;
};

/**
 * Get all Device folders (folders starting with PL)
 * @returns {Promise} List of device folders
 */
export const getDevices = async () => {
    const response = await api.get('/devices');
    return response.data;
}

/**
 * Get Version folders for a specific device
 * @param {number} folderId - Device folder ID
 * @returns {Promise} List of version folders
 */
export const getVersions = async (folderId) => {
    const response = await api.get(`/devices/${folderId}/versions`);
    return response.data;
}

/**
 * Get initial configuration (root folder ID, etc.)
 * @returns {Promise} Config data
 */
export const getConfig = async () => {
    const response = await api.get('/config');
    return response.data;
};

export default api;
