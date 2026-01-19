
import { $id, qs } from '../../core/dom.js';
import { RatingInterpreter } from './rating_interpreter.js';
import { BenchmarkData } from './benchmark_data.js';

export function initSliderDisplays() {
    
    const sliders = [
        { 
            id: 'carrier_rating', 
            format: (val) => `${parseFloat(val).toFixed(1)} ⭐`,
            bubbleFormat: (val) => `${parseFloat(val).toFixed(1)}`,
            interpreter: (val) => RatingInterpreter.getCarrierRating(val),
            benchmark: BenchmarkData.carrierRating
        },
        { 
            id: 'weather_risk', 
            format: (val) => `${parseFloat(val).toFixed(1)}/10`,
            interpreter: (val) => RatingInterpreter.getRiskRating(val),
            bubbleFormat: (val) => `${parseFloat(val).toFixed(1)}`,
            benchmark: null
        },
        { 
            id: 'port_risk', 
            format: (val) => `${parseFloat(val).toFixed(1)}/10`,
            interpreter: (val) => RatingInterpreter.getRiskRating(val),
            bubbleFormat: (val) => `${parseFloat(val).toFixed(1)}`,
            benchmark: null
        },
        { 
            id: 'priority_level', 
            format: (val) => `${parseInt(val)}/10`,
            interpreter: (val) => RatingInterpreter.getPriorityRating(val),
            bubbleFormat: (val) => `${parseInt(val)}`,
            benchmark: null
        },
        { 
            id: 'container_match', 
            format: (val) => `${parseFloat(val).toFixed(1)}/10`,
            interpreter: (val) => RatingInterpreter.getContainerMatchRating(val),
            bubbleFormat: (val) => `${parseFloat(val).toFixed(1)}`,
            benchmark: BenchmarkData.containerMatch
        },
        { 
            id: 'seller_reliability', 
            format: (val) => `${parseInt(val)}/100`,
            interpreter: (val) => RatingInterpreter.getReliabilityRating(val),
            bubbleFormat: (val) => `${parseInt(val)}`,
            benchmark: BenchmarkData.reliability
        },
        { 
            id: 'buyer_reliability', 
            format: (val) => `${parseInt(val)}/100`,
            interpreter: (val) => RatingInterpreter.getReliabilityRating(val),
            bubbleFormat: (val) => `${parseInt(val)}`,
            benchmark: BenchmarkData.reliability
        },
        { 
            id: 'port_climate_stress', 
            format: (val) => `${parseFloat(val).toFixed(1)}/10`,
            interpreter: (val) => RatingInterpreter.getRiskRating(val),
            bubbleFormat: (val) => `${parseFloat(val).toFixed(1)}`,
            benchmark: BenchmarkData.portClimateStress
        },
        { 
            id: 'climate_volatility_index', 
            format: (val) => `${parseInt(val)}/100`,
            interpreter: null,
            bubbleFormat: (val) => `${parseInt(val)}`,
            benchmark: BenchmarkData.climateVolatility
        },
        { 
            id: 'climate_resilience', 
            format: (val) => `${parseFloat(val).toFixed(1)}/10`,
            interpreter: null,
            bubbleFormat: (val) => `${parseFloat(val).toFixed(1)}`,
            benchmark: null
        },
        { 
            id: 'green_packaging', 
            format: (val) => `${parseInt(val)}%`,
            interpreter: null,
            bubbleFormat: (val) => `${parseInt(val)}%`,
            benchmark: null
        }
    ];
    
    let initializedCount = 0;
    
    sliders.forEach(slider => {
        const input = $id(slider.id);
        const display = $id(`${slider.id}_display`);
        
        // Skip if input doesn't exist or is not a range slider
        if (!input || input.type !== 'range' || !display) {
            return;
        }
        
        const formGroup = input.closest('.form-group');
        if (!formGroup) return;
        
        const minValue = parseFloat(input.min) || 0;
        const maxValue = parseFloat(input.max) || 100;
        const sliderRange = maxValue - minValue;
        const numberInput = $id(`${slider.id}_number`);
        
        // Create or get dynamic badge element
        let dynamicBadge = qs('.dynamic-badge', formGroup);
        if (!dynamicBadge && slider.interpreter) {
            dynamicBadge = document.createElement('span');
            dynamicBadge.className = 'dynamic-badge';
            dynamicBadge.setAttribute('data-value', input.value);
            display.parentNode.insertBefore(dynamicBadge, display.nextSibling);
        }

        // Create value bubble (only for long-range sliders)
        const shouldShowBubble = !input.classList.contains('slider-hidden') && (sliderRange > 20 || !!numberInput);
        let valueBubble = null;
        if (shouldShowBubble) {
            valueBubble = qs('.slider-value-bubble', formGroup);
            if (!valueBubble) {
                valueBubble = document.createElement('div');
                valueBubble.className = 'slider-value-bubble';
                formGroup.appendChild(valueBubble);
            }
        }
        
        // Create benchmark hint if benchmark data exists
        let benchmarkHint = qs('.benchmark-hint', formGroup);
        if (!benchmarkHint && slider.benchmark) {
            benchmarkHint = document.createElement('div');
            benchmarkHint.className = 'benchmark-hint';
            formGroup.appendChild(benchmarkHint);
        }
        
        // Initialize display with current value
        const currentValue = input.value || input.getAttribute('value') || input.defaultValue || '0';
        display.textContent = slider.format(currentValue);
        
        // Update functions
        const updateBadge = (value) => {
            if (dynamicBadge && slider.interpreter) {
                const rating = slider.interpreter(value);
                dynamicBadge.className = `dynamic-badge ${rating.class}`;
                dynamicBadge.setAttribute('data-value', value);
                dynamicBadge.innerHTML = `
                    <span class="badge-icon">${rating.icon}</span>
                    <span class="badge-text">${rating.label}</span>
                `;
                
                // Add animation
                dynamicBadge.style.transform = 'scale(1.05)';
                setTimeout(() => {
                    dynamicBadge.style.transform = 'scale(1)';
                }, 150);
            }
        };
        
        const updateBenchmark = (value) => {
            if (benchmarkHint && slider.benchmark) {
                const num = parseFloat(value);
                const avg = slider.benchmark.industryAvg || slider.benchmark.isoStandard || slider.benchmark.noaaAlert;
                const diff = num - avg;
                const comparison = diff >= 0 ? 'Above' : 'Below';
                const benchmarkLabel = slider.benchmark.industryAvg ? 'Industry Avg' : 
                                       slider.benchmark.isoStandard ? 'ISO Standard' : 
                                       slider.benchmark.noaaAlert ? 'NOAA Alert' : 'Benchmark';
                
                benchmarkHint.innerHTML = `
                    <span class="benchmark-marker">${benchmarkLabel}: ${avg}</span>
                    <span class="benchmark-marker">Your Score: ${num.toFixed(1)} (${comparison} ${Math.abs(diff).toFixed(0)})</span>
                `;
            }
        };
        
        const updateValueBubble = (value) => {
            if (!valueBubble) return;
            const numericValue = parseFloat(value) || 0;
            const percent = ((numericValue - minValue) / (maxValue - minValue)) * 100;
            const bubbleFormatter = slider.bubbleFormat || ((val) => {
                const step = parseFloat(input.step) || 1;
                return step < 1 ? parseFloat(val).toFixed(1) : parseFloat(val).toFixed(0);
            });
            valueBubble.textContent = bubbleFormatter(value);

            const sliderRect = input.getBoundingClientRect();
            const groupRect = formGroup?.getBoundingClientRect();
            if (!groupRect.width || !sliderRect.width) return;

            const sliderOffsetLeft = sliderRect.left - groupRect.left;
            const sliderOffsetTop = sliderRect.top - groupRect.top;
            const clampedPercent = Math.min(Math.max(percent, 0), 100) / 100;
            const bubbleLeft = sliderOffsetLeft + clampedPercent * sliderRect.width;

            valueBubble.style.left = `${bubbleLeft}px`;
            valueBubble.style.top = `${sliderOffsetTop - 36}px`;
        };

        const updateNumberInput = (value) => {
            if (!numberInput) return;
            numberInput.value = Math.round(parseFloat(value) || 0);
        };

        // Update display on input change
        const updateDisplay = (e) => {
            const value = e ? e.target.value : input.value;
            display.textContent = slider.format(value);
            updateBadge(value);
            updateBenchmark(value);
            updateValueBubble(value);
            updateNumberInput(value);
        };
        
        // Initialize badge and benchmark
        updateBadge(currentValue);
        updateBenchmark(currentValue);
        updateValueBubble(currentValue);
        updateNumberInput(currentValue);
        
        // Listen for input event
        input.addEventListener('input', updateDisplay);
        input.addEventListener('change', updateDisplay);
        
        // Listen for mousemove on slider
        input.addEventListener('mousemove', (e) => {
            if (e.buttons === 1) {
                updateDisplay(e);
            }
        });

        if (numberInput) {
            numberInput.addEventListener('input', (e) => {
                let newValue = parseFloat(e.target.value);
                if (isNaN(newValue)) newValue = minValue;
                newValue = Math.min(maxValue, Math.max(minValue, newValue));
                input.value = newValue;
                input.dispatchEvent(new Event('input', { bubbles: true }));
            });
        }
        
        initializedCount++;
    });
    
    
    // Retry if we have at least one slider initialized but not all
    if (initializedCount > 0 && initializedCount < sliders.length) {
        setTimeout(() => {
            initSliderDisplays();
        }, 500);
    }
}

