/**
 * Quote System Data
 * 
 * Multilingual quotes from agricultural cultures worldwide.
 * Each quote shown in original language + English translation.
 */

import type { Quote, RegionColorMap } from './types'

export const quotes: Quote[] = [
  // Sanskrit / India - Nishkama Karma (Detachment)
  {
    original: "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन",
    translation: "You have the right to perform your duty, but never to the fruits of action.",
    source: "Bhagavad Gita 2.47",
    culture: "Sanskrit • India",
    icon: "🪷",
    region: "india"
  },
  // Sanskrit / India - The philosophical foundation
  {
    original: "योगः कर्मसु कौशलम्",
    translation: "Excellence in action is yoga.",
    source: "Bhagavad Gita 2.50",
    culture: "Sanskrit • India",
    icon: "🪷",
    region: "india"
  },
  // Chinese - Intergenerational cultivation
  {
    original: "前人栽树，后人乘凉",
    translation: "One generation plants the trees; another gets the shade.",
    source: "Chinese Proverb",
    culture: "中文 • China",
    icon: "🌳",
    region: "east-asia"
  },
  // Japanese - Respect for nature
  {
    original: "実るほど頭を垂れる稲穂かな",
    translation: "The more the rice ripens, the more it bows its head.",
    source: "Japanese Proverb",
    culture: "日本語 • Japan",
    icon: "🌾",
    region: "east-asia"
  },
  // Korean - Patience in farming
  {
    original: "콩 심은 데 콩 나고 팥 심은 데 팥 난다",
    translation: "Plant beans, get beans; plant red beans, get red beans.",
    source: "Korean Proverb",
    culture: "한국어 • Korea",
    icon: "🫘",
    region: "east-asia"
  },
  // Arabic - Daily labor and sustenance
  {
    original: "ازرع كل يوم تأكل كل يوم",
    translation: "Plant every day, eat every day.",
    source: "Arabic Proverb",
    culture: "العربية • Middle East",
    icon: "🌴",
    region: "middle-east"
  },
  // Persian - Ancient agricultural heritage
  {
    original: "درختی که تلخ است وی را سرشت، گرش برنشانی به باغ بهشت",
    translation: "A tree bitter by nature won't sweeten even in paradise's garden.",
    source: "Saadi Shirazi",
    culture: "فارسی • Persia",
    icon: "🏛️",
    region: "middle-east"
  },
  // Hebrew - Biblical agricultural wisdom
  {
    original: "הַזֹּרְעִים בְּדִמְעָה בְּרִנָּה יִקְצֹרוּ",
    translation: "Those who sow in tears shall reap in joy.",
    source: "Psalms 126:5",
    culture: "עברית • Israel",
    icon: "✡️",
    region: "middle-east"
  },
  // Swahili - East African wisdom
  {
    original: "Mkulima ni mfalme",
    translation: "The farmer is king.",
    source: "Swahili Proverb",
    culture: "Kiswahili • East Africa",
    icon: "👑",
    region: "africa"
  },
  // Amharic - Ethiopian coffee heritage
  {
    original: "የዛሬ ችግኝ የነገ ጥላ",
    translation: "Today's seedling is tomorrow's shade.",
    source: "Ethiopian Proverb",
    culture: "አማርኛ • Ethiopia",
    icon: "☕",
    region: "africa"
  },
  // Yoruba - West African agricultural wisdom
  {
    original: "Ẹni tó bá gbìn ọ̀gẹ̀dẹ̀, yóò jẹ ọ̀gẹ̀dẹ̀",
    translation: "He who plants plantain will eat plantain.",
    source: "Yoruba Proverb",
    culture: "Yorùbá • Nigeria",
    icon: "🍌",
    region: "africa"
  },
  // Quechua - Andean agricultural wisdom
  {
    original: "Tarpuqqa mikhunqa",
    translation: "He who plants will eat.",
    source: "Quechua Wisdom",
    culture: "Quechua • Andes",
    icon: "🥔",
    region: "americas"
  },
  // Portuguese - Brazilian agricultural power
  {
    original: "Quem planta colhe",
    translation: "Who plants, harvests.",
    source: "Brazilian Proverb",
    culture: "Português • Brazil",
    icon: "🇧🇷",
    region: "americas"
  },
  // Mexican - Maize as civilizational foundation
  {
    original: "Sin maíz, no hay país",
    translation: "Without maize, there is no country.",
    source: "Mexican Agrarian Saying",
    culture: "Español • Mexico",
    icon: "🌽",
    region: "americas"
  },
  // French - Slow accumulation into abundance
  {
    original: "Les petits ruisseaux font les grandes rivières",
    translation: "Little streams make great rivers.",
    source: "French Proverb",
    culture: "Français • France",
    icon: "🌊",
    region: "europe"
  },
  // Russian - Bread as the center of life
  {
    original: "Хлеб всему голова",
    translation: "Bread is the head of everything.",
    source: "Russian Proverb",
    culture: "Русский • Russia",
    icon: "🍞",
    region: "europe"
  },
  // Greek - Consequence and harvest
  {
    original: "Όποιος σπέρνει, θερίζει",
    translation: "Who sows, reaps.",
    source: "Greek Proverb",
    culture: "Ελληνικά • Greece",
    icon: "🫒",
    region: "europe"
  },
  // Spanish - Patience and ripening
  {
    original: "A su tiempo maduran las uvas",
    translation: "Grapes ripen in their own time.",
    source: "Spanish Proverb",
    culture: "Español • Spain",
    icon: "🍇",
    region: "europe"
  },
  // Portuguese - Grain by grain, abundance grows
  {
    original: "Grão a grão enche a galinha o papo",
    translation: "Grain by grain, the hen fills her crop.",
    source: "Portuguese Proverb",
    culture: "Português • Portugal",
    icon: "🐔",
    region: "europe"
  },
  // Bijmantra's own - English
  {
    original: "Thank you to all those who work in acres, not in hours.",
    translation: "For the farmers who feed the world.",
    source: "Bijmantra",
    culture: "English • Global",
    icon: "🌍",
    region: "global"
  },
  // Maori - Pacific agricultural wisdom
  {
    original: "Nāu te rourou, nāku te rourou, ka ora ai te iwi",
    translation: "With your basket and my basket, the people will thrive.",
    source: "Māori Proverb",
    culture: "Te Reo Māori • New Zealand",
    icon: "🥝",
    region: "oceania"
  },
  // Thai - Classical image of agrarian abundance
  {
    original: "ในน้ำมีปลา ในนามีข้าว",
    translation: "In the water there are fish; in the fields there is rice.",
    source: "Ramkhamhaeng Inscription",
    culture: "ไทย • Thailand",
    icon: "🍚",
    region: "southeast-asia"
  },
  // Vietnamese - Rice civilization
  {
    original: "Có công mài sắt, có ngày nên kim",
    translation: "With enough grinding, an iron rod becomes a needle.",
    source: "Vietnamese Proverb",
    culture: "Tiếng Việt • Vietnam",
    icon: "🌾",
    region: "southeast-asia"
  },
  // Tamil - Ancient agricultural wisdom
  {
    original: "உழவுக்கும் தொழிலுக்கும் வந்தனை",
    translation: "Salutations to farming and labor.",
    source: "Tamil Wisdom",
    culture: "Tamil • India",
    icon: "🌿",
    region: "south-asia"
  },
]

// Region colors for visual variety - Prakruti Design System
export const regionColors: RegionColorMap = {
  'india': 'from-orange-500/20 to-green-500/20',
  'south-asia': 'from-prakruti-sona/20 to-amber-500/20',
  'east-asia': 'from-red-500/20 to-rose-500/20',
  'middle-east': 'from-prakruti-sona/20 to-yellow-500/20',
  'africa': 'from-prakruti-patta/20 to-green-500/20',
  'americas': 'from-prakruti-neela/20 to-indigo-500/20',
  'europe': 'from-purple-500/20 to-violet-500/20',
  'oceania': 'from-cyan-500/20 to-teal-500/20',
  'southeast-asia': 'from-lime-500/20 to-green-500/20',
  'global': 'from-prakruti-patta/20 to-prakruti-patta-light/20',
}

export const quoteRegions = Array.from(new Set(quotes.map((quote) => quote.region)))
