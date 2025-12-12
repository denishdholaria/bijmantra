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
          <Button variant="ghost" size="sm" onClick={getRandomFact}>
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
