/**
 * Enterprise Components Index
 * 
 * Advanced enterprise features:
 * - Audit trail / Activity feed
 * - Collaboration (comments, mentions)
 * - Alerts and notifications
 * - Dashboard builder (types only)
 */

export * from './ActivityFeed';
export * from './CommentThread';
export * from './AlertCreator';

// =============================================================================
// DASHBOARD BUILDER TYPES (Structure for future implementation)
// =============================================================================

/**
 * Dashboard widget types
 */
export type WidgetType = 
  | 'risk_score'
  | 'risk_trend'
  | 'loss_distribution'
  | 'top_drivers'
  | 'comparison'
  | 'timeline'
  | 'recommendations'
  | 'custom_chart'
  | 'kpi_card'
  | 'table';

/**
 * Widget size configuration
 */
export interface WidgetSize {
  width: 1 | 2 | 3 | 4;
  height: 1 | 2 | 3;
}

/**
 * Dashboard widget configuration
 */
export interface DashboardWidget {
  id: string;
  type: WidgetType;
  title: string;
  size: WidgetSize;
  position: { x: number; y: number };
  config?: Record<string, unknown>;
  dataSource?: string;
}

/**
 * Dashboard layout
 */
export interface DashboardLayout {
  id: string;
  name: string;
  description?: string;
  widgets: DashboardWidget[];
  gridColumns: number;
  isDefault?: boolean;
  createdAt: string;
  updatedAt: string;
}

/**
 * Role-based view configuration
 */
export interface RoleBasedView {
  role: 'executive' | 'analyst' | 'operations' | 'custom';
  defaultLayout: string;
  allowedWidgets: WidgetType[];
  permissions: {
    canEdit: boolean;
    canShare: boolean;
    canExport: boolean;
  };
}

/**
 * Dashboard builder configuration (for future implementation)
 */
export interface DashboardBuilderConfig {
  availableWidgets: WidgetType[];
  defaultLayouts: DashboardLayout[];
  roleBasedViews: RoleBasedView[];
  maxWidgets: number;
  enableDragDrop: boolean;
  enableResize: boolean;
}

/**
 * Save view action type (stub for ResultsPage integration)
 */
export interface SaveViewAction {
  type: 'save_view' | 'pin_to_dashboard';
  viewName?: string;
  dashboardId?: string;
}

/**
 * Placeholder function for save view (to be implemented with backend)
 */
export async function saveCurrentView(_action: SaveViewAction): Promise<{ success: boolean; viewId?: string }> {
  // Stub implementation - returns success but doesn't persist
  console.log('[DashboardBuilder] Save view requested:', _action);
  return { success: true, viewId: `view-${Date.now()}` };
}
