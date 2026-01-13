
import { $id, qs, toggleClass } from '../../core/dom.js';
import { toggleClimate } from './utils_input.js';
import { on } from '../../core/events.js';

export function initClimateToggle() {
    const climateHeader = $id('climate-header-toggle');
    
    if (climateHeader) {
        on(climateHeader, 'click', toggleClimate);
    }
}




















