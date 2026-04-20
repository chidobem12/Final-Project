/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                'bg-void': 'var(--bg-void)',
                'bg-surface': 'var(--bg-surface)',
                'bg-raised': 'var(--bg-raised)',
                'bg-border': 'var(--bg-border)',
                'accent-primary': 'var(--accent-primary)',
                'accent-threat': 'var(--accent-threat)',
                'accent-warning': 'var(--accent-warning)',
                'accent-high': 'var(--accent-high)',
                'accent-info': 'var(--accent-info)',
                'accent-dim': 'var(--accent-dim)',
            },
            fontFamily: {
                display: ['Syne', 'sans-serif'],
                body: ['Inter', 'sans-serif'],
                mono: ['IBM Plex Mono', 'monospace'],
            }
        },
    },
    plugins: [],
}
