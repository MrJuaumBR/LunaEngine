// LunaEngine Search Engine - GLOBAL SEARCH WITH JSON DATA
class LunaEngineSearch {
    constructor() {
        this.searchIndex = [];
        this.currentSearchTerm = '';
        this.isLoading = false;
        this.init();
    }

    async init() {
        await this.loadSearchData();
        this.setupEventListeners();
        this.processURLSearch();
        console.log('🔍 Global search engine initialized with', this.searchIndex.length, 'items');
    }

    async loadSearchData() {
        try {
            this.isLoading = true;
            console.log('📥 Loading global search data...');
            
            const response = await fetch('search-data.json');
            if (!response.ok) {
                throw new Error('Failed to load search data');
            }
            
            const data = await response.json();
            this.buildSearchIndexFromData(data);
            this.isLoading = false;
            
            console.log('✅ Search data loaded:', {
                modules: data.modules.length,
                classes: data.classes.length,
                functions: data.functions.length,
                methods: data.methods.length,
                pages: data.pages.length
            });
            
        } catch (error) {
            console.error('❌ Error loading search data:', error);
            this.isLoading = false;
            // Fallback to basic index
            this.buildBasicIndex();
        }
    }

    flattenLink(link) {
        if (!link) return '#';
        // Remove trailing index.html and replace with .html
        let flat = link.replace(/\/index\.html$/, '.html');
        // If it ends in a slash (e.g., 'core/'), convert to 'core.html'
        if (flat.endsWith('/')) {
            flat = flat.slice(0, -1) + '.html';
        }
        return flat;
    }

    buildSearchIndexFromData(data) {
        this.searchIndex = [];

        const processItem = (item, type, icon, score) => {
            return {
                ...item,
                type: type,
                link: this.flattenLink(item.link), // Apply flat structure
                content: this.normalizeText(item.name + ' ' + (item.description || '')),
                icon: icon,
                score: score
            };
        };

        // Index modules
        if (data.modules) data.modules.forEach(m => this.searchIndex.push(processItem(m, 'module', 'bi-folder', 10)));
        // Index classes
        if (data.classes) data.classes.forEach(c => this.searchIndex.push(processItem(c, 'class', 'bi-box', 9)));

        // Index functions
        if (data.functions) data.functions.forEach(f => this.searchIndex.push(processItem(f, 'function', 'bi-gear', 8)));

        // Index methods
        if (data.methods) data.methods.forEach(m => this.searchIndex.push(processItem(m, 'method', 'bi-hammer', 7)));

        // Index pages
        if (data.pages) data.pages.forEach(p => this.searchIndex.push(processItem(p, 'page', 'bi-file-text', 6)));
    }

    renderResultItem(item, searchTerm) {
        const highlightedTitle = this.highlightText(item.title || item.name, searchTerm);
        
        return `
            <div class="col-lg-6 mb-3">
                <div class="search-result-card card h-100 shadow-sm">
                    <div class="card-body d-flex flex-column">
                        <div class="d-flex align-items-center mb-2">
                            <div class="result-icon-wrapper me-2" style="color: var(--primary-color)">
                                <i class="bi ${item.icon} fs-5"></i>
                            </div>
                            <h5 class="card-title mb-0">${highlightedTitle}</h5>
                        </div>
                        <div class="search-result-meta mb-2">
                            <span class="badge" style="background-color: var(--primary-color)">${item.module || 'System'}</span>
                            <span class="badge bg-secondary opacity-75">${item.type}</span>
                        </div>
                        <p class="card-text text-muted small">${item.description || ''}</p>
                        <div class="mt-auto pt-2">
                            <a href="${item.link}${item.element_id ? '#' + item.element_id : ''}" 
                               class="btn btn-sm w-100" 
                               style="border: 1px solid var(--primary-color); color: var(--primary-color);">
                                Open Documentation
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    buildBasicIndex() {
        // Fallback basic index if JSON fails to load
        console.log('🔄 Building basic search index...');
        
        const basicData = {
            modules: [
                { name: 'core', title: 'Core Systems', description: 'Core engine systems', link: 'core/index.html' },
                { name: 'ui', title: 'User Interface', description: 'UI components', link: 'ui/index.html' },
                { name: 'graphics', title: 'Graphics', description: 'Rendering system', link: 'graphics/index.html' },
                { name: 'utils', title: 'Utilities', description: 'Utility functions', link: 'utils/index.html' },
                { name: 'backend', title: 'Backend', description: 'Renderer backends', link: 'backend/index.html' },
                { name: 'tools', title: 'Tools', description: 'Development tools', link: 'tools/index.html' }
            ],
            pages: [
                { name: 'Quick Start', description: 'Get started guide', link: 'quick-start.html', type: 'guide' },
                { name: 'Community', description: 'Community and contact', link: 'contact.html', type: 'community' }
            ]
        };

        this.buildSearchIndexFromData(basicData);
    }

    setupEventListeners() {
        const searchButton = document.getElementById('searchButton');
        const globalSearch = document.getElementById('globalSearch');
        
        if (searchButton) {
            searchButton.addEventListener('click', () => this.performSearch());
        }
        
        if (globalSearch) {
            globalSearch.addEventListener('keypress', (e) => {
                if (e.which === 13) {
                    this.performSearch();
                }
            });

            if (window.location.pathname.includes('search.html')) {
                globalSearch.addEventListener('input', this.debounce(() => {
                    const term = globalSearch.value.trim();
                    if (term.length >= 2) {
                        this.performSearch();
                    } else if (term.length === 0) {
                        this.showSearchInfo();
                    }
                }, 300));
            }
        }
    }

    processURLSearch() {
        const urlParams = new URLSearchParams(window.location.search);
        const searchParam = urlParams.get('q');
        if (searchParam && window.location.pathname.includes('search.html')) {
            const globalSearch = document.getElementById('globalSearch');
            if (globalSearch) {
                globalSearch.value = searchParam;
                // Wait a bit for data to load then search
                setTimeout(() => this.performSearch(), 100);
            }
        }
    }

    performSearch() {
        if (this.isLoading) {
            this.showLoading();
            return;
        }

        const globalSearch = document.getElementById('globalSearch');
        const searchTerm = globalSearch ? globalSearch.value.trim() : '';
        
        if (!searchTerm) {
            this.showSearchInfo();
            return;
        }

        this.updateURL(searchTerm);
        this.currentSearchTerm = searchTerm;

        const results = this.searchIndex.filter(item => 
            (item.content && this.normalizeText(item.content).includes(this.normalizeText(searchTerm))) ||
            (item.title && this.normalizeText(item.title).includes(this.normalizeText(searchTerm))) ||
            (item.description && this.normalizeText(item.description).includes(this.normalizeText(searchTerm))) ||
            (item.module && this.normalizeText(item.module).includes(this.normalizeText(searchTerm)))
        );

        this.displayResults(results, searchTerm);
    }

    updateURL(searchTerm) {
        if (window.location.pathname.includes('search.html')) {
            const newUrl = new URL(window.location);
            newUrl.searchParams.set('q', searchTerm);
            window.history.replaceState({}, '', newUrl);
        }
    }

    displayResults(results, searchTerm) {
        const resultsContainer = document.getElementById('searchResults');
        const noResults = document.getElementById('noResults');
        const searchInfo = document.getElementById('searchInfo');
        const searchStats = document.getElementById('searchStats');

        if (searchInfo) searchInfo.style.display = 'none';
        if (searchStats) searchStats.style.display = 'block';
        
        if (results.length === 0) {
            if (resultsContainer) resultsContainer.style.display = 'none';
            if (noResults) noResults.style.display = 'block';
            if (searchStats) {
                searchStats.innerHTML = `<small class="text-muted">No results found for "${this.escapeHtml(searchTerm)}"</small>`;
            }
            return;
        }

        if (noResults) noResults.style.display = 'none';
        
        const groupedResults = this.groupResultsByType(results);
        let resultsHTML = '';

        resultsHTML += `
            <div class="alert alert-success mb-4">
                <i class="bi bi-check-circle me-2"></i>
                Found <strong>${results.length}</strong> results for "<strong>${this.escapeHtml(searchTerm)}</strong>"
            </div>
        `;

        const typeOrder = ['module', 'class', 'function', 'method', 'page'];
        typeOrder.forEach(type => {
            if (groupedResults[type] && groupedResults[type].length > 0) {
                resultsHTML += this.renderResultGroup(type, groupedResults[type], searchTerm);
            }
        });

        if (resultsContainer) {
            resultsContainer.innerHTML = resultsHTML;
            resultsContainer.style.display = 'block';
        }

        if (searchStats) {
            const statsText = this.getSearchStats(groupedResults);
            searchStats.innerHTML = `<small class="text-muted">${statsText}</small>`;
        }
        
        this.addResultClickHandlers();
    }

    getSearchStats(groupedResults) {
        const stats = [];
        if (groupedResults.module) stats.push(`${groupedResults.module.length} modules`);
        if (groupedResults.class) stats.push(`${groupedResults.class.length} classes`);
        if (groupedResults.function) stats.push(`${groupedResults.function.length} functions`);
        if (groupedResults.method) stats.push(`${groupedResults.method.length} methods`);
        if (groupedResults.page) stats.push(`${groupedResults.page.length} pages`);
        
        return `Results: ${stats.join(', ')}`;
    }

    groupResultsByType(results) {
        const groups = {
            module: [],
            class: [],
            function: [],
            method: [],
            page: []
        };

        results.forEach(result => {
            if (groups[result.type]) {
                groups[result.type].push(result);
            }
        });

        return groups;
    }

    renderResultGroup(type, items, searchTerm) {
        const typeTitles = {
            module: '📁 Modules',
            class: '📦 Classes', 
            function: '🔧 Functions',
            method: '⚙️ Methods',
            page: '📄 Pages'
        };

        const typeIcons = {
            module: 'bi-folder',
            class: 'bi-box',
            function: 'bi-gear',
            method: 'bi-hammer',
            page: 'bi-file-text'
        };

        return `
            <div class="result-group mb-5">
                <h3 class="mb-3">
                    <i class="bi ${typeIcons[type]} me-2"></i>
                    ${typeTitles[type]} <span class="badge bg-primary">${items.length}</span>
                </h3>
                <div class="row g-3">
                    ${items.map(item => this.renderResultItem(item, searchTerm)).join('')}
                </div>
            </div>
        `;
    }

    renderResultItem(item, searchTerm) {
        const highlightedTitle = this.highlightText(item.title, searchTerm);
        const highlightedDesc = this.highlightText(
            item.description.length > 150 ? 
            item.description.substring(0, 150) + '...' : 
            item.description, 
            searchTerm
        );

        return `
            <div class="col-lg-6">
                <div class="search-result-card card h-100">
                    <div class="card-body">
                        <div class="d-flex align-items-start mb-2">
                            <i class="bi ${item.icon} fs-5 text-primary me-2 mt-1"></i>
                            <div class="flex-grow-1">
                                <h6 class="card-title mb-1">${highlightedTitle}</h6>
                                <div class="card-text text-muted small">${highlightedDesc}</div>
                            </div>
                        </div>
                        <div class="search-result-meta">
                            <small class="text-muted">
                                ${this.renderMetaInfo(item)}
                            </small>
                        </div>
                    </div>
                    <div class="card-footer bg-transparent">
                        <button class="btn btn-sm btn-outline-primary view-result" 
                                data-link="${item.link}" 
                                data-element-id="${item.element_id || ''}"
                                data-search-term="${this.escapeHtml(searchTerm)}"
                                data-type="${item.type}"
                                data-title="${this.escapeHtml(item.title)}">
                            <i class="bi bi-arrow-right me-1"></i>View
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    renderMetaInfo(item) {
        const meta = [];
        
        if (item.module && item.module !== 'documentation') {
            meta.push(`<i class="bi bi-folder me-1"></i>${item.module}`);
        }
        
        if (item.file) {
            meta.push(`<i class="bi bi-file-code me-1"></i>${item.file}`);
        }
        
        if (item.class) {
            meta.push(`<i class="bi bi-box me-1"></i>${item.class}`);
        }
        
        if (item.meta) {
            meta.push(item.meta);
        }
        
        return meta.join(' • ');
    }

    addResultClickHandlers() {
        document.querySelectorAll('.view-result').forEach(button => {
            button.addEventListener('click', (e) => {
                const btn = e.currentTarget; // Garante o elemento correto
                const link = btn.getAttribute('data-link');
                const elementId = btn.getAttribute('data-element-id');
                const searchTerm = btn.getAttribute('data-search-term');
                
                if (searchTerm) {
                    sessionStorage.setItem('lunaSearchTerm', searchTerm);
                    sessionStorage.setItem('lunaElementId', elementId);
                }
                
                // Print module name
                // 1. Limpa o link de index.html para o formato flat (ex: core.html)
                let cleanLink = link.replace(/\/index\.html$/, '.html');
                
                // 2. Adiciona o ID (âncora) diretamente na URL para o navegador pular para a função
                if (elementId) {
                    window.location.href = `${cleanLink}#${elementId}`;
                } else {
                    window.location.href = cleanLink;
                }
            });
        });
    }

    showLoading() {
        const resultsContainer = document.getElementById('searchResults');
        if (resultsContainer) {
            resultsContainer.innerHTML = `
                <div class="text-center py-4">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2 text-muted">Loading search data...</p>
                </div>
            `;
            resultsContainer.style.display = 'block';
        }
    }

    showSearchInfo() {
        const searchInfo = document.getElementById('searchInfo');
        const resultsContainer = document.getElementById('searchResults');
        const noResults = document.getElementById('noResults');
        const searchStats = document.getElementById('searchStats');
        
        if (searchInfo) searchInfo.style.display = 'block';
        if (resultsContainer) resultsContainer.style.display = 'none';
        if (noResults) noResults.style.display = 'none';
        if (searchStats) searchStats.style.display = 'none';
    }

    // Utility functions
    normalizeText(text) {
        if (!text) return ''; // Retorna string vazia se o texto for nulo ou indefinido
        return String(text).toLowerCase().trim();
    }

    highlightText(text, searchTerm) {
        if (!searchTerm) return this.escapeHtml(text);
        
        const normalizedText = this.normalizeText(text);
        const normalizedSearch = this.normalizeText(searchTerm);
        
        if (normalizedText.includes(normalizedSearch)) {
            const regex = new RegExp(`(${this.escapeRegex(searchTerm)})`, 'gi');
            return this.escapeHtml(text).replace(regex, '<mark class="search-highlight">$1</mark>');
        }
        
        return this.escapeHtml(text);
    }

    escapeHtml(unsafe) {
        if (!unsafe) return '';
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    debounce(func, wait) {
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
}

// Initialize search when document is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.lunaSearch = new LunaEngineSearch();
    });
} else {
    window.lunaSearch = new LunaEngineSearch();
}

// Handle search highlighting on target pages
document.addEventListener('DOMContentLoaded', function() {

    const searchTerm = sessionStorage.getItem('lunaSearchTerm');
    const elementId = sessionStorage.getItem('lunaElementId');
    
    if (searchTerm) {
        // Clear stored values IMMEDIATELY
        sessionStorage.removeItem('lunaSearchTerm');
        sessionStorage.removeItem('lunaElementId');
        
        // If we have a specific element ID, scroll to it
        if (elementId) {
            const element = document.getElementById(elementId);
            if (element) {
                element.scrollIntoView({ behavior: 'smooth', block: 'center' });
                element.classList.add('search-highlight');
                
                setTimeout(() => {
                    element.classList.remove('search-highlight');
                }, 3000);
            }
        }
        
        // Also highlight all occurrences of the search term on the page
        if (searchTerm.length > 2) {
            const walker = document.createTreeWalker(
                document.body,
                NodeFilter.SHOW_TEXT,
                null,
                false
            );
            
            let node;
            while (node = walker.nextNode()) {
                const parent = node.parentElement;
                if (parent && parent.nodeName !== 'SCRIPT' && parent.nodeName !== 'STYLE') {
                    const text = node.textContent;
                    const regex = new RegExp(`(${searchTerm})`, 'gi');
                    if (regex.test(text)) {
                        const newHTML = text.replace(regex, '<mark class="search-highlight">$1</mark>');
                        parent.innerHTML = parent.innerHTML.replace(text, newHTML);
                    }
                }
            }
            
            // Remove highlights after 5 seconds
            setTimeout(() => {
                document.querySelectorAll('.search-highlight').forEach(el => {
                    el.classList.remove('search-highlight');
                });
            }, 5000);
        }
    }
    
    // Also clear any URL search parameters to prevent re-highlighting on refresh
    if (window.location.search.includes('search=')) {
        const url = new URL(window.location);
        url.searchParams.delete('search');
        window.history.replaceState({}, '', url);
    }
});