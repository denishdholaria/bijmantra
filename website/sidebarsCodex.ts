import type { SidebarsConfig } from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
    codexSidebar: [
        'intro',
        {
            type: 'category',
            label: 'The Philosophy',
            items: [
                '3-year-strategy',
                '10-year-vision',
                'vision-1000-years',
                'brapi-acknowledgment',
                'un-sdg-alignment',
            ],
        },
    ],
};

export default sidebars;
