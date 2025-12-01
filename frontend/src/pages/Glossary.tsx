/**
 * Glossary - Breeding Terminology
 * Comprehensive glossary of plant breeding terms
 */
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'

interface GlossaryTerm {
  term: string
  definition: string
  category: string
  related?: string[]
}

const glossaryTerms: GlossaryTerm[] = [
  // Genetics & Breeding
  { term: 'Allele', definition: 'One of two or more alternative forms of a gene that arise by mutation and are found at the same place on a chromosome.', category: 'genetics', related: ['Gene', 'Locus', 'Genotype'] },
  { term: 'Backcross', definition: 'A cross between a hybrid and one of its parents, or an individual genetically similar to its parent, to achieve offspring with a genetic identity closer to that of the parent.', category: 'breeding', related: ['Cross', 'Introgression'] },
  { term: 'Breeding Value', definition: 'The genetic value of an individual as a parent, measured by the mean performance of its progeny.', category: 'breeding', related: ['Heritability', 'Selection'] },
  { term: 'Cross', definition: 'The deliberate mating of two parent plants to produce offspring with desired characteristics.', category: 'breeding', related: ['Hybridization', 'Backcross'] },
  { term: 'Cultivar', definition: 'A plant variety that has been produced in cultivation by selective breeding and given a unique name.', category: 'breeding', related: ['Variety', 'Line'] },
  { term: 'Dominant', definition: 'An allele that expresses its phenotype even when heterozygous with a recessive allele.', category: 'genetics', related: ['Recessive', 'Allele'] },
  { term: 'F1 Generation', definition: 'The first filial generation; offspring resulting from a cross between two parental lines.', category: 'genetics', related: ['F2 Generation', 'Cross'] },
  { term: 'F2 Generation', definition: 'The second filial generation; offspring resulting from self-pollination or intercrossing of F1 individuals.', category: 'genetics', related: ['F1 Generation', 'Segregation'] },
  { term: 'Gene', definition: 'A unit of heredity that is transferred from a parent to offspring and determines some characteristic of the offspring.', category: 'genetics', related: ['Allele', 'DNA', 'Chromosome'] },
  { term: 'Genetic Gain', definition: 'The amount of increase in performance achieved through selection, usually expressed per unit of time.', category: 'breeding', related: ['Selection', 'Heritability'] },
  { term: 'Genotype', definition: 'The genetic constitution of an individual organism, as distinguished from its physical appearance (phenotype).', category: 'genetics', related: ['Phenotype', 'Allele'] },
  { term: 'Germplasm', definition: 'Living genetic resources such as seeds or tissues that are maintained for breeding, preservation, and research.', category: 'breeding', related: ['Accession', 'Gene Bank'] },
  { term: 'GxE Interaction', definition: 'Genotype by Environment interaction; when the relative performance of genotypes changes across different environments.', category: 'breeding', related: ['Environment', 'Stability'] },
  { term: 'Heritability', definition: 'The proportion of observed variation in a trait that can be attributed to genetic variation.', category: 'genetics', related: ['Genetic Gain', 'Selection'] },
  { term: 'Heterosis', definition: 'The tendency of a crossbred individual to show qualities superior to those of both parents; hybrid vigor.', category: 'genetics', related: ['Hybrid', 'Inbreeding Depression'] },
  { term: 'Heterozygous', definition: 'Having two different alleles of a particular gene or genes.', category: 'genetics', related: ['Homozygous', 'Allele'] },
  { term: 'Homozygous', definition: 'Having two identical alleles of a particular gene or genes.', category: 'genetics', related: ['Heterozygous', 'Inbred'] },
  { term: 'Hybrid', definition: 'The offspring of two plants of different breeds, varieties, species, or genera.', category: 'breeding', related: ['Cross', 'Heterosis'] },
  { term: 'Inbred Line', definition: 'A nearly homozygous line produced by repeated self-fertilization or close inbreeding.', category: 'breeding', related: ['Homozygous', 'Pure Line'] },
  { term: 'Introgression', definition: 'The transfer of genetic information from one species to another through hybridization and repeated backcrossing.', category: 'breeding', related: ['Backcross', 'Gene Flow'] },
  { term: 'Line', definition: 'A group of individuals from a common ancestry that breed true for certain characteristics.', category: 'breeding', related: ['Cultivar', 'Variety'] },
  { term: 'Locus', definition: 'The specific location of a gene or DNA sequence on a chromosome.', category: 'genetics', related: ['Gene', 'Chromosome'] },
  { term: 'Marker', definition: 'A gene or DNA sequence with a known location on a chromosome that can be used to identify individuals or species.', category: 'genetics', related: ['QTL', 'MAS'] },
  { term: 'MAS', definition: 'Marker-Assisted Selection; using molecular markers to select for traits of interest.', category: 'breeding', related: ['Marker', 'Selection'] },
  { term: 'Pedigree', definition: 'A record of the ancestry of an individual, showing the relationship between ancestors and descendants.', category: 'breeding', related: ['Ancestry', 'Lineage'] },
  { term: 'Phenotype', definition: 'The set of observable characteristics of an individual resulting from the interaction of its genotype with the environment.', category: 'genetics', related: ['Genotype', 'Trait'] },
  { term: 'QTL', definition: 'Quantitative Trait Locus; a section of DNA that correlates with variation in a quantitative trait.', category: 'genetics', related: ['Marker', 'Trait'] },
  { term: 'Recessive', definition: 'An allele that only expresses its phenotype when homozygous; masked by a dominant allele when heterozygous.', category: 'genetics', related: ['Dominant', 'Allele'] },
  { term: 'Recurrent Selection', definition: 'A breeding method involving repeated cycles of selection and intercrossing to improve a population.', category: 'breeding', related: ['Selection', 'Population Improvement'] },
  { term: 'Segregation', definition: 'The separation of allele pairs during gamete formation, resulting in offspring with different combinations of alleles.', category: 'genetics', related: ['Mendel', 'F2 Generation'] },
  { term: 'Selection', definition: 'The process of choosing individuals with desirable traits to be parents of the next generation.', category: 'breeding', related: ['Genetic Gain', 'Breeding Value'] },
  { term: 'Selection Index', definition: 'A method of combining information on multiple traits into a single value for selection decisions.', category: 'breeding', related: ['Selection', 'Multi-trait'] },
  { term: 'Self-pollination', definition: 'The transfer of pollen from the anther to the stigma of the same flower or another flower on the same plant.', category: 'breeding', related: ['Cross-pollination', 'Inbreeding'] },
  { term: 'Trait', definition: 'A distinguishing quality or characteristic of an organism, often determined by genes.', category: 'genetics', related: ['Phenotype', 'Character'] },
  { term: 'Variety', definition: 'A taxonomic rank below species; a group of plants with distinct characteristics.', category: 'breeding', related: ['Cultivar', 'Line'] },
  
  // Trial & Experimental Design
  { term: 'Alpha-lattice', definition: 'An incomplete block design used when the number of entries is too large for complete blocks.', category: 'design', related: ['RCBD', 'Block'] },
  { term: 'Block', definition: 'A group of experimental units that are similar to each other and are grouped together to reduce variability.', category: 'design', related: ['Replication', 'RCBD'] },
  { term: 'Check', definition: 'A standard variety or treatment included in an experiment for comparison purposes.', category: 'design', related: ['Control', 'Reference'] },
  { term: 'CRD', definition: 'Completely Randomized Design; an experimental design where treatments are assigned completely at random.', category: 'design', related: ['RCBD', 'Randomization'] },
  { term: 'Entry', definition: 'A genotype, variety, or treatment included in a trial for evaluation.', category: 'design', related: ['Treatment', 'Genotype'] },
  { term: 'Plot', definition: 'The smallest unit in a field experiment to which a treatment is applied.', category: 'design', related: ['Subplot', 'Experimental Unit'] },
  { term: 'RCBD', definition: 'Randomized Complete Block Design; an experimental design where each block contains all treatments.', category: 'design', related: ['Block', 'CRD'] },
  { term: 'Replication', definition: 'The repetition of an experimental treatment to increase reliability and estimate experimental error.', category: 'design', related: ['Block', 'Precision'] },
  
  // BrAPI & Data
  { term: 'BrAPI', definition: 'Breeding API; a standardized RESTful web service specification for plant breeding data.', category: 'data', related: ['API', 'Interoperability'] },
  { term: 'Observation', definition: 'A recorded measurement or assessment of a trait for a specific observation unit.', category: 'data', related: ['Trait', 'Phenotype'] },
  { term: 'Observation Unit', definition: 'The entity being observed, such as a plot, plant, or sample.', category: 'data', related: ['Plot', 'Observation'] },
  { term: 'Ontology', definition: 'A formal representation of knowledge as a set of concepts and relationships between them.', category: 'data', related: ['Trait', 'Standardization'] },
  { term: 'Study', definition: 'A specific experiment or evaluation within a trial, often at a single location and time.', category: 'data', related: ['Trial', 'Experiment'] },
  { term: 'Trial', definition: 'A set of studies evaluating germplasm across locations and/or years.', category: 'data', related: ['Study', 'MET'] },
]

const categories = [
  { id: 'all', label: 'All Terms', icon: '📚' },
  { id: 'genetics', label: 'Genetics', icon: '🧬' },
  { id: 'breeding', label: 'Breeding', icon: '🌱' },
  { id: 'design', label: 'Trial Design', icon: '🎲' },
  { id: 'data', label: 'Data & BrAPI', icon: '💾' },
]

export function Glossary() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [expandedTerm, setExpandedTerm] = useState<string | null>(null)

  const filteredTerms = glossaryTerms
    .filter(term => {
      const matchesSearch = term.term.toLowerCase().includes(searchQuery.toLowerCase()) ||
                           term.definition.toLowerCase().includes(searchQuery.toLowerCase())
      const matchesCategory = selectedCategory === 'all' || term.category === selectedCategory
      return matchesSearch && matchesCategory
    })
    .sort((a, b) => a.term.localeCompare(b.term))

  // Group by first letter
  const groupedTerms = filteredTerms.reduce((acc, term) => {
    const letter = term.term[0].toUpperCase()
    if (!acc[letter]) acc[letter] = []
    acc[letter].push(term)
    return acc
  }, {} as Record<string, GlossaryTerm[]>)

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Glossary</h1>
          <p className="text-muted-foreground mt-1">Plant breeding terminology and definitions</p>
        </div>
        <Link to="/help">
          <Button variant="outline">← Back to Help</Button>
        </Link>
      </div>

      {/* Search and Filter */}
      <Card>
        <CardContent className="pt-6 space-y-4">
          <Input
            type="search"
            placeholder="Search terms..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="max-w-md"
          />
          <div className="flex flex-wrap gap-2">
            {categories.map(cat => (
              <Button
                key={cat.id}
                variant={selectedCategory === cat.id ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedCategory(cat.id)}
              >
                {cat.icon} {cat.label}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Alphabet Navigation */}
      <div className="flex flex-wrap gap-1">
        {Object.keys(groupedTerms).sort().map(letter => (
          <a
            key={letter}
            href={`#letter-${letter}`}
            className="w-8 h-8 flex items-center justify-center bg-muted hover:bg-primary hover:text-primary-foreground rounded transition-colors text-sm font-medium"
          >
            {letter}
          </a>
        ))}
      </div>

      {/* Terms List */}
      <div className="space-y-6">
        {Object.entries(groupedTerms).sort().map(([letter, terms]) => (
          <div key={letter} id={`letter-${letter}`}>
            <h2 className="text-2xl font-bold text-primary mb-3 sticky top-0 bg-background py-2">
              {letter}
            </h2>
            <div className="space-y-2">
              {terms.map(term => (
                <Card 
                  key={term.term}
                  className={`cursor-pointer transition-all ${expandedTerm === term.term ? 'ring-2 ring-primary' : ''}`}
                  onClick={() => setExpandedTerm(expandedTerm === term.term ? null : term.term)}
                >
                  <CardContent className="pt-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="font-semibold text-lg">{term.term}</h3>
                        <p className={`text-muted-foreground mt-1 ${expandedTerm === term.term ? '' : 'line-clamp-2'}`}>
                          {term.definition}
                        </p>
                        {expandedTerm === term.term && term.related && (
                          <div className="mt-3 pt-3 border-t">
                            <p className="text-sm font-medium mb-2">Related terms:</p>
                            <div className="flex flex-wrap gap-1">
                              {term.related.map(rel => (
                                <Badge 
                                  key={rel} 
                                  variant="secondary"
                                  className="cursor-pointer hover:bg-primary hover:text-primary-foreground"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    setSearchQuery(rel)
                                    setExpandedTerm(null)
                                  }}
                                >
                                  {rel}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                      <Badge variant="outline" className="ml-2 flex-shrink-0">
                        {categories.find(c => c.id === term.category)?.label}
                      </Badge>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        ))}
      </div>

      {filteredTerms.length === 0 && (
        <div className="text-center py-12">
          <span className="text-4xl">🔍</span>
          <p className="mt-2 text-muted-foreground">No terms found matching your search</p>
        </div>
      )}

      {/* Stats */}
      <Card className="bg-muted/50">
        <CardContent className="pt-4">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>Showing {filteredTerms.length} of {glossaryTerms.length} terms</span>
            <span>📖 Bijmantra Glossary v1.0</span>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
