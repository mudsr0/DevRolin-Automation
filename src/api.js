const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const getConfig = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/config`);
    if (!response.ok) throw new Error('Network response was not ok');
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch config:', error);
    return null;
  }
};

export const updatePlatformConfig = async (platform, data) => {
  try {
    const response = await fetch(`${API_BASE_URL}/config/${platform}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Network response was not ok');
    return await response.json();
  } catch (error) {
    console.error(`Failed to update ${platform} config:`, error);
    throw error;
  }
};
