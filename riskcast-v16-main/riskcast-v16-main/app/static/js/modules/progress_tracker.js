
function initializeSmartProgressTracking() {
    // Định nghĩa các trường bắt buộc cho mỗi section
    const sectionRequiredFields = {
        'shipping-info': [
            'route', 'transport_mode', 'pol', 'pod', 'shipment-month'
        ],
        'cargo-details': [
            'cargo_type', 'etd', 'eta', 'cargo_value'
        ],
        'seller-info': [
            // Seller info không có required fields - optional
        ],
        'buyer-info': [
            // Buyer info không có required fields - optional
        ],
        'algorithm-modules': [
            // Algorithm modules không có required - chỉ cần ít nhất 1 module được chọn
        ]
    };

    // Helper function để lấy giá trị từ dropdown
    function getDropdownValue(fieldId) {
        // Kiểm tra hidden input trước
        const hiddenInput = document.getElementById(fieldId + '_input');
        if (hiddenInput && hiddenInput.value && hiddenInput.value.trim() !== '') {
            return hiddenInput.value.trim();
        }
        
        // Kiểm tra dropdown
        const dropdown = document.getElementById(fieldId + '_dropdown');
        if (!dropdown) return null;
        
        // Kiểm tra selected option
        const selectedOption = dropdown.querySelector('.dropdown-option.selected');
        if (selectedOption) {
            const value = selectedOption.getAttribute('data-value');
            if (value && value.trim() !== '') return value.trim();
        }
        
        // Kiểm tra dropdown value display
        const dropdownValue = dropdown.querySelector('.dropdown-value');
        if (dropdownValue && !dropdownValue.classList.contains('placeholder')) {
            const value = dropdownValue.textContent.trim();
            if (value && value !== 'Chưa chọn' && value !== 'Select' && value.length > 0) {
                return value;
            }
        }
        
        return null;
    }

    // Kiểm tra field có được điền hay không
    function isFieldFilled(fieldId) {
        // Kiểm tra input thường
        const input = document.getElementById(fieldId);
        if (input) {
            if (input.type === 'checkbox') {
                return input.checked;
            }
            const value = input.value ? input.value.trim() : '';
            // Bỏ qua các giá trị mặc định không hợp lệ
            if (value === '' || value === '0' || value === '--' || value === 'Chưa chọn') {
                return false;
            }
            return value.length > 0;
        }

        // Kiểm tra dropdown
        const dropdownValue = getDropdownValue(fieldId);
        if (dropdownValue) {
            return dropdownValue.length > 0 && !dropdownValue.includes('placeholder');
        }

        return false;
    }

    // Tính tiến độ của một section dựa trên các trường bắt buộc
    function calculateSectionProgress(sectionId) {
        const section = document.getElementById(sectionId);
        if (!section) return 0;

        const requiredFields = sectionRequiredFields[sectionId] || [];
        
        // Special case cho algorithm-modules: chỉ cần ít nhất 1 module được chọn
        if (sectionId === 'algorithm-modules') {
            const modules = ['use_fuzzy', 'use_forecast', 'use_mc', 'use_var'];
            const checkedModules = modules.filter(moduleId => {
                const checkbox = document.getElementById(moduleId);
                return checkbox && checkbox.checked;
            });
            return checkedModules.length > 0 ? 100 : 0;
        }

        if (requiredFields.length === 0) {
            // Nếu không có required fields (seller-info, buyer-info), section tự động hoàn thành
            // Nhưng có thể kiểm tra xem có field nào được điền không để hiển thị progress
            const allInputs = section.querySelectorAll('input:not([type="hidden"]), select, .custom-dropdown');
            const filledInputs = Array.from(allInputs).filter(input => {
                if (input.type === 'checkbox') return input.checked;
                if (input.value && input.value.trim() !== '' && input.value.trim() !== '0') return true;
                return false;
            });
            // Nếu có ít nhất 1 field được điền, coi như 50% progress
            return filledInputs.length > 0 ? 50 : 0;
        }

        const filledFields = requiredFields.filter(fieldId => isFieldFilled(fieldId));
        const progress = (filledFields.length / requiredFields.length) * 100;
        
        return Math.round(progress);
    }

    // Track completed sections
    const completedSectionsTracker = new Set();
    let allSectionsCompleted = false;
    let currentActiveSection = null;

    // Main progress update function
    window.updateProgress = function() {
        const mainSections = [
            { id: 'shipping-info', name: 'Thông Tin Vận Chuyển', index: 0 },
            { id: 'cargo-details', name: 'Chi Tiết Hàng Hóa', index: 1 },
            { id: 'seller-info', name: 'Thông Tin Người Bán', index: 2 },
            { id: 'buyer-info', name: 'Thông Tin Người Mua', index: 3 },
            { id: 'algorithm-modules', name: 'Mô-đun Thuật Toán', index: 4 }
        ];

        let completedSections = 0;

        mainSections.forEach((section, index) => {
            const progress = calculateSectionProgress(section.id);
            const isCompleted = progress === 100; // Chỉ hoàn thành khi 100%
            const wasCompleted = completedSectionsTracker.has(section.id);

            if (isCompleted) {
                completedSections++;
                if (!wasCompleted) {
                    completedSectionsTracker.add(section.id);
                    showSectionCompletionNotification(section.name);
                }
            } else {
                if (wasCompleted) {
                    completedSectionsTracker.delete(section.id);
                }
            }

            // Update progress bar visuals
            updateSectionProgressBar(section, progress, isCompleted, index);
        });

        // Update overall progress
        const overallProgress = (completedSections / mainSections.length) * 100;
        
        // Update header progress
        updateHeaderProgress(overallProgress, completedSections);
        
        // Update sticky progress bar
        updateStickyProgressBar(overallProgress, completedSections);

        // Show ready notification
        if (completedSections === 5 && !allSectionsCompleted) {
            allSectionsCompleted = true;
            showReadyToAnalyzeNotification();
        } else if (completedSections < 5 && allSectionsCompleted) {
            allSectionsCompleted = false;
        }
    };

    // Update section progress bar visuals
    function updateSectionProgressBar(section, progress, isCompleted, index) {
        const sectionElement = document.querySelector(`.progress-section[data-section="${section.id}"]`);
        const sectionFill = sectionElement?.querySelector('.progress-section-fill');
        const sectionIndicator = sectionElement?.querySelector('.progress-section-indicator');
        
        if (sectionFill) {
            sectionFill.style.width = progress + '%';
            
            if (isCompleted && !sectionElement.classList.contains('completed')) {
                sectionElement.classList.add('completed');
                sectionFill.style.background = 'linear-gradient(90deg, #10B981, #34D399)';
                sectionFill.style.boxShadow = '0 0 20px rgba(16, 185, 129, 0.6)';
                
                if (sectionIndicator) {
                    sectionIndicator.innerHTML = '✓';
                    sectionIndicator.style.color = '#10B981';
                    sectionIndicator.style.fontSize = '14px';
                    sectionIndicator.style.fontWeight = '700';
                }
            } else if (!isCompleted) {
                sectionElement.classList.remove('completed');
                sectionFill.style.background = progress > 0 
                    ? 'linear-gradient(90deg, rgba(16, 185, 129, 0.5), rgba(16, 185, 129, 0.3))'
                    : 'rgba(255,255,255,0.05)';
                sectionFill.style.boxShadow = '';
                
                if (sectionIndicator) {
                    sectionIndicator.innerHTML = String(index + 1).padStart(2, '0');
                    sectionIndicator.style.color = progress > 0 ? 'rgba(255,255,255,0.7)' : 'rgba(255,255,255,0.5)';
                    sectionIndicator.style.fontSize = '11px';
                    sectionIndicator.style.fontWeight = '600';
                }
            }
        }

        // Update sticky progress bar
        const stickySectionElement = document.querySelector(`#sticky-progress-bar .progress-section[data-section="${section.id}"]`);
        const stickySectionFill = stickySectionElement?.querySelector('.progress-section-fill');
        const stickySectionIndicator = stickySectionElement?.querySelector('.progress-section-indicator');
        
        if (stickySectionFill) {
            stickySectionFill.style.width = progress + '%';
            
            if (isCompleted && !stickySectionElement.classList.contains('completed')) {
                stickySectionElement.classList.add('completed');
                stickySectionFill.style.background = 'linear-gradient(90deg, #10B981, #34D399)';
                
                if (stickySectionIndicator) {
                    stickySectionIndicator.innerHTML = '✓';
                    stickySectionIndicator.style.color = '#10B981';
                    stickySectionIndicator.style.fontSize = '14px';
                    stickySectionIndicator.style.fontWeight = '700';
                }
            } else if (!isCompleted) {
                stickySectionElement.classList.remove('completed');
                stickySectionFill.style.background = progress > 0 
                    ? 'linear-gradient(90deg, rgba(16, 185, 129, 0.5), rgba(16, 185, 129, 0.3))'
                    : 'rgba(255,255,255,0.05)';
                
                if (stickySectionIndicator) {
                    stickySectionIndicator.innerHTML = String(index + 1).padStart(2, '0');
                    stickySectionIndicator.style.color = progress > 0 ? 'rgba(255,255,255,0.7)' : 'rgba(255,255,255,0.5)';
                    stickySectionIndicator.style.fontSize = '11px';
                    stickySectionIndicator.style.fontWeight = '600';
                }
            }
        }

        // Update section number badge
        const sectionNumber = document.querySelector(`#${section.id} .section-number, #${section.id} .section-number-badge`);
        if (sectionNumber) {
            if (isCompleted) {
                sectionNumber.style.background = '#10B981';
                sectionNumber.style.color = '#000';
                sectionNumber.style.fontWeight = '900';
                sectionNumber.style.boxShadow = '0 0 20px rgba(16, 185, 129, 0.6)';
            } else if (progress > 0) {
                sectionNumber.style.background = 'rgba(16, 185, 129, 0.5)';
                sectionNumber.style.color = '#fff';
                sectionNumber.style.fontWeight = '700';
                sectionNumber.style.boxShadow = '';
            } else {
                sectionNumber.style.background = '';
                sectionNumber.style.color = '';
                sectionNumber.style.fontWeight = '';
                sectionNumber.style.boxShadow = '';
            }
        }
    }

    // Update header progress
    function updateHeaderProgress(overallProgress, completedSections) {
        const progressText = document.getElementById('header_progress_text');
        const sectionsText = document.getElementById('progress-sections-text');
        
        if (progressText) {
            progressText.textContent = Math.round(overallProgress) + '%';
        }
        
        if (sectionsText) {
            sectionsText.textContent = `${completedSections}/5 phần đã hoàn thành`;
            sectionsText.style.color = completedSections === 5 ? '#10B981' : 'rgba(255,255,255,0.6)';
            sectionsText.style.fontWeight = completedSections === 5 ? '700' : '500';
        }
    }

    // Update sticky progress bar
    function updateStickyProgressBar(overallProgress, completedSections) {
        const stickyProgressText = document.getElementById('sticky-progress-text');
        const stickySectionsText = document.getElementById('sticky-progress-sections-text');
        
        if (stickyProgressText) {
            stickyProgressText.textContent = Math.round(overallProgress) + '%';
        }
        
        if (stickySectionsText) {
            stickySectionsText.textContent = `${completedSections}/5 phần đã hoàn thành`;
            stickySectionsText.style.color = completedSections === 5 ? '#10B981' : 'rgba(255,255,255,0.7)';
            stickySectionsText.style.fontWeight = completedSections === 5 ? '700' : '500';
        }
    }

    // Show section completion notification
    function showSectionCompletionNotification(sectionName) {
        const container = document.getElementById('progress-notification-container');
        if (!container) return;
        
        const notification = document.createElement('div');
        notification.className = 'progress-notification completed';
        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-icon">✓</div>
                <div class="notification-text">
                    <div class="notification-title">Đã hoàn thành!</div>
                    <div class="notification-message">Phần "${sectionName}" đã được nhập đầy đủ</div>
                </div>
            </div>
        `;
        
        container.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'notificationSlideDown 0.3s reverse forwards';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    // Show ready to analyze notification
    function showReadyToAnalyzeNotification() {
        const container = document.getElementById('progress-notification-container');
        if (!container) return;
        
        const notification = document.createElement('div');
        notification.className = 'progress-notification ready';
        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-icon">🚀</div>
                <div class="notification-text">
                    <div class="notification-title">Sẵn Sàng Phân Tích!</div>
                    <div class="notification-message">Tất cả thông tin đã được nhập đầy đủ. Bạn có thể chạy phân tích ngay bây giờ.</div>
                </div>
            </div>
        `;
        
        container.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'notificationSlideDown 0.3s reverse forwards';
            setTimeout(() => notification.remove(), 5000);
        }, 5000);
    }

    // Warning khi chuyển section chưa hoàn thành
    function showIncompleteSectionWarning(sectionName, missingFields) {
        const container = document.getElementById('progress-notification-container');
        if (!container) return;
        
        const notification = document.createElement('div');
        notification.className = 'progress-notification warning';
        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-icon">⚠️</div>
                <div class="notification-text">
                    <div class="notification-title">Chưa hoàn thành!</div>
                    <div class="notification-message">Phần "${sectionName}" chưa được điền đầy đủ. Vui lòng hoàn thành trước khi tiếp tục.</div>
                </div>
            </div>
        `;
        
        container.appendChild(notification);
        
        // Auto scroll to section
        const section = document.querySelector(`#${sectionName.toLowerCase().replace(/\s+/g, '-')}`);
        if (section) {
            section.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        
        setTimeout(() => {
            notification.style.animation = 'notificationSlideDown 0.3s reverse forwards';
            setTimeout(() => notification.remove(), 4000);
        }, 4000);
    }

    // Setup navigation warnings
    function setupNavigationWarnings() {
        const sectionHeaders = document.querySelectorAll('.section-header');
        
        sectionHeaders.forEach(header => {
            header.addEventListener('click', function(e) {
                const section = this.closest('.form-section');
                if (!section) return;
                
                const sectionId = section.id;
                const progress = calculateSectionProgress(sectionId);
                
                // Nếu section chưa hoàn thành (progress < 100%)
                if (progress < 100 && sectionId !== 'shipping-info') {
                    // Kiểm tra section trước đó có hoàn thành chưa
                    const sections = ['shipping-info', 'cargo-details', 'seller-info', 'buyer-info', 'algorithm-modules'];
                    const currentIndex = sections.indexOf(sectionId);
                    if (currentIndex > 0) {
                        const prevSectionId = sections[currentIndex - 1];
                        const prevProgress = calculateSectionProgress(prevSectionId);
                        
                        if (prevProgress < 100) {
                            e.preventDefault();
                            e.stopPropagation();
                            
                            const sectionNames = {
                                'shipping-info': 'Thông Tin Vận Chuyển',
                                'cargo-details': 'Chi Tiết Hàng Hóa',
                                'seller-info': 'Thông Tin Người Bán',
                                'buyer-info': 'Thông Tin Người Mua',
                                'algorithm-modules': 'Mô-đun Thuật Toán'
                            };
                            
                            showIncompleteSectionWarning(sectionNames[prevSectionId], []);
                            return false;
                        }
                    }
                }
            });
        });
    }

    // Setup sticky progress bar
    function setupStickyProgressBar() {
        const closeBtn = document.getElementById('close-progress-bar');
        const stickyBar = document.getElementById('sticky-progress-bar');
        
        if (closeBtn && stickyBar) {
            closeBtn.addEventListener('click', () => {
                stickyBar.classList.add('hidden');
                setTimeout(() => {
                    stickyBar.style.display = 'none';
                }, 300);
            });
        }
        
        let lastScrollTop = 0;
        let stickyBarVisible = false;
        
        function handleScroll() {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            
            if (!stickyBar) return;
            
            if (scrollTop > 200 && !stickyBarVisible) {
                stickyBar.style.display = 'block';
                stickyBarVisible = true;
            } else if (scrollTop <= 200 && stickyBarVisible) {
                stickyBar.style.display = 'none';
                stickyBarVisible = false;
            }
            
            lastScrollTop = scrollTop;
        }
        
        window.addEventListener('scroll', handleScroll, { passive: true });
        handleScroll();
    }

    // Debounced progress update
    let progressUpdateScheduled = false;
    window.scheduleProgressUpdate = function() {
        if (progressUpdateScheduled) return;
        progressUpdateScheduled = true;
        
        const runner = () => {
            progressUpdateScheduled = false;
            if (typeof window.updateProgress === 'function') {
                window.updateProgress();
            }
        };
        
        if (window.requestAnimationFrame) {
            window.requestAnimationFrame(runner);
        } else {
            setTimeout(runner, 16);
        }
    };

    // Initialize
    setTimeout(() => {
        window.updateProgress(); // Initial update - should be 0%
        setupNavigationWarnings();
        setupStickyProgressBar();
    }, 100);
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeSmartProgressTracking);
} else {
    initializeSmartProgressTracking();
}

