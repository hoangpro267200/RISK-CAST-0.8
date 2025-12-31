
export const RatingInterpreter = {
    /**
     * Get rating interpretation for reliability score (0-100)
     * @param {number|string} value - The reliability score
     * @returns {Object} Rating interpretation object
     */
    getReliabilityRating(value) {
        const num = parseInt(value);
        if (num >= 86) {
            return {
                label: 'Excellent',
                icon: '✓✓',
                class: 'excellent',
                color: '#10b981',
                bg: 'linear-gradient(135deg, #10b981, #059669)'
            };
        } else if (num >= 61) {
            return {
                label: 'Good',
                icon: '✓',
                class: 'good',
                color: '#3b82f6',
                bg: 'linear-gradient(135deg, #3b82f6, #2563eb)'
            };
        } else if (num >= 31) {
            return {
                label: 'Fair',
                icon: '⚠️',
                class: 'fair',
                color: '#fbbf24',
                bg: 'linear-gradient(135deg, #fbbf24, #f59e0b)'
            };
        } else {
            return {
                label: 'Unreliable',
                icon: '❌',
                class: 'poor',
                color: '#ef4444',
                bg: 'linear-gradient(135deg, #ef4444, #dc2626)'
            };
        }
    },
    
    /**
     * Get rating interpretation for carrier rating (1-5 stars)
     * @param {number|string} value - The carrier rating
     * @returns {Object} Rating interpretation object
     */
    getCarrierRating(value) {
        const num = parseFloat(value);
        if (num >= 4.6) {
            return {
                label: 'Outstanding',
                icon: '⭐⭐⭐⭐⭐',
                class: 'excellent',
                color: '#10b981'
            };
        } else if (num >= 3.6) {
            return {
                label: 'Good',
                icon: '⭐⭐⭐',
                class: 'good',
                color: '#3b82f6'
            };
        } else if (num >= 2.1) {
            return {
                label: 'Average',
                icon: '⭐⭐',
                class: 'fair',
                color: '#fbbf24'
            };
        } else {
            return {
                label: 'Poor',
                icon: '⭐',
                class: 'poor',
                color: '#ef4444'
            };
        }
    },
    
    /**
     * Get rating interpretation for weather/port risk (1-10)
     * @param {number|string} value - The risk score
     * @returns {Object} Rating interpretation object
     */
    getRiskRating(value) {
        const num = parseFloat(value);
        if (num >= 8.1) {
            return {
                label: 'Extreme Risk',
                icon: '🌪️',
                class: 'extreme',
                color: '#dc2626',
                suggestion: 'Delay Recommended'
            };
        } else if (num >= 6.1) {
            return {
                label: 'High Risk',
                icon: '⛈️',
                class: 'high',
                color: '#ef4444',
                suggestion: 'Monitor Closely'
            };
        } else if (num >= 3.1) {
            return {
                label: 'Moderate Risk',
                icon: '🌤️',
                class: 'moderate',
                color: '#fbbf24',
                suggestion: 'Normal Conditions'
            };
        } else {
            return {
                label: 'Low Risk',
                icon: '☀️',
                class: 'low',
                color: '#10b981',
                suggestion: 'Favorable'
            };
        }
    },
    
    /**
     * Get rating interpretation for container match (1-10)
     * @param {number|string} value - The match score
     * @returns {Object} Rating interpretation object
     */
    getContainerMatchRating(value) {
        const num = parseFloat(value);
        if (num >= 8.5) {
            return {
                label: 'Optimal',
                icon: '✓✓',
                class: 'excellent',
                color: '#10b981'
            };
        } else if (num >= 6.0) {
            return {
                label: 'Good',
                icon: '✓',
                class: 'good',
                color: '#3b82f6'
            };
        } else if (num >= 4.0) {
            return {
                label: 'Fair',
                icon: '⚠️',
                class: 'fair',
                color: '#fbbf24'
            };
        } else {
            return {
                label: 'Poor',
                icon: '❌',
                class: 'poor',
                color: '#ef4444'
            };
        }
    },
    
    /**
     * Get rating interpretation for priority level (1-10)
     * @param {number|string} value - The priority level
     * @returns {Object} Rating interpretation object
     */
    getPriorityRating(value) {
        const num = parseInt(value);
        if (num >= 8) {
            return {
                label: 'Highest',
                icon: '🔴',
                class: 'highest',
                color: '#ef4444'
            };
        } else if (num >= 5) {
            return {
                label: 'High',
                icon: '🟡',
                class: 'high',
                color: '#fbbf24'
            };
        } else {
            return {
                label: 'Low',
                icon: '🟢',
                class: 'low',
                color: '#10b981'
            };
        }
    }
};




















