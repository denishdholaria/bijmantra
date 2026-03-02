export type WallpaperOption = {
    id: string
    name: string
    description: string
    backgroundClassName?: string
    previewClassName?: string
    imageUrl?: string
}

export const wallpaperOptions: WallpaperOption[] = [
    {
        id: 'neutral-taupe',
        name: 'Neutral Taupe',
        description: 'Minimalist neutral tone',
        backgroundClassName: 'bg-[#E5E0D5] dark:bg-[image:radial-gradient(100%_100%_at_50%_0%,var(--color-stone-700),var(--color-stone-900),var(--color-stone-950))]',
        previewClassName: 'bg-[#E5E0D5] dark:bg-[image:radial-gradient(100%_100%_at_50%_0%,var(--color-stone-700),var(--color-stone-900),var(--color-stone-950))]',
    },
    {
        id: 'bijmantravw',
        name: 'BijMantraVW',
        description: 'Signature system mark',
        backgroundClassName: 'bg-gradient-to-br from-[#f7efe3] via-[#f4e8d8] to-[#efe0c8] dark:bg-[image:radial-gradient(100%_100%_at_50%_0%,var(--color-amber-800),var(--color-yellow-950),var(--color-stone-950))]',
        previewClassName: 'bg-gradient-to-br from-[#f7efe3] via-[#f4e8d8] to-[#efe0c8] dark:bg-[image:radial-gradient(100%_100%_at_50%_0%,var(--color-amber-800),var(--color-yellow-950),var(--color-stone-950))]',
    },
    {
        id: 'field-dawn',
        name: 'Field Dawn',
        description: 'Soft sunrise over soil textures',
        backgroundClassName: 'bg-gradient-to-br from-[#f5efe4] via-[#f1eadf] to-[#e7dcc7] dark:bg-[image:radial-gradient(100%_100%_at_50%_0%,var(--color-orange-800),var(--color-orange-950),var(--color-red-950))]',
        previewClassName: 'bg-gradient-to-br from-[#f5efe4] via-[#f1eadf] to-[#e7dcc7] dark:bg-[image:radial-gradient(100%_100%_at_50%_0%,var(--color-orange-800),var(--color-orange-950),var(--color-red-950))]',
    },
    {
        id: 'canopy-dusk',
        name: 'Canopy Dusk',
        description: 'Cool canopy gradients for focus',
        backgroundClassName: 'bg-gradient-to-br from-[#eff4f6] via-[#e3edf1] to-[#d7e5ec] dark:bg-[image:radial-gradient(100%_100%_at_50%_0%,var(--color-cyan-800),var(--color-sky-950),var(--color-blue-950))]',
        previewClassName: 'bg-gradient-to-br from-[#eff4f6] via-[#e3edf1] to-[#d7e5ec] dark:bg-[image:radial-gradient(100%_100%_at_50%_0%,var(--color-cyan-800),var(--color-sky-950),var(--color-blue-950))]',
    },
    {
        id: 'monsoon',
        name: 'Monsoon',
        description: 'Deep greens with rainfall calm',
        backgroundClassName: 'bg-gradient-to-br from-[#edf3ee] via-[#e2ece5] to-[#d2e0d7] dark:bg-[image:radial-gradient(100%_100%_at_50%_0%,var(--color-emerald-800),var(--color-green-950),var(--color-teal-950))]',
        previewClassName: 'bg-gradient-to-br from-[#edf3ee] via-[#e2ece5] to-[#d2e0d7] dark:bg-[image:radial-gradient(100%_100%_at_50%_0%,var(--color-emerald-800),var(--color-green-950),var(--color-teal-950))]',
    },
]
