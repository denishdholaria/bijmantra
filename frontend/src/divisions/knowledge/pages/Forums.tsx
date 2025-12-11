/**
 * Community Forums Page
 * 
 * Discussion forums for breeders to share knowledge.
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  MessageSquare,
  Eye,
  Heart,
  Pin,
  Lock,
  Search,
  Plus,
  TrendingUp,
  Clock,
} from 'lucide-react';

interface Category {
  id: string;
  name: string;
  description: string;
  icon: string;
  topic_count: number;
}

interface Topic {
  id: string;
  category_id: string;
  title: string;
  content: string;
  author: { id: string; name: string; avatar: string };
  created_at: string;
  updated_at: string;
  views: number;
  likes: number;
  reply_count: number;
  is_pinned: boolean;
  is_closed: boolean;
  tags: string[];
}

const API_BASE = '/api/v2/forums';

export function Forums() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [search, setSearch] = useState('');
  const selectedCategory = searchParams.get('category') || '';

  // Fetch categories
  const { data: categoriesData, isLoading: loadingCategories } = useQuery({
    queryKey: ['forum-categories'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/categories`);
      if (!res.ok) throw new Error('Failed to fetch categories');
      return res.json();
    },
  });

  // Fetch topics
  const { data: topicsData, isLoading: loadingTopics } = useQuery({
    queryKey: ['forum-topics', selectedCategory, search],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (selectedCategory) params.set('category_id', selectedCategory);
      if (search) params.set('search', search);
      const res = await fetch(`${API_BASE}/topics?${params}`);
      if (!res.ok) throw new Error('Failed to fetch topics');
      return res.json();
    },
  });

  // Fetch stats
  const { data: stats } = useQuery({
    queryKey: ['forum-stats'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/stats`);
      if (!res.ok) throw new Error('Failed to fetch stats');
      return res.json();
    },
  });

  const categories: Category[] = categoriesData?.categories || [];
  const topics: Topic[] = topicsData?.data || [];

  const handleCategoryClick = (categoryId: string) => {
    if (categoryId === selectedCategory) {
      searchParams.delete('category');
    } else {
      searchParams.set('category', categoryId);
    }
    setSearchParams(searchParams);
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2">
            <MessageSquare className="h-8 w-8 text-primary" />
            Community Forums
          </h1>
          <p className="text-muted-foreground mt-1">
            Connect with fellow breeders, share knowledge, ask questions
          </p>
        </div>
        <Button asChild>
          <Link to="/knowledge/forums/new">
            <Plus className="h-4 w-4 mr-2" />
            New Topic
          </Link>
        </Button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card>
            <CardContent className="pt-4 text-center">
              <div className="text-2xl font-bold">{stats.total_categories}</div>
              <p className="text-xs text-muted-foreground">Categories</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 text-center">
              <div className="text-2xl font-bold">{stats.total_topics}</div>
              <p className="text-xs text-muted-foreground">Topics</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 text-center">
              <div className="text-2xl font-bold">{stats.total_replies}</div>
              <p className="text-xs text-muted-foreground">Replies</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 text-center">
              <div className="text-2xl font-bold">{stats.total_views}</div>
              <p className="text-xs text-muted-foreground">Views</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 text-center">
              <div className="text-2xl font-bold">{stats.active_users}</div>
              <p className="text-xs text-muted-foreground">Active Users</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Categories */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg">Categories</CardTitle>
        </CardHeader>
        <CardContent>
          {loadingCategories ? (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <Skeleton key={i} className="h-20" />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              {categories.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => handleCategoryClick(cat.id)}
                  className={`p-3 rounded-lg border text-left transition-all hover:shadow-md ${
                    selectedCategory === cat.id
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/50'
                  }`}
                >
                  <div className="text-2xl mb-1">{cat.icon}</div>
                  <div className="font-medium text-sm truncate">{cat.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {cat.topic_count} topics
                  </div>
                </button>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Search and Topics */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <CardTitle className="text-lg">
              {selectedCategory
                ? categories.find((c) => c.id === selectedCategory)?.name || 'Topics'
                : 'All Topics'}
            </CardTitle>
            <div className="relative w-full sm:w-64">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search topics..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loadingTopics ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-24" />
              ))}
            </div>
          ) : topics.length === 0 ? (
            <div className="text-center py-12">
              <MessageSquare className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">No topics yet</h3>
              <p className="text-muted-foreground mb-4">
                Be the first to start a discussion!
              </p>
              <Button asChild>
                <Link to="/knowledge/forums/new">Create Topic</Link>
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              {topics.map((topic) => (
                <Link
                  key={topic.id}
                  to={`/knowledge/forums/${topic.id}`}
                  className="block p-4 rounded-lg border hover:border-primary/50 hover:shadow-sm transition-all"
                >
                  <div className="flex items-start gap-4">
                    <div className="text-3xl">{topic.author.avatar}</div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        {topic.is_pinned && (
                          <Pin className="h-4 w-4 text-primary" />
                        )}
                        {topic.is_closed && (
                          <Lock className="h-4 w-4 text-muted-foreground" />
                        )}
                        <h3 className="font-semibold hover:text-primary truncate">
                          {topic.title}
                        </h3>
                      </div>
                      <p className="text-sm text-muted-foreground line-clamp-2 mt-1">
                        {topic.content}
                      </p>
                      <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                        <span>{topic.author.name}</span>
                        <span>•</span>
                        <span>{formatDate(topic.created_at)}</span>
                        <div className="flex items-center gap-1">
                          <Eye className="h-3 w-3" />
                          {topic.views}
                        </div>
                        <div className="flex items-center gap-1">
                          <Heart className="h-3 w-3" />
                          {topic.likes}
                        </div>
                        <div className="flex items-center gap-1">
                          <MessageSquare className="h-3 w-3" />
                          {topic.reply_count}
                        </div>
                      </div>
                      {topic.tags.length > 0 && (
                        <div className="flex gap-1 mt-2 flex-wrap">
                          {topic.tags.map((tag) => (
                            <Badge key={tag} variant="secondary" className="text-xs">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default Forums;
