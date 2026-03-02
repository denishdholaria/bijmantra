import { themes as prismThemes } from 'prism-react-renderer';
import type { Config } from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

function tailwindPlugin(context, options) {
  return {
    name: "docusaurus-tailwindcss",
    configurePostCss(postcssOptions) {
      // Appends TailwindCSS and AutoPrefixer.
      postcssOptions.plugins.push(require("tailwindcss"));
      postcssOptions.plugins.push(require("autoprefixer"));
      return postcssOptions;
    },
  };
}

const config: Config = {
  title: 'BijMantra',
  tagline: 'Cross-Domain Agricultural Intelligence',
  favicon: 'img/favicon.ico',

  url: 'https://bijmantra.org',
  baseUrl: '/',

  organizationName: 'denishdholaria',
  projectName: 'bijmantra',

  onBrokenLinks: 'ignore', // Changed to ignore during heavy porting
  onBrokenMarkdownLinks: 'warn',

  scripts: [
    {
      src: 'https://unpkg.com/@phosphor-icons/web',
      async: false,
    },
  ],
  stylesheets: [
    {
      href: 'https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap',
      type: 'text/css',
    },
  ],

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          path: 'docs',
          routeBasePath: 'docs',
        },
        blog: false, // Disabling blog for now
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  plugins: [
    tailwindPlugin,
    [
      '@docusaurus/plugin-content-docs',
      {
        id: 'codex',
        path: 'codex',
        routeBasePath: 'codex',
        sidebarPath: './sidebarsCodex.ts',
      },
    ],
  ],

  themeConfig: {
    colorMode: {
      defaultMode: 'light',
      disableSwitch: false, // Re-enabling for the Ivory/Obsidian choice
      respectPrefersColorScheme: true,
    },
    image: 'img/logo.png', // We will copy the logo over
    navbar: {
      logo: {
        alt: 'BijMantra Logo',
        src: 'img/logo.png', // Needs copying
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'tutorialSidebar',
          position: 'left',
          label: 'The Forge (Architecture)',
        },
        {
          to: '/codex/3-year-strategy',
          label: 'The Codex (Philosophy)',
          position: 'left',
          activeBaseRegex: `/codex/`,
        },
        {
          href: '/codex/3-year-strategy',
          label: 'The Gritty Reality',
          position: 'right',
        },
        {
          href: 'https://github.com/denishdholaria/bijmantra',
          label: 'GitHub',
          position: 'right',
        },
        {
          href: 'https://app.bijmantra.org/login',
          label: 'Login',
          position: 'right',
          className: 'button button--outline button--secondary navbar-btn-login',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Documentation',
          items: [
            {
              label: 'Architecture specs',
              to: '/docs/intro',
            },
          ],
        },
        {
          title: 'Vision',
          items: [
            {
              label: 'The 1000-Year Vision',
              to: '/codex/vision-1000-years',
            },
          ],
        },
        {
          title: 'Network',
          items: [
            {
              label: 'GitHub',
              href: 'https://github.com/denishdholaria/bijmantra',
            },
            {
              label: 'Open Collective',
              href: 'https://opencollective.com/bijmantra',
            },
          ],
        },
      ],
      copyright: `Built with immense determination. © ${new Date().getFullYear()} BijMantra.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
