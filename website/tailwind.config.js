/** @type {import('tailwindcss').Config} */
module.exports = {
    corePlugins: {
        preflight: false,
        container: false,
    },
    darkMode: ['class', '[data-theme="dark"]'],
    content: ['./src/**/*.{jsx,tsx,html}', './docs/**/*.{md,mdx}', './codex/**/*.{md,mdx}'],
    theme: {
        extend: {
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
                heading: ['Outfit', 'sans-serif'],
            },
            colors: {
                devi: { // Padmarāga Ruby / Crimson (Tripura Sundari)
                    50: '#fdf2f4',
                    100: '#fbe2e6',
                    200: '#f7c8d2',
                    300: '#f0a1b3',
                    400: '#e56d8a',
                    500: '#d11149', // Primary Devi Red
                    600: '#c50937',
                    700: '#a7042a',
                    800: '#8c0727',
                    900: '#750b25',
                    950: '#420210',
                },
                gold: { // Ratnagriha / Divine Palace (From Logo)
                    50: '#fffbf2',
                    100: '#fef1d8',
                    200: '#fbe0ad',
                    300: '#f7c577',
                    400: '#f2a647',
                    500: '#d4af37', // BijMantra Gold
                    600: '#bc8f2b',
                    700: '#9d6e24',
                    800: '#815921',
                    900: '#6a4a1e',
                },
                samudra: { // Sudha Samudra (Nectar) & Indranīla (Sapphire)
                    50: '#FDFAF6',  // Nectar / Pearl (Light Theme Base)
                    100: '#F4EFE6', // Soft Lotus white
                    800: '#0c0f1a', // Deep ocean edge
                    900: '#06080F', // Cosmic Sapphire / Noir (Dark Theme Base)
                    950: '#030408', // Void
                },
            },
            animation: {
                'slide-up': 'slideUp 0.8s ease-out forwards',
                'fade-in': 'fadeIn 1s ease-out forwards',
                'blob': 'blob 10s infinite',
                'glow': 'glow 3s ease-in-out infinite alternate',
            },
            keyframes: {
                slideUp: {
                    '0%': { transform: 'translateY(20px)', opacity: 0 },
                    '100%': { transform: 'translateY(0)', opacity: 1 },
                },
                fadeIn: {
                    '0%': { opacity: 0 },
                    '100%': { opacity: 1 },
                },
                blob: {
                    '0%': {
                        transform: 'translate(0px, 0px) scale(1)',
                    },
                    '33%': {
                        transform: 'translate(30px, -50px) scale(1.1)',
                    },
                    '66%': {
                        transform: 'translate(-20px, 20px) scale(0.9)',
                    },
                    '100%': {
                        transform: 'translate(0px, 0px) scale(1)',
                    },
                },
                glow: {
                    '0%': { boxShadow: '0 0 10px rgba(212, 175, 55, 0.2)' }, // Changed to Gold glow
                    '100%': { boxShadow: '0 0 25px rgba(212, 175, 55, 0.6)' },
                },
            },
        },
    },
    plugins: [],
}
