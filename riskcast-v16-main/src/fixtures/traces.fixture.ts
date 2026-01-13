import type { LayerTrace, LayerTraceStep, TraceMeta } from '../types';

let stepSeq = 1;

export function createMockTraceStep(overrides: Partial<LayerTraceStep> = {}): LayerTraceStep {
  const id = overrides.stepId ?? `step-${stepSeq++}`;
  return {
    stepId: id,
    method: overrides.method ?? 'aggregation',
    inputs: overrides.inputs,
    output: overrides.output,
    summary: overrides.summary ?? 'Aggregate layer signals.',
    evidence: overrides.evidence,
  };
}

export function createMockLayerTrace(layerName: string, overrides: Partial<LayerTrace> = {}): LayerTrace {
  return {
    layerName,
    steps: overrides.steps ?? [
      createMockTraceStep({ method: 'aggregation', summary: `Aggregate signals for ${layerName}` }),
    ],
    sensitivity: overrides.sensitivity,
    trace: overrides.trace,
  };
}

export function createMockTraces(params: {
  layerNames: string[];
  includeTraces?: boolean;
  traceMeta?: TraceMeta;
}): Record<string, LayerTrace> | undefined {
  const include = params.includeTraces ?? true;
  if (!include) return undefined;

  const map: Record<string, LayerTrace> = {};
  for (const name of params.layerNames) {
    map[name] = createMockLayerTrace(name, {
      trace: params.traceMeta,
    });
  }
  return map;
}

