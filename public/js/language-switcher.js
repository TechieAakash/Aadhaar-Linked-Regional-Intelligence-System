/**
 * ALRIS Language Switcher
 * Supports Hindi (हिन्दी) and English
 * Stores preference in localStorage
 */

class LanguageSwitcher {
    constructor() {
        this.currentLang = localStorage.getItem('alris_language') || 'en';
        this.translations = {};
        this.init();
    }

    async init() {
        console.log('[LANGUAGE] Initializing language switcher, current:', this.currentLang);
        await this.loadTranslations();
        this.createLanguageToggle();
        this.applyTranslations();
    }

    async loadTranslations() {
        try {
            const [enResponse, hiResponse] = await Promise.all([
                fetch('/data/translations/en.json'),
                fetch('/data/translations/hi.json')
            ]);

            this.translations.en = await enResponse.json();
            this.translations.hi = await hiResponse.json();
            
            console.log('[LANGUAGE] Translations loaded successfully');
        } catch (error) {
            console.error('[LANGUAGE] Failed to load translations:', error);
        }
    }

    createLanguageToggle() {
        // Find the header to add language toggle
        const header = document.querySelector('.gov-masthead');
        if (!header) return;

        // Create language toggle container
        const langToggle = document.createElement('div');
        langToggle.className = 'language-toggle';
        langToggle.innerHTML = `
            <button class="lang-btn ${this.currentLang === 'en' ? 'active' : ''}" data-lang="en">
                EN
            </button>
            <span class="lang-divider">|</span>
            <button class="lang-btn ${this.currentLang === 'hi' ? 'active' : ''}" data-lang="hi">
                हिं
            </button>
        `;

        // Add click listeners
        langToggle.querySelectorAll('.lang-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const lang = e.target.dataset.lang;
                this.switchLanguage(lang);
            });
        });

        // Insert at the end of header
        header.appendChild(langToggle);
        
        console.log('[LANGUAGE] Toggle button created');
    }

    switchLanguage(lang) {
        if (lang === this.currentLang) return;
        
        console.log('[LANGUAGE] Switching to:', lang);
        this.currentLang = lang;
        localStorage.setItem('alris_language', lang);

        // Update active button
        document.querySelectorAll('.lang-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.lang === lang);
        });

        // Apply new translations
        this.applyTranslations();
    }

    applyTranslations() {
        const t = this.translations[this.currentLang];
        if (!t) return;

        console.log('[LANGUAGE] Applying translations for:', this.currentLang);

        // Translate elements with data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.dataset.i18n;
            const translation = this.getTranslation(key, t);
            
            if (translation) {
                if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                    element.placeholder = translation;
                } else {
                    element.textContent = translation;
                }
            }
        });

        // Translate navigation links
        this.translateNav(t);
        
        // Translate header
        this.translateHeader(t);
        
        // Dispatch event for other scripts to react
        window.dispatchEvent(new CustomEvent('languageChanged', { detail: { lang: this.currentLang } }));
    }

    getTranslation(key, translations) {
        // Support nested keys like "nav.dashboard"
        const keys = key.split('.');
        let value = translations;
        
        for (const k of keys) {
            value = value?.[k];
        }
        
        return value;
    }

    translateNav(t) {
        // Translate navigation items
        const navItems = {
            '/': t.nav?.dashboard,
            '/lifecycle': t.nav?.dataInsights,
            '/equity': t.nav?.serviceEquity,
            '/resource_planning': t.nav?.strategicPlanning,
            '/social_risk': t.nav?.socialRisk,
            '/forecasting': t.nav?.forecasting,
            '/anomalies': t.nav?.anomalies,
            '/benchmarking': t.nav?.peerBenchmarking,
            '/decisions': t.nav?.decisions
        };

        document.querySelectorAll('.nav-link').forEach(link => {
            const href = link.getAttribute('href');
            const translation = navItems[href];
            if (translation) {
                // Extract emoji if present
                const emoji = link.textContent.match(/[\p{Emoji}]/u)?.[0] || '';
                link.textContent = emoji ? `${emoji} ${translation}` : translation;
            }
        });
    }

    translateHeader(t) {
        // Translate main header title
        const headerTitle = document.querySelector('.gov-masthead h1');
        if (headerTitle && t.header?.title) {
            headerTitle.textContent = t.header.title;
        }

        // Translate subtitle
        const headerSubtitle = document.querySelector('.gov-masthead p');
        if (headerSubtitle && t.header?.subtitle) {
            headerSubtitle.textContent = t.header.subtitle;
        }

        // Translate watermark
        const watermark = document.querySelector('.watermark');
        if (watermark && t.header?.watermark) {
            watermark.textContent = t.header.watermark;
        }
    }

    // Public method to get current language
    getCurrentLanguage() {
        return this.currentLang;
    }

    // Public method to get translation
    t(key) {
        return this.getTranslation(key, this.translations[this.currentLang]);
    }
}

// Initialize language switcher when DOM is ready
let languageSwitcher;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        languageSwitcher = new LanguageSwitcher();
    });
} else {
    languageSwitcher = new LanguageSwitcher();
}

// Export for use in other scripts
window.LanguageSwitcher = LanguageSwitcher;
window.getLanguageSwitcher = () => languageSwitcher;
