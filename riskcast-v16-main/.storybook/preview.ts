import type { Preview } from '@storybook/react';
import '../src/style.css';
import '../src/styles/perf-a11y.css';

const preview: Preview = {
  parameters: {
    actions: { argTypesRegex: '^on[A-Z].*' },
    controls: { expanded: true },
    a11y: { disable: false },
  },
};

export default preview;

