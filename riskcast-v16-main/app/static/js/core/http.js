
/**
 * Fetch wrapper with error handling
 * @param {string} url - Request URL
 * @param {RequestInit} options - Fetch options
 * @returns {Promise<Response>}
 */
export async function fetchJSON(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        },
        ...options
    };

    try {
        const response = await fetch(url, defaultOptions);
        
        if (!response.ok) {
            const errorText = await response.text();
            let errorData;
            try {
                errorData = JSON.parse(errorText);
            } catch {
                errorData = { detail: errorText || response.statusText };
            }
            throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error(`[HTTP] Error fetching ${url}:`, error);
        throw error;
    }
}

/**
 * POST JSON data
 * @param {string} url - Request URL
 * @param {object} data - Data to send
 * @param {RequestInit} options - Additional fetch options
 * @returns {Promise<any>}
 */
export async function postJSON(url, data, options = {}) {
    return fetchJSON(url, {
        method: 'POST',
        body: JSON.stringify(data),
        ...options
    });
}

/**
 * GET request
 * @param {string} url - Request URL
 * @param {RequestInit} options - Additional fetch options
 * @returns {Promise<any>}
 */
export async function getJSON(url, options = {}) {
    return fetchJSON(url, {
        method: 'GET',
        ...options
    });
}

/**
 * PUT JSON data
 * @param {string} url - Request URL
 * @param {object} data - Data to send
 * @param {RequestInit} options - Additional fetch options
 * @returns {Promise<any>}
 */
export async function putJSON(url, data, options = {}) {
    return fetchJSON(url, {
        method: 'PUT',
        body: JSON.stringify(data),
        ...options
    });
}

/**
 * DELETE request
 * @param {string} url - Request URL
 * @param {RequestInit} options - Additional fetch options
 * @returns {Promise<any>}
 */
export async function deleteJSON(url, options = {}) {
    return fetchJSON(url, {
        method: 'DELETE',
        ...options
    });
}

/**
 * Fetch with timeout
 * @param {string} url - Request URL
 * @param {RequestInit} options - Fetch options
 * @param {number} timeout - Timeout in milliseconds
 * @returns {Promise<Response>}
 */
export async function fetchWithTimeout(url, options = {}, timeout = 30000) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        return response;
    } catch (error) {
        clearTimeout(timeoutId);
        if (error.name === 'AbortError') {
            throw new Error(`Request timeout after ${timeout}ms`);
        }
        throw error;
    }
}




















