/**
 * Feedback Page
 * User feedback and feature requests
 */
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { toast } from 'sonner'

export function Feedback() {
  const [feedbackType, setFeedbackType] = useState('feature')
  const [subject, setSubject] = useState('')
  const [description, setDescription] = useState('')
  const [email, setEmail] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!subject.trim() || !description.trim()) {
      toast.error('Please fill in all required fields')
      return
    }

    setSubmitting(true)
    
    // Simulate submission (in production, this would send to a backend)
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // Store feedback locally for now
    const feedback = {
      id: Date.now(),
      type: feedbackType,
      subject,
      description,
      email,
      timestamp: new Date().toISOString(),
    }
    
    const existingFeedback = JSON.parse(localStorage.getItem('bijmantra_feedback') || '[]')
    existingFeedback.push(feedback)
    localStorage.setItem('bijmantra_feedback', JSON.stringify(existingFeedback))
    
    toast.success('Thank you for your feedback!')
    setSubject('')
    setDescription('')
    setEmail('')
    setSubmitting(false)
  }

  return (
    <div className="space-y-6 animate-fade-in max-w-3xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Feedback</h1>
          <p className="text-muted-foreground mt-1">Help us improve Bijmantra</p>
        </div>
        <Link to="/help">
          <Button variant="outline">📚 Help Center</Button>
        </Link>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => setFeedbackType('bug')}>
          <CardContent className="pt-6 text-center">
            <span className="text-4xl">🐛</span>
            <h3 className="font-semibold mt-2">Report a Bug</h3>
            <p className="text-xs text-muted-foreground">Something not working?</p>
          </CardContent>
        </Card>
        <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => setFeedbackType('feature')}>
          <CardContent className="pt-6 text-center">
            <span className="text-4xl">💡</span>
            <h3 className="font-semibold mt-2">Request Feature</h3>
            <p className="text-xs text-muted-foreground">Have an idea?</p>
          </CardContent>
        </Card>
        <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => setFeedbackType('general')}>
          <CardContent className="pt-6 text-center">
            <span className="text-4xl">💬</span>
            <h3 className="font-semibold mt-2">General Feedback</h3>
            <p className="text-xs text-muted-foreground">Share your thoughts</p>
          </CardContent>
        </Card>
      </div>

      {/* Feedback Form */}
      <Card>
        <CardHeader>
          <CardTitle>Submit Feedback</CardTitle>
          <CardDescription>Your feedback helps us make Bijmantra better</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="type">Feedback Type</Label>
              <Select value={feedbackType} onValueChange={setFeedbackType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="bug">🐛 Bug Report</SelectItem>
                  <SelectItem value="feature">💡 Feature Request</SelectItem>
                  <SelectItem value="improvement">✨ Improvement</SelectItem>
                  <SelectItem value="question">❓ Question</SelectItem>
                  <SelectItem value="general">💬 General Feedback</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="subject">Subject *</Label>
              <Input
                id="subject"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="Brief summary of your feedback"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description *</Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder={
                  feedbackType === 'bug' 
                    ? "Please describe the bug, steps to reproduce, and expected behavior..."
                    : feedbackType === 'feature'
                    ? "Describe the feature you'd like to see and how it would help your workflow..."
                    : "Share your thoughts, suggestions, or questions..."
                }
                rows={6}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email (optional)</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com (for follow-up)"
              />
              <p className="text-xs text-muted-foreground">
                We'll only use this to follow up on your feedback if needed
              </p>
            </div>

            <Button type="submit" className="w-full" disabled={submitting}>
              {submitting ? '⏳ Submitting...' : '📤 Submit Feedback'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Tips */}
      <Card className="border-blue-200 bg-blue-50">
        <CardHeader>
          <CardTitle className="text-base text-blue-800">Tips for Great Feedback</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-blue-700">
          <p>• <strong>Be specific:</strong> Include details about what you were doing when the issue occurred</p>
          <p>• <strong>Include steps:</strong> For bugs, list the steps to reproduce the problem</p>
          <p>• <strong>Describe the impact:</strong> How does this affect your workflow?</p>
          <p>• <strong>Suggest solutions:</strong> If you have ideas for how to fix or improve something, share them!</p>
        </CardContent>
      </Card>

      {/* Community Links */}
      <Card>
        <CardHeader>
          <CardTitle>Community Resources</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <a 
              href="https://github.com/denishdholaria/bijmantra/issues" 
              target="_blank" 
              rel="noopener noreferrer"
              className="p-4 bg-muted rounded-lg hover:bg-muted/80 transition-colors"
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">🐙</span>
                <div>
                  <p className="font-medium">GitHub Issues</p>
                  <p className="text-xs text-muted-foreground">Report bugs and track progress</p>
                </div>
              </div>
            </a>
            <a 
              href="https://github.com/denishdholaria/bijmantra/discussions" 
              target="_blank" 
              rel="noopener noreferrer"
              className="p-4 bg-muted rounded-lg hover:bg-muted/80 transition-colors"
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">💬</span>
                <div>
                  <p className="font-medium">Discussions</p>
                  <p className="text-xs text-muted-foreground">Join the community conversation</p>
                </div>
              </div>
            </a>
            <a 
              href="https://brapi.org" 
              target="_blank" 
              rel="noopener noreferrer"
              className="p-4 bg-muted rounded-lg hover:bg-muted/80 transition-colors"
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">🌐</span>
                <div>
                  <p className="font-medium">BrAPI Community</p>
                  <p className="text-xs text-muted-foreground">Breeding API standards</p>
                </div>
              </div>
            </a>
            <Link 
              to="/ai-assistant"
              className="p-4 bg-muted rounded-lg hover:bg-muted/80 transition-colors"
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">🤖</span>
                <div>
                  <p className="font-medium">AI Assistant</p>
                  <p className="text-xs text-muted-foreground">Get help with questions</p>
                </div>
              </div>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
