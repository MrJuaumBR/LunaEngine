// LunaEngine Documentation JavaScript
$(document).ready(function() {
    console.log('🚀 LunaEngine Theme initialized');
    
    // Theme Toggle
    $('.theme-toggle').click(function() {
        const currentTheme = $('html').attr('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        $('html').attr('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        // Update theme icon
        const themeIcon = $('.theme-icon');
        themeIcon.text(newTheme === 'light' ? '🌙' : '☀️');
    });
    
    // Load saved theme
    const savedTheme = localStorage.getItem('theme') || 'light';
    $('html').attr('data-theme', savedTheme);
    $('.theme-icon').text(savedTheme === 'light' ? '🌙' : '☀️');
    
    // Simple search redirect functionality
    $('#moduleSearch').on('keypress', function(e) {
        if (e.which === 13) { // Enter key
            const searchTerm = $(this).val().trim();
            if (searchTerm) {
                // Redirect to search page
                if (window.location.pathname.includes('search.html')) {
                    // If already on search page, trigger search
                    if (window.lunaSearch) {
                        window.lunaSearch.performSearch();
                    }
                } else {
                    // Redirect to search page
                    window.location.href = `search.html?q=${encodeURIComponent(searchTerm)}`;
                }
            }
        }
    });
    
    // Search button click
    $('#searchButton').on('click', function() {
        const searchTerm = $('#globalSearch').val().trim();
        if (searchTerm) {
            if (window.location.pathname.includes('search.html')) {
                if (window.lunaSearch) {
                    window.lunaSearch.performSearch();
                }
            } else {
                window.location.href = `search.html?q=${encodeURIComponent(searchTerm)}`;
            }
        }
    });
    
    // Quick search on input (for search page only)
    if (window.location.pathname.includes('search.html')) {
        $('#globalSearch').on('input', debounce(function() {
            const term = $(this).val().trim();
            if (term.length >= 2 && window.lunaSearch) {
                window.lunaSearch.performSearch();
            } else if (term.length === 0 && window.lunaSearch) {
                window.lunaSearch.showSearchInfo();
            }
        }, 300));
    }
    
    // Smooth scrolling for anchor links
    $(document).on('click', 'a[href^="#"]', function(event) {
        event.preventDefault();
        const target = $($(this).attr('href'));
        
        if (target.length) {
            $('html, body').animate({
                scrollTop: target.offset().top - 70
            }, 500);
        }
    });
    
    // Copy to clipboard for code blocks
    initCopyButtons();
    
    // Code Statistics Collapse
    initCodeStats();
    
    // Initialize search if on search page
    if (window.location.pathname.includes('search.html')) {
        initSearchPage();
    }
    
    // Initialize markdown parser
    setTimeout(initMarkdownParser, 100);
});

// Markdown parser using Marked.js
function initMarkdownParser() {
    // Check if we have any markdown content to render
    const markdownElements = document.querySelectorAll('.markdown-content, .code-stats-content');
    if (markdownElements.length === 0) return;
    
    // Load marked.js if not already loaded
    if (typeof marked === 'undefined') {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
        script.onload = function() {
            console.log('✅ Marked.js loaded');
            renderMarkdownContent();
        };
        script.onerror = function() {
            console.error('❌ Failed to load Marked.js');
            fallbackMarkdownRender();
        };
        document.head.appendChild(script);
    } else {
        renderMarkdownContent();
    }
}

function renderMarkdownContent() {
    // Find all elements with markdown content
    const markdownElements = document.querySelectorAll('.markdown-content, .code-stats-content');
    
    markdownElements.forEach(element => {
        if (element.textContent && !element.classList.contains('rendered')) {
            const markdownText = element.textContent;
            
            // Configure marked options
            marked.setOptions({
                breaks: true,
                gfm: true,
                tables: true,
                sanitize: false
            });
            
            try {
                // Convert markdown to HTML
                const htmlContent = marked.parse(markdownText);
                element.innerHTML = htmlContent;
                element.classList.add('rendered');
                
                // Add CSS for markdown elements
                addMarkdownStyles();
                
                console.log('✅ Markdown content rendered');
            } catch (error) {
                console.error('❌ Markdown parsing error:', error);
                fallbackMarkdownRender(element);
            }
        }
    });
}

function fallbackMarkdownRender(element = null) {
    // Basic fallback rendering without marked.js
    const elements = element ? [element] : document.querySelectorAll('.markdown-content, .code-stats-content');
    
    elements.forEach(el => {
        if (!el.classList.contains('rendered')) {
            let content = el.textContent;
            
            // Very basic markdown replacements as fallback
            content = content
                .replace(/^# (.*$)/gim, '<h1>$1</h1>')
                .replace(/^## (.*$)/gim, '<h2>$1</h2>')
                .replace(/^### (.*$)/gim, '<h3>$1</h3>')
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/`(.*?)`/g, '<code>$1</code>')
                .replace(/\n\n/g, '</p><p>')
                .replace(/\n/g, '<br>');
            
            if (!content.startsWith('<')) {
                content = '<p>' + content + '</p>';
            }
            
            el.innerHTML = content;
            el.classList.add('rendered');
            addMarkdownStyles();
        }
    });
}

function addMarkdownStyles() {
    if (!document.getElementById('markdown-styles')) {
        const styles = `
            <style id="markdown-styles">
            .markdown-content table, .code-stats-content table {
                width: 100%;
                border-collapse: collapse;
                margin: 1rem 0;
            }
            .markdown-content th, .code-stats-content th,
            .markdown-content td, .code-stats-content td {
                padding: 0.5rem;
                border: 1px solid #dee2e6;
                text-align: left;
            }
            .markdown-content th, .code-stats-content th {
                background-color: #f8f9fa;
                font-weight: bold;
            }
            .markdown-content code, .code-stats-content code {
                background-color: #f8f9fa;
                padding: 0.2rem 0.4rem;
                border-radius: 0.25rem;
                font-family: 'Courier New', monospace;
                font-size: 0.875em;
            }
            .markdown-content pre, .code-stats-content pre {
                background-color: #f8f9fa;
                padding: 1rem;
                border-radius: 0.375rem;
                overflow-x: auto;
                margin: 1rem 0;
            }
            .markdown-content pre code, .code-stats-content pre code {
                background: none;
                padding: 0;
            }
            .markdown-content blockquote, .code-stats-content blockquote {
                border-left: 4px solid #007bff;
                padding-left: 1rem;
                margin-left: 0;
                color: #6c757d;
                font-style: italic;
            }
            .markdown-content ul, .code-stats-content ul,
            .markdown-content ol, .code-stats-content ol {
                margin: 1rem 0;
                padding-left: 2rem;
            }
            .markdown-content li, .code-stats-content li {
                margin: 0.5rem 0;
            }
            .markdown-content h1, .code-stats-content h1 { 
                font-size: 2rem; 
                margin: 1.5rem 0 1rem 0; 
                border-bottom: 2px solid #dee2e6;
                padding-bottom: 0.5rem;
            }
            .markdown-content h2, .code-stats-content h2 { 
                font-size: 1.75rem; 
                margin: 1.25rem 0 0.75rem 0; 
                border-bottom: 1px solid #dee2e6;
                padding-bottom: 0.25rem;
            }
            .markdown-content h3, .code-stats-content h3 { 
                font-size: 1.5rem; 
                margin: 1rem 0 0.5rem 0; 
            }
            .markdown-content h4, .code-stats-content h4 { 
                font-size: 1.25rem; 
                margin: 0.75rem 0 0.5rem 0; 
            }
            .markdown-content h5, .code-stats-content h5 { 
                font-size: 1.1rem; 
                margin: 0.5rem 0; 
            }
            .markdown-content h6, .code-stats-content h6 { 
                font-size: 1rem; 
                margin: 0.5rem 0; 
            }
            
            /* Dark theme support */
            [data-theme="dark"] .markdown-content code,
            [data-theme="dark"] .code-stats-content code,
            [data-theme="dark"] .markdown-content pre,
            [data-theme="dark"] .code-stats-content pre {
                background-color: #2d3748;
                color: #e2e8f0;
            }
            [data-theme="dark"] .markdown-content th,
            [data-theme="dark"] .code-stats-content th {
                background-color: #4a5568;
                color: #e2e8f0;
            }
            [data-theme="dark"] .markdown-content table,
            [data-theme="dark"] .code-stats-content table {
                border-color: #4a5568;
            }
            [data-theme="dark"] .markdown-content td,
            [data-theme="dark"] .code-stats-content td {
                border-color: #4a5568;
                color: #e2e8f0;
            }
            </style>
        `;
        document.head.insertAdjacentHTML('beforeend', styles);
    }
}

function initCopyButtons() {
    $('pre').each(function() {
        const $pre = $(this);
        // Check if copy button already exists
        if ($pre.find('.copy-btn').length === 0) {
            const $copyBtn = $('<button class="btn btn-sm btn-outline-secondary copy-btn">Copy</button>');
            
            $pre.css('position', 'relative').append($copyBtn);
            
            $copyBtn.on('click', function() {
                const code = $pre.find('code').text() || $pre.text();
                navigator.clipboard.writeText(code).then(() => {
                    $copyBtn.text('Copied!');
                    setTimeout(() => $copyBtn.text('Copy'), 2000);
                }).catch(err => {
                    console.error('Failed to copy text: ', err);
                    $copyBtn.text('Failed!');
                    setTimeout(() => $copyBtn.text('Copy'), 2000);
                });
            });
        }
    });
}

function initCodeStats() {
    const $collapse = $('#codeStatsCollapse');
    const $toggleBtn = $('[data-bs-target="#codeStatsCollapse"]');
    
    if ($collapse.length && $toggleBtn.length) {
        const statsCollapsed = localStorage.getItem('statsCollapsed') === 'true';
        
        if (statsCollapsed) {
            $collapse.removeClass('show');
            $toggleBtn.find('i').removeClass('bi-chevron-down').addClass('bi-chevron-right');
        }
        
        $toggleBtn.on('click', function() {
            setTimeout(() => {
                const isCollapsed = !$collapse.hasClass('show');
                localStorage.setItem('statsCollapsed', isCollapsed);
                $toggleBtn.find('i').toggleClass('bi-chevron-down bi-chevron-right', isCollapsed);
            }, 350);
        });
    }
}

function initSearchPage() {
    // Load search.js if not already loaded
    if (typeof window.LunaEngineSearch === 'undefined') {
        console.log('Loading search engine...');
        // The search.js will initialize itself
    }
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Utility function to escape HTML
function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Also initialize markdown when navigating (for SPAs)
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(initMarkdownParser, 100);
});

// Re-render markdown when theme changes (in case styles need update)
$(document).on('themeChange', function() {
    setTimeout(initMarkdownParser, 50);
});