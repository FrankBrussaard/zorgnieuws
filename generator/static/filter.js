// Zorgnieuws - Client-side filtering + dark mode

document.addEventListener('DOMContentLoaded', function() {
    // Dark mode
    initDarkMode();

    const articles = document.querySelectorAll('.article');
    let currentIndex = -1;
    let activeFilters = {
        category: null,
        tag: null
    };

    // Initialize filters if filter bar exists
    const filterBar = document.getElementById('filter-bar');
    if (filterBar) {
        initFilters();
    }

    function initFilters() {
        // Collect all categories and tags from articles
        const categories = new Set();
        const tags = new Set();

        articles.forEach(article => {
            const cat = article.dataset.category;
            if (cat) categories.add(cat);

            const articleTags = article.dataset.tags;
            if (articleTags) {
                articleTags.split(',').forEach(t => {
                    if (t.trim()) tags.add(t.trim());
                });
            }
        });

        // Build category filter
        const categoryFilter = document.getElementById('category-filter');
        if (categoryFilter) {
            categories.forEach(cat => {
                const btn = document.createElement('button');
                btn.className = 'filter-btn';
                btn.textContent = cat;
                btn.dataset.category = cat;
                btn.onclick = () => toggleCategoryFilter(cat, btn);
                categoryFilter.appendChild(btn);
            });
        }

        // Build tag filter
        const tagFilter = document.getElementById('tag-filter');
        if (tagFilter) {
            // Sort tags alphabetically
            const sortedTags = Array.from(tags).sort();
            sortedTags.forEach(tag => {
                const btn = document.createElement('button');
                btn.className = 'filter-btn tag-btn';
                btn.textContent = tag;
                btn.dataset.tag = tag;
                btn.onclick = () => toggleTagFilter(tag, btn);
                tagFilter.appendChild(btn);
            });
        }
    }

    function toggleCategoryFilter(category, btn) {
        const allBtns = document.querySelectorAll('#category-filter .filter-btn');

        if (activeFilters.category === category) {
            // Deactivate
            activeFilters.category = null;
            btn.classList.remove('active');
        } else {
            // Activate this, deactivate others
            allBtns.forEach(b => b.classList.remove('active'));
            activeFilters.category = category;
            btn.classList.add('active');
        }

        applyFilters();
    }

    function toggleTagFilter(tag, btn) {
        const allBtns = document.querySelectorAll('#tag-filter .filter-btn');

        if (activeFilters.tag === tag) {
            // Deactivate
            activeFilters.tag = null;
            btn.classList.remove('active');
        } else {
            // Activate this, deactivate others
            allBtns.forEach(b => b.classList.remove('active'));
            activeFilters.tag = tag;
            btn.classList.add('active');
        }

        applyFilters();
    }

    function applyFilters() {
        let visibleCount = 0;

        articles.forEach(article => {
            let show = true;

            // Category filter
            if (activeFilters.category) {
                const cat = article.dataset.category;
                if (cat !== activeFilters.category) {
                    show = false;
                }
            }

            // Tag filter
            if (activeFilters.tag && show) {
                const articleTags = article.dataset.tags || '';
                if (!articleTags.includes(activeFilters.tag)) {
                    show = false;
                }
            }

            article.style.display = show ? '' : 'none';
            if (show) visibleCount++;
        });

        // Update count
        const countEl = document.getElementById('visible-count');
        if (countEl) {
            countEl.textContent = `${visibleCount} artikelen`;
        }
    }

    // Clear all filters
    window.clearFilters = function() {
        activeFilters = { category: null, tag: null };
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        applyFilters();
    };

    // Keyboard navigation
    function highlightArticle(index) {
        const visibleArticles = Array.from(articles).filter(a => a.style.display !== 'none');
        visibleArticles.forEach(a => a.style.outline = '');

        if (index >= 0 && index < visibleArticles.length) {
            visibleArticles[index].style.outline = '2px solid #ff6600';
            visibleArticles[index].scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    document.addEventListener('keydown', function(e) {
        // Don't intercept if typing in input
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

        const visibleArticles = Array.from(articles).filter(a => a.style.display !== 'none');

        if (e.key === 'j') {
            currentIndex = Math.min(currentIndex + 1, visibleArticles.length - 1);
            highlightArticle(currentIndex);
        } else if (e.key === 'k') {
            currentIndex = Math.max(currentIndex - 1, 0);
            highlightArticle(currentIndex);
        } else if ((e.key === 'o' || e.key === 'Enter') && currentIndex >= 0) {
            const link = visibleArticles[currentIndex]?.querySelector('a.title');
            if (link) window.open(link.href, '_blank');
        } else if (e.key === 'Escape') {
            clearFilters();
        }
    });

    console.log('Zorgnieuws loaded. Keys: j/k navigate, o open, Esc clear filters');
});

// Dark mode functions
function initDarkMode() {
    const savedTheme = localStorage.getItem('zorgnieuws_theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
        document.documentElement.setAttribute('data-theme', 'dark');
    }

    // Update toggle button
    updateThemeToggle();
}

function toggleDarkMode() {
    const current = document.documentElement.getAttribute('data-theme');
    const newTheme = current === 'dark' ? 'light' : 'dark';

    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('zorgnieuws_theme', newTheme);
    updateThemeToggle();
}

function updateThemeToggle() {
    const btn = document.getElementById('theme-toggle');
    if (btn) {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        btn.textContent = isDark ? '☀️' : '🌙';
        btn.title = isDark ? 'Light mode' : 'Dark mode';
    }
}

// Make toggleDarkMode available globally
window.toggleDarkMode = toggleDarkMode;
