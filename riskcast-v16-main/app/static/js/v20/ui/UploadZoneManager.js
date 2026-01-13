/**
 * ========================================================================
 * RISKCAST v20 - Upload Zone Manager
 * ========================================================================
 * Manages file upload zone functionality
 * 
 * @class UploadZoneManager
 */
export class UploadZoneManager {
    /**
     * @param {Object} callbacks - Callback functions (onFileUpload)
     */
    constructor(callbacks = {}) {
        this.callbacks = callbacks;
        this.uploadedFile = null;
    }
    
    /**
     * Initialize upload zone
     */
    initUploadZone() {
        const uploadZone = document.getElementById('rc-upload-zone');
        const fileInput = document.getElementById('rc-file-input');
        const uploadBtn = document.getElementById('rc-upload-btn');
        const uploadPreview = document.getElementById('rc-upload-preview');
        const fileRemove = document.getElementById('rc-file-remove');
        
        if (!uploadZone || !fileInput) return;
        
        uploadBtn.addEventListener('click', () => {
            fileInput.click();
        });
        
        uploadZone.addEventListener('click', (e) => {
            if (e.target === uploadZone || e.target.closest('.rc-upload-content')) {
                fileInput.click();
            }
        });
        
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                this.handleFileUpload(file, uploadPreview);
            }
        });
        
        // Drag & Drop
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('dragging');
        });
        
        uploadZone.addEventListener('dragleave', () => {
            uploadZone.classList.remove('dragging');
        });
        
        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragging');
            
            const file = e.dataTransfer.files[0];
            if (file) {
                this.handleFileUpload(file, uploadPreview);
            }
        });
        
        if (fileRemove) {
            fileRemove.addEventListener('click', (e) => {
                e.stopPropagation();
                this.uploadedFile = null;
                fileInput.value = '';
                uploadPreview.style.display = 'none';
                const uploadContent = document.querySelector('.rc-upload-content');
                if (uploadContent) {
                    uploadContent.style.display = 'flex';
                }
            });
        }
        
        console.log('🔥 Upload zone initialized ✓');
    }
    
    /**
     * Handle file upload
     * @param {File} file - Uploaded file
     * @param {HTMLElement} preview - Preview element
     */
    handleFileUpload(file, preview) {
        if (!preview) return;
        
        this.uploadedFile = file;
        
        if (this.callbacks.onFileUpload) {
            this.callbacks.onFileUpload(file);
        }
        
        preview.querySelector('.rc-file-name').textContent = file.name;
        preview.querySelector('.rc-file-size').textContent = this.formatFileSize(file.size);
        preview.style.display = 'block';
        
        const uploadContent = document.querySelector('.rc-upload-content');
        if (uploadContent) {
            uploadContent.style.display = 'none';
        }
        
        console.log(`File uploaded: ${file.name}`);
        
        if (this.callbacks.showToast) {
            this.callbacks.showToast(`File uploaded: ${file.name}`, 'success');
        }
    }
    
    /**
     * Format file size
     * @param {number} bytes - File size in bytes
     * @returns {string} Formatted file size
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }
}



