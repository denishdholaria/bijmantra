/**
 * Contact & Support Page
 * Contact information and support resources
 */
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

export function Contact() {
  return (
    <div className="space-y-6 animate-fade-in max-w-4xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Contact & Support</h1>
          <p className="text-muted-foreground mt-1">Get help and connect with us</p>
        </div>
        <Link to="/feedback">
          <Button>💬 Send Feedback</Button>
        </Link>
      </div>

      {/* Quick Support Options */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="hover:shadow-md transition-shadow">
          <CardContent className="pt-6 text-center">
            <span className="text-4xl">🤖</span>
            <h3 className="font-semibold mt-3">AI Assistant</h3>
            <p className="text-sm text-muted-foreground mt-1">
              Get instant answers to your questions
            </p>
            <Link to="/ai-assistant">
              <Button className="mt-4" size="sm">Ask AI</Button>
            </Link>
          </CardContent>
        </Card>
        <Card className="hover:shadow-md transition-shadow">
          <CardContent className="pt-6 text-center">
            <span className="text-4xl">📚</span>
            <h3 className="font-semibold mt-3">Documentation</h3>
            <p className="text-sm text-muted-foreground mt-1">
              Browse guides and tutorials
            </p>
            <Link to="/help">
              <Button className="mt-4" size="sm" variant="outline">Help Center</Button>
            </Link>
          </CardContent>
        </Card>
        <Card className="hover:shadow-md transition-shadow">
          <CardContent className="pt-6 text-center">
            <span className="text-4xl">❓</span>
            <h3 className="font-semibold mt-3">FAQ</h3>
            <p className="text-sm text-muted-foreground mt-1">
              Find answers to common questions
            </p>
            <Link to="/faq">
              <Button className="mt-4" size="sm" variant="outline">View FAQ</Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* Developer Info */}
      <Card>
        <CardHeader>
          <CardTitle>About the Developer</CardTitle>
          <CardDescription>Bijmantra is created by Denish Dholaria</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center text-white text-2xl">
              DD
            </div>
            <div>
              <h3 className="font-semibold text-lg">Denish Dholaria</h3>
              <p className="text-muted-foreground">Creator of Bijmantra</p>
              <div className="flex gap-2 mt-2">
                <Badge variant="outline">Plant Breeding</Badge>
                <Badge variant="outline">AI/ML</Badge>
                <Badge variant="outline">Full Stack</Badge>
              </div>
            </div>
          </div>
          <p className="text-sm text-muted-foreground">
            Bijmantra is developed under the R.E.E.V.A.i vision — Rural Empowerment through 
            Emerging Value-driven Agro-Intelligence. Dedicated to building intelligent tools 
            for agriculture and plant breeding. The name is inspired by my daughter REEVA — 
            representing hope, innovation, and the future.
          </p>
        </CardContent>
      </Card>

      {/* Contact Methods */}
      <Card>
        <CardHeader>
          <CardTitle>Get in Touch</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <a 
              href="https://github.com/denishdholaria/bijmantra" 
              target="_blank" 
              rel="noopener noreferrer"
              className="p-4 bg-muted rounded-lg hover:bg-muted/80 transition-colors flex items-center gap-3"
            >
              <span className="text-2xl">🐙</span>
              <div>
                <p className="font-medium">GitHub</p>
                <p className="text-xs text-muted-foreground">View source code and contribute</p>
              </div>
            </a>
            <a 
              href="https://github.com/denishdholaria/bijmantra/issues" 
              target="_blank" 
              rel="noopener noreferrer"
              className="p-4 bg-muted rounded-lg hover:bg-muted/80 transition-colors flex items-center gap-3"
            >
              <span className="text-2xl">🐛</span>
              <div>
                <p className="font-medium">Report Issues</p>
                <p className="text-xs text-muted-foreground">Submit bug reports</p>
              </div>
            </a>
            <a 
              href="https://github.com/denishdholaria/bijmantra/discussions" 
              target="_blank" 
              rel="noopener noreferrer"
              className="p-4 bg-muted rounded-lg hover:bg-muted/80 transition-colors flex items-center gap-3"
            >
              <span className="text-2xl">💬</span>
              <div>
                <p className="font-medium">Discussions</p>
                <p className="text-xs text-muted-foreground">Join the community</p>
              </div>
            </a>
            <a 
              href="https://brapi.org" 
              target="_blank" 
              rel="noopener noreferrer"
              className="p-4 bg-muted rounded-lg hover:bg-muted/80 transition-colors flex items-center gap-3"
            >
              <span className="text-2xl">🌐</span>
              <div>
                <p className="font-medium">BrAPI Community</p>
                <p className="text-xs text-muted-foreground">Breeding API standards</p>
              </div>
            </a>
          </div>
        </CardContent>
      </Card>

      {/* Support the Project */}
      <Card className="border-green-200 bg-green-50">
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <span className="text-4xl">⭐</span>
              <div>
                <h3 className="font-semibold text-green-800">Support the Project</h3>
                <p className="text-sm text-green-700">
                  If you find Bijmantra useful, please star us on GitHub!
                </p>
              </div>
            </div>
            <a 
              href="https://github.com/denishdholaria/bijmantra" 
              target="_blank" 
              rel="noopener noreferrer"
            >
              <Button>⭐ Star on GitHub</Button>
            </a>
          </div>
        </CardContent>
      </Card>

      {/* Response Time */}
      <Card>
        <CardContent className="pt-4">
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            <span>⏱️</span>
            <p>
              We typically respond to GitHub issues within 24-48 hours. 
              For urgent matters, please use the AI Assistant for immediate help.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
