# 🔍 KIỂM TRA VÀ DISABLE CÁC EXTENSION PREVIEW

## ⚠️ CÁC EXTENSION CẦN DISABLE

Để đảm bảo mọi link mở bằng Chrome thay vì VSCode internal browser, bạn **BẮT BUỘC** phải disable các extension sau:

### 1. Simple Browser (VSCode)
- **Publisher:** Microsoft
- **Extension ID:** `ms-vscode.vscode-simple-browser`
- **Cách disable:** 
  - Mở Extensions (Ctrl+Shift+X)
  - Tìm "Simple Browser"
  - Click "Disable" hoặc "Uninstall"

### 2. HTML Preview
- **Tìm kiếm:** "HTML Preview" hoặc "Preview HTML"
- **Cách disable:** Disable tất cả extension có tên chứa "HTML Preview"

### 3. Open in Editor Browser
- **Tìm kiếm:** "Open in Editor Browser" hoặc "Browser Preview"
- **Cách disable:** Disable extension này

### 4. Live Preview (Microsoft)
- **Publisher:** Microsoft
- **Extension ID:** `ms-vscode.live-server` hoặc `ms-vscode.live-preview`
- **Lưu ý:** Chỉ disable "Live Preview", **KHÔNG** disable "Live Server" (cần cho development)
- **Cách disable:** Disable "Live Preview" nhưng giữ "Live Server"

### 5. Markdown Preview Enhanced
- **Extension ID:** `shd101wyy.markdown-preview-enhanced` hoặc tương tự
- **Cách disable:** Disable extension này nếu đang bật

## ✅ CÁCH KIỂM TRA

1. Mở VSCode
2. Nhấn `Ctrl+Shift+X` để mở Extensions
3. Tìm kiếm từng extension ở trên
4. Nếu thấy extension nào đang **Enabled** → Click **Disable** ngay

## 🎯 KẾT QUẢ MONG ĐỢI

Sau khi disable:
- ✅ Click link HTML → Mở Chrome
- ❌ Không còn mở trong VSCode panel
- ❌ Không còn Simple Browser
- ❌ Không còn Preview tab

## 📝 LƯU Ý

- **Live Server** (của Ritwick Dey) vẫn cần **ENABLE** để chạy development server
- Chỉ disable các extension làm mở web trong VSCode editor
- Sau khi disable, reload VSCode (Ctrl+Shift+P → "Reload Window")












<<<<<<< HEAD
=======

>>>>>>> d1581b2 (first commit)

































