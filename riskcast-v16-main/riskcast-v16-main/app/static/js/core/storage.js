
/**
 * LocalStorage wrapper with JSON serialization
 */
export const localStorage = {
    /**
     * Set item in localStorage
     * @param {string} key - Storage key
     * @param {*} value - Value to store
     */
    set(key, value) {
        try {
            const serialized = JSON.stringify(value);
            window.localStorage.setItem(key, serialized);
        } catch (error) {
            console.error(`[Storage] Error setting ${key}:`, error);
        }
    },

    /**
     * Get item from localStorage
     * @param {string} key - Storage key
     * @param {*} defaultValue - Default value if not found
     * @returns {*} Stored value or defaultValue
     */
    get(key, defaultValue = null) {
        try {
            const item = window.localStorage.getItem(key);
            if (item === null) {
                return defaultValue;
            }
            return JSON.parse(item);
        } catch (error) {
            console.error(`[Storage] Error getting ${key}:`, error);
            return defaultValue;
        }
    },

    /**
     * Remove item from localStorage
     * @param {string} key - Storage key
     */
    remove(key) {
        try {
            window.localStorage.removeItem(key);
        } catch (error) {
            console.error(`[Storage] Error removing ${key}:`, error);
        }
    },

    /**
     * Clear all localStorage
     */
    clear() {
        try {
            window.localStorage.clear();
        } catch (error) {
            console.error('[Storage] Error clearing:', error);
        }
    },

    /**
     * Check if key exists
     * @param {string} key - Storage key
     * @returns {boolean}
     */
    has(key) {
        return window.localStorage.getItem(key) !== null;
    }
};

/**
 * SessionStorage wrapper with JSON serialization
 */
export const sessionStorage = {
    /**
     * Set item in sessionStorage
     * @param {string} key - Storage key
     * @param {*} value - Value to store
     */
    set(key, value) {
        try {
            const serialized = JSON.stringify(value);
            window.sessionStorage.setItem(key, serialized);
        } catch (error) {
            console.error(`[SessionStorage] Error setting ${key}:`, error);
        }
    },

    /**
     * Get item from sessionStorage
     * @param {string} key - Storage key
     * @param {*} defaultValue - Default value if not found
     * @returns {*} Stored value or defaultValue
     */
    get(key, defaultValue = null) {
        try {
            const item = window.sessionStorage.getItem(key);
            if (item === null) {
                return defaultValue;
            }
            return JSON.parse(item);
        } catch (error) {
            console.error(`[SessionStorage] Error getting ${key}:`, error);
            return defaultValue;
        }
    },

    /**
     * Remove item from sessionStorage
     * @param {string} key - Storage key
     */
    remove(key) {
        try {
            window.sessionStorage.removeItem(key);
        } catch (error) {
            console.error(`[SessionStorage] Error removing ${key}:`, error);
        }
    },

    /**
     * Clear all sessionStorage
     */
    clear() {
        try {
            window.sessionStorage.clear();
        } catch (error) {
            console.error('[SessionStorage] Error clearing:', error);
        }
    },

    /**
     * Check if key exists
     * @param {string} key - Storage key
     * @returns {boolean}
     */
    has(key) {
        return window.sessionStorage.getItem(key) !== null;
    }
};




















