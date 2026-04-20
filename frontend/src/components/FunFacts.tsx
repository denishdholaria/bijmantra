/**
 * Fun Facts Component
 * 
 * Display random agricultural and breeding facts for user engagement
 */

import React, { useState, useEffect } from 'react';
import { Sparkles, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface FunFact {
  id: string;
  category: string;
  fact: string;
  source?: string;
}

const FUN_FACTS: FunFact[] = [
  {
    id: '1',
    category: 'History',
    fact: 'The Green Revolution, led by Norman Borlaug, saved over a billion people from starvation through improved wheat varieties.',
    source: 'Nobel Peace Prize 1970'
  },
  {
    id: '2',
    category: 'Genetics',
    fact: 'A single rice plant can produce up to 3,000 grains, and each grain contains about 50,000 genes.',
  },
  {
    id: '3',
    category: 'Breeding',
    fact: 'It takes an average of 10-12 years to develop and release a new crop variety through conventional breeding.',
  },
  {
    id: '4',
    category: 'History',
    fact: 'Gregor Mendel, the father of genetics, worked with over 28,000 pea plants in his monastery garden.',
  },
  {
    id: '5',
    category: 'Diversity',
    fact: 'There are over 40,000 varieties of rice worldwide, with colors ranging from white to black, red, and purple.',
  },
  {
    id: '6',
    category: 'Genetics',
    fact: 'Wheat has one of the largest genomes of any crop - about 5 times larger than the human genome!',
  },
  {
    id: '7',
    category: 'Breeding',
    fact: 'The first hybrid corn was commercialized in the 1930s, increasing yields by 15-20% over open-pollinated varieties.',
  },
  {
    id: '8',
    category: 'Conservation',
    fact: 'The Svalbard Global Seed Vault in Norway stores over 1 million seed samples from around the world.',
  },
  {
    id: '9',
    category: 'History',
    fact: 'The first recorded plant breeding dates back to 9000 BCE when humans domesticated wheat in the Fertile Crescent.',
  },
  {
    id: '10',
    category: 'Genetics',
    fact: 'Polyploidy (having multiple sets of chromosomes) is common in crops - wheat is hexaploid (6 sets), strawberries are octoploid (8 sets)!',
  },
  {
    id: '11',
    category: 'Breeding',
    fact: 'Marker-assisted selection can reduce breeding time by 30-50% compared to conventional methods.',
  },
  {
    id: '12',
    category: 'Diversity',
    fact: 'The International Rice Research Institute (IRRI) maintains over 130,000 rice accessions in its genebank.',
  },
  {
    id: '13',
    category: 'History',
    fact: 'The first genetically modified crop (Flavr Savr tomato) was approved for sale in 1994.',
  },
  {
    id: '14',
    category: 'Genetics',
    fact: 'Maize was domesticated from teosinte, a wild grass that looks nothing like modern corn, through thousands of years of selection.',
  },
  {
    id: '15',
    category: 'Breeding',
    fact: 'Doubled haploid technology can create completely homozygous lines in just one generation instead of 6-8 generations.',
  },
  {
    id: '16',
    category: 'Conservation',
    fact: 'Seed banks around the world preserve over 7.4 million accessions of crop genetic resources.',
  },
  {
    id: '17',
    category: 'History',
    fact: 'Luther Burbank developed over 800 new plant varieties including the Russet Burbank potato (used for McDonald\'s fries).',
  },
  {
    id: '18',
    category: 'Genetics',
    fact: 'The tomato genome was sequenced in 2012, revealing 35,000 genes - more than humans have!',
  },
  {
    id: '19',
    category: 'Breeding',
    fact: 'CRISPR gene editing can make precise changes to crop genomes in weeks, compared to years with traditional breeding.',
  },
  {
    id: '20',
    category: 'Diversity',
    fact: 'There are over 5,000 varieties of potatoes, mostly found in the Andes mountains of Peru and Bolivia.',
  },
  {
    id: '21',
    category: 'History',
    fact: 'The first F1 hybrid vegetable (onion) was developed in 1944, revolutionizing vegetable breeding.',
  },
  {
    id: '22',
    category: 'Genetics',
    fact: 'Heterosis (hybrid vigor) can increase yields by 20-50% in crops like maize and rice.',
  },
  {
    id: '23',
    category: 'Breeding',
    fact: 'Genomic selection uses DNA markers across the entire genome to predict breeding values, increasing accuracy by 30-40%.',
  },
  {
    id: '24',
    category: 'Conservation',
    fact: 'The Millennium Seed Bank in the UK has collected seeds from 40,000 plant species - 13% of the world\'s wild plant species.',
  },
  {
    id: '25',
    category: 'History',
    fact: 'The International Maize and Wheat Improvement Center (CIMMYT) has distributed improved varieties to over 100 countries.',
  },
  {
    id: '26',
    category: 'Genetics',
    fact: 'Bananas are triploid (3 sets of chromosomes) and seedless, making them sterile. All commercial bananas are clones propagated vegetatively.',
  },
  {
    id: '27',
    category: 'Breeding',
    fact: 'Apomixis (asexual seed production) occurs naturally in over 400 plant species, allowing plants to produce seeds without fertilization.',
  },
  {
    id: '28',
    category: 'History',
    fact: 'Ancient Egyptians were practicing selective breeding of wheat and barley as early as 3000 BCE, selecting for larger grains.',
  },
  {
    id: '29',
    category: 'Diversity',
    fact: 'Ethiopia is the center of diversity for coffee, with over 5,000 wild coffee varieties still growing in its forests.',
  },
  {
    id: '30',
    category: 'Genetics',
    fact: 'The strawberry genome has 8 copies of each chromosome (octoploid), making it more complex than most mammals!',
  },
  {
    id: '31',
    category: 'Breeding',
    fact: 'Mutation breeding using radiation has created over 3,200 officially released crop varieties worldwide since the 1950s.',
  },
  {
    id: '32',
    category: 'Conservation',
    fact: 'The CGIAR genebanks collectively hold over 750,000 accessions of crops and their wild relatives.',
  },
  {
    id: '33',
    category: 'History',
    fact: 'The Irish Potato Famine (1845-1852) was caused by genetic uniformity - most potatoes were clones susceptible to late blight.',
  },
  {
    id: '34',
    category: 'Genetics',
    fact: 'Wild relatives of crops contain valuable genes for disease resistance, drought tolerance, and nutritional quality.',
  },
  {
    id: '35',
    category: 'Breeding',
    fact: 'Backcross breeding can transfer a single gene from a wild species into an elite variety in just 5-6 generations.',
  },
  {
    id: '36',
    category: 'Diversity',
    fact: 'Mexico is home to 59 wild relatives of maize, containing genes for drought tolerance and pest resistance.',
  },
  {
    id: '37',
    category: 'History',
    fact: 'The first agricultural experiment station was established in Germany in 1852 to study crop nutrition and breeding.',
  },
  {
    id: '38',
    category: 'Genetics',
    fact: 'Somatic hybridization can fuse cells from two different species to create novel combinations impossible through sexual crossing.',
  },
  {
    id: '39',
    category: 'Breeding',
    fact: 'Speed breeding using extended photoperiods can achieve 6 generations per year in wheat, compared to 2 in the field.',
  },
  {
    id: '40',
    category: 'Conservation',
    fact: 'Cryopreservation at -196°C in liquid nitrogen can preserve seeds and plant tissues for centuries.',
  },
  {
    id: '41',
    category: 'History',
    fact: 'The Haber-Bosch process (1909) for synthesizing ammonia fertilizer enabled the Green Revolution and feeds 50% of the world today.',
  },
  {
    id: '42',
    category: 'Genetics',
    fact: 'Epigenetics allows plants to "remember" stress and pass adaptive traits to offspring without DNA sequence changes.',
  },
  {
    id: '43',
    category: 'Breeding',
    fact: 'Participatory plant breeding involves farmers in variety selection, increasing adoption rates by 40-60%.',
  },
  {
    id: '44',
    category: 'Diversity',
    fact: 'The Andes mountains contain over 4,000 native potato varieties, adapted to altitudes from sea level to 4,500 meters.',
  },
  {
    id: '45',
    category: 'History',
    fact: 'Barbara McClintock discovered "jumping genes" (transposons) in maize in the 1940s, winning the Nobel Prize in 1983.',
  },
  {
    id: '46',
    category: 'Genetics',
    fact: 'Cytoplasmic male sterility (CMS) is used to produce hybrid seeds in crops like rice, eliminating the need for hand emasculation.',
  },
  {
    id: '47',
    category: 'Breeding',
    fact: 'Recurrent selection can increase yield by 1-2% per cycle, accumulating gains of 20-30% over 10-15 cycles.',
  },
  {
    id: '48',
    category: 'Conservation',
    fact: 'In situ conservation in farmers\' fields maintains crop evolution and adaptation to local conditions.',
  },
  {
    id: '49',
    category: 'History',
    fact: 'The Columbian Exchange (1492) transferred crops like maize, potatoes, and tomatoes to Europe, transforming global agriculture.',
  },
  {
    id: '50',
    category: 'Genetics',
    fact: 'Quantitative trait loci (QTL) mapping has identified thousands of genes controlling complex traits like yield and quality.',
  },
  {
    id: '51',
    category: 'Breeding',
    fact: 'Shuttle breeding between different latitudes allows 2-3 generations per year, accelerating variety development.',
  },
  {
    id: '52',
    category: 'Diversity',
    fact: 'India has over 200,000 rice landraces, representing incredible genetic diversity for future breeding.',
  },
  {
    id: '53',
    category: 'History',
    fact: 'The Vavilov Centers identify 8 regions where major crops were domesticated, containing the greatest genetic diversity.',
  },
  {
    id: '54',
    category: 'Genetics',
    fact: 'Allopolyploidy (combining genomes from different species) created crops like wheat, cotton, and canola.',
  },
  {
    id: '55',
    category: 'Breeding',
    fact: 'Embryo rescue allows breeders to save hybrid embryos from incompatible crosses that would normally abort.',
  },
  {
    id: '56',
    category: 'Conservation',
    fact: 'Community seed banks empower farmers to preserve local varieties and maintain seed sovereignty.',
  },
  {
    id: '57',
    category: 'History',
    fact: 'The Rockefeller Foundation funded the Mexican Agricultural Program (1943) that launched the Green Revolution.',
  },
  {
    id: '58',
    category: 'Genetics',
    fact: 'Horizontal gene transfer from Agrobacterium created sweet potato naturally - it\'s a "natural GMO" that evolved 8,000 years ago!',
  },
  {
    id: '59',
    category: 'Breeding',
    fact: 'Ideotype breeding designs plant architecture for maximum yield, like semi-dwarf wheat with stronger stems.',
  },
  {
    id: '60',
    category: 'Diversity',
    fact: 'Wild emmer wheat, the ancestor of modern wheat, still grows in the Fertile Crescent and contains valuable disease resistance genes.',
  },
  {
    id: '61',
    category: 'History',
    fact: 'The International Treaty on Plant Genetic Resources (2004) ensures farmers\' rights and benefit-sharing from crop diversity.',
  },
  {
    id: '62',
    category: 'Genetics',
    fact: 'RNA interference (RNAi) can silence specific genes, creating crops resistant to viruses and pests without foreign DNA.',
  },
  {
    id: '63',
    category: 'Breeding',
    fact: 'Pedigree breeding tracks ancestry over 10+ generations, allowing breeders to predict trait combinations.',
  },
  {
    id: '64',
    category: 'Conservation',
    fact: 'The Global Crop Diversity Trust provides endowment funding to ensure genebanks operate in perpetuity.',
  },
  {
    id: '65',
    category: 'History',
    fact: 'Ancient farmers in Mesoamerica domesticated maize from teosinte through 9,000 years of selection - one of agriculture\'s greatest achievements.',
  },
  {
    id: '66',
    category: 'Genetics',
    fact: 'Genome editing can recreate domestication traits in wild relatives, potentially creating new crops in years instead of millennia.',
  },
  {
    id: '67',
    category: 'Breeding',
    fact: 'Multi-environment trials test varieties across 20-50 locations to ensure stable performance in diverse conditions.',
  },
  {
    id: '68',
    category: 'Diversity',
    fact: 'The Amazon rainforest contains thousands of wild crop relatives and indigenous varieties, representing untapped genetic potential.',
  },
  {
    id: '69',
    category: 'History',
    fact: 'The Dust Bowl (1930s) taught the importance of crop rotation, cover crops, and soil conservation in sustainable agriculture.',
  },
  {
    id: '70',
    category: 'Genetics',
    fact: 'Mitochondrial and chloroplast genomes are inherited maternally in most crops, used to trace evolutionary history.',
  },
  {
    id: '71',
    category: 'Breeding',
    fact: 'Hybrid rice increases yields by 15-20% over inbred varieties, feeding an additional 70 million people annually.',
  },
  {
    id: '72',
    category: 'Conservation',
    fact: 'The Crop Trust\'s "Crop Wild Relatives Project" is collecting and conserving wild relatives of 28 priority crops.',
  },
  {
    id: '73',
    category: 'History',
    fact: 'The discovery of cytoplasmic male sterility in onions (1925) revolutionized hybrid seed production across many crops.',
  },
  {
    id: '74',
    category: 'Genetics',
    fact: 'Ancient DNA from archaeological sites reveals how crops evolved under human selection over thousands of years.',
  },
  {
    id: '75',
    category: 'Breeding',
    fact: 'Genomic prediction models can estimate breeding values for traits that haven\'t been measured yet, saving years of field testing.',
  },
  {
    id: '76',
    category: 'Nanotechnology',
    fact: 'Nano-fertilizers can increase nutrient use efficiency by 30-40% by delivering nutrients directly to plant cells, reducing environmental pollution.',
  },
  {
    id: '77',
    category: 'Biotechnology',
    fact: 'Golden Rice, enriched with beta-carotene through genetic engineering, could prevent 2 million deaths annually from Vitamin A deficiency.',
  },
  {
    id: '78',
    category: 'Recent',
    fact: 'In 2020, CRISPR-edited tomatoes with high GABA (stress-reducing compound) were approved for sale in Japan - the first gene-edited food product.',
  },
  {
    id: '79',
    category: 'Nanotechnology',
    fact: 'Carbon nanotubes can enhance photosynthesis by 30% when delivered to chloroplasts, potentially revolutionizing crop productivity.',
  },
  {
    id: '80',
    category: 'Biotechnology',
    fact: 'Bt crops produce their own insecticide from Bacillus thuringiensis, reducing pesticide use by 37% globally since 1996.',
  },
  {
    id: '81',
    category: 'Recent',
    fact: 'In 2022, scientists created C4 rice by engineering C4 photosynthesis pathways, potentially increasing yields by 50%.',
  },
  {
    id: '82',
    category: 'Nanotechnology',
    fact: 'Nano-sensors can detect plant diseases 7-10 days before visible symptoms appear, enabling early intervention.',
  },
  {
    id: '83',
    category: 'Biotechnology',
    fact: 'Synthetic biology created yeast that produces artemisinin (anti-malaria drug) from sugar, making treatment affordable for millions.',
  },
  {
    id: '84',
    category: 'Recent',
    fact: 'The first perennial wheat variety was released in 2023, reducing soil erosion and eliminating annual replanting.',
  },
  {
    id: '85',
    category: 'Nanotechnology',
    fact: 'Nano-encapsulated pesticides release active ingredients slowly, reducing application frequency by 50-70%.',
  },
  {
    id: '86',
    category: 'Biotechnology',
    fact: 'Drought-tolerant maize developed through genetic engineering is now grown on 20 million hectares in Africa.',
  },
  {
    id: '87',
    category: 'Recent',
    fact: 'In 2021, scientists used AI to discover a new antibiotic from soil bacteria in just 3 days - a process that traditionally takes years.',
  },
  {
    id: '88',
    category: 'Nanotechnology',
    fact: 'Quantum dots can track nutrient uptake in real-time at the cellular level, optimizing fertilizer application.',
  },
  {
    id: '89',
    category: 'Biotechnology',
    fact: 'Biopharming uses plants as factories to produce vaccines and medicines - tobacco plants can produce COVID-19 vaccine candidates.',
  },
  {
    id: '90',
    category: 'Recent',
    fact: 'Vertical farms using LED lighting can produce 350 times more food per square meter than traditional farming.',
  },
  {
    id: '91',
    category: 'Nanotechnology',
    fact: 'Nano-clay composites can increase water retention in sandy soils by 40%, crucial for drought-prone regions.',
  },
  {
    id: '92',
    category: 'Biotechnology',
    fact: 'Gene drives could eliminate invasive species or disease vectors, but raise ethical concerns about ecosystem impacts.',
  },
  {
    id: '93',
    category: 'Recent',
    fact: 'In 2023, lab-grown coffee was produced from cell cultures, potentially saving rainforests from coffee plantation expansion.',
  },
  {
    id: '94',
    category: 'Nanotechnology',
    fact: 'Silver nanoparticles can protect seeds from fungal diseases, increasing germination rates by 20-30% without chemical fungicides.',
  },
  {
    id: '95',
    category: 'Biotechnology',
    fact: 'Nitrogen-fixing cereals are being developed by transferring genes from legumes, potentially eliminating the need for nitrogen fertilizer.',
  },
  {
    id: '96',
    category: 'Recent',
    fact: 'The "Doomsday Vault" in Svalbard received its 1 millionth seed sample in 2020, including seeds from war-torn Syria and Yemen.',
  },
  {
    id: '97',
    category: 'Nanotechnology',
    fact: 'Graphene-based sensors can detect single molecules of plant hormones, enabling precision agriculture at the molecular level.',
  },
  {
    id: '98',
    category: 'Biotechnology',
    fact: 'CRISPR base editing can change single DNA letters without cutting the DNA strand, achieving 99.9% precision in gene editing.',
  },
  {
    id: '99',
    category: 'Recent',
    fact: 'In 2022, scientists revived a 32,000-year-old plant from Siberian permafrost, the oldest living organism ever regenerated.',
  },
  {
    id: '100',
    category: 'Nanotechnology',
    fact: 'Nano-biostimulants can increase crop stress tolerance by 25-35% by enhancing plant immune responses at the cellular level.',
  },
];

interface FunFactsProps {
  variant?: 'card' | 'inline';
  showCategory?: boolean;
  autoRotate?: boolean;
  rotateInterval?: number; // in seconds
}

export function FunFacts({
  variant = 'card',
  showCategory = true,
  autoRotate = false,
  rotateInterval = 30,
}: FunFactsProps) {
  const [currentFact, setCurrentFact] = useState<FunFact>(
    FUN_FACTS[Math.floor(Math.random() * FUN_FACTS.length)]
  );

  const getRandomFact = () => {
    let newFact;
    do {
      newFact = FUN_FACTS[Math.floor(Math.random() * FUN_FACTS.length)];
    } while (newFact.id === currentFact.id && FUN_FACTS.length > 1);
    setCurrentFact(newFact);
  };

  useEffect(() => {
    if (autoRotate) {
      const interval = setInterval(getRandomFact, rotateInterval * 1000);
      return () => clearInterval(interval);
    }
  }, [autoRotate, rotateInterval, currentFact]);

  if (variant === 'inline') {
    return (
      <div className="flex items-start gap-3 p-4 bg-muted/50 rounded-lg">
        <Sparkles className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
        <div className="flex-1 space-y-1">
          {showCategory && (
            <div className="text-xs font-semibold text-primary uppercase tracking-wide">
              {currentFact.category}
            </div>
          )}
          <p className="text-sm text-foreground">{currentFact.fact}</p>
          {currentFact.source && (
            <p className="text-xs text-muted-foreground italic">
              Source: {currentFact.source}
            </p>
          )}
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={getRandomFact}
          className="flex-shrink-0"
          aria-label="Show another fact"
        >
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            Did You Know?
          </div>
          <Button variant="ghost" size="sm" onClick={getRandomFact} aria-label="Show another fact">
            <RefreshCw className="h-4 w-4" />
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {showCategory && (
          <div className="text-xs font-semibold text-primary uppercase tracking-wide">
            {currentFact.category}
          </div>
        )}
        <p className="text-sm leading-relaxed">{currentFact.fact}</p>
        {currentFact.source && (
          <p className="text-xs text-muted-foreground italic">
            Source: {currentFact.source}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

export default FunFacts;
