# RiskCast V22 - AI Risk Intelligence UI Layer

## 🎨 Enterprise-Grade Vue 3 Visualization Dashboard

RiskCast V22 features a modern, glassmorphism-based UI with dark mode optimization, built with Vue 3 Composition API, Pinia state management, and D3.js visualizations.

## ✨ Features Implemented

### ✅ Phase 1-3 Complete (Foundation + Summary Dashboard)

- **Foundation Architecture**: Complete state management, utilities, and composables
- **Shared Components**: 7 reusable UI primitives with glassmorphism design
- **Summary Dashboard**: 8 risk intelligence cards with interactive visualizations
- **Responsive Design**: Mobile-first with tablet and desktop breakpoints
- **Persona System**: Role-based views (Logistics, Executive, Analyst, Compliance)
- **Animation System**: Spring physics with stagger effects

## 🚀 Quick Start

### Prerequisites

```bash
# Node.js 18+ required
node --version
```

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Access the Dashboard

Open http://localhost:3000 in your browser. The dashboard will load with mock data automatically.

## 📁 Project Structure

```
src/
├── features/risk-intelligence/
│   ├── components/
│   │   ├── dashboard/          # Main dashboard container
│   │   ├── summary/            # Summary cards (8 cards)
│   │   ├── shared/             # Reusable UI components (7 components)
│   │   ├── driver-tree/        # D3 tree visualization (TODO)
│   │   ├── timeline/           # Event timeline (TODO)
│   │   ├── what-if/            # Simulator (TODO)
│   │   ├── explanation/        # AI panel (TODO)
│   │   └── persona/            # Persona switcher (TODO)
│   ├── stores/                 # Pinia stores (5 stores)
│   ├── composables/            # Vue composables (6 composables)
│   ├── utils/                  # Utilities & formatters
│   ├── constants/              # Configuration & themes
│   └── types/                  # Type definitions
```

## 🎨 Design System

### Glassmorphism Theme

- **Background**: Frosted glass with blur effects
- **Colors**: Neon accents (cyan, blue, purple)
- **Dark Mode**: Optimized for low-light environments
- **Animations**: Spring physics with smooth transitions

### Color Palette

```javascript
Risk Levels:
- Low: #10B981 (Green)
- Medium: #F59E0B (Yellow)
- High: #F97316 (Orange)
- Critical: #EF4444 (Red)

Neon Accents:
- Blue: #4FC3F7
- Cyan: #00BCD4
- Purple: #9C27B0
```

## 🧩 Components Reference

### Shared Components

1. **GlassCard** - Glassmorphism container with glow effects
2. **RiskBadge** - Color-coded score pills
3. **MetricDisplay** - Label + value + trend indicator
4. **ProgressRing** - Circular SVG progress
5. **SparklineChart** - Inline mini charts
6. **NeonDivider** - Glowing separators
7. **LoadingShimmer** - Skeleton loading states

### Summary Cards

1. **OverallRiskCard** - Hero card with progress ring + sparkline
2. **LayerScoresCard** - 16 risk layers in mini grid
3. **CategoryBreakdownCard** - Category aggregation
4. **ESGScoreCard** - Environmental/Social/Governance triplet
5. **MonteCarloCard** - P50/P95 distribution chart
6. **DelayPredictionCard** - Expected delay visualization
7. **ShockScenariosCard** - Scenario comparison table

## 🔧 Development Guide

### Adding New Components

```vue
<template>
  <GlassCard padding="p-6">
    <h3 class="text-lg font-semibold text-white mb-4">Component Title</h3>
    <!-- Your content -->
  </GlassCard>
</template>

<script setup>
import { computed } from 'vue'
import { useRiskStore } from '../../stores/riskStore'
import GlassCard from '../shared/GlassCard.vue'

const riskStore = useRiskStore()
const data = computed(() => riskStore.someData)
</script>
```

### Using Stores

```javascript
import { useRiskStore } from '@/features/risk-intelligence/stores/riskStore'

const riskStore = useRiskStore()

// Access data
const score = riskStore.baseline.overallScore
const layers = riskStore.layers

// Call actions
riskStore.setData(newData)
```

### Using Composables

```javascript
import { useRiskData } from '@/features/risk-intelligence/composables/useRiskData'

const { fetchRiskData, isRefreshing } = useRiskData()

// Fetch data
await fetchRiskData('SHIP-001')
```

## 🎯 Remaining Work (Phases 4-13)

### Phase 4: Risk Driver Tree (D3.js)
- Interactive hierarchical tree visualization
- Expandable/collapsible nodes
- Color-coded by risk level
- Hover tooltips with details

### Phase 5: Timeline
- Sequential event visualization
- Phase segments with risk bands
- Zoom and pan functionality
- Event markers

### Phase 6: What-If Simulator
- Parameter adjustment sliders
- Real-time recalculation (client-side)
- Before/after comparison
- Impact visualization

### Phase 7: AI Explanation Panel
- Narrative text sections
- Insight cards
- Recommendations list
- Scroll-to-section linking

### Phase 8: Persona Switcher
- Role selector dropdown
- Dynamic view filtering
- Card reordering
- Metric visibility control

### Phase 9: Main Dashboard Layout
- Tab navigation
- Header with actions
- Responsive grid system
- Section integration

### Phases 10-13: Polish & Testing
- Animation refinements
- Edge case handling
- Performance optimization
- Production build testing

## 📊 State Management

### Risk Store
```javascript
{
  baseline: { overallScore, riskLevel, timestamp },
  layers: [...], // 16 risk layers
  categories: [...], // 5 categories
  esg: { environmental, social, governance },
  monteCarlo: { p50, p95, distribution },
  delayPrediction: { expected, min, max },
  shockScenarios: [...],
  driverTree: {...}, // Hierarchical structure
  timeline: { phases, events }
}
```

### Persona Store
```javascript
{
  activePersona: 'logistics' | 'executive' | 'analyst' | 'compliance',
  currentConfig: { 
    priorityMetrics, 
    hiddenSections, 
    treeDepth,
    cardOrder 
  }
}
```

## 🔌 API Integration

The UI expects data from:

```
GET /api/v22/shipments/{id}/risk-intelligence
```

Mock data is provided for development. Replace `loadMockData()` calls with actual API calls in production.

## 🎨 Customization

### Themes

Edit `src/features/risk-intelligence/constants/colorPalette.js` to customize colors.

### Personas

Edit `src/features/risk-intelligence/constants/personaConfigs.js` to add or modify personas.

### Breakpoints

Edit `src/features/risk-intelligence/constants/layoutBreakpoints.js` for responsive behavior.

## 📝 Best Practices

1. **Use Composition API**: Prefer `<script setup>` for all components
2. **Type Hints**: Use JSDoc comments for better IntelliSense
3. **Reactive Data**: Access store data through computed properties
4. **Animations**: Respect `prefers-reduced-motion`
5. **Mobile First**: Design for mobile, enhance for desktop
6. **Error Handling**: Always handle loading and error states

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Change port in vite.config.js
server: { port: 3001 }
```

### Dependencies Error

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Linting Issues

```bash
# Auto-fix linting errors
npm run lint
```

## 📚 Tech Stack

- **Vue 3.4+**: Composition API, `<script setup>`
- **Pinia 2.1+**: State management
- **Vite 5.0+**: Build tool
- **Tailwind CSS 3.4+**: Utility-first CSS
- **D3.js 7.9+**: Data visualization
- **Axios 1.6+**: HTTP client
- **@vueuse/core**: Vue utilities

## 🤝 Contributing

When adding features:
1. Follow the established folder structure
2. Use existing shared components
3. Add JSDoc type hints
4. Test on mobile, tablet, and desktop
5. Respect the design system

## 📄 License

Enterprise License - Internal Use Only

## 🔗 Related Documentation

- [V22 Architecture Spec](./V22_ARCHITECTURE.md)
- [Implementation Progress](./IMPLEMENTATION_PROGRESS.md)
- [API Documentation](./API_DOCS.md)

---

**Built with ❤️ for Enterprise Risk Intelligence**

*Version: V22.3.0*  
*Last Updated: December 4, 2025*






