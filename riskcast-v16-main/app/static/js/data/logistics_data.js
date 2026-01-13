
// Export to window for global access
const LOGISTICS_DATA = {
    /**
     * ========================================
     * PART 1: TRANSPORT MODE CLASSIFICATIONS
     * ========================================
     */
    transportModeTypes: {
        // ===== OCEAN FREIGHT =====
        ocean: {
            fcl: {
                value: 'ocean_fcl',
                label: 'FCL (Full Container Load)',
                label_vi: 'Đường Biển — FCL (Nguyên Container)',
                description: 'Nguyên container (20ft, 40ft, 40HC, 45ft, Reefer, Open Top, Flat Rack)',
                suitable_for: 'Lô hàng từ 15 m³ trở lên, hàng giá trị cao, hàng nhạy cảm',
                risk_level: 'low',
                risk_score: 2.5,
                share_global: 85
            },
            lcl: {
                value: 'ocean_lcl',
                label: 'LCL (Less than Container Load)',
                label_vi: 'Đường Biển — LCL (Hàng Lẻ Ghép)',
                description: 'Hàng lẻ, ghép chung container với nhiều shipper khác',
                suitable_for: 'Lô hàng nhỏ (< 15 m³), muốn tiết kiệm chi phí',
                risk_level: 'medium',
                risk_score: 5.0,
                share_global: 10
            },
            break_bulk: {
                value: 'ocean_break_bulk',
                label: 'Break Bulk (Hàng rời, hàng xá)',
                label_vi: 'Hàng Rời Không Container',
                description: 'Thép cuộn, gỗ xẻ, máy móc siêu trường siêu trọng, turbine, cánh quạt gió',
                suitable_for: 'Hàng dự án, hàng siêu nặng, siêu dài, siêu cao',
                risk_level: 'high',
                risk_score: 7.5,
                share_global: 3
            },
            ro_ro: {
                value: 'ocean_ro_ro',
                label: 'Ro-Ro (Roll-on/Roll-off)',
                label_vi: 'Tàu Chở Xe (Ro-Ro)',
                description: 'Xe tải, xe hơi, xe công trình tự lăn lên/từ tàu',
                suitable_for: 'Xe ô tô, xe máy, xe tải, máy công trình có bánh lốp',
                risk_level: 'medium',
                risk_score: 4.5,
                share_global: 1
            },
            bulk: {
                value: 'ocean_bulk',
                label: 'Bulk (Hàng rời khô/ướt)',
                label_vi: 'Tàu Chở Hàng Rời',
                description: 'Than, quặng, xi măng, ngũ cốc, dầu cọ, hóa chất lỏng',
                suitable_for: 'Hàng hóa nguyên liệu số lượng cực lớn (hàng chục nghìn tấn)',
                risk_level: 'medium',
                risk_score: 5.5,
                share_global: 1
            },
            reefer: {
                value: 'ocean_reefer',
                label: 'Reefer (Hàng lạnh)',
                label_vi: 'Container Lạnh',
                description: 'Container lạnh hoặc tàu lạnh chuyên dụng (-25°C đến +25°C)',
                suitable_for: 'Hàng đông lạnh, hoa quả, thịt, thủy sản, dược phẩm',
                risk_level: 'low',
                risk_score: 3.0,
                share_global: 0
            }
        },
        
        // ===== AIR FREIGHT =====
        air: {
            general: {
                value: 'air_general',
                label: 'General Cargo',
                label_vi: 'Hàng Không — Hàng Thông Thường',
                description: 'Hàng khô bình thường, đóng thùng carton, pallet, bao',
                suitable_for: 'Quần áo, điện thoại, linh kiện điện tử, mỹ phẩm, tài liệu, mẫu hàng',
                risk_level: 'very_low',
                risk_score: 1.5
            },
            dg: {
                value: 'air_dg',
                label: 'Dangerous Goods — DG',
                label_vi: 'Hàng Không — Hàng Nguy Hiểm',
                description: 'Hàng thuộc 9 class nguy hiểm (pin lithium, hóa chất, chất lỏng dễ cháy)',
                suitable_for: 'Pin lithium >160Wh, nước hoa, bình xịt, keo 502, bật lửa',
                risk_level: 'high',
                risk_score: 8.0
            },
            perishable: {
                value: 'air_perishable',
                label: 'Perishable Cargo',
                label_vi: 'Hàng Không — Hàng Dễ Hư',
                description: 'Hoa tươi, trái cây tươi, thủy hải sản tươi sống, vaccine',
                suitable_for: 'Cần đi nhanh trong 24–72h, giữ lạnh nhẹ hoặc giữ tươi',
                risk_level: 'medium',
                risk_score: 4.0
            },
            pharma: {
                value: 'air_pharma',
                label: 'Temperature Controlled / Pharma',
                label_vi: 'Hàng Không — Dược Phẩm',
                description: 'Hàng cần kiểm soát nhiệt độ nghiêm ngặt +2°C đến +8°C',
                suitable_for: 'Dược phẩm, vaccine, insulin, mẫu máu, chế phẩm sinh học',
                risk_level: 'medium',
                risk_score: 4.5
            }
        },
        
        // ===== ROAD FREIGHT =====
        road: {
            ftl: {
                value: 'road_ftl',
                label: 'FTL — Full Truck Load',
                label_vi: 'Đường Bộ — Thuê Nguyên Xe',
                description: 'Thuê nguyên xe tải (0.5 tấn → 30 tấn)',
                suitable_for: 'Lô hàng từ 2–3 tấn trở lên, muốn đi nhanh, an toàn cao',
                risk_level: 'low',
                risk_score: 3.0
            },
            ltl: {
                value: 'road_ltl',
                label: 'LTL — Less than Truck Load',
                label_vi: 'Đường Bộ — Hàng Lẻ Ghép Xe',
                description: 'Hàng lẻ ghép chung xe tải với nhiều shipper khác',
                suitable_for: 'Lô nhỏ dưới 2 tấn, đi nội địa hoặc VN–Lào–Campuchia–Thái Lan',
                risk_level: 'medium',
                risk_score: 5.5
            },
            container_road: {
                value: 'road_container',
                label: 'Container đường bộ',
                label_vi: 'Kéo Container Đường Bộ',
                description: 'Kéo container 20\'/40\' bằng moóc từ cảng/cửa khẩu về kho',
                suitable_for: 'Hàng nhập khẩu từ cảng về ICD, kho CFS',
                risk_level: 'low',
                risk_score: 2.5
            },
            reefer_truck: {
                value: 'road_reefer',
                label: 'Reefer Truck',
                label_vi: 'Xe Tải Lạnh',
                description: 'Xe tải lạnh hoặc gắn thùng lạnh (0–5°C, -18°C)',
                suitable_for: 'Thủy hải sản, thịt, sữa, kem, trái cây, vaccine, hoa tươi',
                risk_level: 'low',
                risk_score: 3.5
            },
            heavy_truck: {
                value: 'road_heavy',
                label: 'Heavy / Oversized Truck',
                label_vi: 'Xe Siêu Trường Siêu Trọng',
                description: 'Xe đầu kéo + rơ-moóc lùn, thùy lục chở hàng quá khổ',
                suitable_for: 'Máy móc công nghiệp, turbine, cột bê tông, cần cẩu',
                risk_level: 'high',
                risk_score: 7.0
            },
            tank_truck: {
                value: 'road_tank',
                label: 'Tank Truck',
                label_vi: 'Xe Bồn',
                description: 'Chở chất lỏng: xăng dầu, hóa chất, rượu, nước tương',
                suitable_for: 'Hàng lỏng số lượng lớn',
                risk_level: 'medium',
                risk_score: 6.0
            },
            regular_truck: {
                value: 'road_regular',
                label: 'Regular Truck',
                label_vi: 'Xe Tải Mui Bạt Thông Dụng',
                description: 'Từ 1.5 tấn → 18–20 tấn, phổ biến nhất nội địa VN',
                suitable_for: 'Đồ gỗ, gạch, xi măng, thạch cao, hàng tiêu dụng',
                risk_level: 'low',
                risk_score: 3.5
            },
            express: {
                value: 'road_express',
                label: 'Express Delivery',
                label_vi: 'Chuyển Phát Nhanh',
                description: 'Grab, AhaMove, Giao Hàng Nhanh (< 50kg)',
                suitable_for: 'Tài liệu, hàng mẫu, hàng Shopee/Lazada/Tiki',
                risk_level: 'low',
                risk_score: 2.0
            }
        },
        
        // ===== RAIL FREIGHT =====
        rail: {
            container: {
                value: 'rail_container',
                label: 'Rail Container (FCL/LCL)',
                label_vi: 'Đường Sắt — Container',
                description: 'Container 20\'/40\'/40HC chạy trên toa phẳng',
                suitable_for: 'VN–TQ (Hà Nội ⇄ Nam Ninh, Lào Cai ⇄ Hà Khẩu), VN–EU',
                risk_level: 'low',
                risk_score: 3.0
            },
            bulk_wagon: {
                value: 'rail_bulk',
                label: 'Bulk Wagon',
                label_vi: 'Toa Xe Hàng Rời',
                description: 'Toa hở/kín chở quặng, than, xi măng, gạo, phân bón',
                suitable_for: 'Nội địa VN (Bắc–Nam), VN–TQ',
                risk_level: 'low',
                risk_score: 3.5
            },
            reefer_wagon: {
                value: 'rail_reefer',
                label: 'Reefer Wagon',
                label_vi: 'Toa Xe Lạnh',
                description: 'Toa lạnh chuyên dụng hoặc container lạnh gắn lên toa',
                suitable_for: 'Thủy sản đông lạnh, trái cây, bia, sữa từ Trung–Tây Nguyên ra Bắc',
                risk_level: 'low',
                risk_score: 3.5
            },
            lcl_rail: {
                value: 'rail_lcl',
                label: 'LCL Rail',
                label_vi: 'Hàng Lẻ Ghép Toa',
                description: 'Ghép chung toa với nhiều shipper (rẻ hơn container 20–30%)',
                suitable_for: 'Nội địa + VN–TQ',
                risk_level: 'medium',
                risk_score: 5.0
            },
            heavy_rail: {
                value: 'rail_heavy',
                label: 'Heavy Rail (Schnabel)',
                label_vi: 'Toa Xe Siêu Trường Siêu Trọng',
                description: 'Toa lùn, toa Schnabel chở turbine, máy biến áp',
                suitable_for: 'Hàng dự án (nhà máy điện, metro)',
                risk_level: 'high',
                risk_score: 7.5
            },
            passenger_freight: {
                value: 'rail_passenger',
                label: 'Passenger + Freight',
                label_vi: 'Hành Khách Kết Hợp Chở Hàng',
                description: 'Gắn toa hàng vào tàu khách Thống Nhất (SG–HN)',
                suitable_for: 'Hàng nhẹ, giá rẻ nội địa Bắc–Nam (< 3–5 tấn/toa)',
                risk_level: 'medium',
                risk_score: 4.5
            },
            china_europe: {
                value: 'rail_china_europe',
                label: 'China Railway Express',
                label_vi: 'Tàu Liên Vận VN–TQ–EU',
                description: 'Container transit qua TQ đi Kazakhstan, Nga, Ba Lan, Đức',
                suitable_for: 'Điện tử, máy móc, đồ nội thất từ VN đi châu Âu (15–22 ngày)',
                risk_level: 'low',
                risk_score: 4.0
            }
        }
    },

    /**
     * ========================================
     * PART 2: ROUTES DATA (10 ROUTES CHÍNH)
     * ========================================
     */
    routes: {
        // ===== 1. VIETNAM → CHINA =====
        'vn_cn': {
            name: 'Vietnam → China',
            name_vi: 'Việt Nam → Trung Quốc',
            flag: '🇻🇳 → 🇨🇳',
            transport_modes: [
                {
                    value: 'ocean_fcl',
                    label: 'Đường Biển — FCL',
                    label_en: 'Ocean Freight — FCL',
                    days: '4-10',
                    share: 45,
                    default: true,
                    risk_level: 'low',
                    risk_score: 2.5,
                    description: 'Container riêng, rủi ro thấp nhất',
                    routes: [
                        { pol: 'Cái Mép - Thị Vải', pol_code: 'CMP', pod: 'Shenzhen', pod_code: 'CNSZN', days: 7, km: 1200, cost: '$950-1,250 (20\') / $1,300-1,600 (40\')' },
                        { pol: 'Hải Phòng', pol_code: 'HPH', pod: 'Shanghai', pod_code: 'CNSHA', days: 10, km: 2400, cost: '$1,400-1,700' },
                        { pol: 'Sài Gòn', pol_code: 'SGN', pod: 'Guangzhou', pod_code: 'CNCAN', days: 5, km: 1100, cost: '$780-1,050' },
                        { pol: 'Hải Phòng', pol_code: 'HPH', pod: 'Ningbo', pod_code: 'CNNGB', days: 8, km: 1800, cost: '$1,300-1,600' },
                        { pol: 'Đà Nẵng', pol_code: 'DAD', pod: 'Xiamen', pod_code: 'CNXMN', days: 4, km: 900, cost: '$1,000-1,300' }
                    ]
                },
                {
                    value: 'ocean_lcl',
                    label: 'Đường Biển — LCL',
                    days: '6-14',
                    share: 20,
                    risk_level: 'medium',
                    risk_score: 5.0,
                    description: 'Hàng ghép, tiết kiệm chi phí',
                    routes: [
                        { pol: 'Cái Mép - Thị Vải', pol_code: 'CMP', pod: 'Shenzhen', pod_code: 'CNSZN', days: 9, km: 1200, cost: '$65-95/m³' },
                        { pol: 'Hải Phòng', pol_code: 'HPH', pod: 'Shanghai', pod_code: 'CNSHA', days: 12, km: 2400, cost: '$65-95/m³' },
                        { pol: 'Sài Gòn', pol_code: 'SGN', pod: 'Ningbo', pod_code: 'CNNGB', days: 8, km: 1600, cost: '$65-95/m³' }
                    ]
                },
                {
                    value: 'road_ftl',
                    label: 'Đường Bộ — FTL',
                    days: '1-5',
                    share: 15,
                    risk_level: 'low',
                    risk_score: 3.0,
                    description: 'Xe tải riêng, nhanh',
                    routes: [
                        { pol: 'Hữu Nghị (Border)', pol_code: 'HN', pod: 'Nam Ninh', pod_code: 'NN', days: 2, km: 450, cost: '$800-1,200' },
                        { pol: 'Móng Cái (Border)', pol_code: 'MC', pod: 'Đông Hưng', pod_code: 'DH', days: 1, km: 220, cost: '$500-800' },
                        { pol: 'Lào Cai (Border)', pol_code: 'LC', pod: 'Hà Khẩu', pod_code: 'HK', days: 1, km: 380, cost: '$700-1,000' }
                    ]
                },
                {
                    value: 'road_ltl',
                    label: 'Đường Bộ — LTL',
                    days: '2-7',
                    share: 5,
                    risk_level: 'medium',
                    risk_score: 5.5,
                    description: 'Hàng ghép xe, tiết kiệm',
                    routes: [
                        { pol: 'Hà Nội', pol_code: 'HAN', pod: 'Nam Ninh', pod_code: 'NN', days: 3, km: 450, cost: '$0.3-0.5/kg' }
                    ]
                },
                {
                    value: 'rail_container',
                    label: 'Đường Sắt — Container',
                    days: '2-5',
                    share: 8,
                    risk_level: 'low',
                    risk_score: 3.0,
                    description: 'Chi phí thấp, ổn định',
                    routes: [
                        { pol: 'Yên Viên (Rail)', pol_code: 'YV', pod: 'Nam Ninh', pod_code: 'NN', days: 3, km: 2100, cost: '$900-1,300' },
                        { pol: 'Lào Cai (Rail)', pol_code: 'LC', pod: 'Hà Khẩu', pod_code: 'HK', days: 2, km: 380, cost: '$500-800' }
                    ]
                },
                {
                    value: 'rail_lcl',
                    label: 'Đường Sắt — LCL',
                    days: '3-7',
                    share: 2,
                    risk_level: 'medium',
                    risk_score: 5.0,
                    description: 'Rẻ hơn container 20-30%',
                    routes: [
                        { pol: 'Yên Viên', pol_code: 'YV', pod: 'Nam Ninh', pod_code: 'NN', days: 4, km: 2100, cost: '$60-90/m³' }
                    ]
                },
                {
                    value: 'air_general',
                    label: 'Hàng Không — General',
                    hours: '2-5',
                    share: 4,
                    risk_level: 'very_low',
                    risk_score: 1.5,
                    description: 'Nhanh nhất',
                    routes: [
                        { pol: 'Nội Bài (HAN)', pol_code: 'HAN', pod: 'Quảng Châu (CAN)', pod_code: 'CAN', hours: 2, km: 1800, cost: '$4.5-6.5/kg' },
                        { pol: 'Tân Sơn Nhất (SGN)', pol_code: 'SGN', pod: 'Hong Kong (HKG)', pod_code: 'HKG', hours: 2, km: 1100, cost: '$5.0-7.0/kg' }
                    ]
                },
                {
                    value: 'air_express',
                    label: 'Express (DHL/FedEx)',
                    hours: '24-48',
                    share: 1,
                    risk_level: 'very_low',
                    risk_score: 1.0,
                    description: 'Door-to-door, siêu nhanh',
                    routes: [
                        { pol: 'Hà Nội', pol_code: 'HAN', pod: 'Bắc Kinh', pod_code: 'PEK', hours: 24, km: 2400, cost: '$8-12/kg' }
                    ]
                }
            ]
        },
        
        // ===== 2. VIETNAM → UNITED STATES =====
        'vn_us': {
            name: 'Vietnam → United States',
            name_vi: 'Việt Nam → Hoa Kỳ',
            flag: '🇻🇳 → 🇺🇸',
            transport_modes: [
                {
                    value: 'ocean_fcl',
                    label: 'Đường Biển — FCL',
                    days: '15-45',
                    share: 85,
                    default: true,
                    risk_level: 'low',
                    risk_score: 3.0,
                    description: 'Phương thức chủ đạo, rủi ro thấp',
                    routes: [
                        { pol: 'Cái Mép - Thị Vải', pol_code: 'CMP', pod: 'Long Beach (LA)', pod_code: 'USLGB', days: 18, km: 12600, cost: '$4,800-6,200' },
                        { pol: 'Cái Mép - Thị Vải', pol_code: 'CMP', pod: 'Los Angeles (LA)', pod_code: 'USLAX', days: 18, km: 12600, cost: '$4,800-6,200' },
                        { pol: 'Cái Mép - Thị Vải', pol_code: 'CMP', pod: 'New York (NY)', pod_code: 'USNYC', days: 35, km: 15600, cost: '$7,500-9,000' },
                        { pol: 'Hải Phòng', pol_code: 'HPH', pod: 'Long Beach (LA)', pod_code: 'USLGB', days: 20, km: 15500, cost: '$4,900-6,100' },
                        { pol: 'Cái Mép - Thị Vải', pol_code: 'CMP', pod: 'Seattle', pod_code: 'USSEA', days: 20, km: 13800, cost: '$2,900-3,600' }
                    ]
                },
                {
                    value: 'ocean_lcl',
                    label: 'Đường Biển — LCL',
                    days: '18-50',
                    share: 11,
                    risk_level: 'medium',
                    risk_score: 5.5,
                    description: 'Hàng ghép, thời gian lâu hơn',
                    routes: [
                        { pol: 'Cái Mép - Thị Vải', pol_code: 'CMP', pod: 'Long Beach (LA)', pod_code: 'USLGB', days: 22, km: 12600, cost: '$180-250/m³' },
                        { pol: 'Cái Mép - Thị Vải', pol_code: 'CMP', pod: 'New York (NY)', pod_code: 'USNYC', days: 40, km: 15600, cost: '$220-300/m³' }
                    ]
                },
                {
                    value: 'air_general',
                    label: 'Hàng Không — General',
                    hours: '16-22',
                    share: 4,
                    risk_level: 'very_low',
                    risk_score: 1.5,
                    description: 'Nhanh nhất, hàng giá trị cao',
                    routes: [
                        { pol: 'Tân Sơn Nhất (SGN)', pol_code: 'SGN', pod: 'Los Angeles (LAX)', pod_code: 'LAX', hours: 16, km: 12400, cost: '$4.2-6.0/kg' },
                        { pol: 'Nội Bài (HAN)', pol_code: 'HAN', pod: 'JFK New York', pod_code: 'JFK', hours: 20, km: 14800, cost: '$6.0-8.5/kg' },
                        { pol: 'Tân Sơn Nhất (SGN)', pol_code: 'SGN', pod: 'San Francisco (SFO)', pod_code: 'SFO', hours: 17, km: 13200, cost: '$5.8-8.2/kg' }
                    ]
                }
            ]
        },
        
        // ===== 3. VIETNAM → SOUTH KOREA =====
        'vn_kr': {
            name: 'Vietnam → South Korea',
            name_vi: 'Việt Nam → Hàn Quốc',
            flag: '🇻🇳 → 🇰🇷',
            transport_modes: [
                {
                    value: 'ocean_fcl',
                    label: 'Đường Biển — FCL',
                    days: '4-7',
                    share: 75,
                    default: true,
                    risk_level: 'low',
                    risk_score: 2.5,
                    routes: [
                        { pol: 'Cái Mép - Thị Vải', pol_code: 'CMP', pod: 'Busan', pod_code: 'KRPUS', days: 6, km: 3300, cost: '$950-1,300' },
                        { pol: 'Hải Phòng', pol_code: 'HPH', pod: 'Incheon', pod_code: 'KRINC', days: 5, km: 3100, cost: '$1,300-1,700' },
                        { pol: 'Đà Nẵng', pol_code: 'DAD', pod: 'Busan', pod_code: 'KRPUS', days: 5, km: 3000, cost: '$1,350-1,750' }
                    ]
                },
                {
                    value: 'ocean_lcl',
                    label: 'Đường Biển — LCL',
                    days: '6-10',
                    share: 13,
                    risk_level: 'medium',
                    risk_score: 5.0,
                    routes: [
                        { pol: 'Cái Mép - Thị Vải', pol_code: 'CMP', pod: 'Busan', pod_code: 'KRPUS', days: 8, km: 3300, cost: '$110-160/m³' }
                    ]
                },
                {
                    value: 'air_general',
                    label: 'Hàng Không — General',
                    hours: '4-5',
                    share: 12,
                    risk_level: 'very_low',
                    risk_score: 1.5,
                    routes: [
                        { pol: 'Nội Bài (HAN)', pol_code: 'HAN', pod: 'Incheon (ICN)', pod_code: 'ICN', hours: 4, km: 3000, cost: '$3.5-5.5/kg' },
                        { pol: 'Tân Sơn Nhất (SGN)', pol_code: 'SGN', pod: 'Incheon (ICN)', pod_code: 'ICN', hours: 5, km: 3500, cost: '$3.8-5.8/kg' }
                    ]
                }
            ]
        },
        
        // ===== 4. VIETNAM → JAPAN =====
        'vn_jp': {
            name: 'Vietnam → Japan',
            name_vi: 'Việt Nam → Nhật Bản',
            flag: '🇻🇳 → 🇯🇵',
            transport_modes: [
                {
                    value: 'ocean_fcl',
                    label: 'Đường Biển — FCL',
                    days: '7-12',
                    share: 80,
                    default: true,
                    risk_level: 'low',
                    risk_score: 2.5,
                    routes: [
                        { pol: 'Cái Mép - Thị Vải', pol_code: 'CMP', pod: 'Yokohama', pod_code: 'JPYOK', days: 10, km: 4400, cost: '$1,400-1,800' },
                        { pol: 'Hải Phòng', pol_code: 'HPH', pod: 'Osaka', pod_code: 'JPOSA', days: 8, km: 4200, cost: '$1,500-1,900' },
                        { pol: 'Cái Mép - Thị Vải', pol_code: 'CMP', pod: 'Tokyo', pod_code: 'JPTYO', days: 9, km: 4500, cost: '$1,650-2,050' },
                        { pol: 'Đà Nẵng', pol_code: 'DAD', pod: 'Kobe', pod_code: 'JPUKB', days: 8, km: 4100, cost: '$1,550-1,950' }
                    ]
                },
                {
                    value: 'ocean_lcl',
                    label: 'Đường Biển — LCL',
                    days: '9-15',
                    share: 13,
                    risk_level: 'medium',
                    risk_score: 5.0,
                    routes: [
                        { pol: 'Cái Mép - Thị Vải', pol_code: 'CMP', pod: 'Yokohama', pod_code: 'JPYOK', days: 12, km: 4400, cost: '$130-180/m³' }
                    ]
                },
                {
                    value: 'air_general',
                    label: 'Hàng Không — General',
                    hours: '5-7',
                    share: 7,
                    risk_level: 'very_low',
                    risk_score: 1.5,
                    routes: [
                        { pol: 'Nội Bài (HAN)', pol_code: 'HAN', pod: 'Narita (NRT)', pod_code: 'NRT', hours: 5, km: 4300, cost: '$4.0-6.0/kg' },
                        { pol: 'Tân Sơn Nhất (SGN)', pol_code: 'SGN', pod: 'Kansai (KIX)', pod_code: 'KIX', hours: 5, km: 4200, cost: '$4.2-6.2/kg' }
                    ]
                }
            ]
        },
        
        // ===== 5. VIETNAM → EU (NETHERLANDS/GERMANY) =====
        'vn_eu': {
            name: 'Vietnam → Europe (NL/DE)',
            name_vi: 'Việt Nam → Châu Âu',
            flag: '🇻🇳 → 🇪🇺',
            transport_modes: [
                {
                    value: 'ocean_fcl',
                    label: 'Đường Biển — FCL',
                    days: '32-38',
                    share: 93,
                    default: true,
                    risk_level: 'low',
                    risk_score: 3.5,
                    routes: [
                        { pol: 'Cái Mép - Thị Vải', pol_code: 'CMP', pod: 'Rotterdam', pod_code: 'NLRTM', days: 35, km: 15800, cost: '$6,500-8,200' },
                        { pol: 'Cái Mép - Thị Vải', pol_code: 'CMP', pod: 'Hamburg', pod_code: 'DEHAM', days: 36, km: 16200, cost: '$6,600-8,400' },
                        { pol: 'Hải Phòng', pol_code: 'HPH', pod: 'Bremerhaven', pod_code: 'DEBRV', days: 38, km: 16500, cost: '$6,600-8,400' },
                        { pol: 'Cái Mép - Thị Vải', pol_code: 'CMP', pod: 'Antwerp', pod_code: 'BEANR', days: 35, km: 15900, cost: '$6,600-8,400' }
                    ]
                },
                {
                    value: 'ocean_lcl',
                    label: 'Đường Biển — LCL',
                    days: '35-42',
                    share: 5,
                    risk_level: 'medium',
                    risk_score: 5.5,
                    routes: [
                        { pol: 'Cái Mép - Thị Vải', pol_code: 'CMP', pod: 'Rotterdam', pod_code: 'NLRTM', days: 38, km: 15800, cost: '$200-280/m³' }
                    ]
                },
                {
                    value: 'air_general',
                    label: 'Hàng Không — General',
                    hours: '14-16',
                    share: 1.5,
                    risk_level: 'very_low',
                    risk_score: 1.5,
                    routes: [
                        { pol: 'Tân Sơn Nhất (SGN)', pol_code: 'SGN', pod: 'Amsterdam (AMS)', pod_code: 'AMS', hours: 14, km: 9800, cost: '$6.5-9.0/kg' },
                        { pol: 'Nội Bài (HAN)', pol_code: 'HAN', pod: 'Frankfurt (FRA)', pod_code: 'FRA', hours: 14, km: 9900, cost: '$6.8-9.2/kg' }
                    ]
                },
                {
                    value: 'rail_china_europe',
                    label: 'Đường Sắt (Liên vận VN-TQ-EU)',
                    days: '18-25',
                    share: 0.5,
                    risk_level: 'medium',
                    risk_score: 4.0,
                    description: 'Tuyến mới 2025, qua TQ-Kazakhstan',
                    routes: [
                        { pol: 'Hà Nội (Rail)', pol_code: 'HAN', pod: 'Rotterdam', pod_code: 'NLRTM', days: 22, km: 14000, cost: '$4,800-6,200' },
                        { pol: 'Hà Nội (Rail)', pol_code: 'HAN', pod: 'Hamburg', pod_code: 'DEHAM', days: 23, km: 14200, cost: '$2,900-3,600' }
                    ]
                }
            ]
        },
        
        // ===== 6. VIETNAM → HONG KONG =====
        'vn_hk': {
            name: 'Vietnam → Hong Kong',
            name_vi: 'Việt Nam → Hồng Kông',
            flag: '🇻🇳 → 🇭🇰',
            transport_modes: [
                {
                    value: 'ocean_fcl',
                    label: 'Đường Biển — FCL',
                    days: '1-3',
                    share: 60,
                    default: true,
                    risk_level: 'low',
                    risk_score: 2.0,
                    routes: [
                        { pol: 'Cái Mép - Thị Vải', pol_code: 'CMP', pod: 'Hong Kong', pod_code: 'HKHKG', days: 2, km: 900, cost: '$650-900' },
                        { pol: 'Hải Phòng', pol_code: 'HPH', pod: 'Hong Kong', pod_code: 'HKHKG', days: 3, km: 1200, cost: '$900-1,200' }
                    ]
                },
                {
                    value: 'ocean_lcl',
                    label: 'Đường Biển — LCL',
                    days: '3-5',
                    share: 10,
                    risk_level: 'medium',
                    risk_score: 4.5,
                    routes: [
                        { pol: 'Cái Mép - Thị Vải', pol_code: 'CMP', pod: 'Hong Kong', pod_code: 'HKHKG', days: 3, km: 900, cost: '$70-100/m³' }
                    ]
                },
                {
                    value: 'road_ftl',
                    label: 'Đường Bộ — FTL',
                    days: '2-4',
                    share: 15,
                    risk_level: 'low',
                    risk_score: 3.0,
                    routes: [
                        { pol: 'Hà Nội', pol_code: 'HAN', pod: 'Hong Kong (qua Shenzhen)', pod_code: 'HKG', days: 3, km: 1600, cost: '$1,000-1,400' }
                    ]
                },
                {
                    value: 'rail_container',
                    label: 'Đường Sắt — Container',
                    days: '2-4',
                    share: 10,
                    risk_level: 'low',
                    risk_score: 3.0,
                    routes: [
                        { pol: 'Yên Viên (Rail)', pol_code: 'YV', pod: 'Shenzhen', pod_code: 'SZN', days: 3, km: 2000, cost: '$800-1,200' }
                    ]
                },
                {
                    value: 'air_general',
                    label: 'Hàng Không — General',
                    hours: '2',
                    share: 5,
                    risk_level: 'very_low',
                    risk_score: 1.0,
                    routes: [
                        { pol: 'Tân Sơn Nhất (SGN)', pol_code: 'SGN', pod: 'Hong Kong (HKG)', pod_code: 'HKG', hours: 2, km: 1100, cost: '$3.0-5.0/kg' }
                    ]
                }
            ]
        },
        
        // ===== 7. VIETNAM → INDIA =====
        'vn_in': {
            name: 'Vietnam → India',
            name_vi: 'Việt Nam → Ấn Độ',
            flag: '🇻🇳 → 🇮🇳',
            transport_modes: [
                {
                    value: 'ocean_fcl',
                    label: 'Đường Biển — FCL',
                    days: '7-14',
                    share: 95,
                    default: true,
                    risk_level: 'low',
                    risk_score: 3.0,
                    routes: [
                        { pol: 'Chu Lai', pol_code: 'CLA', pod: 'Chennai', pod_code: 'INMAA', days: 10, km: 4300, cost: '$1,300-1,800' },
                        { pol: 'Cái Mép - Thị Vải', pol_code: 'CMP', pod: 'Mumbai', pod_code: 'INBOM', days: 12, km: 4700, cost: '$1,300-1,800' },
                        { pol: 'Hải Phòng', pol_code: 'HPH', pod: 'Kolkata', pod_code: 'INCCU', days: 8, km: 3800, cost: '$1,400-1,900' }
                    ]
                },
                {
                    value: 'ocean_lcl',
                    label: 'Đường Biển — LCL',
                    days: '10-18',
                    share: 4,
                    risk_level: 'medium',
                    risk_score: 5.0,
                    routes: [
                        { pol: 'Cái Mép - Thị Vải', pol_code: 'CMP', pod: 'Mumbai', pod_code: 'INBOM', days: 14, km: 4700, cost: '$120-170/m³' }
                    ]
                },
                {
                    value: 'air_general',
                    label: 'Hàng Không — General',
                    hours: '5-7',
                    share: 1,
                    risk_level: 'very_low',
                    risk_score: 1.5,
                    routes: [
                        { pol: 'Nội Bài (HAN)', pol_code: 'HAN', pod: 'Delhi (DEL)', pod_code: 'DEL', hours: 5, km: 4000, cost: '$4.5-6.5/kg' },
                        { pol: 'Tân Sơn Nhất (SGN)', pol_code: 'SGN', pod: 'Mumbai (BOM)', pod_code: 'BOM', hours: 6, km: 4600, cost: '$4.8-6.8/kg' }
                    ]
                }
            ]
        },
        
        // ===== 8. VIETNAM → THAILAND =====
        'vn_th': {
            name: 'Vietnam → Thailand',
            name_vi: 'Việt Nam → Thái Lan',
            flag: '🇻🇳 → 🇹🇭',
            transport_modes: [
                {
                    value: 'road_ftl',
                    label: 'Đường Bộ — FTL',
                    hours: '16-36',
                    share: 60,
                    default: true,
                    risk_level: 'low',
                    risk_score: 3.5,
                    routes: [
                        { pol: 'TP.HCM', pol_code: 'SGN', pod: 'Bangkok (qua Mộc Bài)', pod_code: 'BKK', hours: 24, km: 900, cost: '$950-1,350' },
                        { pol: 'Hà Nội', pol_code: 'HAN', pod: 'Bangkok (qua Lào)', pod_code: 'BKK', hours: 36, km: 1400, cost: '$1,100-1,500' }
                    ]
                },
                {
                    value: 'road_ltl',
                    label: 'Đường Bộ — LTL',
                    hours: '24-48',
                    share: 15,
                    risk_level: 'medium',
                    risk_score: 5.5,
                    routes: [
                        { pol: 'TP.HCM', pol_code: 'SGN', pod: 'Bangkok', pod_code: 'BKK', hours: 30, km: 900, cost: '$0.4-0.7/kg' }
                    ]
                },
                {
                    value: 'ocean_fcl',
                    label: 'Đường Biển — FCL',
                    days: '5-8',
                    share: 20,
                    risk_level: 'low',
                    risk_score: 2.5,
                    routes: [
                        { pol: 'Cái Mép - Thị Vải', pol_code: 'CMP', pod: 'Laem Chabang', pod_code: 'THLCH', days: 6, km: 900, cost: '$850-1,200' }
                    ]
                },
                {
                    value: 'air_general',
                    label: 'Hàng Không — General',
                    hours: '1.5',
                    share: 5,
                    risk_level: 'very_low',
                    risk_score: 1.0,
                    routes: [
                        { pol: 'Tân Sơn Nhất (SGN)', pol_code: 'SGN', pod: 'Bangkok (BKK)', pod_code: 'BKK', hours: 1.5, km: 750, cost: '$2.5-4.5/kg' }
                    ]
                }
            ]
        },
        
        // ===== 9. VIETNAM → TAIWAN =====
        'vn_tw': {
            name: 'Vietnam → Taiwan',
            name_vi: 'Việt Nam → Đài Loan',
            flag: '🇻🇳 → 🇹🇼',
            transport_modes: [
                {
                    value: 'ocean_fcl',
                    label: 'Đường Biển — FCL',
                    days: '2-5',
                    share: 85,
                    default: true,
                    risk_level: 'low',
                    risk_score: 2.0,
                    routes: [
                        { pol: 'Hải Phòng', pol_code: 'HPH', pod: 'Kaohsiung', pod_code: 'TWKHH', days: 3, km: 1900, cost: '$950-1,300' },
                        { pol: 'Cái Mép - Thị Vải', pol_code: 'CMP', pod: 'Keelung', pod_code: 'TWKEL', days: 4, km: 2100, cost: '$1,300-1,700' },
                        { pol: 'Đà Nẵng', pol_code: 'DAD', pod: 'Taichung', pod_code: 'TWTXG', days: 3, km: 1800, cost: '$1,250-1,650' }
                    ]
                },
                {
                    value: 'ocean_lcl',
                    label: 'Đường Biển — LCL',
                    days: '4-7',
                    share: 5,
                    risk_level: 'medium',
                    risk_score: 4.5,
                    routes: [
                        { pol: 'Hải Phòng', pol_code: 'HPH', pod: 'Kaohsiung', pod_code: 'TWKHH', days: 5, km: 1900, cost: '$90-130/m³' }
                    ]
                },
                {
                    value: 'air_general',
                    label: 'Hàng Không — General',
                    hours: '3-4',
                    share: 10,
                    risk_level: 'very_low',
                    risk_score: 1.5,
                    routes: [
                        { pol: 'Nội Bài (HAN)', pol_code: 'HAN', pod: 'Đào Viên (TPE)', pod_code: 'TPE', hours: 3, km: 1900, cost: '$3.5-5.5/kg' },
                        { pol: 'Tân Sơn Nhất (SGN)', pol_code: 'SGN', pod: 'Cao Hùng (KHH)', pod_code: 'KHH', hours: 3, km: 2000, cost: '$3.8-5.8/kg' }
                    ]
                }
            ]
        },
        
        // ===== 10. DOMESTIC (NỘI ĐỊA) =====
        'domestic': {
            name: 'Domestic Vietnam',
            name_vi: 'Nội Địa Việt Nam',
            flag: '🇻🇳 Nội Địa',
            transport_modes: [
                {
                    value: 'road_ftl',
                    label: 'Đường Bộ — FTL',
                    days: '1-3',
                    share: 85,
                    default: true,
                    risk_level: 'low',
                    risk_score: 3.0,
                    routes: [
                        { pol: 'Hà Nội', pol_code: 'HAN', pod: 'TP. Hồ Chí Minh', pod_code: 'SGN', days: 2, km: 1700, cost: '$1,400-1,800' },
                        { pol: 'TP. Hồ Chí Minh', pol_code: 'SGN', pod: 'Đà Nẵng', pod_code: 'DAD', days: 1, km: 900, cost: '$700-1,000' },
                        { pol: 'Hà Nội', pol_code: 'HAN', pod: 'Hải Phòng', pod_code: 'HPH', hours: 3, km: 120, cost: '$150-250' }
                    ]
                },
                {
                    value: 'road_ltl',
                    label: 'Đường Bộ — LTL',
                    days: '2-4',
                    share: 10,
                    risk_level: 'medium',
                    risk_score: 5.0,
                    routes: [
                        { pol: 'Hà Nội', pol_code: 'HAN', pod: 'TP. Hồ Chí Minh', pod_code: 'SGN', days: 3, km: 1700, cost: '$0.3-0.5/kg' }
                    ]
                },
                {
                    value: 'rail_container',
                    label: 'Đường Sắt — Container',
                    days: '2-4',
                    share: 3,
                    risk_level: 'low',
                    risk_score: 3.5,
                    routes: [
                        { pol: 'Hà Nội (Ga Yên Viên)', pol_code: 'YV', pod: 'TP.HCM (Ga Sài Gòn)', pod_code: 'SGN', days: 3, km: 1700, cost: '$1,100-1,500' }
                    ]
                },
                {
                    value: 'air_general',
                    label: 'Hàng Không — General',
                    hours: '2',
                    share: 2,
                    risk_level: 'very_low',
                    risk_score: 1.0,
                    routes: [
                        { pol: 'Nội Bài (HAN)', pol_code: 'HAN', pod: 'Tân Sơn Nhất (SGN)', pod_code: 'SGN', hours: 2, km: 1170, cost: '$2.0-4.0/kg' }
                    ]
                }
            ]
        }
    },
    
    /**
     * ========================================
     * PART 3: CARRIER DATA BY ROUTE
     * ========================================
     */
    carriersByRoute: {
        'vn_cn': [
            { name: 'Maersk', rating: 4.8, votes: 28420, color: '#10B981', note: 'Lịch ổn định 92%, tracking tốt, giá hợp lý; hơi nhiều phụ phí nếu tắc Shenzhen.', services: ['FCL', 'LCL', 'feeder'] },
            { name: 'MSC', rating: 4.6, votes: 31250, color: '#10B981', note: 'Nhiều chuyến, giá thấp, mạnh LCL; đôi lúc tắc Shanghai mùa cao điểm.', services: ['FCL', 'LCL'] },
            { name: 'COSCO/OOCL', rating: 4.5, votes: 26500, color: '#3B82F6', note: 'Giá tốt nhất, nối transit TQ mạnh; road-border đôi lúc chậm thủ tục.', services: ['FCL', 'bulk'] },
            { name: 'Evergreen', rating: 4.4, votes: 22340, color: '#3B82F6', note: 'Nhanh từ HPH/Ningbo, ổn định; phù hợp hàng điện tử.', services: ['FCL'] },
            { name: 'Wan Hai', rating: 4.3, votes: 6540, color: '#3B82F6', note: 'Rẻ, linh hoạt nội Á; ít slot mùa Tết.', services: ['FCL', 'LCL'] }
        ],
        'vn_us': [
            { name: 'Maersk', rating: 4.7, votes: 28420, color: '#10B981', note: 'On-time cao dù tắc cảng, tracking mạnh; Q4 thường +2–4 ngày.', services: ['FCL', 'LCL'] },
            { name: 'MSC', rating: 4.6, votes: 31250, color: '#10B981', note: 'Giá cạnh tranh, nhiều chuyến; thủ tục NY đôi lúc chậm.', services: ['FCL', 'LCL'] },
            { name: 'CMA CGM', rating: 4.5, votes: 18760, color: '#3B82F6', note: 'Nhanh từ Cái Mép, tốt hàng DG; ít phụ phí.', services: ['FCL', 'LCL'] },
            { name: 'ONE', rating: 4.4, votes: 15680, color: '#3B82F6', note: 'Ổn định, mạnh Seattle; tracking realtime tốt.', services: ['FCL'] },
            { name: 'Evergreen', rating: 4.3, votes: 22340, color: '#3B82F6', note: 'Giá hợp lý, phù hợp East Coast; LA đôi khi tắc.', services: ['FCL', 'LCL'] }
        ],
        'vn_kr': [
            { name: 'HMM', rating: 4.7, votes: 9870, color: '#10B981', note: 'Nhanh nhất (5 ngày), on-time 93%; tracking chính xác.', services: ['FCL', 'LCL'] },
            { name: 'Maersk', rating: 4.6, votes: 28420, color: '#10B981', note: 'Schedule tốt, ít delay; giá ổn định.', services: ['FCL'] },
            { name: 'Evergreen', rating: 4.5, votes: 22340, color: '#3B82F6', note: 'Giá rẻ, hợp Incheon; tốt cho điện tử.', services: ['FCL', 'LCL'] },
            { name: 'Yang Ming', rating: 4.4, votes: 8760, color: '#3B82F6', note: 'Cạnh tranh, nhưng ít chuyến từ Đà Nẵng.', services: ['FCL'] }
        ],
        'vn_jp': [
            { name: 'NYK', rating: 4.8, votes: 11200, color: '#10B981', note: 'On-time 94%, dịch vụ chuẩn Nhật; giá cao nhưng đáng.', services: ['FCL', 'LCL'] },
            { name: 'K Line', rating: 4.6, votes: 9800, color: '#10B981', note: 'Nhanh cho Kobe, ít hư hỏng; giá cao hơn mặt bằng.', services: ['FCL'] },
            { name: 'Maersk', rating: 4.5, votes: 28420, color: '#3B82F6', note: 'Rẻ hơn các hãng Nhật; tracking tốt.', services: ['FCL', 'LCL'] },
            { name: 'MOL', rating: 4.4, votes: 8900, color: '#3B82F6', note: 'Tốt cho Osaka; phụ phí hơi cao.', services: ['FCL'] }
        ],
        'vn_eu': [
            { name: 'Maersk', rating: 4.7, votes: 28420, color: '#10B981', note: 'Ổn dù reroute, tracking EU mạnh; đáng tin nhất tuyến EU.', services: ['FCL', 'LCL'] },
            { name: 'MSC', rating: 4.6, votes: 31250, color: '#10B981', note: 'Giá tốt, nhiều chuyến; Hamburg hay bị delay.', services: ['FCL'] },
            { name: 'CMA CGM', rating: 4.5, votes: 18760, color: '#3B82F6', note: 'Tốt cho reefer, on-time ổn định.', services: ['FCL', 'LCL'] },
            { name: 'Hapag-Lloyd', rating: 4.4, votes: 13450, color: '#3B82F6', note: 'Mạnh heavy cargo; Suez ảnh hưởng nhiều.', services: ['FCL'] }
        ],
        'vn_hk': [
            { name: 'OOCL', rating: 4.6, votes: 15200, color: '#10B981', note: 'Rất nhanh (2 ngày), on-time cao.', services: ['FCL', 'LCL'] },
            { name: 'Maersk', rating: 4.5, votes: 28420, color: '#3B82F6', note: 'Ổn định, tracking tốt; giá trung bình.', services: ['FCL'] },
            { name: 'COSCO/OOCL', rating: 4.4, votes: 26500, color: '#3B82F6', note: 'Rẻ nhất tuyến HK; phù hợp LCL.', services: ['FCL', 'LCL'] }
        ],
        'vn_in': [
            { name: 'Maersk', rating: 4.5, votes: 28420, color: '#3B82F6', note: 'Nhanh, ít delay; hợp Chennai.', services: ['FCL', 'LCL'] },
            { name: 'MSC', rating: 4.4, votes: 31250, color: '#3B82F6', note: 'Giá rẻ Mumbai; thủ tục Ấn hơi chậm.', services: ['FCL'] },
            { name: 'Evergreen', rating: 4.3, votes: 22340, color: '#3B82F6', note: 'Tốt cho Kolkata; mạnh hàng dệt.', services: ['FCL', 'LCL'] }
        ],
        'vn_th': [
            { name: 'RCL', rating: 4.6, votes: 3210, color: '#10B981', note: 'Rất nhanh, kết nối road linh hoạt.', services: ['FCL', 'LCL'] },
            { name: 'Maersk', rating: 4.5, votes: 28420, color: '#3B82F6', note: 'Tích hợp tốt vào Bangkok; giá ổn.', services: ['FCL'] },
            { name: 'Wan Hai', rating: 4.4, votes: 6540, color: '#3B82F6', note: 'Rẻ, phù hợp intra-Asia.', services: ['FCL', 'LCL'] }
        ],
        'vn_tw': [
            { name: 'Evergreen', rating: 4.7, votes: 22340, color: '#10B981', note: 'Nhanh nhất, on-time 93%; tracking chuẩn Taiwan.', services: ['FCL', 'LCL'] },
            { name: 'Yang Ming', rating: 4.6, votes: 8760, color: '#10B981', note: 'Ổn cho Taichung; mạnh hàng điện tử.', services: ['FCL'] },
            { name: 'Wan Hai', rating: 4.5, votes: 6540, color: '#3B82F6', note: 'Rẻ, ít delay; linh hoạt.', services: ['FCL', 'LCL'] }
        ],
        'domestic': [
            { name: 'ViettelPost', rating: 4.6, votes: 125000, color: '#10B981', note: 'Nhanh, mạng lưới rộng; ổn cho HN–SGN.', services: ['Road LTL', 'FTL'] },
            { name: 'Vietnam Airlines', rating: 4.5, votes: 45000, color: '#3B82F6', note: 'An toàn, đúng giờ; chi phí cao.', services: ['Air general'] },
            { name: 'Giao Hàng Nhanh (GHN)', rating: 4.4, votes: 89000, color: '#3B82F6', note: 'Tốt e-com, tracking app mạnh.', services: ['Road express'] },
            { name: 'Vietnam Railway', rating: 4.3, votes: 12000, color: '#3B82F6', note: 'Rẻ Bắc–Nam; hơi chậm.', services: ['Rail container'] }
        ]
    },
    
    /**
     * Get carriers for a specific route
     */
    getCarriersByRoute: function(routeKey) {
        return this.carriersByRoute[routeKey] || [];
    },
    
    /**
     * ========================================
     * PART 4: HELPER FUNCTIONS
     * ========================================
     */
    
    /**
     * Get all available routes
     */
    getAllRoutes: function() {
        return Object.keys(this.routes);
    },
    
    /**
     * Get route data by key
     */
    getRoute: function(routeKey) {
        return this.routes[routeKey] || null;
    },
    
    /**
     * Get transport modes for a route
     */
    getTransportModes: function(routeKey) {
        const route = this.getRoute(routeKey);
        return route ? route.transport_modes : [];
    },
    
    /**
     * Get risk level color
     */
    getRiskColor: function(riskLevel) {
        const colors = {
            'very_low': '#00ffc3',
            'low': '#3b82f6',
            'medium': '#fbbf24',
            'high': '#f87171',
            'very_high': '#ef4444'
        };
        return colors[riskLevel] || '#71717a';
    },
    
    /**
     * Get risk label in Vietnamese
     */
    getRiskLabel: function(riskLevel) {
        const labels = {
            'very_low': 'Rất Thấp',
            'low': 'Thấp',
            'medium': 'Trung Bình',
            'high': 'Cao',
            'very_high': 'Rất Cao'
        };
        return labels[riskLevel] || 'N/A';
    },
    
    /**
     * Calculate distance between ports
     */
    calculateDistance: function(polCode, podCode, routeKey) {
        const route = this.getRoute(routeKey);
        if (!route) return null;
        
        for (const mode of route.transport_modes) {
            if (mode.routes) {
                const matchingRoute = mode.routes.find(r => 
                    r.pol_code === polCode && r.pod_code === podCode
                );
                if (matchingRoute) return matchingRoute.km;
            }
        }
        return null;
    },
    
    /**
     * Convert raw transport_modes routes → standardized service routes
     * Required by input_controller_v20.js
     */
    getServiceRoutes: function(tradeLane, modePrefix) {
        const route = this.getRoute(tradeLane);
        if (!route || !route.transport_modes) return [];
        
        const modeKey = {
            'SEA': 'ocean',
            'AIR': 'air',
            'ROAD': 'road',
            'RAIL': 'rail'
        }[modePrefix];
        
        if (!modeKey) return [];
        
        // Extract origin/destination country codes from trade lane key
        // e.g., 'vn_cn' → originCountry: 'VN', destinationCountry: 'CN'
        const [origin, destination] = tradeLane.split('_').map(c => c.toUpperCase());
        
        let results = [];
        
        route.transport_modes
            .filter(m => m.value.startsWith(modeKey))
            .forEach((mode) => {
                if (mode.routes) {
                    mode.routes.forEach((r, idx) => {
                        results.push({
                            route_id: `${tradeLane}_${mode.value}_${idx}`,
                            route_name: `${r.pol} → ${r.pod}`,
                            
                            pol: r.pol,
                            pod: r.pod,
                            pol_code: r.pol_code,
                            pod_code: r.pod_code,
                            
                            originCountry: origin,
                            destinationCountry: destination,
                            
                            transit_days: r.days || null,
                            transit_hours: r.hours || null,
                            schedule: "Weekly",
                            reliability: Math.floor(85 + Math.random() * 10),
                            seasonality: 1.00,
                            carrier: "Maersk",
                            
                            km: r.km || null,
                            raw_cost: r.cost || null,
                            cost: this._estimateCost(r),
                            
                            mode: mode.value,
                            mode_label: mode.label
                        });
                    });
                }
            });
        
        return results;
    },
    
    /** Estimate cost fallback */
    _estimateCost: function(r) {
        const base = 1000;
        const days = r.days || 7;
        return Math.round(base + days * 40);
    },
    
    /**
     * ========================================
     * PART 5: CONTAINER COMPATIBILITY SCORES
     * ========================================
     * Container Compatibility Score (0-10)
     */
    containerCompatibility: {
        // Hàng Hóa Thông Thường
        "thong_thuong": {
            "20ft": 9.8, "40ft": 10.0, "40hc": 9.9, "45hc": 9.5, 
            "reefer": 4.0, "opentop": 6.0, "flatrack": 5.0, 
            "isotank": 1.0, "bulk": 3.0
        },
        
        // Điện Tử
        "dien_tu": {
            "20ft": 10.0, "40ft": 9.8, "40hc": 9.9, "45hc": 9.7, 
            "reefer": 7.0, "opentop": 2.0, "flatrack": 3.0, 
            "isotank": 1.0, "bulk": 1.0
        },
        
        // Thực Phẩm & Đồ Uống (khô)
        "thuc_pham_do_uong": {
            "20ft": 9.5, "40ft": 10.0, "40hc": 9.8, "45hc": 9.0, 
            "reefer": 8.5, "opentop": 7.0, "flatrack": 4.0, 
            "isotank": 2.0, "bulk": 6.0
        },
        
        // May Mặc / Dệt May
        "may_mac_det_may": {
            "20ft": 8.0, "40ft": 9.0, "40hc": 10.0, "45hc": 9.8, 
            "reefer": 3.0, "opentop": 5.0, "flatrack": 6.0, 
            "isotank": 1.0, "bulk": 2.0
        },
        
        // Nông Sản
        "nong_san": {
            "20ft": 9.0, "40ft": 9.5, "40hc": 9.2, "45hc": 8.0, 
            "reefer": 6.0, "opentop": 8.5, "flatrack": 7.0, 
            "isotank": 1.0, "bulk": 9.0
        },
        
        // Hàng Lạnh / Đông Lạnh
        "hang_lanh_dong_lanh": {
            "20ft": 3.0, "40ft": 3.5, "40hc": 4.0, "45hc": 2.0, 
            "reefer": 10.0, "opentop": 1.0, "flatrack": 1.0, 
            "isotank": 2.0, "bulk": 1.0
        },
        
        // Hóa Chất (không DG)
        "hoa_chat": {
            "20ft": 7.0, "40ft": 8.0, "40hc": 7.5, "45hc": 6.0, 
            "reefer": 4.0, "opentop": 5.0, "flatrack": 6.0, 
            "isotank": 10.0, "bulk": 8.0
        },
        
        // Máy Móc Thiết Bị
        "may_moc_thiet_bi": {
            "20ft": 7.5, "40ft": 8.5, "40hc": 8.0, "45hc": 7.0, 
            "reefer": 2.0, "opentop": 9.5, "flatrack": 10.0, 
            "isotank": 1.0, "bulk": 3.0
        },
        
        // Hàng Dễ Vỡ
        "hang_de_vo": {
            "20ft": 9.8, "40ft": 9.5, "40hc": 9.0, "45hc": 8.0, 
            "reefer": 6.0, "opentop": 3.0, "flatrack": 4.0, 
            "isotank": 1.0, "bulk": 1.0
        },
        
        // Linh Kiện Ô Tô
        "linh_kien_o_to": {
            "20ft": 8.5, "40ft": 9.5, "40hc": 9.8, "45hc": 9.0, 
            "reefer": 3.0, "opentop": 7.0, "flatrack": 8.5, 
            "isotank": 1.0, "bulk": 2.0
        },
        
        // Hàng Nguy Hiểm (DG)
        "hang_nguy_hiem_dg": {
            "20ft": 8.0, "40ft": 8.5, "40hc": 8.0, "45hc": 6.0, 
            "reefer": 5.0, "opentop": 4.0, "flatrack": 7.0, 
            "isotank": 9.5, "bulk": 3.0
        },
        
        // Dược Phẩm
        "duoc_pham": {
            "20ft": 4.0, "40ft": 4.5, "40hc": 5.0, "45hc": 3.0, 
            "reefer": 10.0, "opentop": 1.0, "flatrack": 1.0, 
            "isotank": 2.0, "bulk": 1.0
        }
    },
    
    /**
     * ========================================
     * PART 6: CARRIER RATINGS BY ROUTE
     * ========================================
     */
    carrierRatings: {
        "vn_cn": [
            { name: "Maersk", rating: 4.8, ontime: 92, price: "$950-1,300", note: "Schedule hàng tuần ổn định, giá cạnh tranh, tracking tốt" },
            { name: "MSC", rating: 4.6, ontime: 88, price: "$900-1,200", note: "Nhiều chuyến/tuần, giá thấp, mạnh LCL ghép" },
            { name: "COSCO", rating: 4.5, ontime: 90, price: "$800-1,100", note: "Rẻ nhất, tích hợp tốt với TQ transit" },
            { name: "Evergreen", rating: 4.4, ontime: 89, price: "$850-1,200", note: "Schedule từ HPH/Ningbo nhanh, ổn định" },
            { name: "Wan Hai", rating: 4.3, ontime: 85, price: "$700-1,000", note: "Giá địa phương rẻ, mạnh nội Á" }
        ],
        
        "vn_us": [
            { name: "Maersk", rating: 4.7, ontime: 90, price: "$4,800-6,200", note: "On-time 90% dù tắc LB, tracking AI tốt" },
            { name: "MSC", rating: 4.6, ontime: 87, price: "$4,700-6,000", note: "Giá cạnh tranh, nhiều chuyến/tuần" },
            { name: "CMA CGM", rating: 4.5, ontime: 88, price: "$4,800-6,100", note: "Mạnh direct từ CMP, nhanh cho hàng DG" },
            { name: "ONE", rating: 4.4, ontime: 89, price: "$4,900-6,200", note: "Ổn cho Seattle, tracking realtime" },
            { name: "Evergreen", rating: 4.3, ontime: 86, price: "$4,700-6,000", note: "Tốt cho East Coast" }
        ],
        
        "vn_kr": [
            { name: "HMM", rating: 4.7, ontime: 93, price: "$950-1,300", note: "Nhanh nhất (5 ngày), tracking Hàn chuẩn" },
            { name: "Maersk", rating: 4.6, ontime: 90, price: "$1,000-1,400", note: "Schedule hàng tuần, ổn định" },
            { name: "Evergreen", rating: 4.5, ontime: 88, price: "$950-1,300", note: "Giá rẻ, phù hợp hàng điện tử" },
            { name: "Yang Ming", rating: 4.4, ontime: 87, price: "$1,100-1,500", note: "Cạnh tranh nhưng ít chuyến từ DAD" }
        ],
        
        "vn_jp": [
            { name: "NYK", rating: 4.8, ontime: 94, price: "$1,400-1,800", note: "Chính xác, dịch vụ Nhật cao cấp" },
            { name: "K Line", rating: 4.6, ontime: 91, price: "$1,500-1,900", note: "Nhanh cho Kobe, ít hư hỏng" },
            { name: "Maersk", rating: 4.5, ontime: 89, price: "$1,400-1,800", note: "Rẻ hơn, tracking tốt" },
            { name: "MOL", rating: 4.4, ontime: 88, price: "$1,550-1,950", note: "Ổn cho Osaka" }
        ],
        
        "vn_eu": [
            { name: "Maersk", rating: 4.7, ontime: 88, price: "$6,500-8,200", note: "Đáng tin Rotterdam, tracking EU chuẩn" },
            { name: "MSC", rating: 4.6, ontime: 86, price: "$6,400-8,000", note: "Nhiều chuyến Antwerp" },
            { name: "CMA CGM", rating: 4.5, ontime: 87, price: "$6,500-8,200", note: "Mạnh Bremerhaven, tốt cho reefer" },
            { name: "Hapag-Lloyd", rating: 4.4, ontime: 85, price: "$6,600-8,400", note: "Chuyên heavy cargo" }
        ],
        
        "vn_hk": [
            { name: "OOCL", rating: 4.6, ontime: 92, price: "$650-900", note: "Nhanh 2 ngày, transit tốt" },
            { name: "Maersk", rating: 4.5, ontime: 90, price: "$700-950", note: "Ổn định, tracking realtime" },
            { name: "COSCO", rating: 4.4, ontime: 88, price: "$600-850", note: "Rẻ nhất, phù hợp LCL ghép" }
        ],
        
        "vn_in": [
            { name: "Maersk", rating: 4.5, ontime: 87, price: "$1,300-1,800", note: "Nhanh Chennai, ít delay" },
            { name: "MSC", rating: 4.4, ontime: 85, price: "$1,200-1,700", note: "Rẻ Mumbai" },
            { name: "Evergreen", rating: 4.3, ontime: 86, price: "$1,300-1,800", note: "Tốt cho Kolkata" }
        ],
        
        "vn_th": [
            { name: "RCL", rating: 4.6, ontime: 91, price: "$850-1,200", note: "Nhanh LCB, linh hoạt road" },
            { name: "Maersk", rating: 4.5, ontime: 89, price: "$900-1,300", note: "Tích hợp road BKK tốt" },
            { name: "Wan Hai", rating: 4.4, ontime: 87, price: "$800-1,100", note: "Mạnh intra-Asia" }
        ],
        
        "vn_tw": [
            { name: "Evergreen", rating: 4.7, ontime: 93, price: "$950-1,300", note: "Nhanh KHH, tracking Đài chuẩn" },
            { name: "Yang Ming", rating: 4.6, ontime: 90, price: "$1,000-1,400", note: "Ổn Taichung" },
            { name: "Wan Hai", rating: 4.5, ontime: 88, price: "$900-1,200", note: "Linh hoạt, ít delay" }
        ],
        
        "domestic_vn": [
            { name: "ViettelPost", rating: 4.6, ontime: 90, price: "$0.3-0.5/kg", note: "Mạng lưới rộng, nhanh HN-SGN" },
            { name: "Vietnam Airlines", rating: 4.5, ontime: 88, price: "$2-4/kg", note: "An toàn nhưng đắt" },
            { name: "GHN", rating: 4.4, ontime: 85, price: "$0.2-0.4/kg", note: "Tốt e-com, tracking app hay" },
            { name: "Vietnam Railway", rating: 4.3, ontime: 82, price: "$1,100-1,500", note: "Rẻ Bắc-Nam nhưng chậm" }
        ]
    },
    
    /**
     * ========================================
     * PART 7: SERVICE ROUTES (AI-ready dataset)
     * ========================================
     * Comprehensive service route objects generated from routes data
     * Each service route represents a concrete service with specific trade lane,
     * transport mode, POL/POD pair, carrier, container types, schedule, transit time,
     * seasonality profile, and reliability score.
     */
    
    /**
     * Helper function to generate seasonality index based on trade lane
     */
    _buildSeasonalityIndex: function(tradeLane, mode) {
        // Pacific lanes (vn_us, vn_jp, vn_kr, vn_tw) - peak season Jul-Oct
        if (['vn_us', 'vn_jp', 'vn_kr', 'vn_tw'].includes(tradeLane)) {
            return {
                jan: 1.03, feb: 1.05, mar: 1.00, apr: 0.99,
                may: 1.00, jun: 1.02, jul: 1.04, aug: 1.05,
                sep: 1.04, oct: 1.02, nov: 0.98, dec: 1.01
            };
        }
        
        // EU via Cape route (vn_eu) - elevated Q1 and Q4
        if (tradeLane === 'vn_eu') {
            return {
                jan: 1.04, feb: 1.03, mar: 1.01, apr: 0.98,
                may: 0.97, jun: 0.98, jul: 0.99, aug: 1.00,
                sep: 1.01, oct: 1.02, nov: 1.04, dec: 1.05
            };
        }
        
        // India/monsoon (vn_in) - higher delays Jun-Sep
        if (tradeLane === 'vn_in') {
            return {
                jan: 1.00, feb: 0.99, mar: 0.98, apr: 0.97,
                may: 0.98, jun: 1.05, jul: 1.06, aug: 1.05,
                sep: 1.03, oct: 1.00, nov: 0.99, dec: 1.01
            };
        }
        
        // Intra-Asia (vn_cn, vn_hk, vn_th, domestic) - relatively flat with peaks around Lunar New Year
        if (['vn_cn', 'vn_hk', 'vn_th', 'domestic'].includes(tradeLane)) {
            return {
                jan: 1.05, feb: 1.06, mar: 1.00, apr: 0.98,
                may: 0.99, jun: 1.00, jul: 1.01, aug: 1.00,
                sep: 0.99, oct: 1.00, nov: 1.01, dec: 1.03
            };
        }
        
        // Default flat profile
        return {
            jan: 1.00, feb: 1.00, mar: 1.00, apr: 1.00,
            may: 1.00, jun: 1.00, jul: 1.00, aug: 1.00,
            sep: 1.00, oct: 1.00, nov: 1.00, dec: 1.00
        };
    },
    
    /**
     * Helper function to get container types for a transport mode
     */
    _getContainerTypesForMode: function(mode) {
        if (mode === 'ocean_fcl') {
            return ['20ft', '40ft', '40hc'];
        }
        if (mode === 'ocean_lcl') {
            return ['20ft', '40ft'];
        }
        if (mode.includes('reefer') || mode === 'ocean_reefer' || mode === 'road_reefer' || mode === 'rail_reefer') {
            return ['reefer'];
        }
        if (mode === 'road_ftl' || mode === 'road_ltl' || mode === 'road_container') {
            return ['20ft', '40ft'];
        }
        if (mode === 'rail_container' || mode === 'rail_china_europe') {
            return ['20ft', '40ft', '40hc'];
        }
        if (mode === 'air_general' || mode === 'air_express') {
            return ['palletized', 'wooden_crates'];
        }
        // Default
        return ['20ft'];
    },
    
    /**
     * Helper function to get schedule for trade lane and mode
     */
    _getScheduleForRoute: function(tradeLane, mode) {
        const highVolumeLanes = ['vn_us', 'vn_eu', 'vn_cn', 'vn_jp', 'vn_kr', 'vn_tw'];
        const isHighVolume = highVolumeLanes.includes(tradeLane);
        
        if (mode === 'ocean_fcl' || mode === 'ocean_lcl') {
            return isHighVolume ? 'Weekly' : 'Weekly';
        }
        if (mode === 'rail_container' || mode === 'rail_china_europe') {
            return isHighVolume ? 'Weekly' : 'Biweekly';
        }
        if (mode === 'air_general' || mode === 'air_express') {
            return isHighVolume ? 'Daily' : 'Daily';
        }
        if (mode === 'road_ftl' || mode === 'road_ltl') {
            return 'Daily';
        }
        return 'Weekly';
    },
    
    /**
     * Helper function to get carrier abbreviation
     */
    _getCarrierAbbreviation: function(carrierName) {
        const abbrevMap = {
            'Maersk': 'MSK',
            'MSC': 'MSC',
            'CMA CGM': 'CMA',
            'COSCO': 'CSC',
            'COSCO/OOCL': 'CSC',
            'OOCL': 'OOC',
            'Evergreen': 'EVG',
            'Hapag-Lloyd': 'HPL',
            'ONE': 'ONE',
            'HMM': 'HMM',
            'Yang Ming': 'YML',
            'NYK': 'NYK',
            'K Line': 'KLN',
            'MOL': 'MOL',
            'Wan Hai': 'WHL',
            'RCL': 'RCL',
            'ViettelPost': 'VTP',
            'Vietnam Airlines': 'VNA',
            'GHN': 'GHN',
            'Giao Hàng Nhanh (GHN)': 'GHN',
            'Vietnam Railway': 'VNR'
        };
        return abbrevMap[carrierName] || carrierName.substring(0, 3).toUpperCase();
    },
    
    /**
     * Helper function to get mode abbreviation
     */
    _getModeAbbreviation: function(mode) {
        const modeMap = {
            'ocean_fcl': 'FCL',
            'ocean_lcl': 'LCL',
            'air_general': 'AIR',
            'air_express': 'AIR',
            'road_ftl': 'FTL',
            'road_ltl': 'LTL',
            'rail_container': 'RAIL',
            'rail_china_europe': 'RAIL',
            'rail_lcl': 'RAIL',
            'road_container': 'FTL'
        };
        return modeMap[mode] || mode.toUpperCase().substring(0, 4);
    },
    
    /**
     * Helper function to parse transit time (days or hours)
     */
    _parseTransitTime: function(routeObj) {
        if (routeObj.days !== undefined) {
            if (typeof routeObj.days === 'string') {
                // Handle ranges like "18-22" - take upper bound
                const parts = routeObj.days.split('-');
                return Math.max(1, parseInt(parts[parts.length - 1]) || 1);
            }
            return Math.max(1, parseInt(routeObj.days) || 1);
        }
        if (routeObj.hours !== undefined) {
            if (typeof routeObj.hours === 'string') {
                const parts = routeObj.hours.split('-');
                const hours = parseFloat(parts[parts.length - 1]) || 24;
                return Math.max(1, Math.round(hours / 24));
            }
            return Math.max(1, Math.round(parseFloat(routeObj.hours) / 24));
        }
        return 1;
    },
    
    /**
     * Helper function to get reliability from carrier ratings
     */
    _getReliabilityForCarrier: function(tradeLane, carrierName) {
        const ratings = this.carrierRatings[tradeLane] || this.carrierRatings['domestic_vn'] || [];
        const carrier = ratings.find(c => c.name === carrierName || c.name.includes(carrierName));
        
        if (!carrier) {
            return 0.85; // Default reliability
        }
        
        // Prefer ontime if available, else use rating
        let reliability;
        if (carrier.ontime !== undefined) {
            reliability = carrier.ontime / 100.0;
        } else {
            reliability = carrier.rating / 5.0;
        }
        
        // Clamp between 0.75 and 0.98
        return Math.max(0.75, Math.min(0.98, reliability));
    },
    
    serviceRoutes: [],
    
    /**
     * Get service routes for a specific trade lane
     */
    getServiceRoutesForTradeLane: function(tradeLaneKey) {
        return this.serviceRoutes.filter(r => r.trade_lane === tradeLaneKey);
    },
    
    /**
     * ========================================
     * PART 8: CONTAINER TYPE DESCRIPTIONS
     * ========================================
     */
    containerDescriptions: {
        "20ft": "Container khô 20 feet tiêu chuẩn - phù hợp hàng nhỏ, hàng nặng, dễ xếp dỡ",
        "40ft": "Container khô 40 feet tiêu chuẩn - tối ưu chi phí/khối, phổ biến nhất",
        "40hc": "Container cao 40 feet - tối ưu cho hàng nhẹ, cồng kềnh (dệt may, nội thất)",
        "45hc": "Container cao 45 feet - thể tích lớn nhất, phù hợp hàng thể tích cao",
        "reefer": "Container lạnh - chỉ dùng cho hàng đông lạnh, dược phẩm (phụ phí cao)",
        "opentop": "Container nóc mở - dùng cho hàng quá cao hoặc cần cẩu từ trên xuống",
        "flatrack": "Flat rack - không thành bên, dùng cho máy móc, thiết bị quá khổ",
        "isotank": "Iso tank - container chứa chất lỏng (hóa chất, dầu mỡ)",
        "bulk": "Bulk carrier - vận chuyển rời (gạo, than, quặng) - không container"
    },
    
    /**
     * Get container compatibility score
     */
    getContainerCompatibility: function(cargoType, containerType) {
        if (!this.containerCompatibility[cargoType]) return 0;
        return this.containerCompatibility[cargoType][containerType] || 0;
    },
    
    /**
     * Get carrier ratings for a route
     */
    getCarrierRatings: function(routeKey) {
        return this.carrierRatings[routeKey] || [];
    },
    
    /**
     * Get container description
     */
    getContainerDescription: function(containerType) {
        return this.containerDescriptions[containerType] || "Không có mô tả";
    },
    
    /**
     * ========================================
     * MAPPING FUNCTIONS: HTML Values <-> Logistics Keys
     * ========================================
     */
    
    /**
     * Convert HTML cargo type value to logistics key
     * HTML: "general", "electronics", "food_bev", etc.
     * Logistics: "thong_thuong", "dien_tu", "thuc_pham_do_uong", etc.
     */
    mapCargoTypeFromHTML: function(htmlValue) {
        const mapping = {
            'general': 'thong_thuong',
            'electronics': 'dien_tu',
            'food_bev': 'thuc_pham_do_uong',
            'garments': 'may_mac_det_may',
            'agriculture': 'nong_san',
            'refrigerated': 'hang_lanh_dong_lanh',
            'chemicals': 'hoa_chat',
            'machinery': 'may_moc_thiet_bi',
            'fragile': 'hang_de_vo',
            'auto_parts': 'linh_kien_o_to',
            'dg': 'hang_nguy_hiem_dg',
            'pharma': 'duoc_pham'
        };
        return mapping[htmlValue] || htmlValue; // Return original if not found
    },
    
    /**
     * Convert HTML container type value to logistics key
     * HTML: "20ft_standard", "40ft_standard", "40ft_highcube", etc.
     * Logistics: "20ft", "40ft", "40hc", "45hc", etc.
     */
    mapContainerTypeFromHTML: function(htmlValue) {
        const mapping = {
            '20ft_standard': '20ft',
            '40ft_standard': '40ft',
            '40ft_highcube': '40hc',
            '45ft_highcube': '45hc',
            'reefer': 'reefer',
            'open_top': 'opentop',
            'flat_rack': 'flatrack',
            'iso_tank': 'isotank',
            'bulk_container': 'bulk',
            'palletized': '20ft', // Default to 20ft for palletized
            'wooden_crates': '20ft' // Default to 20ft for wooden crates
        };
        return mapping[htmlValue] || htmlValue; // Return original if not found
    },
    
    /**
     * Convert logistics cargo key to HTML value (reverse mapping)
     */
    mapCargoTypeToHTML: function(logisticsKey) {
        const mapping = {
            'thong_thuong': 'general',
            'dien_tu': 'electronics',
            'thuc_pham_do_uong': 'food_bev',
            'may_mac_det_may': 'garments',
            'nong_san': 'agriculture',
            'hang_lanh_dong_lanh': 'refrigerated',
            'hoa_chat': 'chemicals',
            'may_moc_thiet_bi': 'machinery',
            'hang_de_vo': 'fragile',
            'linh_kien_o_to': 'auto_parts',
            'hang_nguy_hiem_dg': 'dg',
            'duoc_pham': 'pharma'
        };
        return mapping[logisticsKey] || logisticsKey;
    },
    
    /**
     * Convert logistics container key to HTML value (reverse mapping)
     */
    mapContainerTypeToHTML: function(logisticsKey) {
        const mapping = {
            '20ft': '20ft_standard',
            '40ft': '40ft_standard',
            '40hc': '40ft_highcube',
            '45hc': '45ft_highcube',
            'reefer': 'reefer',
            'opentop': 'open_top',
            'flatrack': 'flat_rack',
            'isotank': 'iso_tank',
            'bulk': 'bulk_container'
        };
        return mapping[logisticsKey] || logisticsKey;
    },
    
    /**
     * Convert HTML route value to logistics key
     * HTML: "domestic" -> Logistics: "domestic_vn"
     */
    mapRouteFromHTML: function(htmlValue) {
        if (htmlValue === 'domestic') {
            return 'domestic_vn';
        }
        return htmlValue; // Most routes match directly
    },
    
    /**
     * Convert logistics route key to HTML value (reverse mapping)
     */
    mapRouteToHTML: function(logisticsKey) {
        if (logisticsKey === 'domestic_vn') {
            return 'domestic';
        }
        return logisticsKey;
    },
    
    /**
     * ========================================
     * DETAILED ROUTE OPTIONS BY TRADE ROUTE
     * ========================================
     * Chi tiết các tuyến vận chuyển cho từng tuyến đường thương mại
     */
    detailedRoutes: {
        'vn_cn': [
            {
                id: 'vn_cn_direct_sea',
                name: 'Direct Sea (Cái Mép → Shenzhen)',
                transitTime: '4–7',
                surcharge: '+$200–400/40\' (BAF)',
                climateRisk: 'Thấp (typhoon cuối mùa)',
                conflictRisk: 'Thấp',
                usagePercent: '60% (Maersk, COSCO)',
                note: 'Ổn định nhất, 50% volume FCL'
            },
            {
                id: 'vn_cn_road_border',
                name: 'Road Border (Lào Cai → Hà Khẩu)',
                transitTime: '1–3',
                surcharge: '+$100–300 (customs)',
                climateRisk: 'Thấp',
                conflictRisk: 'Thấp',
                usagePercent: '25% (trucks)',
                note: 'Nhanh cho hàng lẻ, tăng 20% do rail chậm'
            },
            {
                id: 'vn_cn_rail',
                name: 'Rail (Yên Viên → Nam Ninh)',
                transitTime: '2–5',
                surcharge: '+$150–250 (rail fee)',
                climateRisk: 'Thấp',
                conflictRisk: 'Thấp',
                usagePercent: '10% (China Railway)',
                note: 'Rẻ hơn biển 30%, tăng mạnh 2025'
            },
            {
                id: 'vn_cn_feeder_hk',
                name: 'Feeder via HK (Cái Mép → HK → Shanghai)',
                transitTime: '7–10',
                surcharge: '+$300–500 (transit)',
                climateRisk: 'Trung bình',
                conflictRisk: 'Thấp',
                usagePercent: '5% (OOCL)',
                note: 'Dùng khi direct full, ít dùng do tắc HK'
            }
        ],
        'vn_us': [
            {
                id: 'vn_us_west_coast',
                name: 'West Coast Direct (Cái Mép → LA/Long Beach)',
                transitTime: '18–22',
                surcharge: '+$1,500–2,500/40\' (PSS + BAF)',
                climateRisk: 'Cao (La Niña bão)',
                conflictRisk: 'Thấp',
                usagePercent: '70% (MSC, CMA)',
                note: '85% đi Pacific direct, tắc LA cao'
            },
            {
                id: 'vn_us_east_coast_panama',
                name: 'East Coast via Panama (Cái Mép → NY via Panama)',
                transitTime: '35–40',
                surcharge: '+$2,000–3,000 (Panama fee)',
                climateRisk: 'Trung bình',
                conflictRisk: 'Thấp',
                usagePercent: '20% (Maersk)',
                note: 'Tăng 10% do drought Panama, phụ phí +$40/TEU'
            },
            {
                id: 'vn_us_transpacific_feeder',
                name: 'Trans-Pacific Feeder (HPH → Shanghai → NY)',
                transitTime: '25–30',
                surcharge: '+$1,000–1,800 (transshipment)',
                climateRisk: 'Cao',
                conflictRisk: 'Thấp',
                usagePercent: '8% (COSCO)',
                note: 'Dùng khi direct full, reroute do trade war'
            },
            {
                id: 'vn_us_air',
                name: 'Air Express (SGN → LAX)',
                transitTime: '2–5',
                surcharge: '+$4.5–6.5/kg',
                climateRisk: 'Không',
                conflictRisk: 'Không',
                usagePercent: '2% (FedEx)',
                note: 'Chỉ cho high-value, tăng do tariffs'
            }
        ],
        'vn_kr': [
            {
                id: 'vn_kr_direct_sea',
                name: 'Direct Sea (Cái Mép → Busan)',
                transitTime: '4–6',
                surcharge: '+$200–400/40\' (BAF)',
                climateRisk: 'Trung bình (typhoon)',
                conflictRisk: 'Thấp',
                usagePercent: '85% (HMM, Evergreen)',
                note: '90% direct, ổn định cao'
            },
            {
                id: 'vn_kr_feeder_hk',
                name: 'Feeder via HK (HPH → HK → Incheon)',
                transitTime: '6–8',
                surcharge: '+$300–500 (transit)',
                climateRisk: 'Trung bình',
                conflictRisk: 'Thấp',
                usagePercent: '10% (OOCL)',
                note: 'Dùng khi direct full, ít tắc'
            },
            {
                id: 'vn_kr_air',
                name: 'Air (HAN → ICN)',
                transitTime: '1–2',
                surcharge: '+$3.5–5.5/kg',
                climateRisk: 'Không',
                conflictRisk: 'Không',
                usagePercent: '5% (Korean Air)',
                note: 'Cho electronics, tăng 15% 2025'
            }
        ],
        'vn_jp': [
            {
                id: 'vn_jp_direct_sea',
                name: 'Direct Sea (Cái Mép → Yokohama)',
                transitTime: '7–10',
                surcharge: '+$300–500/40\' (BAF)',
                climateRisk: 'Cao (typhoon cuối mùa)',
                conflictRisk: 'Thấp',
                usagePercent: '80% (NYK, MOL)',
                note: '95% direct, ít biến động'
            },
            {
                id: 'vn_jp_feeder_busan',
                name: 'Feeder via Busan (HPH → Busan → Osaka)',
                transitTime: '9–12',
                surcharge: '+$400–600 (transit)',
                climateRisk: 'Cao',
                conflictRisk: 'Thấp',
                usagePercent: '15% (Evergreen)',
                note: 'Dùng cho volume nhỏ, ổn định'
            },
            {
                id: 'vn_jp_air',
                name: 'Air (SGN → NRT)',
                transitTime: '1–2',
                surcharge: '+$4.0–6.0/kg',
                climateRisk: 'Không',
                conflictRisk: 'Không',
                usagePercent: '5% (Vietnam Airlines)',
                note: 'Cho pharma/high-value'
            }
        ],
        'vn_eu': [
            {
                id: 'vn_eu_cape_good_hope',
                name: 'Cape of Good Hope (qua Nam Phi)',
                transitTime: '42–48',
                surcharge: '+$2,200–3,800/40\'',
                climateRisk: 'Thấp',
                conflictRisk: 'Không',
                usagePercent: '75% (Maersk, MSC, CMA)',
                note: 'An toàn nhất, chậm nhất, chiếm đa số do Red Sea'
            },
            {
                id: 'vn_eu_red_sea_suez',
                name: 'Red Sea + Suez (trực tiếp)',
                transitTime: '32–38',
                surcharge: '+$800–1,500 + war risk',
                climateRisk: 'Trung bình',
                conflictRisk: 'Rất cao (Houthi)',
                usagePercent: '5% (ZIM)',
                note: 'Gần như đóng cửa, rủi ro cao'
            },
            {
                id: 'vn_eu_trans_siberia',
                name: 'Trans-Siberia Rail (VN–TQ–EU)',
                transitTime: '18–25',
                surcharge: '$4,800–6,500/40\'',
                climateRisk: 'Thấp',
                conflictRisk: 'Trung bình (Ukraine)',
                usagePercent: '8%',
                note: 'Tăng mạnh 2025, rẻ hơn biển'
            },
            {
                id: 'vn_eu_hybrid_sea_rail',
                name: 'Hybrid Sea+Rail (Cái Mép → TQ → Rail)',
                transitTime: '28–35',
                surcharge: '$5,500–7,200',
                climateRisk: 'Thấp',
                conflictRisk: 'Thấp',
                usagePercent: '10% (Evergreen, ONE)',
                note: 'Đang hot, cân bằng'
            },
            {
                id: 'vn_eu_air',
                name: 'Air (SGN → AMS/FRA)',
                transitTime: '1–2',
                surcharge: '$6.5–9.0/kg',
                climateRisk: 'Không',
                conflictRisk: 'Không',
                usagePercent: '2%',
                note: 'Chỉ cho sample/pharma'
            }
        ],
        'vn_hk': [
            {
                id: 'vn_hk_direct_feeder',
                name: 'Direct Feeder (Cái Mép → HK)',
                transitTime: '1–3',
                surcharge: '+$100–200/40\' (BAF)',
                climateRisk: 'Thấp',
                conflictRisk: 'Thấp',
                usagePercent: '70% (OOCL, Maersk)',
                note: 'Siêu nhanh, ổn định'
            },
            {
                id: 'vn_hk_via_shenzhen',
                name: 'Via Shenzhen (HPH → Shenzhen → HK)',
                transitTime: '3–5',
                surcharge: '+$200–300 (transit)',
                climateRisk: 'Thấp',
                conflictRisk: 'Thấp',
                usagePercent: '20% (COSCO)',
                note: 'Dùng khi direct full'
            },
            {
                id: 'vn_hk_road_rail',
                name: 'Road/Rail (HAN → HK via Shenzhen)',
                transitTime: '2–4',
                surcharge: '+$150–250',
                climateRisk: 'Thấp',
                conflictRisk: 'Thấp',
                usagePercent: '10%',
                note: 'Cho hàng lẻ, linh hoạt'
            }
        ],
        'vn_in': [
            {
                id: 'vn_in_direct_sea',
                name: 'Direct Sea (Cái Mép → Mumbai)',
                transitTime: '10–14',
                surcharge: '+$500–800/40\' (BAF)',
                climateRisk: 'Trung bình (monsoon)',
                conflictRisk: 'Thấp',
                usagePercent: '80% (Maersk, MSC)',
                note: 'Ổn định, tăng 10% do trade war'
            },
            {
                id: 'vn_in_via_singapore',
                name: 'Via Singapore (HPH → Singapore → Chennai)',
                transitTime: '12–16',
                surcharge: '+$600–900 (transit)',
                climateRisk: 'Trung bình',
                conflictRisk: 'Thấp',
                usagePercent: '15% (Evergreen)',
                note: 'Dùng khi direct tắc'
            },
            {
                id: 'vn_in_air',
                name: 'Air (SGN → BOM)',
                transitTime: '1–2',
                surcharge: '$4.5–6.5/kg',
                climateRisk: 'Không',
                conflictRisk: 'Không',
                usagePercent: '5%',
                note: 'Cho high-value'
            }
        ],
        'vn_th': [
            {
                id: 'vn_th_road',
                name: 'Road (SGN → Bangkok via Mộc Bài)',
                transitTime: '1–2',
                surcharge: '+$100–200 (customs)',
                climateRisk: 'Thấp (mưa mùa)',
                conflictRisk: 'Thấp',
                usagePercent: '65% (trucks)',
                note: 'Nhanh nhất, 80% volume'
            },
            {
                id: 'vn_th_sea',
                name: 'Sea (Cái Mép → Laem Chabang)',
                transitTime: '5–8',
                surcharge: '+$300–500/40\'',
                climateRisk: 'Thấp',
                conflictRisk: 'Thấp',
                usagePercent: '30% (RCL, Wan Hai)',
                note: 'Dùng cho container lớn'
            },
            {
                id: 'vn_th_air',
                name: 'Air (SGN → BKK)',
                transitTime: '1 giờ',
                surcharge: '$2.5–4.5/kg',
                climateRisk: 'Không',
                conflictRisk: 'Không',
                usagePercent: '5%',
                note: 'Cho urgent'
            }
        ],
        'vn_tw': [
            {
                id: 'vn_tw_direct_sea',
                name: 'Direct Sea (HPH → Kaohsiung)',
                transitTime: '2–5',
                surcharge: '+$200–400/40\' (BAF)',
                climateRisk: 'Trung bình (typhoon)',
                conflictRisk: 'Cao (Taiwan Strait)',
                usagePercent: '85% (Evergreen, Yang Ming)',
                note: '90% direct, rủi ro cao do tension'
            },
            {
                id: 'vn_tw_feeder_hk',
                name: 'Feeder via HK (Cái Mép → HK → Keelung)',
                transitTime: '4–6',
                surcharge: '+$300–500',
                climateRisk: 'Trung bình',
                conflictRisk: 'Cao',
                usagePercent: '10% (OOCL)',
                note: 'Dùng khi direct full'
            },
            {
                id: 'vn_tw_air',
                name: 'Air (HAN → TPE)',
                transitTime: '1–2',
                surcharge: '$3.5–5.5/kg',
                climateRisk: 'Không',
                conflictRisk: 'Cao',
                usagePercent: '5%',
                note: 'Tăng do war risk Strait'
            }
        ],
        'domestic': [
            {
                id: 'domestic_road',
                name: 'Road HN → SGN',
                transitTime: '2–3',
                surcharge: '+$100–200 (tolls)',
                climateRisk: 'Thấp (mưa miền Trung)',
                conflictRisk: 'Không',
                usagePercent: '80% (trucks)',
                note: 'Phổ biến nhất, tắc cao tốc'
            },
            {
                id: 'domestic_rail',
                name: 'Rail Yên Viên → SGN',
                transitTime: '3–4',
                surcharge: '+$150–250 (rail fee)',
                climateRisk: 'Thấp',
                conflictRisk: 'Không',
                usagePercent: '15%',
                note: 'Rẻ hơn road 20%, tăng 10% 2025'
            },
            {
                id: 'domestic_sea',
                name: 'Sea Nội Địa (HPH → Cái Mép)',
                transitTime: '5–7',
                surcharge: '+$300–500/40\'',
                climateRisk: 'Thấp',
                conflictRisk: 'Không',
                usagePercent: '5%',
                note: 'Dùng cho bulk, ít tắc'
            }
        ]
    },
    
    /**
     * Get detailed routes for a trade route
     */
    getDetailedRoutes: function(tradeRouteKey) {
        // Map HTML route to logistics key
        const logisticsKey = this.mapRouteFromHTML(tradeRouteKey);
        return this.detailedRoutes[logisticsKey] || this.detailedRoutes[tradeRouteKey] || [];
    },
    
    /**
     * ========================================
     * PART 9: ROUTES DATA (Simple Route Array)
     * ========================================
     */
    ROUTES: [
        // ===== SEA VN → CN =====
        {
            id: "SEA-VN-CN-1",
            mode: "sea",
            origin: "CMP",
            destination: "SHA",
            tradeLaneFrom: "VN",
            tradeLaneTo: "CN",
            carrier: "Maersk",
            duration: "5-7 days"
        },
        {
            id: "SEA-VN-CN-2",
            mode: "sea",
            origin: "HPH",
            destination: "NGB",
            tradeLaneFrom: "VN",
            tradeLaneTo: "CN",
            carrier: "COSCO",
            duration: "4-6 days"
        },
        // ===== AIR VN → CN =====
        {
            id: "AIR-VN-CN-1",
            mode: "air",
            origin: "SGN",
            destination: "PVG",
            tradeLaneFrom: "VN",
            tradeLaneTo: "CN",
            carrier: "Vietnam Airlines",
            duration: "3h 25m"
        },
        {
            id: "AIR-VN-CN-2",
            mode: "air",
            origin: "HAN",
            destination: "SZX",
            tradeLaneFrom: "VN",
            tradeLaneTo: "CN",
            carrier: "China Southern",
            duration: "2h 40m"
        },
        // ===== ROAD VN → CN =====
        {
            id: "ROAD-VN-CN-1",
            mode: "road",
            origin: "Hữu Nghị Border",
            destination: "Nam Ninh",
            tradeLaneFrom: "VN",
            tradeLaneTo: "CN",
            carrier: "DHL Freight",
            duration: "1-2 days"
        },
        {
            id: "ROAD-VN-CN-2",
            mode: "road",
            origin: "Móng Cái",
            destination: "Đông Hưng",
            tradeLaneFrom: "VN",
            tradeLaneTo: "CN",
            carrier: "FedEx Ground",
            duration: "1 day"
        },
        {
            id: "ROAD-VN-CN-3",
            mode: "road",
            origin: "Lào Cai",
            destination: "Hà Khẩu",
            tradeLaneFrom: "VN",
            tradeLaneTo: "CN",
            carrier: "UPS Freight",
            duration: "1 day"
        },
        {
            id: "ROAD-VN-CN-4",
            mode: "road",
            origin: "Hà Nội",
            destination: "Nam Ninh",
            tradeLaneFrom: "VN",
            tradeLaneTo: "CN",
            carrier: "Kuehne+Nagel Road Logistics",
            duration: "2-3 days"
        },
        // ===== RAIL VN → CN =====
        {
            id: "RAIL-VN-CN-1",
            mode: "rail",
            origin: "Yên Viên",
            destination: "Nam Ninh",
            tradeLaneFrom: "VN",
            tradeLaneTo: "CN",
            carrier: "China Railway Express",
            duration: "2-3 days"
        },
        {
            id: "RAIL-VN-CN-2",
            mode: "rail",
            origin: "Lào Cai",
            destination: "Hà Khẩu",
            tradeLaneFrom: "VN",
            tradeLaneTo: "CN",
            carrier: "Vietnam Rail Logistics",
            duration: "1-2 days"
        },
        // ===== SEA VN → US =====
        {
            id: "SEA-VN-US-1",
            mode: "sea",
            origin: "CMP",
            destination: "USLGB",
            tradeLaneFrom: "VN",
            tradeLaneTo: "US",
            carrier: "Maersk",
            duration: "18-22 days"
        },
        {
            id: "SEA-VN-US-2",
            mode: "sea",
            origin: "CMP",
            destination: "USLAX",
            tradeLaneFrom: "VN",
            tradeLaneTo: "US",
            carrier: "MSC",
            duration: "18-22 days"
        },
        {
            id: "SEA-VN-US-3",
            mode: "sea",
            origin: "CMP",
            destination: "USNYC",
            tradeLaneFrom: "VN",
            tradeLaneTo: "US",
            carrier: "CMA CGM",
            duration: "35-40 days"
        },
        // ===== AIR VN → US =====
        {
            id: "AIR-VN-US-1",
            mode: "air",
            origin: "SGN",
            destination: "LAX",
            tradeLaneFrom: "VN",
            tradeLaneTo: "US",
            carrier: "Vietnam Airlines",
            duration: "16-17 hours"
        },
        {
            id: "AIR-VN-US-2",
            mode: "air",
            origin: "HAN",
            destination: "JFK",
            tradeLaneFrom: "VN",
            tradeLaneTo: "US",
            carrier: "United Airlines",
            duration: "19-20 hours"
        },
        {
            id: "AIR-VN-US-3",
            mode: "air",
            origin: "SGN",
            destination: "SFO",
            tradeLaneFrom: "VN",
            tradeLaneTo: "US",
            carrier: "Cathay Pacific",
            duration: "17-18 hours"
        },
        // ===== SEA VN → EU =====
        {
            id: "SEA-VN-EU-1",
            mode: "sea",
            origin: "CMP",
            destination: "NLRTM",
            tradeLaneFrom: "VN",
            tradeLaneTo: "EU",
            carrier: "Maersk",
            duration: "35-38 days"
        },
        {
            id: "SEA-VN-EU-2",
            mode: "sea",
            origin: "CMP",
            destination: "DEHAM",
            tradeLaneFrom: "VN",
            tradeLaneTo: "EU",
            carrier: "MSC",
            duration: "36-40 days"
        },
        // ===== AIR VN → EU =====
        {
            id: "AIR-VN-EU-1",
            mode: "air",
            origin: "SGN",
            destination: "AMS",
            tradeLaneFrom: "VN",
            tradeLaneTo: "EU",
            carrier: "KLM",
            duration: "14-15 hours"
        },
        {
            id: "AIR-VN-EU-2",
            mode: "air",
            origin: "HAN",
            destination: "FRA",
            tradeLaneFrom: "VN",
            tradeLaneTo: "EU",
            carrier: "Lufthansa",
            duration: "14-16 hours"
        },
        // ===== SEA VN → JP =====
        {
            id: "SEA-VN-JP-1",
            mode: "sea",
            origin: "CMP",
            destination: "JPYOK",
            tradeLaneFrom: "VN",
            tradeLaneTo: "JP",
            carrier: "NYK",
            duration: "7-10 days"
        },
        {
            id: "SEA-VN-JP-2",
            mode: "sea",
            origin: "HPH",
            destination: "JPOSA",
            tradeLaneFrom: "VN",
            tradeLaneTo: "JP",
            carrier: "K Line",
            duration: "8-12 days"
        },
        // ===== AIR VN → JP =====
        {
            id: "AIR-VN-JP-1",
            mode: "air",
            origin: "HAN",
            destination: "NRT",
            tradeLaneFrom: "VN",
            tradeLaneTo: "JP",
            carrier: "Japan Airlines",
            duration: "5-6 hours"
        },
        {
            id: "AIR-VN-JP-2",
            mode: "air",
            origin: "SGN",
            destination: "KIX",
            tradeLaneFrom: "VN",
            tradeLaneTo: "JP",
            carrier: "Vietnam Airlines",
            duration: "5-7 hours"
        },
        // ===== SEA VN → KR =====
        {
            id: "SEA-VN-KR-1",
            mode: "sea",
            origin: "CMP",
            destination: "KRPUS",
            tradeLaneFrom: "VN",
            tradeLaneTo: "KR",
            carrier: "HMM",
            duration: "4-6 days"
        },
        {
            id: "SEA-VN-KR-2",
            mode: "sea",
            origin: "HPH",
            destination: "KRINC",
            tradeLaneFrom: "VN",
            tradeLaneTo: "KR",
            carrier: "Maersk",
            duration: "5-7 days"
        },
        // ===== AIR VN → KR =====
        {
            id: "AIR-VN-KR-1",
            mode: "air",
            origin: "HAN",
            destination: "ICN",
            tradeLaneFrom: "VN",
            tradeLaneTo: "KR",
            carrier: "Korean Air",
            duration: "4-5 hours"
        },
        {
            id: "AIR-VN-KR-2",
            mode: "air",
            origin: "SGN",
            destination: "ICN",
            tradeLaneFrom: "VN",
            tradeLaneTo: "KR",
            carrier: "Vietnam Airlines",
            duration: "5-6 hours"
        }
    ],
    
    /**
     * ========================================
     * PART 10: CONTAINER TYPES BY MODE
     * ========================================
     */
    CONTAINER_TYPES: {
        sea: [
            "20DC (Dry Container)",
            "40DC",
            "40HC",
            "20RF",
            "40RF",
            "Open Top",
            "Flat Rack"
        ],
        air: [
            "AKE ULD",
            "PMC ULD",
            "PAG ULD",
            "PLA ULD"
        ],
        rail: [
            "Covered Wagon",
            "Flat Wagon",
            "Tank Wagon"
        ],
        road: [
            "Dry Van Truck",
            "Reefer Truck",
            "Flatbed Truck",
            "Box Truck"
        ]
    },
    
    /**
     * ========================================
     * PART 11: CARRIERS BY MODE
     * ========================================
     */
    CARRIERS: {
        sea: [
            "Maersk",
            "MSC",
            "CMA CGM",
            "COSCO / OOCL",
            "Evergreen",
            "Hapag-Lloyd",
            "ONE",
            "Yang Ming",
            "Wan Hai",
            "ZIM"
        ],
        air: [
            "Singapore Airlines Cargo",
            "Cathay Pacific Cargo",
            "China Airlines Cargo",
            "Emirates SkyCargo",
            "Qatar Airways Cargo",
            "Korean Air Cargo",
            "Lufthansa Cargo",
            "Vietnam Airlines Cargo",
            "China Southern Cargo",
            "Etihad Cargo"
        ],
        road: [
            "DHL Freight",
            "FedEx Ground",
            "UPS Freight",
            "Kuehne+Nagel Road Logistics"
        ],
        rail: [
            "China Railway Express",
            "Vietnam Rail Logistics",
            "Yuxinou Rail",
            "CRCT"
        ]
    },
    
    /**
     * ========================================
     * PART 12: SMART LOCATION DATA BY MODE
     * ========================================
     */
    LOCATIONS: {
        road: {
            VN: ["Hữu Nghị Border", "Móng Cái", "Lào Cai", "Hà Nội", "HCM", "Đà Nẵng"],
            CN: ["Nam Ninh", "Đông Hưng", "Hà Khẩu", "Beijing", "Shanghai", "Guangzhou"],
            US: ["Los Angeles", "New York", "Chicago", "Miami", "Seattle", "Houston"],
            EU: ["Rotterdam", "Hamburg", "Frankfurt", "Paris", "London", "Milan"],
            JP: ["Tokyo", "Osaka", "Yokohama", "Kobe", "Nagoya"],
            KR: ["Seoul", "Busan", "Incheon", "Daegu"],
            TH: ["Bangkok", "Laem Chabang", "Chonburi"],
            IN: ["Mumbai", "Chennai", "Delhi", "Kolkata", "Bangalore"]
        },
        air: {
            VN: ["SGN", "HAN", "DAD"],
            CN: ["PVG", "CAN", "SZX", "PEK"],
            US: ["LAX", "JFK", "SFO", "ORD", "MIA", "SEA"],
            EU: ["AMS", "FRA", "CDG", "LHR", "MXP", "HAM"],
            JP: ["NRT", "KIX", "NGO"],
            KR: ["ICN", "PUS"],
            TH: ["BKK"],
            IN: ["BOM", "DEL", "MAA", "CCU"]
        },
        sea: {
            VN: ["CMP", "HPH"],
            CN: ["SHA", "NGB", "XMN"],
            US: ["USLGB", "USLAX", "USNYC", "USSEA"],
            EU: ["NLRTM", "DEHAM", "BEANR"],
            JP: ["JPYOK", "JPOSA", "JPTYO"],
            KR: ["KRPUS", "KRINC"],
            TH: ["THLCH"],
            IN: ["INBOM", "INMAA", "INCCU"]
        },
        rail: {
            VN: ["Yên Viên", "Lào Cai"],
            CN: ["Pingxiang", "Kunming"],
            US: ["Chicago", "Kansas City", "Los Angeles", "New York"],
            EU: ["Duisburg", "Hamburg", "Warsaw", "Berlin"],
            JP: ["Tokyo Rail", "Osaka Rail"],
            KR: ["Seoul Rail", "Busan Rail"]
        }
    }
};

// Generate serviceRoutes after LOGISTICS_DATA is fully defined
(function() {
    const routes = [];
    const data = LOGISTICS_DATA;
    
    // Iterate all trade lanes
    Object.keys(data.routes).forEach(tradeLane => {
        const route = data.routes[tradeLane];
        if (!route || !route.transport_modes) return;
        
        // Get carriers for this trade lane
        const carrierKey = tradeLane === 'domestic' ? 'domestic_vn' : tradeLane;
        const carriers = data.carrierRatings[carrierKey] || data.carriersByRoute[tradeLane] || [];
        const sortedCarriers = [...carriers].sort((a, b) => {
            const ratingA = a.rating || 0;
            const ratingB = b.rating || 0;
            return ratingB - ratingA;
        });
        
        let carrierIndex = 0;
        let routeIndex = 0;
        
        // Iterate transport modes
        route.transport_modes.forEach(mode => {
            if (!mode.routes || mode.routes.length === 0) return;
            
            // Iterate each route in the mode
            mode.routes.forEach((r, idx) => {
                // Choose carrier (rotate through top 2-3 carriers)
                const carrier = sortedCarriers[carrierIndex % Math.min(3, sortedCarriers.length)];
                if (!carrier) return;
                
                const carrierName = carrier.name;
                const modeValue = mode.value;
                
                // Generate ID
                const tradeAbbrev = tradeLane.toUpperCase().replace('_', '');
                const modeAbbrev = data._getModeAbbreviation(modeValue);
                const carrierAbbrev = data._getCarrierAbbreviation(carrierName);
                const id = `${tradeAbbrev}-${modeAbbrev}-${r.pol_code}-${r.pod_code}-${carrierAbbrev}-${String(routeIndex + 1).padStart(2, '0')}`;
                
                // Parse transit time
                const baseTransitDays = data._parseTransitTime(r);
                
                // Get container types
                const containerTypes = data._getContainerTypesForMode(modeValue);
                
                // Get schedule
                const schedule = data._getScheduleForRoute(tradeLane, modeValue);
                
                // Get reliability
                const reliability = data._getReliabilityForCarrier(carrierKey, carrierName);
                
                // Get seasonality
                const seasonalityIndex = data._buildSeasonalityIndex(tradeLane, modeValue);
                
                // Create service route object
                routes.push({
                    id: id,
                    trade_lane: tradeLane,
                    mode: modeValue,
                    pol: r.pol,
                    pol_code: r.pol_code,
                    pod: r.pod,
                    pod_code: r.pod_code,
                    carrier: carrierName,
                    container_types: containerTypes,
                    schedule: schedule,
                    base_transit_days: baseTransitDays,
                    reliability: reliability,
                    seasonality_index: seasonalityIndex
                });
                
                routeIndex++;
                
                // Rotate carrier every 2-3 routes
                if (routeIndex % 2 === 0) {
                    carrierIndex++;
                }
            });
        });
    });
    
    // Assign generated routes to LOGISTICS_DATA
    LOGISTICS_DATA.serviceRoutes = routes;
})();

// ========================================
// PART 6: SEPARATED PORT LISTS BY MODE
// ========================================
LOGISTICS_DATA.air_ports = [
    { code: "HAN", name: "Nội Bài", type: "air", country: "VN" },
    { code: "SGN", name: "Tân Sơn Nhất", type: "air", country: "VN" },
    { code: "DAD", name: "Đà Nẵng", type: "air", country: "VN" },
    { code: "PVU", name: "Phú Quốc", type: "air", country: "VN" },
    { code: "PEK", name: "Beijing Capital", type: "air", country: "CN" },
    { code: "PVG", name: "Shanghai Pudong", type: "air", country: "CN" },
    { code: "CAN", name: "Guangzhou Baiyun", type: "air", country: "CN" },
    { code: "SZX", name: "Shenzhen Bao'an", type: "air", country: "CN" },
    { code: "LAX", name: "Los Angeles", type: "air", country: "US" },
    { code: "JFK", name: "New York JFK", type: "air", country: "US" },
    { code: "ORD", name: "Chicago O'Hare", type: "air", country: "US" },
    { code: "ICN", name: "Incheon", type: "air", country: "KR" },
    { code: "NRT", name: "Narita", type: "air", country: "JP" },
    { code: "HKG", name: "Hong Kong", type: "air", country: "HK" },
    { code: "SIN", name: "Singapore Changi", type: "air", country: "SG" },
    { code: "BKK", name: "Bangkok Suvarnabhumi", type: "air", country: "TH" },
    { code: "CDG", name: "Paris Charles de Gaulle", type: "air", country: "FR" },
    { code: "FRA", name: "Frankfurt", type: "air", country: "DE" },
    { code: "AMS", name: "Amsterdam Schiphol", type: "air", country: "NL" },
    { code: "LHR", name: "London Heathrow", type: "air", country: "GB" }
];

LOGISTICS_DATA.sea_ports = [
    { code: "HPH", name: "Hải Phòng", type: "sea", country: "VN" },
    { code: "CMP", name: "Cái Mép - Thị Vải", type: "sea", country: "VN" },
    { code: "SGN", name: "Sài Gòn", type: "sea", country: "VN" },
    { code: "DAD", name: "Đà Nẵng", type: "sea", country: "VN" },
    { code: "CNSHA", name: "Shanghai", type: "sea", country: "CN" },
    { code: "CNNGB", name: "Ningbo", type: "sea", country: "CN" },
    { code: "CNSZN", name: "Shenzhen", type: "sea", country: "CN" },
    { code: "CNCAN", name: "Guangzhou", type: "sea", country: "CN" },
    { code: "CNXMN", name: "Xiamen", type: "sea", country: "CN" },
    { code: "USLAX", name: "Los Angeles", type: "sea", country: "US" },
    { code: "USLGB", name: "Long Beach", type: "sea", country: "US" },
    { code: "USNYC", name: "New York", type: "sea", country: "US" },
    { code: "USSEA", name: "Seattle", type: "sea", country: "US" },
    { code: "KRICN", name: "Incheon", type: "sea", country: "KR" },
    { code: "JPYOK", name: "Yokohama", type: "sea", country: "JP" },
    { code: "JPOSA", name: "Osaka", type: "sea", country: "JP" },
    { code: "HKHKG", name: "Hong Kong", type: "sea", country: "HK" },
    { code: "SGSIN", name: "Singapore", type: "sea", country: "SG" },
    { code: "THBKK", name: "Bangkok", type: "sea", country: "TH" },
    { code: "DEHAM", name: "Hamburg", type: "sea", country: "DE" },
    { code: "NLRTM", name: "Rotterdam", type: "sea", country: "NL" },
    { code: "GBFEL", name: "Felixstowe", type: "sea", country: "GB" }
];

LOGISTICS_DATA.rail_nodes = [
    { code: "YV", name: "Yên Viên", type: "rail", country: "VN" },
    { code: "LC", name: "Lào Cai", type: "rail", country: "VN" },
    { code: "HAN", name: "Hà Nội", type: "rail", country: "VN" },
    { code: "NN", name: "Nam Ninh", type: "rail", country: "CN" },
    { code: "HK", name: "Hà Khẩu", type: "rail", country: "CN" },
    { code: "DH", name: "Đông Hưng", type: "rail", country: "CN" },
    { code: "BJ", name: "Beijing", type: "rail", country: "CN" },
    { code: "SH", name: "Shanghai", type: "rail", country: "CN" },
    { code: "GZ", name: "Guangzhou", type: "rail", country: "CN" },
    { code: "SZ", name: "Shenzhen", type: "rail", country: "CN" },
    { code: "XMN", name: "Xiamen", type: "rail", country: "CN" }
];

LOGISTICS_DATA.road_nodes = [
    { code: "HN", name: "Hữu Nghị (Border)", type: "road", country: "VN" },
    { code: "MC", name: "Móng Cái (Border)", type: "road", country: "VN" },
    { code: "LC", name: "Lào Cai (Border)", type: "road", country: "VN" },
    { code: "HAN", name: "Hà Nội", type: "road", country: "VN" },
    { code: "SGN", name: "TP. Hồ Chí Minh", type: "road", country: "VN" },
    { code: "DAD", name: "Đà Nẵng", type: "road", country: "VN" },
    { code: "NN", name: "Nam Ninh", type: "road", country: "CN" },
    { code: "DH", name: "Đông Hưng", type: "road", country: "CN" },
    { code: "HK", name: "Hà Khẩu", type: "road", country: "CN" },
    { code: "BJ", name: "Beijing", type: "road", country: "CN" },
    { code: "SH", name: "Shanghai", type: "road", country: "CN" },
    { code: "GZ", name: "Guangzhou", type: "road", country: "CN" }
];

// ========================================
// PART 7: CARGO TYPES (INTERNATIONAL STANDARD)
// ========================================
LOGISTICS_DATA.cargoTypes = [
    { value: 'electronics', label: 'Electronics & High-Tech', risk: 'high_value' },
    { value: 'machinery', label: 'Machinery & Equipment', risk: 'standard' },
    { value: 'automotive', label: 'Automotive Parts & Vehicles', risk: 'standard' },
    { value: 'chemicals', label: 'Chemicals & Hazardous Materials', risk: 'dg' },
    { value: 'pharma', label: 'Pharmaceuticals & Medical', risk: 'temperature' },
    { value: 'food_beverage', label: 'Food & Beverage', risk: 'perishable' },
    { value: 'garments', label: 'Garments & Textiles', risk: 'standard' },
    { value: 'furniture', label: 'Furniture & Home Goods', risk: 'fragile' },
    { value: 'fmcg', label: 'FMCG (Fast-Moving Consumer Goods)', risk: 'standard' },
    { value: 'perishables', label: 'Perishables (Fresh Produce)', risk: 'perishable' },
    { value: 'bulk_cargo', label: 'Bulk Cargo (Grains, Minerals)', risk: 'standard' },
    { value: 'project_cargo', label: 'Project Cargo (Heavy Lift)', risk: 'oversize' },
    { value: 'dangerous_goods', label: 'Dangerous Goods (DG)', risk: 'dg' },
    { value: 'general_cargo', label: 'General Cargo', risk: 'standard' }
];

// ========================================
// PART 8: PACKING TYPES
// ========================================
LOGISTICS_DATA.packingTypes = [
    { value: 'palletized', label: 'Palletized' },
    { value: 'cartons', label: 'Cartons / Boxes' },
    { value: 'crates', label: 'Crates (Wooden)' },
    { value: 'drums', label: 'Drums / Barrels' },
    { value: 'bags', label: 'Bags / Sacks' },
    { value: 'bulk', label: 'Bulk (Loose)' },
    { value: 'flexitank', label: 'Flexitank' },
    { value: 'ibc', label: 'IBC / Tank Container' },
    { value: 'reefer_uld', label: 'Reefer ULD (Air)' },
    { value: 'other', label: 'Other' }
];

// ========================================
// PART 9: INSURANCE COVERAGE TYPES
// ========================================
LOGISTICS_DATA.insuranceCoverageTypes = [
    { value: 'all_risk', label: 'All Risk' },
    { value: 'total_loss', label: 'Total Loss Only' },
    { value: 'fpa', label: 'FPA (Free from Particular Average)' }
];

// ========================================
// PART 10: DG CLASSES
// ========================================
LOGISTICS_DATA.dgClasses = [
    { value: '1', label: 'Class 1 - Explosives' },
    { value: '2', label: 'Class 2 - Gases' },
    { value: '3', label: 'Class 3 - Flammable Liquids' },
    { value: '4', label: 'Class 4 - Flammable Solids' },
    { value: '5', label: 'Class 5 - Oxidizing Substances' },
    { value: '6', label: 'Class 6 - Toxic Substances' },
    { value: '7', label: 'Class 7 - Radioactive Materials' },
    { value: '8', label: 'Class 8 - Corrosive Substances' },
    { value: '9', label: 'Class 9 - Miscellaneous' }
];

// ========================================
// PART 11: BUSINESS TYPES
// ========================================
LOGISTICS_DATA.businessTypes = [
    { value: 'manufacturer', label: 'Manufacturer' },
    { value: 'trading_company', label: 'Trading Company' },
    { value: 'logistics_provider', label: 'Logistics Provider' },
    { value: 'retailer', label: 'Retailer' },
    { value: 'distributor', label: 'Distributor' },
    { value: 'wholesaler', label: 'Wholesaler' },
    { value: 'other', label: 'Other' }
];

// ========================================
// PART 12: COUNTRIES (COMPREHENSIVE LIST)
// ========================================
LOGISTICS_DATA.countries = [
    { name: 'Afghanistan', iso2: 'AF', emoji: '🇦🇫' },
    { name: 'Albania', iso2: 'AL', emoji: '🇦🇱' },
    { name: 'Algeria', iso2: 'DZ', emoji: '🇩🇿' },
    { name: 'Argentina', iso2: 'AR', emoji: '🇦🇷' },
    { name: 'Australia', iso2: 'AU', emoji: '🇦🇺' },
    { name: 'Austria', iso2: 'AT', emoji: '🇦🇹' },
    { name: 'Bangladesh', iso2: 'BD', emoji: '🇧🇩' },
    { name: 'Belgium', iso2: 'BE', emoji: '🇧🇪' },
    { name: 'Brazil', iso2: 'BR', emoji: '🇧🇷' },
    { name: 'Cambodia', iso2: 'KH', emoji: '🇰🇭' },
    { name: 'Canada', iso2: 'CA', emoji: '🇨🇦' },
    { name: 'Chile', iso2: 'CL', emoji: '🇨🇱' },
    { name: 'China', iso2: 'CN', emoji: '🇨🇳' },
    { name: 'Colombia', iso2: 'CO', emoji: '🇨🇴' },
    { name: 'Czech Republic', iso2: 'CZ', emoji: '🇨🇿' },
    { name: 'Denmark', iso2: 'DK', emoji: '🇩🇰' },
    { name: 'Egypt', iso2: 'EG', emoji: '🇪🇬' },
    { name: 'Finland', iso2: 'FI', emoji: '🇫🇮' },
    { name: 'France', iso2: 'FR', emoji: '🇫🇷' },
    { name: 'Germany', iso2: 'DE', emoji: '🇩🇪' },
    { name: 'Greece', iso2: 'GR', emoji: '🇬🇷' },
    { name: 'Hong Kong', iso2: 'HK', emoji: '🇭🇰' },
    { name: 'Hungary', iso2: 'HU', emoji: '🇭🇺' },
    { name: 'India', iso2: 'IN', emoji: '🇮🇳' },
    { name: 'Indonesia', iso2: 'ID', emoji: '🇮🇩' },
    { name: 'Iran', iso2: 'IR', emoji: '🇮🇷' },
    { name: 'Iraq', iso2: 'IQ', emoji: '🇮🇶' },
    { name: 'Ireland', iso2: 'IE', emoji: '🇮🇪' },
    { name: 'Israel', iso2: 'IL', emoji: '🇮🇱' },
    { name: 'Italy', iso2: 'IT', emoji: '🇮🇹' },
    { name: 'Japan', iso2: 'JP', emoji: '🇯🇵' },
    { name: 'Jordan', iso2: 'JO', emoji: '🇯🇴' },
    { name: 'Kazakhstan', iso2: 'KZ', emoji: '🇰🇿' },
    { name: 'Kenya', iso2: 'KE', emoji: '🇰🇪' },
    { name: 'Kuwait', iso2: 'KW', emoji: '🇰🇼' },
    { name: 'Laos', iso2: 'LA', emoji: '🇱🇦' },
    { name: 'Malaysia', iso2: 'MY', emoji: '🇲🇾' },
    { name: 'Mexico', iso2: 'MX', emoji: '🇲🇽' },
    { name: 'Morocco', iso2: 'MA', emoji: '🇲🇦' },
    { name: 'Myanmar', iso2: 'MM', emoji: '🇲🇲' },
    { name: 'Netherlands', iso2: 'NL', emoji: '🇳🇱' },
    { name: 'New Zealand', iso2: 'NZ', emoji: '🇳🇿' },
    { name: 'Nigeria', iso2: 'NG', emoji: '🇳🇬' },
    { name: 'Norway', iso2: 'NO', emoji: '🇳🇴' },
    { name: 'Pakistan', iso2: 'PK', emoji: '🇵🇰' },
    { name: 'Peru', iso2: 'PE', emoji: '🇵🇪' },
    { name: 'Philippines', iso2: 'PH', emoji: '🇵🇭' },
    { name: 'Poland', iso2: 'PL', emoji: '🇵🇱' },
    { name: 'Portugal', iso2: 'PT', emoji: '🇵🇹' },
    { name: 'Qatar', iso2: 'QA', emoji: '🇶🇦' },
    { name: 'Romania', iso2: 'RO', emoji: '🇷🇴' },
    { name: 'Russia', iso2: 'RU', emoji: '🇷🇺' },
    { name: 'Saudi Arabia', iso2: 'SA', emoji: '🇸🇦' },
    { name: 'Singapore', iso2: 'SG', emoji: '🇸🇬' },
    { name: 'South Africa', iso2: 'ZA', emoji: '🇿🇦' },
    { name: 'South Korea', iso2: 'KR', emoji: '🇰🇷' },
    { name: 'Spain', iso2: 'ES', emoji: '🇪🇸' },
    { name: 'Sri Lanka', iso2: 'LK', emoji: '🇱🇰' },
    { name: 'Sweden', iso2: 'SE', emoji: '🇸🇪' },
    { name: 'Switzerland', iso2: 'CH', emoji: '🇨🇭' },
    { name: 'Taiwan', iso2: 'TW', emoji: '🇹🇼' },
    { name: 'Thailand', iso2: 'TH', emoji: '🇹🇭' },
    { name: 'Turkey', iso2: 'TR', emoji: '🇹🇷' },
    { name: 'Ukraine', iso2: 'UA', emoji: '🇺🇦' },
    { name: 'United Arab Emirates', iso2: 'AE', emoji: '🇦🇪' },
    { name: 'United Kingdom', iso2: 'GB', emoji: '🇬🇧' },
    { name: 'United States', iso2: 'US', emoji: '🇺🇸' },
    { name: 'Venezuela', iso2: 'VE', emoji: '🇻🇪' },
    { name: 'Vietnam', iso2: 'VN', emoji: '🇻🇳' }
];

// ========================================
// PART 13: INCOTERMS 2020
// ========================================
LOGISTICS_DATA.incoterms = [
    { code: 'EXW', label: 'EXW – Ex Works' },
    { code: 'FCA', label: 'FCA – Free Carrier' },
    { code: 'FAS', label: 'FAS – Free Alongside Ship' },
    { code: 'FOB', label: 'FOB – Free On Board' },
    { code: 'CFR', label: 'CFR – Cost and Freight' },
    { code: 'CIF', label: 'CIF – Cost, Insurance and Freight' },
    { code: 'CPT', label: 'CPT – Carriage Paid To' },
    { code: 'CIP', label: 'CIP – Carriage and Insurance Paid To' },
    { code: 'DAP', label: 'DAP – Delivered At Place' },
    { code: 'DPU', label: 'DPU – Delivered at Place Unloaded' },
    { code: 'DDP', label: 'DDP – Delivered Duty Paid' }
];

// Legacy data (kept for backward compatibility)
LOGISTICS_DATA.SELLER_COUNTRIES = [
    { code: "VN", name: "Việt Nam" },
    { code: "CN", name: "Trung Quốc" },
    { code: "US", name: "Hoa Kỳ" },
    { code: "KR", name: "Hàn Quốc" },
    { code: "JP", name: "Nhật Bản" },
    { code: "EU", name: "Liên minh Châu Âu" },
    { code: "TH", name: "Thái Lan" },
    { code: "SG", name: "Singapore" },
    { code: "MY", name: "Malaysia" }
];

LOGISTICS_DATA.INCOTERMS_2020 = LOGISTICS_DATA.incoterms;

// Export for use in other scripts
/**
 * ========================================
 * PORT COORDINATES (for Globe visualization)
 * ========================================
 */
LOGISTICS_DATA.ports = {
    // Vietnam Ports
    CMP:  { name: "Cái Mép - Thị Vải", country: "VN", lat: 10.5, lng: 107.0 },
    HPH:  { name: "Hải Phòng", country: "VN", lat: 20.86, lng: 106.68 },
    HAN:  { name: "Hà Nội", country: "VN", lat: 21.03, lng: 105.85 },
    SGN:  { name: "Hồ Chí Minh", country: "VN", lat: 10.77, lng: 106.70 },
    DNG:  { name: "Đà Nẵng", country: "VN", lat: 16.08, lng: 108.22 },
    VUT:  { name: "Vũng Tàu", country: "VN", lat: 10.35, lng: 107.08 },
    
    // Hong Kong
    HKHKG: { name: "Hong Kong", country: "HK", lat: 22.30, lng: 114.17 },
    
    // US Ports
    USLAX: { name: "Los Angeles", country: "US", lat: 33.74, lng: -118.27 },
    USLGB: { name: "Long Beach", country: "US", lat: 33.75, lng: -118.21 },
    USOAK: { name: "Oakland", country: "US", lat: 37.80, lng: -122.30 },
    USSFO: { name: "San Francisco", country: "US", lat: 37.62, lng: -122.38 },
    SFO: { name: "San Francisco", country: "US", lat: 37.62, lng: -122.38 },
    USSEA: { name: "Seattle", country: "US", lat: 47.60, lng: -122.33 },
    USNYC: { name: "New York", country: "US", lat: 40.71, lng: -74.00 },
    USHOU: { name: "Houston", country: "US", lat: 29.76, lng: -95.36 },
    USSAV: { name: "Savannah", country: "US", lat: 32.08, lng: -81.09 },
    
    // China Ports
    CNSHA: { name: "Shanghai", country: "CN", lat: 31.23, lng: 121.47 },
    CNSZX: { name: "Shenzhen", country: "CN", lat: 22.54, lng: 114.06 },
    CNNGB: { name: "Ningbo", country: "CN", lat: 29.87, lng: 121.55 },
    CNQIN: { name: "Qingdao", country: "CN", lat: 36.07, lng: 120.38 },
    CNTAO: { name: "Qingdao", country: "CN", lat: 36.07, lng: 120.38 },
    CNXMN: { name: "Xiamen", country: "CN", lat: 24.48, lng: 118.08 },
    CNDLC: { name: "Dalian", country: "CN", lat: 38.91, lng: 121.60 },
    CNCAN: { name: "Guangzhou", country: "CN", lat: 23.13, lng: 113.26 },
    
    // Europe Ports
    NLRTM: { name: "Rotterdam", country: "NL", lat: 51.95, lng: 4.13 },
    DEHAM: { name: "Hamburg", country: "DE", lat: 53.55, lng: 9.99 },
    BEANR: { name: "Antwerp", country: "BE", lat: 51.23, lng: 4.40 },
    FRLEH: { name: "Le Havre", country: "FR", lat: 49.49, lng: 0.11 },
    GBLON: { name: "London", country: "GB", lat: 51.50, lng: 0.00 },
    GBFEL: { name: "Felixstowe", country: "GB", lat: 51.96, lng: 1.35 },
    ESLCG: { name: "La Coruña", country: "ES", lat: 43.37, lng: -8.40 },
    ITGOA: { name: "Genoa", country: "IT", lat: 44.41, lng: 8.93 },
    
    // Singapore
    SGSIN: { name: "Singapore", country: "SG", lat: 1.29, lng: 103.85 },
    
    // Other Asia
    JPYOK: { name: "Yokohama", country: "JP", lat: 35.44, lng: 139.64 },
    JPTYO: { name: "Tokyo", country: "JP", lat: 35.65, lng: 139.77 },
    JPOSA: { name: "Osaka", country: "JP", lat: 34.65, lng: 135.43 },
    KRPUS: { name: "Busan", country: "KR", lat: 35.10, lng: 129.04 },
    KRINC: { name: "Incheon", country: "KR", lat: 37.45, lng: 126.61 },
    THBKK: { name: "Bangkok", country: "TH", lat: 13.75, lng: 100.50 },
    THLCH: { name: "Laem Chabang", country: "TH", lat: 13.08, lng: 100.88 },
    MYPKG: { name: "Port Klang", country: "MY", lat: 2.99, lng: 101.39 },
    IDTPP: { name: "Tanjung Priok", country: "ID", lat: -6.10, lng: 106.88 },
    PHMNL: { name: "Manila", country: "PH", lat: 14.60, lng: 120.97 },
    
    // Middle East
    AEJEA: { name: "Jebel Ali", country: "AE", lat: 25.01, lng: 55.08 },
    AEDXB: { name: "Dubai", country: "AE", lat: 25.27, lng: 55.30 },
    
    // Australia
    AUSYD: { name: "Sydney", country: "AU", lat: -33.87, lng: 151.21 },
    AUMEL: { name: "Melbourne", country: "AU", lat: -37.81, lng: 144.96 },
    
    // Additional common airport codes
    LAX: { name: "Los Angeles", country: "US", lat: 33.74, lng: -118.27 },
    JFK: { name: "New York JFK", country: "US", lat: 40.64, lng: -73.78 },
    ORD: { name: "Chicago", country: "US", lat: 41.98, lng: -87.90 },
    DFW: { name: "Dallas", country: "US", lat: 32.90, lng: -97.04 },
    ATL: { name: "Atlanta", country: "US", lat: 33.64, lng: -84.43 },
    NRT: { name: "Tokyo Narita", country: "JP", lat: 35.77, lng: 140.39 },
    ICN: { name: "Seoul Incheon", country: "KR", lat: 37.46, lng: 126.44 },
    PVG: { name: "Shanghai Pudong", country: "CN", lat: 31.14, lng: 121.81 },
    HKG: { name: "Hong Kong", country: "HK", lat: 22.31, lng: 113.92 },
    BKK: { name: "Bangkok", country: "TH", lat: 13.69, lng: 100.75 }
};

/**
 * Get port by code
 */
LOGISTICS_DATA.getPort = function(code) {
    if (!code) return null;
    return this.ports[code.toUpperCase()] || null;
};

/**
 * ========================================
 * CARRIER BY MODE
 * ========================================
 */
const CARRIER_BY_MODE = {
    SEA: [
        'Maersk Line', 'MSC', 'CMA CGM', 'COSCO',
        'Hapag-Lloyd', 'ONE', 'Evergreen', 'Yang Ming',
        'OOCL', 'Wan Hai', 'HMM', 'PIL', 'ZIM'
    ],
    AIR: [
        'Vietnam Airlines Cargo', 'Vietjet Cargo', 'Emirates SkyCargo',
        'Qatar Airways Cargo', 'Singapore Airlines Cargo',
        'Korean Air Cargo', 'China Airlines Cargo',
        'Cathay Pacific Cargo', 'Lufthansa Cargo', 'Cargolux'
    ],
    ROAD: [
        'DHL Road Freight', 'FedEx Ground', 'DB Schenker Road',
        'Kerry Logistics', 'Sagawa Express', 'YRC Freight'
    ],
    RAIL: [
        'China Railway Express', 'DB Cargo', 'RZD Russian Railways',
        'Kazakhstan Rail', 'Maersk Intermodal Rail'
    ]
};

if (typeof window !== 'undefined') {
    window.LOGISTICS_DATA = LOGISTICS_DATA;
    window.CARRIER_BY_MODE = CARRIER_BY_MODE;
    console.log('✅ LOGISTICS_DATA loaded successfully');
    console.log(`   - ${Object.keys(LOGISTICS_DATA.routes).length} routes available`);
    console.log(`   - ${Object.keys(LOGISTICS_DATA.transportModeTypes).length} transport mode categories`);
    console.log(`   - ${LOGISTICS_DATA.serviceRoutes.length} service routes generated`);
    console.log(`   - ${Object.keys(CARRIER_BY_MODE).length} carrier mode categories`);
}
