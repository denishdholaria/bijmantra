/** @type {import('tailwindcss').Config} */
export default {
    darkMode: ["class"],
    content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
  	extend: {
  		colors: {
  			border: 'hsl(var(--border))',
  			input: 'hsl(var(--input))',
  			ring: 'hsl(var(--ring))',
  			background: 'hsl(var(--background))',
  			foreground: 'hsl(var(--foreground))',
  			primary: {
  				'50': '#f0fdf4',
  				'100': '#dcfce7',
  				'200': '#bbf7d0',
  				'300': '#86efac',
  				'400': '#4ade80',
  				'500': '#22c55e',
  				'600': '#16a34a',
  				'700': '#15803d',
  				'800': '#166534',
  				'900': '#14532d',
  				DEFAULT: 'hsl(var(--primary))',
  				foreground: 'hsl(var(--primary-foreground))'
  			},
  			secondary: {
  				DEFAULT: 'hsl(var(--secondary))',
  				foreground: 'hsl(var(--secondary-foreground))'
  			},
  			destructive: {
  				DEFAULT: 'hsl(var(--destructive))',
  				foreground: 'hsl(var(--destructive-foreground))'
  			},
  			muted: {
  				DEFAULT: 'hsl(var(--muted))',
  				foreground: 'hsl(var(--muted-foreground))'
  			},
  			accent: {
  				DEFAULT: 'hsl(var(--accent))',
  				foreground: 'hsl(var(--accent-foreground))'
  			},
  			card: {
  				DEFAULT: 'hsl(var(--card))',
  				foreground: 'hsl(var(--card-foreground))'
  			},
  			popover: {
  				DEFAULT: 'hsl(var(--popover))',
  				foreground: 'hsl(var(--popover-foreground))'
  			},
  			chart: {
  				'1': 'hsl(var(--chart-1))',
  				'2': 'hsl(var(--chart-2))',
  				'3': 'hsl(var(--chart-3))',
  				'4': 'hsl(var(--chart-4))',
  				'5': 'hsl(var(--chart-5))'
  			},
  			// 🌿 Prakruti Design System Colors
  			prakruti: {
  				// Earth (Mitti - मिट्टी)
  				mitti: {
  					DEFAULT: '#8B5A2B',
  					light: '#D4A574',
  					dark: '#5D3A1A',
  					50: '#FAF6F1',
  					100: '#F0E6D9',
  					200: '#E0CCB3',
  					900: '#3D2510',
  				},
  				// Leaf (Patta - पत्ता)
  				patta: {
  					DEFAULT: '#2D5A27',
  					light: '#6FCF5F',  /* Brightened for WCAG AA on dark backgrounds */
  					dark: '#1A3A16',
  					pale: '#E8F5E9',
  					50: '#F1F8F1',
  					100: '#DCEFDC',
  					200: '#B8DFB8',
  					900: '#0D2A0A',
  				},
  				// Gold (Sona - सोना)
  				sona: {
  					DEFAULT: '#D4A012',
  					light: '#F5D742',
  					dark: '#9A7400',
  					pale: '#FFF8E1',
  					50: '#FFFBEB',
  					100: '#FEF3C7',
  					200: '#FDE68A',
  				},
  				// Sky (Neela - नीला)
  				neela: {
  					DEFAULT: '#1E6091',
  					light: '#3B8AC4',
  					dark: '#0D4A6F',
  					pale: '#E3F2FD',
  					50: '#EFF6FF',
  					100: '#DBEAFE',
  					200: '#BFDBFE',
  				},
  				// Error (Laal - लाल)
  				laal: {
  					DEFAULT: '#C62828',
  					light: '#EF5350',
  					dark: '#8E0000',
  					pale: '#FFEBEE',
  				},
  				// Warning (Narangi - नारंगी)
  				narangi: {
  					DEFAULT: '#E65100',
  					light: '#FF8A50',
  					dark: '#AC1900',
  					pale: '#FFF3E0',
  				},
  				// Neutral (Dhool - धूल) - WCAG 2 AA Compliant
  				// Light shades (50-300): For backgrounds
  				// Medium shades (400-500): For text on LIGHT backgrounds only (4.5:1 on white)
  				// Dark shades (600-900): For backgrounds in dark mode
  				// NOTE: For text on DARK backgrounds, use dhool-200 or dhool-300 (not 400/500)
  				dhool: {
  					50: '#FAFAF8',
  					100: '#F5F5F0',
  					200: '#E8E8E0',
  					300: '#D4D4C8',
  					400: '#737363',  /* WCAG AA: 4.5:1 on white - use dhool-300 on dark */
  					500: '#5F5F4F',  /* WCAG AA: 5.5:1 on white - use dhool-300 on dark */
  					600: '#484838',
  					700: '#383830',
  					800: '#282820',
  					900: '#181810',
  				},
  			},
  		},
  		borderRadius: {
  			lg: 'var(--radius)',
  			md: 'calc(var(--radius) - 2px)',
  			sm: 'calc(var(--radius) - 4px)'
  		},
  		keyframes: {
  			'fade-in': {
  				'0%': {
  					opacity: '0',
  					transform: 'translateY(10px)'
  				},
  				'100%': {
  					opacity: '1',
  					transform: 'translateY(0)'
  				}
  			},
  			'slide-in': {
  				'0%': {
  					transform: 'translateX(-100%)'
  				},
  				'100%': {
  					transform: 'translateX(0)'
  				}
  			},
  			// 🌿 Prakruti Animations
  			'prakruti-grow': {
  				'0%': {
  					opacity: '0',
  					transform: 'scale(0.95) translateY(8px)'
  				},
  				'100%': {
  					opacity: '1',
  					transform: 'scale(1) translateY(0)'
  				}
  			},
  			'prakruti-sprout': {
  				'0%': {
  					transform: 'scale(0) rotate(-45deg)',
  					opacity: '0'
  				},
  				'50%': {
  					transform: 'scale(1.2) rotate(0deg)',
  					opacity: '1'
  				},
  				'100%': {
  					transform: 'scale(1) rotate(0deg)',
  					opacity: '1'
  				}
  			},
  			'prakruti-sway': {
  				'0%, 100%': { transform: 'rotate(-3deg)' },
  				'50%': { transform: 'rotate(3deg)' }
  			},
  			'prakruti-pulse': {
  				'0%, 100%': { opacity: '1' },
  				'50%': { opacity: '0.7' }
  			}
  		},
  		animation: {
  			'fade-in': 'fade-in 0.3s ease-out',
  			'slide-in': 'slide-in 0.3s ease-out',
  			// 🌿 Prakruti Animations
  			'prakruti-grow': 'prakruti-grow 0.25s cubic-bezier(0, 0, 0.2, 1)',
  			'prakruti-sprout': 'prakruti-sprout 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
  			'prakruti-sway': 'prakruti-sway 2s cubic-bezier(0.4, 0, 0.2, 1) infinite',
  			'prakruti-pulse': 'prakruti-pulse 2s cubic-bezier(0.4, 0, 0.2, 1) infinite'
  		},
  		// 🌿 Prakruti Shadows
  		boxShadow: {
  			'prakruti-sm': '0 1px 2px 0 rgb(0 0 0 / 0.05)',
  			'prakruti-md': '0 4px 6px -1px rgb(0 0 0 / 0.07), 0 2px 4px -2px rgb(0 0 0 / 0.07)',
  			'prakruti-lg': '0 10px 15px -3px rgb(0 0 0 / 0.08), 0 4px 6px -4px rgb(0 0 0 / 0.08)',
  			'prakruti-xl': '0 20px 25px -5px rgb(0 0 0 / 0.08), 0 8px 10px -6px rgb(0 0 0 / 0.08)',
  			'prakruti-patta': '0 4px 14px 0 rgb(45 90 39 / 0.25)',
  			'prakruti-sona': '0 4px 14px 0 rgb(212 160 18 / 0.25)',
  			'prakruti-mitti': '0 4px 14px 0 rgb(139 90 43 / 0.25)',
  			'prakruti-neela': '0 4px 14px 0 rgb(30 96 145 / 0.25)',
  		},
  		// 🌿 Prakruti Border Radius
  		borderRadius: {
  			'prakruti-sm': '0.25rem',
  			'prakruti-md': '0.5rem',
  			'prakruti-lg': '0.75rem',
  			'prakruti-xl': '1rem',
  			'prakruti-2xl': '1.5rem',
  			'prakruti-3xl': '2rem',
  		},
  		// 🌿 Prakruti Transitions
  		transitionTimingFunction: {
  			'prakruti-natural': 'cubic-bezier(0.4, 0, 0.2, 1)',
  			'prakruti-grow': 'cubic-bezier(0, 0, 0.2, 1)',
  			'prakruti-settle': 'cubic-bezier(0.4, 0, 0, 1)',
  			'prakruti-spring': 'cubic-bezier(0.175, 0.885, 0.32, 1.275)',
  		}
  	}
  },
  plugins: [require("tailwindcss-animate")],
}
