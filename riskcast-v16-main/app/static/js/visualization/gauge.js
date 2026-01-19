
(function() {
    'use strict';

    if (typeof window.RISKCAST === 'undefined') {
        window.RISKCAST = {};
    }
    if (typeof window.RISKCAST.visualization === 'undefined') {
        window.RISKCAST.visualization = {};
    }

    const utils = window.RISKCAST.visualization.utils || {};

    /**
     * Get color for confidence level
     */
    function getConfidenceColor(confidence) {
        if (confidence < 0.5) {
            return '#FF6B35'; // Orange
        } else if (confidence < 0.75) {
            return '#00D9FF'; // Cyan
        } else {
            return '#00FFC8'; // Neon green
        }
    }

    /**
     * Create confidence gauge
     */
    function createGauge(containerId, confidence) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Gauge container not found: ${containerId}`);
            return null;
        }

        // Clear container
        container.innerHTML = '';

        // Create canvas
        const canvas = document.createElement('canvas');
        canvas.width = 300;
        canvas.height = 300;
        container.appendChild(canvas);

        const ctx = canvas.getContext('2d');
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        const radius = 100;
        const lineWidth = 20;

        // Clamp confidence to 0-1
        confidence = Math.max(0, Math.min(1, confidence || 0));

        // Get color
        const color = getConfidenceColor(confidence);

        /**
         * Draw gauge
         */
        function drawGauge() {
            // Clear canvas
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Draw background arc (gray)
            ctx.beginPath();
            ctx.arc(centerX, centerY, radius, Math.PI, 0, false);
            ctx.strokeStyle = 'rgba(143, 255, 208, 0.2)';
            ctx.lineWidth = lineWidth;
            ctx.lineCap = 'round';
            ctx.stroke();

            // Draw confidence arc
            const angle = Math.PI * (1 - confidence);
            ctx.beginPath();
            ctx.arc(centerX, centerY, radius, Math.PI, angle, false);
            ctx.strokeStyle = color;
            ctx.lineWidth = lineWidth;
            ctx.lineCap = 'round';
            ctx.stroke();
            
            // Add glow effect
            ctx.shadowBlur = 20;
            ctx.shadowColor = color;
            ctx.stroke();

            // Draw needle
            const needleAngle = Math.PI - (Math.PI * confidence);
            const needleLength = radius - 10;
            const needleX = centerX + Math.cos(needleAngle) * needleLength;
            const needleY = centerY - Math.sin(needleAngle) * needleLength;

            ctx.save();
            ctx.translate(centerX, centerY);
            ctx.rotate(-needleAngle + Math.PI);
            
            ctx.beginPath();
            ctx.moveTo(0, 0);
            ctx.lineTo(needleLength, 0);
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 3;
            ctx.lineCap = 'round';
            ctx.shadowBlur = 0;
            ctx.stroke();
            
            // Needle center circle
            ctx.beginPath();
            ctx.arc(0, 0, 8, 0, Math.PI * 2);
            ctx.fillStyle = '#ffffff';
            ctx.fill();
            ctx.strokeStyle = color;
            ctx.lineWidth = 2;
            ctx.stroke();
            
            ctx.restore();

            // Draw confidence value text
            ctx.fillStyle = color;
            ctx.font = 'bold 32px Inter, sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText((confidence * 100).toFixed(0) + '%', centerX, centerY + 40);

            // Draw label
            ctx.fillStyle = '#8FFFD0';
            ctx.font = '14px Inter, sans-serif';
            ctx.fillText('Confidence', centerX, centerY + 70);
        }

        /**
         * Animate gauge
         */
        function animateGauge() {
            const startValue = 0;
            const endValue = confidence;
            const duration = 1500;
            const startTime = performance.now();

            function animate(currentTime) {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);
                
                // Easing function
                const eased = 1 - Math.pow(1 - progress, 3);
                const currentValue = startValue + (endValue - startValue) * eased;
                
                // Redraw with current value
                const currentColor = getConfidenceColor(currentValue);
                const angle = Math.PI * (1 - currentValue);
                
                // Clear and redraw
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                
                // Background
                ctx.beginPath();
                ctx.arc(centerX, centerY, radius, Math.PI, 0, false);
                ctx.strokeStyle = 'rgba(143, 255, 208, 0.2)';
                ctx.lineWidth = lineWidth;
                ctx.lineCap = 'round';
                ctx.stroke();

                // Confidence arc
                ctx.beginPath();
                ctx.arc(centerX, centerY, radius, Math.PI, angle, false);
                ctx.strokeStyle = currentColor;
                ctx.lineWidth = lineWidth;
                ctx.lineCap = 'round';
                ctx.stroke();
                ctx.shadowBlur = 20;
                ctx.shadowColor = currentColor;
                ctx.stroke();

                // Needle
                const needleAngle = Math.PI - (Math.PI * currentValue);
                ctx.save();
                ctx.translate(centerX, centerY);
                ctx.rotate(-needleAngle + Math.PI);
                
                ctx.beginPath();
                ctx.moveTo(0, 0);
                ctx.lineTo(radius - 10, 0);
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 3;
                ctx.lineCap = 'round';
                ctx.shadowBlur = 0;
                ctx.stroke();
                
                ctx.beginPath();
                ctx.arc(0, 0, 8, 0, Math.PI * 2);
                ctx.fillStyle = '#ffffff';
                ctx.fill();
                ctx.strokeStyle = currentColor;
                ctx.lineWidth = 2;
                ctx.stroke();
                
                ctx.restore();

                // Text
                ctx.shadowBlur = 0;
                ctx.fillStyle = currentColor;
                ctx.font = 'bold 32px Inter, sans-serif';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText((currentValue * 100).toFixed(0) + '%', centerX, centerY + 40);

                ctx.fillStyle = '#8FFFD0';
                ctx.font = '14px Inter, sans-serif';
                ctx.fillText('Confidence', centerX, centerY + 70);

                if (progress < 1) {
                    requestAnimationFrame(animate);
                }
            }

            requestAnimationFrame(animate);
        }

        // Start animation
        animateGauge();

        // Store update function with animation
        canvas.updateGauge = function(newConfidence) {
            const targetConfidence = Math.max(0, Math.min(1, newConfidence || 0));
            
            // If value changed significantly, animate
            if (Math.abs(targetConfidence - confidence) > 0.01) {
                const startValue = confidence;
                const endValue = targetConfidence;
                const duration = 1500;
                const startTime = performance.now();

                function animate(currentTime) {
                    const elapsed = currentTime - startTime;
                    const progress = Math.min(elapsed / duration, 1);
                    
                    // Easing function
                    const eased = 1 - Math.pow(1 - progress, 3);
                    const currentValue = startValue + (endValue - startValue) * eased;
                    confidence = currentValue;
                    
                    // Redraw with current value
                    const currentColor = getConfidenceColor(currentValue);
                    const angle = Math.PI * (1 - currentValue);
                    
                    // Clear and redraw
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    
                    // Background
                    ctx.beginPath();
                    ctx.arc(centerX, centerY, radius, Math.PI, 0, false);
                    ctx.strokeStyle = 'rgba(143, 255, 208, 0.2)';
                    ctx.lineWidth = lineWidth;
                    ctx.lineCap = 'round';
                    ctx.stroke();

                    // Confidence arc
                    ctx.beginPath();
                    ctx.arc(centerX, centerY, radius, Math.PI, angle, false);
                    ctx.strokeStyle = currentColor;
                    ctx.lineWidth = lineWidth;
                    ctx.lineCap = 'round';
                    ctx.stroke();
                    ctx.shadowBlur = 20;
                    ctx.shadowColor = currentColor;
                    ctx.stroke();

                    // Needle
                    const needleAngle = Math.PI - (Math.PI * currentValue);
                    ctx.save();
                    ctx.translate(centerX, centerY);
                    ctx.rotate(-needleAngle + Math.PI);
                    
                    ctx.beginPath();
                    ctx.moveTo(0, 0);
                    ctx.lineTo(radius - 10, 0);
                    ctx.strokeStyle = '#ffffff';
                    ctx.lineWidth = 3;
                    ctx.lineCap = 'round';
                    ctx.shadowBlur = 0;
                    ctx.stroke();
                    
                    ctx.beginPath();
                    ctx.arc(0, 0, 8, 0, Math.PI * 2);
                    ctx.fillStyle = '#ffffff';
                    ctx.fill();
                    ctx.strokeStyle = currentColor;
                    ctx.lineWidth = 2;
                    ctx.stroke();
                    
                    ctx.restore();

                    // Text
                    ctx.shadowBlur = 0;
                    ctx.fillStyle = currentColor;
                    ctx.font = 'bold 32px Inter, sans-serif';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillText((currentValue * 100).toFixed(0) + '%', centerX, centerY + 40);

                    ctx.fillStyle = '#8FFFD0';
                    ctx.font = '14px Inter, sans-serif';
                    ctx.fillText('Confidence', centerX, centerY + 70);

                    if (progress < 1) {
                        requestAnimationFrame(animate);
                    } else {
                        confidence = targetConfidence; // Ensure final value
                    }
                }

                requestAnimationFrame(animate);
            } else {
                // Small change, just update without animation
                confidence = targetConfidence;
            drawGauge();
            }
        };

        return canvas;
    }

    /**
     * Update gauge
     */
    function updateGauge(gauge, confidence) {
        if (gauge && typeof gauge.updateGauge === 'function') {
            gauge.updateGauge(confidence);
        }
    }

    // Export API
    window.RISKCAST.visualization.gauge = {
        create: createGauge,
        update: updateGauge,
    };

    console.log('✅ RISKCAST Confidence gauge initialized');

})();





















