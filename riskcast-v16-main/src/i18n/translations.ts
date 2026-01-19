/**
 * Frontend Translations (RC-A012)
 * 
 * CRITICAL: Complete Vietnamese translations for 100% i18n coverage.
 * All user-facing text must be in Vietnamese (or support multi-language).
 */

export const translations = {
  vi: {
    // Common
    common: {
      loading: 'Đang tải...',
      error: 'Đã xảy ra lỗi',
      retry: 'Thử lại',
      cancel: 'Hủy',
      save: 'Lưu',
      delete: 'Xóa',
      edit: 'Sửa',
      view: 'Xem',
      export: 'Xuất',
      close: 'Đóng',
      back: 'Quay lại',
      next: 'Tiếp theo',
      previous: 'Trước',
      search: 'Tìm kiếm',
      filter: 'Lọc',
      sort: 'Sắp xếp',
      refresh: 'Làm mới',
    },
    
    // Risk Levels
    risk: {
      level: {
        low: 'Thấp',
        medium: 'Trung Bình',
        high: 'Cao',
        critical: 'Cực Kỳ Cao',
        unknown: 'Không Xác Định',
      },
      score: 'Điểm Rủi Ro',
      confidence: 'Độ Tin Cậy',
      assessment: 'Đánh Giá Rủi Ro',
      analysis: 'Phân Tích Rủi Ro',
    },
    
    // Executive Summary
    executive: {
      title: 'Tóm Tắt Điều Hành',
      summary: 'Tóm Tắt',
      topRisks: 'Top 3 Rủi Ro',
      viewDetails: 'Xem Chi Tiết',
      exportReport: 'Xuất Báo Cáo',
      impact: 'Tác Động',
      contribution: 'Đóng Góp',
      percent: '%',
      confidence: 'Độ Tin Cậy Dữ Liệu',
      explanation: 'Giải Thích',
    },
    
    // Pages
    pages: {
      results: {
        title: 'Kết Quả Phân Tích',
        subtitle: 'Chi tiết đánh giá rủi ro',
        noData: 'Chưa có dữ liệu phân tích',
        noDataDescription: 'Vui lòng chạy phân tích rủi ro từ trang Input để xem kết quả tại đây.',
        goToInput: 'Đi đến Input',
        refresh: 'Tải lại',
      },
      summary: {
        title: 'Tóm Tắt Lô Hàng',
        subtitle: 'Thông tin và phân tích lô hàng',
        runAnalysis: 'Chạy Phân Tích',
        analyzing: 'Đang phân tích...',
      },
    },
    
    // States
    states: {
      loading: 'Đang tải dữ liệu...',
      loadingDescription: 'Vui lòng chờ trong giây lát.',
      error: 'Đã xảy ra lỗi',
      errorDescription: 'Không thể tải dữ liệu. Vui lòng thử lại.',
      empty: 'Chưa có dữ liệu',
      emptyDescription: 'Không có dữ liệu để hiển thị.',
    },
    
    // Charts
    charts: {
      riskDistribution: 'Phân Bố Rủi Ro',
      riskLayers: 'Các Lớp Rủi Ro',
      contribution: 'Đóng Góp',
      score: 'Điểm Số',
      timeSeries: 'Chuỗi Thời Gian',
      noData: 'Không có dữ liệu để hiển thị',
    },
    
    // AI Advisor
    ai: {
      advisor: 'Cố Vấn AI',
      askQuestion: 'Đặt câu hỏi...',
      send: 'Gửi',
      thinking: 'Đang suy nghĩ...',
      error: 'Không thể xử lý câu hỏi. Vui lòng thử lại.',
      placeholder: 'Ví dụ: "Rủi ro nào cao nhất?" hoặc "Làm thế nào để giảm rủi ro?"',
    },
    
    // Validation
    validation: {
      required: 'Trường này là bắt buộc',
      invalid: 'Giá trị không hợp lệ',
      tooShort: 'Quá ngắn',
      tooLong: 'Quá dài',
      outOfRange: 'Ngoài phạm vi cho phép',
      invalidFormat: 'Định dạng không hợp lệ',
    },
    
    // Errors
    errors: {
      network: 'Lỗi kết nối mạng',
      networkDescription: 'Không thể kết nối đến server. Vui lòng kiểm tra kết nối và thử lại.',
      server: 'Lỗi server',
      serverDescription: 'Server gặp sự cố. Vui lòng thử lại sau.',
      notFound: 'Không tìm thấy',
      notFoundDescription: 'Trang hoặc tài nguyên không tồn tại.',
      unauthorized: 'Không có quyền truy cập',
      unauthorizedDescription: 'Bạn không có quyền truy cập tài nguyên này.',
      timeout: 'Hết thời gian chờ',
      timeoutDescription: 'Yêu cầu mất quá nhiều thời gian. Vui lòng thử lại.',
    },
  },
  
  en: {
    // English translations (fallback)
    common: {
      loading: 'Loading...',
      error: 'An error occurred',
      retry: 'Retry',
      cancel: 'Cancel',
      save: 'Save',
      delete: 'Delete',
      edit: 'Edit',
      view: 'View',
      export: 'Export',
      close: 'Close',
      back: 'Back',
      next: 'Next',
      previous: 'Previous',
      search: 'Search',
      filter: 'Filter',
      sort: 'Sort',
      refresh: 'Refresh',
    },
    risk: {
      level: {
        low: 'Low',
        medium: 'Medium',
        high: 'High',
        critical: 'Critical',
        unknown: 'Unknown',
      },
      score: 'Risk Score',
      confidence: 'Confidence',
      assessment: 'Risk Assessment',
      analysis: 'Risk Analysis',
    },
    executive: {
      title: 'Executive Summary',
      summary: 'Summary',
      topRisks: 'Top 3 Risks',
      viewDetails: 'View Details',
      exportReport: 'Export Report',
      impact: 'Impact',
      contribution: 'Contribution',
      percent: '%',
      confidence: 'Data Confidence',
      explanation: 'Explanation',
    },
    pages: {
      results: {
        title: 'Analysis Results',
        subtitle: 'Detailed risk assessment',
        noData: 'No analysis data',
        noDataDescription: 'Please run risk analysis from the Input page to see results here.',
        goToInput: 'Go to Input',
        refresh: 'Refresh',
      },
      summary: {
        title: 'Shipment Summary',
        subtitle: 'Shipment information and analysis',
        runAnalysis: 'Run Analysis',
        analyzing: 'Analyzing...',
      },
    },
    states: {
      loading: 'Loading data...',
      loadingDescription: 'Please wait a moment.',
      error: 'An error occurred',
      errorDescription: 'Unable to load data. Please try again.',
      empty: 'No data',
      emptyDescription: 'No data to display.',
    },
    charts: {
      riskDistribution: 'Risk Distribution',
      riskLayers: 'Risk Layers',
      contribution: 'Contribution',
      score: 'Score',
      timeSeries: 'Time Series',
      noData: 'No data to display',
    },
    ai: {
      advisor: 'AI Advisor',
      askQuestion: 'Ask a question...',
      send: 'Send',
      thinking: 'Thinking...',
      error: 'Unable to process question. Please try again.',
      placeholder: 'Example: "What is the highest risk?" or "How to reduce risk?"',
    },
    validation: {
      required: 'This field is required',
      invalid: 'Invalid value',
      tooShort: 'Too short',
      tooLong: 'Too long',
      outOfRange: 'Out of allowed range',
      invalidFormat: 'Invalid format',
    },
    errors: {
      network: 'Network error',
      networkDescription: 'Unable to connect to server. Please check your connection and try again.',
      server: 'Server error',
      serverDescription: 'Server encountered an issue. Please try again later.',
      notFound: 'Not found',
      notFoundDescription: 'Page or resource does not exist.',
      unauthorized: 'Unauthorized',
      unauthorizedDescription: 'You do not have permission to access this resource.',
      timeout: 'Request timeout',
      timeoutDescription: 'Request took too long. Please try again.',
    },
  },
  
  zh: {
    // Chinese translations (simplified)
    common: {
      loading: '加载中...',
      error: '发生错误',
      retry: '重试',
      cancel: '取消',
      save: '保存',
      delete: '删除',
      edit: '编辑',
      view: '查看',
      export: '导出',
      close: '关闭',
      back: '返回',
      next: '下一步',
      previous: '上一步',
      search: '搜索',
      filter: '筛选',
      sort: '排序',
      refresh: '刷新',
    },
    risk: {
      level: {
        low: '低',
        medium: '中',
        high: '高',
        critical: '严重',
        unknown: '未知',
      },
      score: '风险评分',
      confidence: '置信度',
      assessment: '风险评估',
      analysis: '风险分析',
    },
    executive: {
      title: '执行摘要',
      summary: '摘要',
      topRisks: '前3大风险',
      viewDetails: '查看详情',
      exportReport: '导出报告',
      impact: '影响',
      contribution: '贡献',
      percent: '%',
      confidence: '数据置信度',
      explanation: '说明',
    },
    pages: {
      results: {
        title: '分析结果',
        subtitle: '详细风险评估',
        noData: '无分析数据',
        noDataDescription: '请从输入页面运行风险分析以查看结果。',
        goToInput: '前往输入',
        refresh: '刷新',
      },
      summary: {
        title: '货物摘要',
        subtitle: '货物信息和分析',
        runAnalysis: '运行分析',
        analyzing: '分析中...',
      },
    },
    states: {
      loading: '加载数据...',
      loadingDescription: '请稍候。',
      error: '发生错误',
      errorDescription: '无法加载数据。请重试。',
      empty: '无数据',
      emptyDescription: '没有要显示的数据。',
    },
    charts: {
      riskDistribution: '风险分布',
      riskLayers: '风险层',
      contribution: '贡献',
      score: '分数',
      timeSeries: '时间序列',
      noData: '无数据显示',
    },
    ai: {
      advisor: 'AI顾问',
      askQuestion: '提问...',
      send: '发送',
      thinking: '思考中...',
      error: '无法处理问题。请重试。',
      placeholder: '例如："最高风险是什么？"或"如何降低风险？"',
    },
    validation: {
      required: '此字段为必填项',
      invalid: '无效值',
      tooShort: '太短',
      tooLong: '太长',
      outOfRange: '超出允许范围',
      invalidFormat: '格式无效',
    },
    errors: {
      network: '网络错误',
      networkDescription: '无法连接到服务器。请检查连接并重试。',
      server: '服务器错误',
      serverDescription: '服务器遇到问题。请稍后再试。',
      notFound: '未找到',
      notFoundDescription: '页面或资源不存在。',
      unauthorized: '未授权',
      unauthorizedDescription: '您无权访问此资源。',
      timeout: '请求超时',
      timeoutDescription: '请求耗时过长。请重试。',
    },
  },
};

/**
 * Get translation by key path (supports dot notation)
 * Example: getTranslation('risk.level.high', 'vi') -> 'Cao'
 */
export function getTranslation(
  key: string,
  language: 'vi' | 'en' | 'zh' = 'vi'
): string {
  const keys = key.split('.');
  let value: any = translations[language];
  
  for (const k of keys) {
    if (value && typeof value === 'object' && k in value) {
      value = value[k];
    } else {
      // Fallback to English if not found
      if (language !== 'en') {
        return getTranslation(key, 'en');
      }
      // Return key if not found in English either
      return key;
    }
  }
  
  return typeof value === 'string' ? value : key;
}

/**
 * Hook for using translations in React components
 */
export function useTranslation(language: 'vi' | 'en' | 'zh' = 'vi') {
  const t = (key: string): string => getTranslation(key, language);
  return { t, language };
}
