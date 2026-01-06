/**
 * Forum Topic Page
 * 
 * View a single topic with all replies.
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import {
  ArrowLeft,
  Eye,
  Heart,
  MessageSquare,
  Pin,
  Lock,
  Share2,
  Flag,
  MoreHorizontal,
} from 'lucide-react';
import { toast } from 'sonner';

interface Reply {
  id: string;
  topic_id: string;
  content: string;
  author: { id: string; name: string; avatar: string };
  created_at: string;
  likes: number;
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
  replies: Reply[];
}

const API_BASE = '/api/v2/forums';

export function ForumTopic() {
  const { topicId } = useParams<{ topicId: string }>();
  const queryClient = useQueryClient();
  const [replyContent, setReplyContent] = useState('');

  // Fetch topic
  const { data: topic, isLoading } = useQuery<Topic>({
    queryKey: ['forum-topic', topicId],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/topics/${topicId}`);
      if (!res.ok) throw new Error('Failed to fetch topic');
      return res.json();
    },
    enabled: !!topicId,
  });

  // Like topic mutation
  const likeMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_BASE}/topics/${topicId}/like`, {
        method: 'POST',
      });
      if (!res.ok) throw new Error('Failed to like topic');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['forum-topic', topicId] });
      toast.success('Liked!');
    },
  });

  // Reply mutation
  const replyMutation = useMutation({
    mutationFn: async (content: string) => {
      const res = await fetch(`${API_BASE}/topics/${topicId}/replies`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content }),
      });
      if (!res.ok) throw new Error('Failed to post reply');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['forum-topic', topicId] });
      setReplyContent('');
      toast.success('Reply posted!');
    },
    onError: () => {
      toast.error('Failed to post reply');
    },
  });

  // Like reply mutation
  const likeReplyMutation = useMutation({
    mutationFn: async (replyId: string) => {
      const res = await fetch(`${API_BASE}/topics/${topicId}/replies/${replyId}/like`, {
        method: 'POST',
      });
      if (!res.ok) throw new Error('Failed to like reply');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['forum-topic', topicId] });
    },
  });

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleSubmitReply = () => {
    if (!replyContent.trim()) {
      toast.error('Please enter a reply');
      return;
    }
    replyMutation.mutate(replyContent);
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64" />
        <Skeleton className="h-32" />
      </div>
    );
  }

  if (!topic) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-bold mb-2">Topic not found</h2>
        <Button asChild variant="outline">
          <Link to="/knowledge/forums">Back to Forums</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild>
          <Link to="/knowledge/forums">
            <ArrowLeft className="h-5 w-5" />
          </Link>
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            {topic.is_pinned && <Pin className="h-4 w-4 text-primary" />}
            {topic.is_closed && <Lock className="h-4 w-4 text-muted-foreground" />}
            <h1 className="text-2xl font-bold">{topic.title}</h1>
          </div>
          <div className="flex items-center gap-2 mt-1 text-sm text-muted-foreground">
            <span>Posted by {topic.author.name}</span>
            <span>•</span>
            <span>{formatDate(topic.created_at)}</span>
          </div>
        </div>
      </div>

      {/* Main Topic */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4">
            <div className="text-4xl">{topic.author.avatar}</div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <span className="font-semibold">{topic.author.name}</span>
                <Badge variant="secondary">Author</Badge>
              </div>
              <div className="prose prose-sm max-w-none dark:prose-invert">
                {topic.content.split('\n').map((paragraph, i) => (
                  <p key={i}>{paragraph}</p>
                ))}
              </div>
              {topic.tags.length > 0 && (
                <div className="flex gap-1 mt-4 flex-wrap">
                  {topic.tags.map((tag) => (
                    <Badge key={tag} variant="outline">
                      {tag}
                    </Badge>
                  ))}
                </div>
              )}
              <Separator className="my-4" />
              <div className="flex items-center gap-4">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => likeMutation.mutate()}
                  disabled={likeMutation.isPending}
                >
                  <Heart className="h-4 w-4 mr-1" />
                  {topic.likes}
                </Button>
                <div className="flex items-center gap-1 text-sm text-muted-foreground">
                  <Eye className="h-4 w-4" />
                  {topic.views} views
                </div>
                <div className="flex items-center gap-1 text-sm text-muted-foreground">
                  <MessageSquare className="h-4 w-4" />
                  {topic.reply_count} replies
                </div>
                <div className="ml-auto flex gap-2">
                  <Button variant="ghost" size="sm">
                    <Share2 className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="sm">
                    <Flag className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Replies */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold">
          {topic.replies.length} {topic.replies.length === 1 ? 'Reply' : 'Replies'}
        </h2>
        
        {topic.replies.map((reply, index) => (
          <Card key={reply.id}>
            <CardContent className="pt-6">
              <div className="flex gap-4">
                <div className="text-3xl">{reply.author.avatar}</div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-semibold">{reply.author.name}</span>
                    <span className="text-xs text-muted-foreground">
                      {formatDate(reply.created_at)}
                    </span>
                  </div>
                  <div className="prose prose-sm max-w-none dark:prose-invert">
                    {reply.content.split('\n').map((paragraph, i) => (
                      <p key={i}>{paragraph}</p>
                    ))}
                  </div>
                  <div className="flex items-center gap-4 mt-4">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => likeReplyMutation.mutate(reply.id)}
                    >
                      <Heart className="h-4 w-4 mr-1" />
                      {reply.likes}
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Reply Form */}
      {!topic.is_closed ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Post a Reply</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea
              placeholder="Share your thoughts..."
              value={replyContent}
              onChange={(e) => setReplyContent(e.target.value)}
              rows={4}
            />
            <div className="flex justify-end">
              <Button
                onClick={handleSubmitReply}
                disabled={replyMutation.isPending || !replyContent.trim()}
              >
                {replyMutation.isPending ? 'Posting...' : 'Post Reply'}
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="py-6 text-center text-muted-foreground">
            <Lock className="h-8 w-8 mx-auto mb-2" />
            <p>This topic is closed for new replies.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default ForumTopic;
