// LunaEngine Theme Manager
document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.querySelector('.theme-toggle');
    const themeIcon = document.querySelector('.theme-icon');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            console.log("Toggle theme to " + newTheme);
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            if (themeIcon) themeIcon.textContent = newTheme === 'dark' ? '☀️' : '🌙';
            this.innerHTML = `<span class="theme-icon">${newTheme === 'dark' ? '☀️' : '🌙'}</span>`;
        });
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        if (themeIcon) {
            themeIcon.textContent = savedTheme === 'dark' ? '☀️' : '🌙';
            themeToggle.innerHTML = `<span class="theme-icon">${savedTheme === 'dark' ? '☀️' : '🌙'}</span>`;
        }
    }
    // 3D Tilt effect for stats card
    const tiltCard = document.querySelector('.tilt-card');
    if (tiltCard) {
        tiltCard.addEventListener('mousemove', function(e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const rotateX = (y - centerY) / 10;
            const rotateY = (centerX - x) / 10;
            this.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
        });
        tiltCard.addEventListener('mouseleave', function() {
            this.style.transform = 'perspective(1000px) rotateX(0) rotateY(0)';
        });
    }
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
    document.querySelectorAll('pre code').forEach(codeBlock => {
        const pre = codeBlock.parentElement;
        const button = document.createElement('button');
        button.className = 'btn btn-sm btn-outline-secondary copy-button';
        button.innerHTML = '<i class="bi bi-clipboard"></i>';
        button.style.position = 'absolute';
        button.style.top = '10px';
        button.style.right = '10px';
        button.style.opacity = '0.7';
        pre.style.position = 'relative';
        pre.appendChild(button);
        button.addEventListener('click', function() {
            const text = codeBlock.textContent;
            navigator.clipboard.writeText(text).then(() => {
                button.innerHTML = '<i class="bi bi-check"></i>';
                button.classList.replace('btn-outline-secondary', 'btn-success');
                setTimeout(() => {
                    button.innerHTML = '<i class="bi bi-clipboard"></i>';
                    button.classList.replace('btn-success', 'btn-outline-secondary');
                }, 2000);
            });
        });
    });
    const urlParams = new URLSearchParams(window.location.search);
    const searchTerm = urlParams.get('q');
    if (searchTerm) highlightSearchTerm(searchTerm);
});

function highlightSearchTerm(term) {
    const elements = document.querySelectorAll('.card-body, .docstring-content, p, li');
    const regex = new RegExp(`(${term})`, 'gi');
    elements.forEach(element => {
        const html = element.innerHTML;
        const highlighted = html.replace(regex, '<mark class="search-highlight">$1</mark>');
        element.innerHTML = highlighted;
    });
}

// Simple markdown parser without external dependencies
function initSimpleMarkdownParser() {
    const elements = document.querySelectorAll('.markdown-content, .code-stats-content');
    
    console.log(`🔍 Found ${elements.length} markdown elements to render`);
    
    elements.forEach(element => {
        if (element.textContent && !element.classList.contains('rendered')) {
            let content = element.textContent;
            
            // Enhanced markdown parsing
            content = parseMarkdown(content);
            element.innerHTML = content;
            element.classList.add('rendered');
            
            addMarkdownStyles();
            initCopyButtons(); // Re-init copy buttons for new code blocks
            
            console.log('✅ Markdown content rendered');
        }
    });
}

function parseMarkdown(text) {
    if (!text) return '';
    
    // Processar tabelas PRIMEIRO (antes de qualquer outra coisa)
    text = parseMarkdownTables(text);
    
    // Process code blocks (proteger o conteúdo)
    text = text.replace(/```(\w+)?\n([\s\S]*?)```/g, function(match, lang, code) {
        return `<pre><code class="language-${lang || ''}">${code.trim()}</code></pre>`;
    });
    
    // Headers (só no início da linha)
    text = text.replace(/^# (.*?)$/gm, '<h1>$1</h1>');
    text = text.replace(/^## (.*?)$/gm, '<h2>$1</h2>');
    text = text.replace(/^### (.*?)$/gm, '<h3>$1</h3>');
    text = text.replace(/^#### (.*?)$/gm, '<h4>$1</h4>');
    text = text.replace(/^##### (.*?)$/gm, '<h5>$1</h5>');
    text = text.replace(/^###### (.*?)$/gm, '<h6>$1</h6>');
    
    // Bold - apenas **text** (não __text__ para evitar conflitos)
    text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    
    // Italic - apenas *text* (não _text_ para evitar conflitos)
    text = text.replace(/(^|\s)\*([^*\s][^*]*[^*\s]?)\*($|\s)/g, '$1<em>$2</em>$3');
    
    // Inline code
    text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Links
    text = text.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
    
    // Lists - unordered
    text = text.replace(/^\s*[-*+] (.*?)$/gm, '<li>$1</li>');
    // Wrap consecutive list items in ul
    text = text.replace(/(<li>.*<\/li>)/gs, function(match) {
        if (match.includes('</li><li>')) {
            return '<ul>' + match + '</ul>';
        }
        return match;
    });
    
    // Lists - ordered
    text = text.replace(/^\s*\d+\. (.*?)$/gm, '<li>$1</li>');
    text = text.replace(/(<li>.*<\/li>)/gs, function(match) {
        if (match.includes('</li><li>')) {
            return '<ol>' + match + '</ol>';
        }
        return match;
    });
    
    // Blockquotes
    text = text.replace(/^> (.*?)$/gm, '<blockquote>$1</blockquote>');
    
    // Horizontal rule
    text = text.replace(/^\s*---\s*$/gm, '<hr>');
    text = text.replace(/^\s*\*\*\*\s*$/gm, '<hr>');
    
    // IMPORTANTE: Processar parágrafos ANTES de juntar tudo
    // Dividir em blocos primeiro
    const blocks = text.split(/\n\s*\n/);
    const processedBlocks = blocks.map(block => {
        // Se já é um elemento HTML (table, pre, etc.), não envolver em <p>
        if (block.trim().startsWith('<table') || 
            block.trim().startsWith('<pre') || 
            block.trim().startsWith('<ul') || 
            block.trim().startsWith('<ol') || 
            block.trim().startsWith('<blockquote') ||
            block.trim().startsWith('<h1') ||
            block.trim().startsWith('<h2') ||
            block.trim().startsWith('<h3') ||
            block.trim().startsWith('<h4') ||
            block.trim().startsWith('<h5') ||
            block.trim().startsWith('<h6')) {
            return block;
        }
        
        // Se está vazio, pular
        if (!block.trim()) return '';
        
        // Para blocos de texto normais, substituir quebras de linha simples por <br>
        const withLineBreaks = block.replace(/\n/g, '<br>');
        return `<p>${withLineBreaks}</p>`;
    });
    
    // Juntar os blocos processados
    text = processedBlocks.filter(block => block !== '').join('\n');
    
    return text;
}

// Função específica para parse de tabelas markdown - MELHORADA
function parseMarkdownTables(text) {
    const lines = text.split('\n');
    let result = [];
    let i = 0;
    
    while (i < lines.length) {
        const line = lines[i];
        
        // Check if this could be a table start
        if (line.includes('|') && !line.includes('```') && line.trim()) {
            const tableRows = [];
            let headerRow = null;
            let separatorRow = null;
            
            // Collect potential table rows
            let j = i;
            while (j < lines.length && lines[j].includes('|') && !lines[j].includes('```') && lines[j].trim()) {
                tableRows.push(lines[j]);
                j++;
            }
            
            // Verify if it's a valid markdown table (at least 2 rows, with separator)
            if (tableRows.length >= 2) {
                headerRow = tableRows[0];
                separatorRow = tableRows[1];
                
                // Check if separator row has dashes (markdown table format)
                if (separatorRow.replace(/[^\-|]/g, '').length > 0 && 
                    separatorRow.includes('-')) {
                    // It's a valid table!
                    result.push(convertMarkdownTableToHTML(tableRows));
                    i = j; // Skip the processed rows
                    continue;
                }
            }
        }
        
        // If not a table, just add the line as is
        result.push(line);
        i++;
    }
    
    return result.join('\n');
}

function convertMarkdownTableToHTML(tableRows) {
    if (tableRows.length < 2) return tableRows.join('\n');
    
    let html = '<table>\n';
    
    // Header row
    const headerCells = splitTableRow(tableRows[0]);
    html += '  <thead>\n    <tr>\n';
    headerCells.forEach(cell => {
        html += `      <th>${cell.trim()}</th>\n`;
    });
    html += '    </tr>\n  </thead>\n';
    
    // Data rows (skip the separator row at index 1)
    html += '  <tbody>\n';
    for (let i = 2; i < tableRows.length; i++) {
        const cells = splitTableRow(tableRows[i]);
        if (cells.length > 0) {
            html += '    <tr>\n';
            cells.forEach(cell => {
                // Processar formatação básica dentro das células
                let cellContent = cell.trim();
                cellContent = cellContent.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
                cellContent = cellContent.replace(/\*([^*]+)\*/g, '<em>$1</em>');
                cellContent = cellContent.replace(/`([^`]+)`/g, '<code>$1</code>');
                html += `      <td>${cellContent}</td>\n`;
            });
            html += '    </tr>\n';
        }
    }
    html += '  </tbody>\n</table>';
    
    return html;
}

function splitTableRow(row) {
    return row.split('|')
        .map(cell => cell.trim())
        .filter(cell => cell !== '' && !/^\-+$/.test(cell));
}

function addMarkdownStyles() {
    if (!document.getElementById('markdown-styles')) {
        const styles = `
            <style id="markdown-styles">
            .markdown-content, .code-stats-content {
                line-height: 1.6;
            }
            
            .markdown-content table, .code-stats-content table {
                width: 100%;
                border-collapse: collapse;
                margin: 0.5rem 0 1rem 0; /* MENOS espaçamento */
                background: white;
                font-size: 0.9em;
            }
            .markdown-content th, .code-stats-content th,
            .markdown-content td, .code-stats-content td {
                padding: 0.5rem 0.75rem; /* Padding mais compacto */
                border: 1px solid #dee2e6;
                text-align: left;
            }
            .markdown-content th, .code-stats-content th {
                background-color: #f8f9fa;
                font-weight: bold;
                color: #495057;
                font-size: 0.85em;
            }
            .markdown-content td, .code-stats-content td {
                font-size: 0.85em;
            }
            
            /* Espaçamento geral melhorado */
            .markdown-content p, .code-stats-content p {
                margin: 0.5rem 0 1rem 0;
            }
            
            .markdown-content h1, .code-stats-content h1 { 
                font-size: 2rem; 
                margin: 1rem 0 0.5rem 0; /* Menos margem */
            }
            .markdown-content h2, .code-stats-content h2 { 
                font-size: 1.75rem; 
                margin: 0.75rem 0 0.5rem 0;
                border-bottom: 1px solid #dee2e6;
                padding-bottom: 0.25rem;
                color: #343a40;
            }
            .markdown-content h3, .code-stats-content h3 { 
                font-size: 1.5rem; 
                margin: 1rem 0 0.5rem 0; 
                color: #495057;
            }
            .markdown-content h4, .code-stats-content h4 { 
                font-size: 1.25rem; 
                margin: 0.75rem 0 0.5rem 0; 
                color: #6c757d;
            }
            .markdown-content h5, .code-stats-content h5 { 
                font-size: 1.1rem; 
                margin: 0.5rem 0; 
                color: #6c757d;
            }
            .markdown-content h6, .code-stats-content h6 { 
                font-size: 1rem; 
                margin: 0.5rem 0; 
                color: #6c757d;
            }
            .markdown-content hr, .code-stats-content hr {
                border: none;
                border-top: 2px solid #dee2e6;
                margin: 2rem 0;
            }
            .markdown-content a, .code-stats-content a {
                color: #007bff;
                text-decoration: none;
            }
            .markdown-content a:hover, .code-stats-content a:hover {
                text-decoration: underline;
            }
            
            /* Dark theme support */
            [data-theme="dark"] .markdown-content,
            [data-theme="dark"] .code-stats-content {
                color: #e9ecef;
            }
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
                border-color: #718096;
            }
            [data-theme="dark"] .markdown-content table,
            [data-theme="dark"] .code-stats-content table {
                border-color: #718096;
                background-color: #2d3748;
            }
            [data-theme="dark"] .markdown-content td,
            [data-theme="dark"] .code-stats-content td {
                border-color: #718096;
                color: #e2e8f0;
            }
            [data-theme="dark"] .markdown-content blockquote,
            [data-theme="dark"] .code-stats-content blockquote {
                background-color: #2d3748;
                border-left-color: #63b3ed;
                color: #cbd5e0;
            }
            [data-theme="dark"] .markdown-content h1,
            [data-theme="dark"] .code-stats-content h1,
            [data-theme="dark"] .markdown-content h2,
            [data-theme="dark"] .code-stats-content h2,
            [data-theme="dark"] .markdown-content h3,
            [data-theme="dark"] .code-stats-content h3 {
                color: #f7fafc;
                border-color: #4a5568;
            }
            [data-theme="dark"] .markdown-content a,
            [data-theme="dark"] .code-stats-content a {
                color: #63b3ed;
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

// Also initialize when navigating
document.addEventListener('DOMContentLoaded', function() {
    // document.getElementById('navbar-logo-link').addEventListener('click', function(e) {
    //     e.preventDefault();
    //     window.location.href = '/';
    // })
    setTimeout(initSimpleMarkdownParser, 100);
});