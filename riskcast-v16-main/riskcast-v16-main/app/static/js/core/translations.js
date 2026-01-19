
(function() {
    'use strict';

    // Initialize RISKCAST namespace if it doesn't exist
    if (typeof window.RISKCAST === 'undefined') {
        window.RISKCAST = {};
    }
    if (typeof window.RISKCAST.core === 'undefined') {
        window.RISKCAST.core = {};
    }

    // ============================================
    // TRANSLATION DICTIONARIES
    // ============================================

    const TRANSLATIONS_VI = {
        // Header & Navigation
        brand_title: "RISKCAST v12.5",
        brand_subtitle: "Nền Tảng Thông Minh Phân Tích Rủi Ro Logistics Được Hỗ Trợ Bởi AI",
        status_ready: "Phân Tích Hoàn Tất",
        status_loading: "Đang tải dữ liệu...",
        
        // View Mode Tabs
        tab_enterprise: "Chế Độ Doanh Nghiệp",
        tab_research: "Chế Độ Phân Tích NCKH",
        tab_investor: "Chế Độ Trình Bày Nhà Đầu Tư",
        
        // Executive Snapshot
        section_executive: "Tổng Quan Điều Hành",
        label_overall_risk: "Chỉ số rủi ro tổng hợp",
        label_expected_loss: "Tổn thất kỳ vọng",
        label_reliability: "Độ tin cậy giao hàng",
        label_esg: "Điểm ESG (Môi trường – Xã hội – Quản trị)",
        subtitle_per_shipment: "Mỗi lô hàng",
        subtitle_on_time_prob: "Xác suất đúng hạn",
        subtitle_climate_political: "Khí hậu + Chính trị",
        label_top_route: "Rủi ro tuyến vận tải lớn nhất:",
        label_main_driver: "Nguyên nhân chính:",
        label_recommendation: "Khuyến nghị của hệ thống:",
        
        // Risk Gauges Section
        section_risk_gauges: "Tổng Quan Đồng Hồ Rủi Ro",
        gauge_risk_title: "Chỉ Số Rủi Ro Tổng Thể",
        gauge_reliability_title: "Điểm Độ Tin Cậy",
        gauge_esg_title: "Điểm ESG",
        
        // Gauge Explanations (NCKH/Academic style)
        gauge_explanations: {
            title: "Giải Thích Chuyên Sâu",
            risk_title: "Chỉ Số Rủi Ro Tổng Thể",
            risk: {
                low: "Mức rủi ro thấp (0–40). Chuỗi vận tải duy trì độ ổn định cao, xác suất biến cố thấp. Có thể tối ưu thêm chi phí hoặc thời gian.",
                medium: "Rủi ro trung bình (40–70). Một số yếu tố vận hành – thời tiết – cảng có xu hướng biến động. Doanh nghiệp nên theo dõi sát để giảm thiểu tổn thất.",
                high: "Rủi ro cao (70–100). Xác suất sự cố hoặc chậm trễ tăng rõ rệt. Cần đánh giá lại tuyến đường, phương thức vận tải và điều kiện cargo."
            },
            reliability_title: "Điểm Độ Tin Cậy",
            reliability: {
                very_high: "Độ tin cậy rất cao (>85). Biến động thấp, mô hình dự báo ổn định. Phù hợp các lô hàng giá trị lớn.",
                stable: "Ổn định (60–85). Hệ thống có dao động nhẹ nhưng trong giới hạn cho phép.",
                unstable: "Không ổn định (<60). Hoạt động dễ chịu tác động bởi thời tiết hoặc tắc nghẽn. Không khuyến nghị với hàng nhạy cảm thời gian."
            },
            esg_title: "Điểm ESG",
            esg: {
                strong: "Tuân thủ ESG mạnh (>70). Tuyến vận tải thân thiện môi trường, phù hợp các doanh nghiệp ưu tiên bền vững.",
                moderate: "Mức trung bình (40–70). Chưa tối ưu ESG nhưng vẫn chấp nhận được.",
                weak: "Mức thấp (<40). Rủi ro tuân thủ ESG cao. Nên xem xét tuyến vận tải khác."
            }
        },
        
        // Risk Levels
        risk_level_low: "Thấp",
        risk_level_medium: "Trung Bình",
        risk_level_high: "Cao",
        
        // Charts & Sections
        section_radar: "Biểu Đồ Radar Hồ Sơ Rủi Ro",
        section_layers: "Phân Tích Phân Lớp Rủi Ro",
        section_montecarlo: "Phân Phối Monte Carlo",
        section_timeline: "Dòng Thời Gian Rủi Ro",
        section_matrix: "Ma Trận Rủi Ro Xác Suất × Tác Động",
        section_scenario: "Kiểm Tra Áp Lực Kịch Bản (What-if)",
        section_tradeoff: "Đánh Đổi Chi Phí-Thời Gian-Rủi Ro",
        section_route: "Phân Tích Theo Cấp Độ Tuyến Đường",
        section_recommendations: "Khuyến Nghị Từ Chuyên Gia AI",
        
        // Research View
        section_research_methodology: "Tổng Quan Phương Pháp Nghiên Cứu",
        panel_dataset: "Bảng 1: Giải Thích Dữ Liệu",
        panel_criteria: "Bảng 2: Xây Dựng Tiêu Chí",
        panel_fuzzy_ahp: "Bảng 3: Phương Pháp Fuzzy AHP",
        panel_fuzzy_topsis: "Bảng 4: Phân Tích Fuzzy-TOPSIS",
        panel_montecarlo: "Bảng 5: Mô Phỏng Monte Carlo",
        panel_integrated: "Bảng 6: Mô Hình Rủi Ro Tích Hợp",
        panel_policy: "Bảng 7: Ý Nghĩa Chính Sách Cho SME Việt Nam",
        panel_sensitivity: "Bảng 8: Kiểm Tra Độ Nhạy & Độ Vững Chắc",
        
        // Investor View
        section_problem_solution: "Vấn Đề → Giải Pháp → Tại Sao Bây Giờ",
        problem_title: "Vấn Đề",
        solution_title: "Giải Pháp",
        why_now_title: "Tại Sao Bây Giờ",
        section_economics: "Tóm Tắt Tác Động Kinh Tế",
        section_arr: "ARR / Tiềm Năng Doanh Thu",
        section_architecture: "Kiến Trúc Engine-as-a-Service",
        section_pitch: "Câu Chuyện Một Trang Cho Nhà Đầu Tư",
        investor_ask: "Yêu Cầu:",
        
        // Scenario Names
        scenario_base: "Trường Hợp Cơ Bản",
        scenario_best: "Kịch Bản Tốt Nhất",
        scenario_worst: "Kịch Bản Xấu Nhất",
        
        // Risk Layer Names
        layer_delay: "Rủi Ro Trễ",
        layer_damage: "Rủi Ro Hư Hại",
        layer_cost: "Biến Động Chi Phí",
        layer_operational: "Rủi Ro Vận Hành",
        layer_esg: "Rủi Ro ESG",
        layer_political: "Rủi Ro Chính Trị",
        layer_climate: "Rủi Ro Khí Hậu",
        
        // Common Terms
        based_on_simulations: "Dựa trên",
        simulations: "mô phỏng",
        days: "ngày",
        usd: "USD",
        percent: "%",
        loading: "Đang tải...",
        no_data: "Không có dữ liệu",
        calculating: "Đang tính toán...",
        
        // Buttons & Actions
        btn_analyze: "Chạy Phân Tích",
        btn_reset: "Đặt Lại",
        btn_export: "Xuất Báo Cáo",
        
        // Errors
        error_no_data: "Không có dữ liệu. Vui lòng chạy phân tích trước.",
        error_fetch: "Không thể tải dữ liệu từ máy chủ.",
        
        // Input Page Labels
        input_transport_mode: "Phương Thức Vận Tải",
        input_cargo_type: "Loại Hàng Hóa",
        input_route: "Tuyến Đường",
        input_incoterm: "Điều Kiện Incoterm",
        input_container: "Loại Container",
        input_quality: "Chất Lượng Bao Bì",
        input_priority: "Chế Độ Ưu Tiên",
        input_analysis_button: "Phân Tích Rủi Ro",
        input_transport_placeholder: "Chọn phương thức vận tải",
        placeholder_select: "Chọn...",
        placeholder_packages: "Nhập số lượng",
        placeholder_auto: "Tự động tính toán",
        
        // Transport Mode Options (11 International Modes)
        transport_sea: "Đường biển",
        transport_air: "Đường hàng không",
        transport_road: "Đường bộ",
        transport_rail: "Đường sắt",
        transport_multimodal: "Đa phương thức",
        transport_intermodal: "Liên hợp vận tải",
        transport_express: "Chuyển phát nhanh",
        transport_postal: "Bưu kiện quốc tế",
        transport_pipeline: "Đường ống",
        transport_inland: "Đường thủy nội địa",
        transport_roro: "Vận tải Ro-Ro",
        transport_mode: "Phương thức vận tải",
        cargo_type: "Loại hàng hóa",
        route: "Tuyến đường",
        incoterm: "Điều kiện Incoterm",
        container: "Loại container",
        packaging: "Chất lượng bao bì",
        priority: "Chế độ ưu tiên",
        
        // Input Page Sections
        section1_title: "Cấu Hình Hàng Hóa",
        section1_subtitle: "Dữ liệu nền để AI tối ưu lộ trình, thời gian và rủi ro theo từng khu vực vận chuyển.",
        section2_title: "Thông Tin Vận Chuyển",
        section2_subtitle: "Chi tiết tuyến đường và điều kiện giao hàng",
        section3_title: "Thông Số Bổ Sung",
        section3_subtitle: "Các yếu tố ảnh hưởng đến rủi ro",
        
        // Input Page Status
        status_ready: "Hệ Thống Sẵn Sàng",
        loading_text: "Đang khởi tạo Risk Engine...",
        
        // Input Page Labels (detailed)
        label_transport_mode: "Phương Thức Vận Tải",
        label_cargo_type: "Loại Hàng Hóa",
        label_route: "Tuyến Đường",
        label_incoterm: "Điều Kiện Incoterm",
        label_container: "Loại Container",
        label_packaging: "Chất Lượng Bao Bì",
        label_priority: "Chế Độ Ưu Tiên",
        label_packages: "Số Lượng Kiện Hàng",
        label_etd: "Ngày Gửi Hàng Dự Kiến (ETD)",
        label_eta: "Ngày Đến Dự Kiến (ETA)",
        label_cargo_value: "Giá Trị Hàng Hóa (USD)",
        
        // Input Page Options (Transport Mode)
        opt_tm_ocean_fcl: "Vận Tải Biển — FCL",
        opt_tm_ocean_lcl: "Vận Tải Biển — LCL",
        opt_tm_air: "Vận Tải Hàng Không",
        opt_tm_rail: "Vận Tải Đường Sắt",
        opt_tm_road: "Đường Bộ — Xe Tải",
        opt_tm_multimodal: "Vận Tải Đa Phương Thức",
        opt_tm_courier: "Chuyển Phát Nhanh / Express",
        opt_tm_inland: "Đường Thủy Nội Địa",
        opt_tm_pipeline: "Đường Ống",
        opt_tm_cross: "Đường Bộ Xuyên Biên Giới",
        opt_tm_lastmile: "Giao Hàng Cuối Dặm",
        
        // Input Page Error Messages
        error_required: "Trường này là bắt buộc",
        error_positive: "Giá trị phải là số dương",
        error_date_invalid: "Ngày không hợp lệ",
        confirm_reset: "Bạn có chắc chắn muốn đặt lại tất cả các trường?",
        alert_success: "Phân tích rủi ro hoàn tất thành công!",
        
        // Buyer/Seller Fields
        buyer_section: "Thông tin Người Mua (Buyer)",
        buyer_name: "Tên người mua",
        buyer_country: "Quốc gia người mua",
        buyer_size: "Quy mô doanh nghiệp",
        buyer_esg: "Điểm ESG (nếu có)",
        buyer_reliability: "Điểm uy tín (Reliability)",
        seller_section: "Thông tin Người Bán (Seller)",
        seller_name: "Tên người bán",
        seller_country: "Quốc gia người bán",
        seller_size: "Quy mô doanh nghiệp",
        seller_esg: "Điểm ESG (nếu có)",
        seller_reliability: "Điểm uy tín (Reliability)",
        
        // Country Options
        country_vn: "Việt Nam",
        country_cn: "Trung Quốc",
        country_jp: "Nhật Bản",
        country_kr: "Hàn Quốc",
        country_us: "Hoa Kỳ",
        country_eu: "Liên Minh Châu Âu",
        
        // Company Size Options
        company_sme: "SME (10–200 lao động)",
        company_medium: "Trung bình (200–500)",
        company_large: "Lớn (>500)",
        
        // Cargo Type Options
        opt_ct_general: "Hàng Hóa Thông Thường",
        opt_ct_electronics: "Điện Tử",
        opt_ct_food_bev: "Thực Phẩm & Đồ Uống",
        opt_ct_garments: "May Mặc / Dệt May",
        opt_ct_agriculture: "Nông Sản",
        opt_ct_refrigerated: "Hàng Lạnh / Đông Lạnh",
        opt_ct_chemicals: "Hóa Chất",
        opt_ct_machinery: "Máy Móc Thiết Bị",
        opt_ct_fragile: "Hàng Dễ Vỡ",
        opt_ct_auto_parts: "Linh Kiện Ô Tô",
        
        // Route Options
        opt_vn_us: "Việt Nam → Hoa Kỳ",
        opt_vn_eu: "Việt Nam → Châu Âu",
        opt_vn_cn: "Việt Nam → Trung Quốc",
        opt_vn_sg: "Việt Nam → Singapore",
        opt_domestic: "Nội Địa",
        
        // Incoterm Options
        opt_ic_exw: "EXW",
        opt_ic_fca: "FCA",
        opt_ic_fas: "FAS",
        opt_ic_fob: "FOB",
        opt_ic_cfr: "CFR",
        opt_ic_cif: "CIF",
        opt_ic_cpt: "CPT",
        opt_ic_cip: "CIP",
        opt_ic_dap: "DAP",
        opt_ic_dpu: "DPU",
        opt_ic_ddp: "DDP",
        
        // Container Type Options
        opt_cn_20ft: "20ft Thường",
        opt_cn_40ft: "40ft Thường",
        opt_cn_40hc: "40ft Cao (High Cube)",
        opt_cn_45hc: "45ft Cao (High Cube)",
        opt_cn_reefer: "Container Lạnh (Reefer)",
        opt_cn_opentop: "Container Mở Nóc (Open-top)",
        opt_cn_flatrack: "Flat-rack (Sàn Phẳng)",
        opt_cn_isotank: "ISO Tank",
        
        // Packaging Quality Options
        opt_pk_poor: "Kém",
        opt_pk_medium: "Trung Bình",
        opt_pk_good: "Tốt",
        opt_pk_excellent: "Xuất Sắc",
        
        // Climate Inputs
        label_climate_tail_prob: "Xác Suất Sự Kiện Khí Hậu Cực Đoan",
        
        // Priority Profile Options
        opt_pr_economy: "Tiết Kiệm (Economy)",
        opt_pr_standard: "Tiêu Chuẩn (Standard)",
        opt_pr_express: "Hỏa Tốc (Express)",
        opt_pr_critical: "Cấp Bách (Critical)",
        
        // Section Titles
        section_buyer_seller: "Người Mua & Người Bán",
        section_buyer_seller_subtitle: "Thông tin đối tác thương mại",
        
        // Transit Time Label
        label_transit_time: "Thời Gian Vận Chuyển",
        
        // Suffixes
        suffix_days: "ngày",
        suffix_units: "đơn vị",
        
        // Module Titles & Descriptions
        module_fuzzy_title: "Fuzzy AHP",
        module_fuzzy_desc: "Phân tích quyết định đa tiêu chí",
        module_arima_title: "Dự Báo ARIMA",
        module_arima_desc: "Mô hình dự đoán chuỗi thời gian",
        module_mc_title: "Monte Carlo",
        module_mc_desc: "Công cụ mô phỏng ngẫu nhiên",
        module_var_title: "VaR / CVaR",
        module_var_desc: "Định lượng rủi ro cực đoan"
    };

    const TRANSLATIONS_EN = {
        // Header & Navigation
        brand_title: "RISKCAST v12.5",
        brand_subtitle: "AI-Powered Logistics Risk Intelligence Platform",
        status_ready: "Analysis Complete",
        status_loading: "Loading data...",
        
        // View Mode Tabs
        tab_enterprise: "Enterprise Dashboard",
        tab_research: "Research / NCKH View",
        tab_investor: "Investor Pitch View",
        
        // Executive Snapshot
        section_executive: "Executive Snapshot",
        label_overall_risk: "Overall Risk Index",
        label_expected_loss: "Expected Loss",
        label_reliability: "Delivery Reliability",
        label_esg: "ESG Score (Environment – Social – Governance)",
        subtitle_per_shipment: "Per shipment",
        subtitle_on_time_prob: "On-time probability",
        subtitle_climate_political: "Climate + Political",
        label_top_route: "Top Route Risk:",
        label_main_driver: "Main Driver:",
        label_recommendation: "System Recommendation:",
        
        // Risk Gauges Section
        section_risk_gauges: "Risk Gauges Overview",
        gauge_risk_title: "Overall Risk Index",
        gauge_reliability_title: "Reliability Score",
        gauge_esg_title: "ESG Score",
        
        // Gauge Explanations (McKinsey-style)
        gauge_explanations: {
            title: "Detailed Insights",
            risk_title: "Overall Risk Index",
            risk: {
                low: "Low risk (0–40). The logistics flow is stable with minimal disruption probability. Suitable for cost/time optimization.",
                medium: "Moderate risk (40–70). Certain operational or weather-driven fluctuations are emerging. Active monitoring required.",
                high: "High risk (70–100). Elevated probability of delays or incidents. Route reassessment and mitigation actions recommended."
            },
            reliability_title: "Reliability Score",
            reliability: {
                very_high: "Very high reliability (>85). Strong predictive stability; ideal for high-value shipments.",
                stable: "Stable (60–85). Acceptable variations within control limits.",
                unstable: "Unstable (<60). Sensitive to disruptions. Not ideal for time-critical cargo."
            },
            esg_title: "ESG Score",
            esg: {
                strong: "Strong ESG compliance (>70). Environmentally aligned route, suitable for sustainability-focused businesses.",
                moderate: "Moderate ESG performance (40–70). Acceptable but not optimized.",
                weak: "Weak ESG compliance (<40). Elevated ESG risk; alternative routing recommended."
            }
        },
        
        // Risk Levels
        risk_level_low: "Low",
        risk_level_medium: "Medium",
        risk_level_high: "High",
        
        // Charts & Sections
        section_radar: "Risk Profile Radar Chart",
        section_layers: "Risk Layer Decomposition",
        section_montecarlo: "Monte Carlo Distribution",
        section_timeline: "Risk Timeline",
        section_matrix: "Probability × Impact Risk Matrix",
        section_scenario: "Scenario Stress Test (What-if)",
        section_tradeoff: "Cost-Time-Risk Tradeoff",
        section_route: "Route Segment Analysis",
        section_recommendations: "AI Expert Recommendations",
        
        // Research View
        section_research_methodology: "Research Methodology Overview",
        panel_dataset: "Panel 1: Dataset Interpretation",
        panel_criteria: "Panel 2: Criteria Construction",
        panel_fuzzy_ahp: "Panel 3: Fuzzy AHP Methodology",
        panel_fuzzy_topsis: "Panel 4: Fuzzy-TOPSIS Analysis",
        panel_montecarlo: "Panel 5: Monte Carlo Simulation",
        panel_integrated: "Panel 6: Integrated Risk Model",
        panel_policy: "Panel 7: Policy Implications for Vietnamese SMEs",
        panel_sensitivity: "Panel 8: Sensitivity & Robustness Check",
        
        // Investor View
        section_problem_solution: "Problem → Solution → Why Now",
        problem_title: "Problem",
        solution_title: "Solution",
        why_now_title: "Why Now",
        section_economics: "Economics Snapshot",
        section_arr: "ARR / Revenue Potential",
        section_architecture: "Engine-as-a-Service Architecture",
        section_pitch: "One-Slide Story for Investors",
        investor_ask: "The Ask:",
        
        // Scenario Names
        scenario_base: "Base Case",
        scenario_best: "Best Case",
        scenario_worst: "Worst Case",
        
        // Risk Layer Names
        layer_delay: "Delay Risk",
        layer_damage: "Damage Risk",
        layer_cost: "Cost Volatility",
        layer_operational: "Operational Risk",
        layer_esg: "ESG Risk",
        layer_political: "Political Risk",
        layer_climate: "Climate Risk",
        
        // Common Terms
        based_on_simulations: "Based on",
        simulations: "simulations",
        days: "days",
        usd: "USD",
        percent: "%",
        loading: "Loading...",
        no_data: "No data available",
        calculating: "Calculating...",
        
        // Buttons & Actions
        btn_analyze: "Run Analysis",
        btn_reset: "Reset",
        btn_export: "Export Report",
        
        // Errors
        error_no_data: "No data available. Please run analysis first.",
        error_fetch: "Failed to fetch data from server.",
        
        // Input Page Labels
        input_transport_mode: "Transport Mode",
        input_cargo_type: "Cargo Type",
        input_route: "Route",
        input_incoterm: "Incoterm Condition",
        input_container: "Container Type",
        input_quality: "Packaging Quality",
        input_priority: "Priority Mode",
        input_analysis_button: "Run Risk Analysis",
        input_transport_placeholder: "Select transport mode",
        placeholder_select: "Select...",
        placeholder_packages: "Enter quantity",
        placeholder_auto: "Auto-calculated",
        
        // Input Page Sections
        section1_title: "Cargo Configuration",
        section1_subtitle: "Background data for AI to optimize routes, time and risks by shipping region.",
        section2_title: "Shipping Information",
        section2_subtitle: "Route details and delivery conditions",
        section3_title: "Additional Parameters",
        section3_subtitle: "Factors affecting risk",
        
        // Input Page Status
        status_ready: "System Ready",
        loading_text: "Initializing Risk Engine...",
        
        // Input Page Labels (detailed)
        label_transport_mode: "Transport Mode",
        label_cargo_type: "Cargo Type",
        label_route: "Route",
        label_incoterm: "Incoterm Condition",
        label_container: "Container Type",
        label_packaging: "Packaging Quality",
        label_priority: "Priority Mode",
        label_packages: "Number of Packages",
        label_etd: "Expected Departure Date (ETD)",
        label_eta: "Expected Arrival Date (ETA)",
        label_cargo_value: "Cargo Value (USD)",
        
        // Transport Mode Options (11 International Modes)
        transport_sea: "Sea Freight",
        transport_air: "Air Freight",
        transport_road: "Road Transport",
        transport_rail: "Rail Transport",
        transport_multimodal: "Multimodal Transport",
        transport_intermodal: "Intermodal Transport",
        transport_express: "Courier / Express",
        transport_postal: "International Postal / Parcel",
        transport_pipeline: "Pipeline Transport",
        transport_inland: "Inland Waterway",
        transport_roro: "Ro-Ro Transport",
        opt_tm_ocean_fcl: "Ocean Freight — FCL",
        opt_tm_ocean_lcl: "Ocean Freight — LCL",
        opt_tm_air: "Air Freight",
        opt_tm_rail: "Rail Freight",
        opt_tm_road: "Road — Truck",
        opt_tm_multimodal: "Multimodal Transport",
        opt_tm_courier: "Courier / Express",
        opt_tm_inland: "Inland Waterway",
        opt_tm_pipeline: "Pipeline",
        opt_tm_cross: "Cross-border Road",
        opt_tm_lastmile: "Last-mile Delivery",
        
        // Input Page Error Messages
        error_required: "This field is required",
        error_positive: "Value must be a positive number",
        error_date_invalid: "Invalid date",
        confirm_reset: "Are you sure you want to reset all fields?",
        alert_success: "Risk analysis completed successfully!",
        
        // Buyer/Seller Fields
        buyer_section: "Buyer Information",
        buyer_name: "Buyer Name",
        buyer_country: "Buyer Country",
        buyer_size: "Company Size",
        buyer_esg: "ESG Score (if available)",
        buyer_reliability: "Reliability Score",
        seller_section: "Seller Information",
        seller_name: "Seller Name",
        seller_country: "Seller Country",
        seller_size: "Company Size",
        seller_esg: "ESG Score (if available)",
        seller_reliability: "Reliability Score",
        
        // Country Options
        country_vn: "Vietnam",
        country_cn: "China",
        country_jp: "Japan",
        country_kr: "South Korea",
        country_us: "United States",
        country_eu: "European Union",
        
        // Company Size Options
        company_sme: "SME (10–200 employees)",
        company_medium: "Medium (200–500)",
        company_large: "Large (>500)",
        
        // Cargo Type Options
        opt_ct_general: "General Cargo",
        opt_ct_electronics: "Electronics",
        opt_ct_food_bev: "Food & Beverage",
        opt_ct_garments: "Garments / Textile",
        opt_ct_agriculture: "Agriculture",
        opt_ct_refrigerated: "Refrigerated / Frozen",
        opt_ct_chemicals: "Chemicals",
        opt_ct_machinery: "Machinery",
        opt_ct_fragile: "Fragile Goods",
        opt_ct_auto_parts: "Automotive Parts",
        
        // Route Options
        opt_vn_us: "Vietnam → United States",
        opt_vn_eu: "Vietnam → Europe",
        opt_vn_cn: "Vietnam → China",
        opt_vn_sg: "Vietnam → Singapore",
        opt_domestic: "Domestic",
        
        // Incoterm Options
        opt_ic_exw: "EXW",
        opt_ic_fca: "FCA",
        opt_ic_fas: "FAS",
        opt_ic_fob: "FOB",
        opt_ic_cfr: "CFR",
        opt_ic_cif: "CIF",
        opt_ic_cpt: "CPT",
        opt_ic_cip: "CIP",
        opt_ic_dap: "DAP",
        opt_ic_dpu: "DPU",
        opt_ic_ddp: "DDP",
        
        // Container Type Options
        opt_cn_20ft: "20ft Standard",
        opt_cn_40ft: "40ft Standard",
        opt_cn_40hc: "40ft High Cube",
        opt_cn_45hc: "45ft High Cube",
        opt_cn_reefer: "Reefer Container",
        opt_cn_opentop: "Open-top",
        opt_cn_flatrack: "Flat-rack",
        opt_cn_isotank: "ISO Tank",
        
        // Packaging Quality Options
        opt_pk_poor: "Poor",
        opt_pk_medium: "Medium",
        opt_pk_good: "Good",
        opt_pk_excellent: "Excellent",
        
        // Climate Inputs
        label_climate_tail_prob: "Climate Tail Event Probability",
        
        // Priority Profile Options
        opt_pr_economy: "Economy",
        opt_pr_standard: "Standard",
        opt_pr_express: "Express",
        opt_pr_critical: "Critical",
        
        // Section Titles
        section_buyer_seller: "Buyer & Seller",
        section_buyer_seller_subtitle: "Trading partner information",
        
        // Transit Time Label
        label_transit_time: "Transit Time",
        
        // Suffixes
        suffix_days: "days",
        suffix_units: "units",
        
        // Module Titles & Descriptions
        module_fuzzy_title: "Fuzzy AHP",
        module_fuzzy_desc: "Multi-criteria decision analysis",
        module_arima_title: "ARIMA Forecasting",
        module_arima_desc: "Time series prediction model",
        module_mc_title: "Monte Carlo",
        module_mc_desc: "Stochastic simulation engine",
        module_var_title: "VaR / CVaR",
        module_var_desc: "Extreme risk quantification"
    };

    // ============================================
    // LANGUAGE MANAGEMENT
    // ============================================

    // Get current language from localStorage or default to 'vi'
    let currentLang = localStorage.getItem('riskcast_lang') || 'vi';

    // Get translations object based on current language
    function getTranslations() {
        if (currentLang === 'en') {
            return TRANSLATIONS_EN;
        } else {
            return TRANSLATIONS_VI;
        }
    }

    // Performance: Cache DOM elements to avoid repeated queries
    let translationCache = {
        dataLang: null,
        dataI18n: null,
        dropdownItems: null,
        dropdownSelected: null,
        dropdownWrappers: null,
        dataPlaceholder: null,
        dropdownValue: null,
        cardTitles: null,
        cardBadges: null,
        langButtons: null,
        tabButtons: null,
        cached: false
    };

    // Build translation cache on first load
    function buildTranslationCache() {
        if (translationCache.cached) return;
        
        translationCache.dataLang = Array.from(document.querySelectorAll('[data-lang]'));
        translationCache.dataI18n = Array.from(document.querySelectorAll('[data-i18n]'));
        translationCache.dropdownItems = Array.from(document.querySelectorAll(".dropdown-item"));
        translationCache.dropdownSelected = Array.from(document.querySelectorAll(".dropdown-selected.placeholder"));
        translationCache.dropdownWrappers = Array.from(document.querySelectorAll('.dropdown-wrapper .dropdown'));
        translationCache.dataPlaceholder = Array.from(document.querySelectorAll('[data-placeholder]'));
        translationCache.dropdownValue = Array.from(document.querySelectorAll('.dropdown-value.placeholder'));
        translationCache.cardTitles = Array.from(document.querySelectorAll('.card-title span[data-lang]'));
        translationCache.cardBadges = Array.from(document.querySelectorAll('.card-badge[data-lang]'));
        translationCache.langButtons = Array.from(document.querySelectorAll('.lang-btn'));
        
        // Cache tab buttons individually
        translationCache.tabButtons = {
            enterprise: document.querySelector('#tab-enterprise span[data-lang="tab_enterprise"]'),
            research: document.querySelector('#tab-research span[data-lang="tab_research"]'),
            investor: document.querySelector('#tab-investor span[data-lang="tab_investor"]')
        };
        
        translationCache.cached = true;
    }

    // Clear cache when DOM changes significantly
    function clearTranslationCache() {
        translationCache.cached = false;
        translationCache.dataLang = null;
        translationCache.dataI18n = null;
        translationCache.dropdownItems = null;
        translationCache.dropdownSelected = null;
        translationCache.dropdownWrappers = null;
        translationCache.dataPlaceholder = null;
        translationCache.dropdownValue = null;
        translationCache.cardTitles = null;
        translationCache.cardBadges = null;
        translationCache.langButtons = null;
        translationCache.tabButtons = null;
    }

    // Apply language to all elements with data-lang attribute (OPTIMIZED)
    function applyLanguage() {
        const t = getTranslations();
        
        // Build cache on first call
        buildTranslationCache();
        
        // Update all elements with data-lang attribute (using cache)
        translationCache.dataLang.forEach(el => {
            const key = el.getAttribute('data-lang');
            if (t[key]) {
                if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                    el.placeholder = t[key];
                } else {
                    el.textContent = t[key];
                }
            }
        });
        
        // Update elements with data-i18n (using cache)
        translationCache.dataI18n.forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (t[key]) {
                if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                    el.placeholder = t[key];
                } else {
                    el.textContent = t[key];
                }
            }
        });
        
        // Update dropdown items (using cache)
        translationCache.dropdownItems.forEach(item => {
            const key = item.getAttribute('data-i18n');
            if (key && t[key]) {
                item.textContent = t[key];
            }
        });
        
        // Update dropdown selected text (using cache)
        translationCache.dropdownSelected.forEach(sel => {
            const key = sel.getAttribute('data-i18n');
            if (key && t[key]) {
                sel.textContent = t[key];
            }
        });
        
        // Update selected dropdown text if value exists (using cache)
        translationCache.dropdownWrappers.forEach(dropdown => {
            const selected = dropdown.querySelector('.dropdown-selected');
            if (selected && selected.dataset.value && !selected.classList.contains('placeholder')) {
                const value = selected.dataset.value;
                const item = dropdown.querySelector(`.dropdown-item[data-value="${value}"]`);
                if (item) {
                    const key = item.getAttribute('data-i18n');
                    if (key && t[key]) {
                        selected.textContent = t[key];
                    }
                }
            }
        });
        translationCache.dataPlaceholder.forEach(el => {
            const key = el.getAttribute('data-placeholder');
            if (t[key]) {
                el.placeholder = t[key];
            }
        });
        translationCache.dropdownValue.forEach(el => {
            const key = el.getAttribute('data-lang') || el.getAttribute('data-i18n');
            if (key && t[key]) {
                el.textContent = t[key];
            } else if (t.placeholder_select) {
                el.textContent = t.placeholder_select;
            }
        });
        
        // Update tab buttons (using cache)
        const tabs = translationCache.tabButtons;
        if (tabs.enterprise && t.tab_enterprise) tabs.enterprise.textContent = t.tab_enterprise;
        if (tabs.research && t.tab_research) tabs.research.textContent = t.tab_research;
        if (tabs.investor && t.tab_investor) tabs.investor.textContent = t.tab_investor;
        
        // Update card titles (using cache)
        translationCache.cardTitles.forEach(el => {
            const key = el.getAttribute('data-lang');
            if (t[key]) {
                el.textContent = t[key];
            }
        });
        
        // Update card badges (using cache)
        translationCache.cardBadges.forEach(el => {
            const key = el.getAttribute('data-lang');
            if (t[key]) {
                el.textContent = t[key];
            }
        });
        
        // Language applied (console.log removed for production)
    }

    // Set language and apply
    function setLanguage(lang) {
        if (lang === 'vi' || lang === 'en') {
            currentLang = lang;
            localStorage.setItem('riskcast_lang', lang);
            applyLanguage();
            updateLanguageButtons();
            
            // Trigger re-render for ResultsCore if it exists
            if (window.RISKCAST?.pages?.results?.renderGaugeExplanation && window.appData) {
                window.RISKCAST.pages.results.renderGaugeExplanation(window.appData);
            }
            
            if (window.RISKCAST?.pages?.results?.renderGaugeCharts && window.appData?.summary) {
                window.RISKCAST.pages.results.renderGaugeCharts(window.appData.summary);
            }
        }
    }

    // Update language button states (OPTIMIZED)
    function updateLanguageButtons() {
        buildTranslationCache();
        translationCache.langButtons.forEach(btn => {
            const btnLang = btn.getAttribute('data-lang');
            if (btnLang === currentLang) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
        
        const btnVI = document.getElementById('lang-btn-vi') || document.getElementById('btn-lang-vi');
        const btnEN = document.getElementById('lang-btn-en') || document.getElementById('btn-lang-en');
        
        if (btnVI) {
            if (currentLang === 'vi') {
                btnVI.classList.add('active');
            } else {
                btnVI.classList.remove('active');
            }
        }
        if (btnEN) {
            if (currentLang === 'en') {
                btnEN.classList.add('active');
            } else {
                btnEN.classList.remove('active');
            }
        }
    }

    // Initialize language system (OPTIMIZED)
    function initializeLanguage() {
        // Build cache first
        buildTranslationCache();
        
        // Bind language buttons (using cache)
        translationCache.langButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                const lang = this.getAttribute('data-lang');
                setLanguage(lang);
            });
        });
        
        const btnVI = document.getElementById('lang-btn-vi') || document.getElementById('btn-lang-vi');
        const btnEN = document.getElementById('lang-btn-en') || document.getElementById('btn-lang-en');
        
        if (btnVI) {
            btnVI.addEventListener('click', () => setLanguage('vi'));
        }
        if (btnEN) {
            btnEN.addEventListener('click', () => setLanguage('en'));
        }
        
        // Apply initial language
        applyLanguage();
        updateLanguageButtons();
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeLanguage);
    } else {
        initializeLanguage();
    }

    // ============================================
    // EXPORT TO RISKCAST NAMESPACE
    // ============================================

    window.RISKCAST.core.translations = {
        // Translation dictionaries
        TRANSLATIONS_VI: TRANSLATIONS_VI,
        TRANSLATIONS_EN: TRANSLATIONS_EN,
        
        // Language management
        setLanguage: setLanguage,
        applyLanguage: applyLanguage,
        getCurrentLang: () => currentLang,
        getTranslations: getTranslations,
        initialize: initializeLanguage,
        clearCache: clearTranslationCache,
        
        // Backward compatibility
        get: (key) => {
            const t = getTranslations();
            return t[key] || key;
        }
    };

    // Backward compatibility - keep window.TRANSLATIONS_VI and TRANSLATIONS_EN
    window.TRANSLATIONS_VI = TRANSLATIONS_VI;
    window.TRANSLATIONS_EN = TRANSLATIONS_EN;
    window.RiskcastLang = window.RISKCAST.core.translations;


})();

