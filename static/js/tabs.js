function initTabs() {
    const tabContainers = document.querySelectorAll('.tab-container');
    
    tabContainers.forEach(container => {
        const tabButtons = container.querySelectorAll('.tab-nav .tab-button');
        const tabPanels = container.querySelectorAll('.tab-panel');
        
        // Set initial active tab
        if (tabButtons.length > 0 && tabPanels.length > 0) {
            // Don't add active class if it's already set in the HTML
            if (!tabButtons[0].classList.contains('active')) {
                tabButtons[0].classList.add('active');
            }
            if (!tabPanels[0].classList.contains('active')) {
                tabPanels[0].classList.add('active');
            }
        }
        
        // Add click handlers to tab buttons
        tabButtons.forEach((button, index) => {
            button.addEventListener('click', () => {
                // Remove active class from all buttons and panels
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabPanels.forEach(panel => panel.classList.remove('active'));
                
                // Add active class to clicked button and corresponding panel
                button.classList.add('active');
                
                // Get target panel based on data-tab attribute
                const tabId = button.getAttribute('data-tab');
                let targetPanel;
                
                if (tabId) {
                    targetPanel = container.querySelector(`#${tabId}`);
                } else {
                    targetPanel = tabPanels[index];
                }
                
                if (targetPanel) {
                    targetPanel.classList.add('active');
                }
                
                // Save active tab to localStorage if container has an id
                const containerId = container.getAttribute('id');
                if (containerId) {
                    localStorage.setItem(`activeTab-${containerId}`, index);
                }
            });
        });
        
        // Restore active tab from localStorage if available
        const containerId = container.getAttribute('id');
        if (containerId) {
            const activeTabIndex = localStorage.getItem(`activeTab-${containerId}`);
            if (activeTabIndex !== null && tabButtons[activeTabIndex] && tabPanels[activeTabIndex]) {
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabPanels.forEach(panel => panel.classList.remove('active'));
                
                tabButtons[activeTabIndex].classList.add('active');
                tabPanels[activeTabIndex].classList.add('active');
            }
        }
    });
}

// Function to switch to a specific tab programmatically
function switchTab(containerId, tabIndex) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const tabButtons = container.querySelectorAll('.tab-nav .tab-button');
    const tabPanels = container.querySelectorAll('.tab-panel');
    
    if (tabButtons[tabIndex] && tabPanels[tabIndex]) {
        tabButtons.forEach(btn => btn.classList.remove('active'));
        tabPanels.forEach(panel => panel.classList.remove('active'));
        
        tabButtons[tabIndex].classList.add('active');
        tabPanels[tabIndex].classList.add('active');
        
        localStorage.setItem(`activeTab-${containerId}`, tabIndex);
    }
}

// Initialize tabs when DOM is loaded
document.addEventListener('DOMContentLoaded', initTabs); 