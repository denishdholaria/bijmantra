/**
 * Glossary Page
 *
 * Plant breeding and agricultural terminology.
 */

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';

interface Term {
  term: string;
  definition: string;
  category: string;
}

export function Glossary() {
  const [search, setSearch] = useState('');

  const terms: Term[] = [
    { term: 'Accession', definition: 'A distinct sample of seeds or plant material collected and stored in a gene bank.', category: 'Seed Bank' },
    { term: 'Allele', definition: 'One of two or more alternative forms of a gene at a particular locus.', category: 'Genetics' },
    { term: 'BrAPI', definition: 'Breeding API - a standardized interface for plant breeding databases.', category: 'Technology' },
    { term: 'Cross', definition: 'The offspring resulting from mating two genetically different parents.', category: 'Breeding' },
    { term: 'GEBV', definition: 'Genomic Estimated Breeding Value - predicted genetic merit using genomic data.', category: 'Genomics' },
    { term: 'Germplasm', definition: 'Living genetic resources such as seeds or tissue maintained for breeding.', category: 'Seed Bank' },
    { term: 'GDD', definition: 'Growing Degree Days - accumulated heat units for crop development.', category: 'Agronomy' },
    { term: 'Heritability', definition: 'The proportion of phenotypic variance attributable to genetic variance.', category: 'Genetics' },
    { term: 'MAS', definition: 'Marker-Assisted Selection - using DNA markers to select for traits.', category: 'Breeding' },
    { term: 'Pedigree', definition: 'The ancestry or lineage of an individual or variety.', category: 'Breeding' },
    { term: 'Phenotype', definition: 'The observable characteristics of an organism.', category: 'Genetics' },
    { term: 'QTL', definition: 'Quantitative Trait Locus - a region of DNA associated with a quantitative trait.', category: 'Genomics' },
    { term: 'RCBD', definition: 'Randomized Complete Block Design - an experimental design for field trials.', category: 'Statistics' },
    { term: 'Viability', definition: 'The ability of seeds to germinate under favorable conditions.', category: 'Seed Bank' },
  ];

  const filteredTerms = terms.filter(
    (t) => t.term.toLowerCase().includes(search.toLowerCase()) || t.definition.toLowerCase().includes(search.toLowerCase())
  );

  const categories = [...new Set(terms.map((t) => t.category))];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-foreground">Glossary</h1>
        <p className="text-muted-foreground mt-1">Plant breeding and agricultural terminology</p>
      </div>

      <Card>
        <CardContent className="p-4">
          <Input
            placeholder="Search terms..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="max-w-md"
          />
        </CardContent>
      </Card>

      <div className="grid md:grid-cols-2 gap-4">
        {filteredTerms.map((item) => (
          <Card key={item.term}>
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <h3 className="font-bold text-lg text-primary">{item.term}</h3>
                <span className="text-xs px-2 py-0.5 bg-muted text-muted-foreground rounded">{item.category}</span>
              </div>
              <p className="text-muted-foreground mt-2">{item.definition}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredTerms.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          No terms found matching "{search}"
        </div>
      )}
    </div>
  );
}

export default Glossary;
