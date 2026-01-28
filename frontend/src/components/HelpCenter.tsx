/**
 * Help Center Component
 * 
 * Provides contextual help, documentation links, and support options.
 * Can be triggered from anywhere in the app.
 */

import { useState } from 'react';
import { 
  HelpCircle, Book, MessageCircle, Video, ExternalLink, 
  Search, ChevronRight, Keyboard, Lightbulb, Bug, Mail
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';

interface HelpArticle {
  id: string;
  title: string;
  description: string;
  category: string;
  tags: string[];
  url?: string;
}

interface HelpCenterProps {
  contextPage?: string;
  trigger?: React.ReactNode;
}

const HELP_ARTICLES: HelpArticle[] = [
  // Getting Started
  {
    id: 'gs-1',
    title: 'Quick Start Guide',
    description: 'Get up and running with Bijmantra in 5 minutes',
    category: 'Getting Started',
    tags: ['beginner', 'setup'],
  },
  {
    id: 'gs-2',
    title: 'Creating Your First Trial',
    description: 'Step-by-step guide to setting up a breeding trial',
    category: 'Getting Started',
    tags: ['trial', 'beginner'],
  },
  {
    id: 'gs-3',
    title: 'Importing Germplasm Data',
    description: 'How to import germplasm from CSV or BrAPI',
    category: 'Getting Started',
    tags: ['import', 'germplasm', 'data'],
  },
  // Plant Sciences
  {
    id: 'ps-1',
    title: 'Understanding Breeding Programs',
    description: 'How to structure and manage breeding programs',
    category: 'Plant Sciences',
    tags: ['breeding', 'programs'],
  },
  {
    id: 'ps-2',
    title: 'Recording Observations',
    description: 'Best practices for phenotypic data collection',
    category: 'Plant Sciences',
    tags: ['observations', 'phenotype'],
  },
  {
    id: 'ps-3',
    title: 'Genomic Selection (GBLUP)',
    description: 'Using genomic data for breeding decisions',
    category: 'Plant Sciences',
    tags: ['genomics', 'gblup', 'selection'],
  },
  // Seed Bank
  {
    id: 'sb-1',
    title: 'Managing Accessions',
    description: 'How to register and track germplasm accessions',
    category: 'Seed Bank',
    tags: ['accessions', 'germplasm'],
  },
  {
    id: 'sb-2',
    title: 'Viability Testing',
    description: 'Conducting and recording germination tests',
    category: 'Seed Bank',
    tags: ['viability', 'germination'],
  },
  // Field Work
  {
    id: 'fw-1',
    title: 'Using Field Mode',
    description: 'Optimizing the interface for outdoor data collection',
    category: 'Field Work',
    tags: ['field', 'mobile', 'offline'],
  },
  {
    id: 'fw-2',
    title: 'Offline Data Entry',
    description: 'Working without internet and syncing later',
    category: 'Field Work',
    tags: ['offline', 'sync'],
  },
  // API & Integration
  {
    id: 'api-1',
    title: 'BrAPI Integration',
    description: 'Connecting with other BrAPI-compatible systems',
    category: 'API & Integration',
    tags: ['brapi', 'api', 'integration'],
  },
  {
    id: 'api-2',
    title: 'Data Export Options',
    description: 'Exporting data in various formats',
    category: 'API & Integration',
    tags: ['export', 'csv', 'json'],
  },
];

const QUICK_TIPS = [
  { icon: <Keyboard className="h-4 w-4" />, tip: 'Press ⌘K to open the command palette' },
  { icon: <Lightbulb className="h-4 w-4" />, tip: 'Use Field Mode for outdoor data collection' },
  { icon: <Lightbulb className="h-4 w-4" />, tip: 'Right-click on any entity for quick actions' },
  { icon: <Lightbulb className="h-4 w-4" />, tip: 'Data syncs automatically when you\'re back online' },
  { icon: <Lightbulb className="h-4 w-4" />, tip: 'Ask Veena AI for help with any task' },
];

const CATEGORIES = ['All', 'Getting Started', 'Plant Sciences', 'Seed Bank', 'Field Work', 'API & Integration'];

export function HelpCenter({ contextPage, trigger }: HelpCenterProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');

  const filteredArticles = HELP_ARTICLES.filter(article => {
    const matchesSearch = search === '' || 
      article.title.toLowerCase().includes(search.toLowerCase()) ||
      article.description.toLowerCase().includes(search.toLowerCase()) ||
      article.tags.some(tag => tag.toLowerCase().includes(search.toLowerCase()));
    
    const matchesCategory = selectedCategory === 'All' || article.category === selectedCategory;
    
    return matchesSearch && matchesCategory;
  });

  // Get contextual articles based on current page
  const contextualArticles = contextPage
    ? HELP_ARTICLES.filter(a => 
        a.tags.some(tag => contextPage.toLowerCase().includes(tag)) ||
        a.category.toLowerCase().includes(contextPage.toLowerCase())
      ).slice(0, 3)
    : [];

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button variant="ghost" size="icon" aria-label="Open help center">
            <HelpCircle className="h-5 w-5" />
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-3xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <HelpCircle className="h-5 w-5" />
            Help Center
          </DialogTitle>
          <DialogDescription>
            Find answers, learn features, and get support
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="articles" className="mt-4">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="articles">
              <Book className="h-4 w-4 mr-2" />
              Articles
            </TabsTrigger>
            <TabsTrigger value="tips">
              <Lightbulb className="h-4 w-4 mr-2" />
              Tips
            </TabsTrigger>
            <TabsTrigger value="shortcuts">
              <Keyboard className="h-4 w-4 mr-2" />
              Shortcuts
            </TabsTrigger>
            <TabsTrigger value="support">
              <MessageCircle className="h-4 w-4 mr-2" />
              Support
            </TabsTrigger>
          </TabsList>

          <TabsContent value="articles" className="space-y-4 mt-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search help articles..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>

            {/* Categories */}
            <div className="flex gap-2 flex-wrap">
              {CATEGORIES.map((cat) => (
                <Button
                  key={cat}
                  variant={selectedCategory === cat ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setSelectedCategory(cat)}
                >
                  {cat}
                </Button>
              ))}
            </div>

            {/* Contextual Help */}
            {contextualArticles.length > 0 && !search && selectedCategory === 'All' && (
              <div className="p-4 bg-primary/5 rounded-lg border border-primary/20">
                <p className="text-sm font-medium text-primary mb-2">
                  📍 Related to this page
                </p>
                <div className="space-y-2">
                  {contextualArticles.map((article) => (
                    <button
                      key={article.id}
                      className="w-full text-left p-2 rounded hover:bg-primary/10 transition-colors"
                    >
                      <p className="font-medium text-sm">{article.title}</p>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Articles List */}
            <ScrollArea className="h-[300px]">
              <div className="space-y-2">
                {filteredArticles.map((article) => (
                  <button
                    key={article.id}
                    className="w-full text-left p-4 rounded-lg border hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-medium">{article.title}</p>
                        <p className="text-sm text-muted-foreground mt-1">
                          {article.description}
                        </p>
                        <div className="flex gap-1 mt-2">
                          {article.tags.slice(0, 3).map((tag) => (
                            <Badge key={tag} variant="secondary" className="text-xs">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <ChevronRight className="h-5 w-5 text-muted-foreground" />
                    </div>
                  </button>
                ))}
                {filteredArticles.length === 0 && (
                  <div className="text-center py-8 text-muted-foreground">
                    <Search className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p>No articles found</p>
                  </div>
                )}
              </div>
            </ScrollArea>
          </TabsContent>

          <TabsContent value="tips" className="mt-4">
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground">
                Quick tips to help you work more efficiently:
              </p>
              {QUICK_TIPS.map((item, i) => (
                <div
                  key={i}
                  className="flex items-center gap-3 p-3 bg-muted rounded-lg"
                >
                  <div className="p-2 bg-background rounded-lg">
                    {item.icon}
                  </div>
                  <p className="text-sm">{item.tip}</p>
                </div>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="shortcuts" className="mt-4">
            <ScrollArea className="h-[350px]">
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium mb-2">Navigation</h4>
                  <div className="space-y-2">
                    <ShortcutRow keys={['⌘', 'K']} description="Open command palette" />
                    <ShortcutRow keys={['⌘', '/']} description="Quick search" />
                    <ShortcutRow keys={['⌘', 'B']} description="Toggle sidebar" />
                    <ShortcutRow keys={['G', 'H']} description="Go to home" />
                    <ShortcutRow keys={['G', 'T']} description="Go to trials" />
                    <ShortcutRow keys={['G', 'G']} description="Go to germplasm" />
                  </div>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Data Entry</h4>
                  <div className="space-y-2">
                    <ShortcutRow keys={['⌘', 'N']} description="New observation" />
                    <ShortcutRow keys={['⌘', 'S']} description="Save" />
                    <ShortcutRow keys={['Tab']} description="Next field" />
                    <ShortcutRow keys={['Shift', 'Tab']} description="Previous field" />
                    <ShortcutRow keys={['Enter']} description="Submit form" />
                  </div>
                </div>
                <div>
                  <h4 className="font-medium mb-2">View</h4>
                  <div className="space-y-2">
                    <ShortcutRow keys={['⌘', 'F']} description="Toggle field mode" />
                    <ShortcutRow keys={['⌘', '+']} description="Zoom in" />
                    <ShortcutRow keys={['⌘', '-']} description="Zoom out" />
                    <ShortcutRow keys={['?']} description="Show all shortcuts" />
                  </div>
                </div>
              </div>
            </ScrollArea>
          </TabsContent>

          <TabsContent value="support" className="mt-4">
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <button className="p-4 border rounded-lg hover:bg-muted/50 transition-colors text-left">
                  <Book className="h-6 w-6 text-primary mb-2" />
                  <p className="font-medium">Documentation</p>
                  <p className="text-sm text-muted-foreground">
                    Browse full documentation
                  </p>
                </button>
                <button className="p-4 border rounded-lg hover:bg-muted/50 transition-colors text-left">
                  <Video className="h-6 w-6 text-primary mb-2" />
                  <p className="font-medium">Video Tutorials</p>
                  <p className="text-sm text-muted-foreground">
                    Watch step-by-step guides
                  </p>
                </button>
                <button className="p-4 border rounded-lg hover:bg-muted/50 transition-colors text-left">
                  <MessageCircle className="h-6 w-6 text-primary mb-2" />
                  <p className="font-medium">Community Forum</p>
                  <p className="text-sm text-muted-foreground">
                    Ask questions, share tips
                  </p>
                </button>
                <button className="p-4 border rounded-lg hover:bg-muted/50 transition-colors text-left">
                  <Bug className="h-6 w-6 text-primary mb-2" />
                  <p className="font-medium">Report a Bug</p>
                  <p className="text-sm text-muted-foreground">
                    Help us improve Bijmantra
                  </p>
                </button>
              </div>

              <div className="p-4 bg-muted rounded-lg">
                <div className="flex items-center gap-3">
                  <Mail className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="font-medium">Need more help?</p>
                    <p className="text-sm text-muted-foreground">
                      Contact support via GitHub Issues
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}

function ShortcutRow({ keys, description }: { keys: string[]; description: string }) {
  return (
    <div className="flex items-center justify-between py-1">
      <span className="text-sm text-muted-foreground">{description}</span>
      <div className="flex gap-1">
        {keys.map((key, i) => (
          <kbd
            key={i}
            className="px-2 py-1 bg-muted rounded text-xs font-mono"
          >
            {key}
          </kbd>
        ))}
      </div>
    </div>
  );
}

// Floating help button for pages
export function FloatingHelpButton({ contextPage }: { contextPage?: string }) {
  return (
    <div className="fixed bottom-4 right-4 z-40">
      <HelpCenter
        contextPage={contextPage}
        trigger={
          <Button size="lg" className="rounded-full shadow-lg h-14 w-14">
            <HelpCircle className="h-6 w-6" />
          </Button>
        }
      />
    </div>
  );
}
