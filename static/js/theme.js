// Theme management
const themes = ['light', 'dark', 'medical'];
let currentTheme = localStorage.getItem('theme') || 'light';

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    currentTheme = theme;
}

function initTheme() {
    // Create theme switcher
    const switcher = document.createElement('div');
    switcher.className = 'theme-switcher';
    
    themes.forEach(theme => {
        const btn = document.createElement('button');
        btn.className = 'theme-btn';
        btn.setAttribute('data-theme', theme);
        btn.style.background = theme === 'dark' ? '#1e293b' : 
                             theme === 'medical' ? '#059669' : '#ffffff';
        btn.onclick = () => setTheme(theme);
        switcher.appendChild(btn);
    });

    document.body.appendChild(switcher);
    
    // Set initial theme
    setTheme(currentTheme);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Set default theme if none is stored
    if (!localStorage.getItem('theme')) {
        localStorage.setItem('theme', 'light');
    }
    
    // Apply the stored theme
    applyTheme(localStorage.getItem('theme'));
    
    // Add theme switcher functionality if it exists
    const themeSwitcher = document.getElementById('theme-switcher');
    if (themeSwitcher) {
        themeSwitcher.addEventListener('change', (e) => {
            const theme = e.target.value;
            applyTheme(theme);
            localStorage.setItem('theme', theme);
        });
    }
});

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    
    // Update theme switcher if it exists
    const themeSwitcher = document.getElementById('theme-switcher');
    if (themeSwitcher) {
        themeSwitcher.value = theme;
    }
} 