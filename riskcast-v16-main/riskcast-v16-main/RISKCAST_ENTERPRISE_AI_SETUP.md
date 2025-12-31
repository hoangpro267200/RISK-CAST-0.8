# RISKCAST Enterprise AI - Setup Guide

## 🎯 Overview

RISKCAST Enterprise AI là hệ thống phân tích - dự báo - tối ưu rủi ro vận tải bằng AI theo chuẩn SaaS với:

- **AI Adviser** dạng ChatGPT với streaming real-time
- **Route Recommendation** - Gợi ý tuyến đường tối ưu
- **Stochastic Delay Prediction** - Dự đoán trễ giao hàng
- **Risk-based Insurance** - Tối ưu bảo hiểm theo rủi ro
- **ESG Advisory** - Tư vấn môi trường và carbon
- **Enterprise Dashboard** với Neon UI
- **Mini Memory** - Lưu lịch sử phân tích

## 📁 Cấu Trúc Project

```
RISKCAST/
│── app/
│    ├── main.py              # FastAPI app với CORS
│    ├── api_ai.py            # 6 AI endpoints
│    ├── risk_engine.py       # Risk calculation functions
│    ├── memory.py             # Mini Memory system
│    ├── utils.py             # Utility functions
│    └── __init__.py
│
│── static/
│    ├── css/
│    │    ├── ai_panel.css    # AI Adviser Panel styles
│    │    └── neon.css        # Neon effects
│    └── js/
│         ├── streaming.js     # Streaming text handler
│         └── ai_adviser.js    # AI panel controller
│
└── data/
     └── history.json         # Shipment history (auto-created)
```

## 🚀 Installation

### 1. Install Dependencies

```bash
pip install -r files/requirements.txt
```

### 2. Environment Setup

Tạo file `.env` trong thư mục gốc:

```env
ANTHROPIC_API_KEY=your_claude_api_key_here
```

### 3. Run Server

```bash
uvicorn app.main:app --reload
```

Server sẽ chạy tại: `http://localhost:8000`

## 🔌 API Endpoints

### 1. `/api/ai/stream` - Streaming Response
**POST** - Real-time streaming text response

```json
{
  "prompt": "Analyze this shipment...",
  "context": {}
}
```

### 2. `/api/ai/analyze` - AI Insights Panel
**POST** - Main risk analysis với AI insights

```json
{
  "shipment_data": {
    "distance": 1000,
    "cargo_value": 50000,
    "transport_mode": "sea",
    ...
  }
}
```

### 3. `/api/ai/route` - Route Recommendation
**POST** - AI-recommended route với evidence

### 4. `/api/ai/insurance` - Insurance Optimizer
**POST** - Risk-based insurance guidance

### 5. `/api/ai/delay` - Delay Prediction
**POST** - Predictive delay analysis

### 6. `/api/ai/esg` - ESG Advisory
**POST** - Carbon footprint và ESG score

### 7. `/api/ai/history` - Mini Memory
**POST** - Compare shipments và historical trends

## 💻 Frontend Integration

### 1. Include CSS

```html
<link rel="stylesheet" href="/static/css/ai_panel.css">
<link rel="stylesheet" href="/static/css/neon.css">
```

### 2. Include JavaScript

```html
<script src="/static/js/streaming.js"></script>
<script src="/static/js/ai_adviser.js"></script>
```

### 3. Add AI Panel Toggle Button

```html
<button id="ai-panel-toggle" class="neon-button">
    Open AI Adviser
</button>
```

### 4. Use Programmatically

```javascript
// Open panel
window.aiAdviser.open();

// Ask question
window.aiAdviser.ask("What is the risk level?");

// Analyze shipment
window.aiAdviser.analyzeShipment(shipmentData);
```

## 🎨 UI Components

### Neon Effects

- `.neon-border` - Neon border effect
- `.neon-glow` - Glow effect (green)
- `.neon-glow-cyan` - Cyan glow
- `.neon-button` - Neon button style
- `.neon-card` - Neon card container
- `.gradient-text` - Gradient text effect

### AI Panel

- `.ai-panel` - Main panel container
- `.ai-message` - Message bubble
- `.ai-streaming` - Streaming text container
- `.ai-loading` - Loading dots

## 📊 Risk Calculation

### Risk Levels

- **0-33**: Low Risk
- **34-66**: Medium Risk  
- **67-100**: High Risk

### Insurance Logic

- **Risk > 70**: Must buy insurance
- **Risk 40-70**: Recommended
- **Risk < 40**: Optional

### ESG Score

```
ESG = (GreenScore * 0.4) + (Social * 0.3) + (Governance * 0.3)
```

## 🔧 Configuration

### Memory System

History được lưu tại: `data/history.json`

Mỗi shipment có UUID riêng và được lưu với:
- Timestamp
- Shipment data
- Risk analysis
- Executive summary

### Claude Model

Mặc định sử dụng: `claude-3-5-sonnet-20241022`

Có thể thay đổi trong `app/api_ai.py`

## 🐛 Troubleshooting

### API Key Not Found

Đảm bảo file `.env` có `ANTHROPIC_API_KEY`

### Streaming Not Working

Kiểm tra CORS settings trong `app/main.py`

### Memory Not Saving

Đảm bảo thư mục `data/` có quyền ghi

## 📝 Notes

- Tất cả endpoints sử dụng async/await
- Streaming response sử dụng Server-Sent Events (SSE)
- Memory system tự động tạo file nếu chưa có
- CSS và JS đã được tối ưu cho mobile responsive

## 🎯 Next Steps

1. Tích hợp AI panel vào `results.html`
2. Thêm animation effects
3. Customize prompts cho từng use case
4. Thêm authentication nếu cần
5. Deploy lên production server

---

**Version**: 15.0.0  
**Author**: RISKCAST Team  
**License**: Proprietary











<<<<<<< HEAD
=======

>>>>>>> d1581b2 (first commit)

































