document.addEventListener('DOMContentLoaded', () => {
    const langSelect = document.getElementById('language-select');
    const versionSelect = document.getElementById('version-select');
    const contentEl = document.getElementById('content');
    const tocEl = document.getElementById('toc');
    const searchBox = document.getElementById('search-box');
    const clearAllBtn = document.getElementById('clear-all-btn');
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');

    let langverData = {};
    let currentMarkdown = '';

    // Initialize the application
    async function init() {
        try {
            const response = await fetch('langver.json');
            if (!response.ok) {
                throw new Error('Failed to load langver.json');
            }
            langverData = await response.json();
            populateLanguages();
            await setInitialLanguageAndVersion();
            setupEventListeners();
        } catch (error) {
            console.error('Initialization failed:', error);
            contentEl.innerHTML = '<p>Error loading application data. Please try again later.</p>';
        }
    }

    // Populate the language selector
    function populateLanguages() {
        const languages = Object.keys(langverData);
        langSelect.innerHTML = languages.map(lang => `<option value="${lang}">${getLanguageName(lang)}</option>`).join('');
    }

    // Set the initial language and version based on browser settings or defaults
    async function setInitialLanguageAndVersion() {
        const browserLang = navigator.language.split('-')[0];
        if (langverData[browserLang]) {
            langSelect.value = browserLang;
        }
        await updateVersions();
    }

    // Update the version selector when a language changes
    async function updateVersions() {
        const selectedLang = langSelect.value;
        const versions = langverData[selectedLang];
        if (!versions) return;

        versionSelect.innerHTML = versions.map(v => `<option value="${v.version}">${v.name}</option>`).join('');
        await loadContent();
    }

    // Load the markdown content for the selected version
    async function loadContent() {
        const lang = langSelect.value;
        const version = versionSelect.value;
        const versionData = langverData[lang]?.find(v => v.version === version);

        if (versionData && versionData.files.md) {
            try {
                const response = await fetch(versionData.files.md);
                if (!response.ok) throw new Error(`File not found: ${versionData.files.md}`);
                currentMarkdown = await response.text();
                renderMarkdown(currentMarkdown);
                generateToc(currentMarkdown);
            } catch (error) {
                console.error('Error loading markdown file:', error);
                contentEl.innerHTML = `<p>Error loading content.</p>`;
                currentMarkdown = '';
                tocEl.innerHTML = '';
            }
        } else {
            contentEl.innerHTML = '<p>No markdown file available for this version.</p>';
            currentMarkdown = '';
            tocEl.innerHTML = '';
        }
    }

    // Render markdown to HTML
    function renderMarkdown(markdown) {
        // Use a custom renderer to add IDs to headings
        const renderer = new marked.Renderer();
        renderer.heading = function (text, level) {
            const escapedText = text.toLowerCase().replace(/[^\w]+/g, '-');
            return `<h${level} id="${escapedText}">${text}</h${level}>`;
        };
        contentEl.innerHTML = marked(markdown, { renderer: renderer });
    }

    // Generate Table of Contents from markdown
    function generateToc(markdown) {
        const lines = markdown.split('\n');
        const tocLines = lines.filter(line => /^#{1,6} /.test(line));
        const tocHTML = tocLines.map(line => {
            const level = line.match(/^#+/)[0].length;
            const text = line.replace(/^#+ /, '');
            const escapedText = text.toLowerCase().replace(/[^\w]+/g, '-');
            return `<a href="#${escapedText}" class="toc-link h${level}">${text}</a>`;
        }).join('');
        tocEl.innerHTML = `<ul>${tocHTML.replace(/<a/g, '<li><a').replace(/<\/a>/g, '</a></li>')}</ul>`;
    }

    // Handle search input
    function handleSearch() {
        const query = searchBox.value.toLowerCase();
        const links = tocEl.getElementsByTagName('a');
        for (let link of links) {
            const text = link.textContent.toLowerCase();
            const parentLi = link.parentElement;
            if (text.includes(query)) {
                parentLi.style.display = '';
            } else {
                parentLi.style.display = 'none';
            }
        }
    }

    // Setup all event listeners
    function setupEventListeners() {
        langSelect.addEventListener('change', updateVersions);
        versionSelect.addEventListener('change', loadContent);
        searchBox.addEventListener('input', handleSearch);
        clearAllBtn.addEventListener('click', () => {
            searchBox.value = '';
            handleSearch();
            langSelect.selectedIndex = 0;
            // Manually trigger change to update versions and content
            langSelect.dispatchEvent(new Event('change'));
        });

        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });

        // Close sidebar when a TOC link is clicked on mobile
        tocEl.addEventListener('click', (e) => {
            if (e.target.classList.contains('toc-link') && window.innerWidth <= 768) {
                sidebar.classList.remove('open');
            }
        });
    }

    // Helper to get a more readable language name
    function getLanguageName(langCode) {
        try {
            return new Intl.DisplayNames(['en'], { type: 'language' }).of(langCode) || langCode;
        } catch (e) {
            return langCode; // Fallback for unsupported codes
        }
    }

    // Start the app
    init();
});
