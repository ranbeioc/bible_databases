document.addEventListener('DOMContentLoaded', () => {
    const langSelect = document.getElementById('language-select');
    const versionSelect = document.getElementById('version-select');
    const contentEl = document.getElementById('content');
    const tocEl = document.getElementById('toc');
    const searchBox = document.getElementById('search-box');
    const clearAllBtn = document.getElementById('clear-all-btn');
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const scrollToTopBtn = document.getElementById('scrollToTopBtn');

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
        const savedLang = localStorage.getItem('selectedLanguage');
        const savedVersion = localStorage.getItem('selectedVersion');

        if (savedLang && langverData[savedLang]) {
            langSelect.value = savedLang;
            await updateVersions(savedVersion);
        } else {
            const browserLang = navigator.language.split('-')[0];
            if (langverData[browserLang]) {
                langSelect.value = browserLang;
            }
            await updateVersions();
        }
    }

    // Update the version selector when a language changes
    async function updateVersions(versionToSelect = null) {
        const selectedLang = langSelect.value;
        localStorage.setItem('selectedLanguage', selectedLang);

        const versions = langverData[selectedLang];
        if (!versions || versions.length === 0) {
            versionSelect.innerHTML = '';
            contentEl.innerHTML = '<p>No versions available for this language.</p>';
            tocEl.innerHTML = '';
            return;
        }

        versionSelect.innerHTML = versions.map(v => `<option value="${v.version}">${v.name}</option>`).join('');

        const validVersion = versions.some(v => v.version === versionToSelect);

        if (versionToSelect && validVersion) {
            versionSelect.value = versionToSelect;
            await loadContent(versionToSelect);
        } else {
            // Explicitly pass the new version to loadContent to avoid race conditions.
            const newVersion = versions[0].version;
            await loadContent(newVersion);
        }
    }

    // Load the markdown content for the selected version
    async function loadContent(versionOverride = null) {
        console.log('loadContent called. versionOverride:', versionOverride);
        const lang = langSelect.value;
        const version = versionOverride || versionSelect.value;
        console.log(`Loading content for lang: ${lang}, version: ${version}`);
        localStorage.setItem('selectedVersion', version);

        if (!lang || !version) {
            contentEl.innerHTML = '<p>Please select a language and version.</p>';
            console.error('Missing lang or version.');
            return;
        }

        const versionData = langverData[lang]?.find(v => v.version === version);
        console.log('Found version data:', versionData);

        if (versionData && versionData.files.md) {
            console.log('Fetching markdown from:', versionData.files.md);
            try {
                const response = await fetch(versionData.files.md);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status} while fetching ${versionData.files.md}`);
                }
                currentMarkdown = await response.text();
                renderMarkdown(currentMarkdown);
                generateToc(currentMarkdown);
                console.log('Content loaded and rendered successfully.');
            } catch (error) {
                console.error('Error loading markdown file:', error);
                contentEl.innerHTML = `<p>Error loading content. See console for details.</p>`;
                currentMarkdown = '';
                tocEl.innerHTML = '';
            }
        } else {
            console.error('No markdown file available for this version.');
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
            // Ensure text is a string before processing
            const safeText = typeof text === 'string' ? text : JSON.stringify(text);
            const escapedText = safeText.toLowerCase().replace(/[^\w]+/g, '-');
            return `<h${level} id="${escapedText}">${safeText}</h${level}>`;
        };
        contentEl.innerHTML = marked.parse(markdown, { renderer: renderer });
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
        // Wrap listener calls in anonymous functions to avoid passing the Event object
        langSelect.addEventListener('change', () => updateVersions());
        versionSelect.addEventListener('change', () => loadContent());
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

        // Handle TOC link clicks for smooth scrolling and sidebar management
        tocEl.addEventListener('click', (e) => {
            if (e.target.classList.contains('toc-link')) {
                e.preventDefault();
                const targetId = e.target.getAttribute('href').substring(1);
                const targetElement = document.getElementById(targetId);
                if (targetElement) {
                    targetElement.scrollIntoView({ behavior: 'smooth' });
                }

                // Close sidebar on mobile after clicking a link
                if (window.innerWidth <= 768) {
                    sidebar.classList.remove('open');
                }
            }
        });

        // Scroll to top button logic
        window.onscroll = function() {
            if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
                scrollToTopBtn.style.display = "block";
            } else {
                scrollToTopBtn.style.display = "none";
            }
        };

        scrollToTopBtn.addEventListener('click', () => {
            document.body.scrollTop = 0; // For Safari
            document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE and Opera
        });

        // View dropdown
        const viewDropdown = document.querySelector('.dropdown');
        const viewDropdownBtn = document.getElementById('view-dropdown-btn');
        const toggleThemeBtn = document.getElementById('toggle-theme');
        const toggleFullscreenBtn = document.getElementById('toggle-fullscreen');
        const toggleZenModeBtn = document.getElementById('toggle-zen-mode');

        viewDropdownBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            viewDropdown.classList.toggle('show');
        });

        toggleThemeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            const currentTheme = document.body.classList.contains('dark-theme') ? 'dark' : 'light';
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            applyTheme(newTheme);
            viewDropdown.classList.remove('show');
        });

        toggleFullscreenBtn.addEventListener('click', (e) => {
            e.preventDefault();
            toggleFullScreen();
            viewDropdown.classList.remove('show');
        });

        toggleZenModeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            toggleZenMode();
            viewDropdown.classList.remove('show');
        });

        // Close dropdown when clicking outside
        window.addEventListener('click', (e) => {
            if (!viewDropdown.contains(e.target)) {
                viewDropdown.classList.remove('show');
            }
        });
    }

    // Helper to get a more readable language name
    function getLanguageName(langCode) {
        // Manual map for all codes to ensure consistency and support for non-standard ones.
        const nameMap = {
            "en": "English",
            "sq": "Albanian",
            "hy": "Armenian",
            "bea": "Beaver",
            "my": "Burmese",
            "grc": "Ancient Greek",
            "cu": "Church Slavonic",
            "ceb": "Cebuano",
            "chr": "Cherokee",
            "zh-hans": "Chinese (Simplified)",
            "zh-hant": "Chinese (Traditional)",
            "cop-sa": "Coptic (Sahidic)",
            "hr": "Croatian",
            "cs": "Czech",
            "da": "Danish",
            "nl": "Dutch",
            "eo": "Esperanto",
            "et": "Estonian",
            "fi": "Finnish",
            "fr": "French",
            "de": "German",
            "el": "Greek",
            "ht": "Haitian Creole",
            "he": "Hebrew",
            "hu": "Hungarian",
            "ja": "Japanese",
            "tlh": "Klingon",
            "ko": "Korean",
            "lv": "Latvian",
            "mlf": "Malayalam",
            "gv": "Manx",
            "mi": "Maori",
            "hbo": "Ancient Hebrew",
            "mg": "Malagasy",
            "nn": "Norwegian Nynorsk",
            "nb": "Norwegian Bokmål",
            "syr": "Syriac",
            "pon": "Pohnpeian",
            "pl": "Polish",
            "pt": "Portuguese",
            "ru": "Russian",
            "sl": "Slovenian",
            "es": "Spanish",
            "sr": "Serbian",
            "sv": "Swedish",
            "tl": "Tagalog",
            "tsg": "Tausug",
            "th": "Thai",
            "tpi": "Tok Pisin",
            "uk": "Ukrainian",
            "vi": "Vietnamese",
            "la": "Latin",
            "got": "Gothic",
            "enm": "Middle English",
            "sml": "Sama",
            "vls": "Flemish"
        };
        return nameMap[langCode] || langCode;
    }

    function applyTheme(theme) {
        document.body.classList.remove('light-theme', 'dark-theme');
        document.body.classList.add(`${theme}-theme`);
        localStorage.setItem('theme', theme);
    }

    function toggleFullScreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            }
        }
    }

    function toggleZenMode() {
        document.body.classList.toggle('zen-mode');
    }

    // Start the app
    init();

    // Apply saved theme on load
    const savedTheme = localStorage.getItem('theme') || 'light';
    applyTheme(savedTheme);
});
