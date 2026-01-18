/**
 * Privacy Policy Page
 * Privacy information and data handling
 */
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export function Privacy() {
  return (
    <div className="space-y-6 animate-fade-in max-w-4xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Privacy Policy</h1>
          <p className="text-muted-foreground mt-1">Last updated: December 1, 2025</p>
        </div>
        <Link to="/about">
          <Button variant="outline">ℹ️ About</Button>
        </Link>
      </div>

      {/* Summary */}
      <Card className="border-green-200 bg-green-50">
        <CardContent className="pt-6">
          <div className="flex items-start gap-4">
            <span className="text-3xl">🔒</span>
            <div>
              <h3 className="font-semibold text-green-800">Privacy First</h3>
              <p className="text-sm text-green-700 mt-1">
                Bijmantra is designed with privacy in mind. Your breeding data stays on your device 
                or your own server. We don't collect, store, or sell your data.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Data Collection */}
      <Card>
        <CardHeader>
          <CardTitle>Data Collection</CardTitle>
          <CardDescription>What data we collect and why</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <h4 className="font-medium">Data We DON'T Collect:</h4>
            <ul className="space-y-2 text-sm">
              <li className="flex items-start gap-2">
                <span className="text-green-500">✓</span>
                <span>Your breeding data (germplasm, trials, observations)</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-500">✓</span>
                <span>Personal information beyond what you provide</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-500">✓</span>
                <span>Usage analytics or tracking data</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-500">✓</span>
                <span>Location data (unless you explicitly add it to locations)</span>
              </li>
            </ul>
          </div>

          <div className="space-y-3">
            <h4 className="font-medium">Data Storage:</h4>
            <ul className="space-y-2 text-sm">
              <li className="flex items-start gap-2">
                <span>📱</span>
                <span><strong>Demo Mode:</strong> Data is stored locally in your browser (localStorage/IndexedDB)</span>
              </li>
              <li className="flex items-start gap-2">
                <span>🖥️</span>
                <span><strong>With Backend:</strong> Data is stored on your own server that you control</span>
              </li>
              <li className="flex items-start gap-2">
                <span>☁️</span>
                <span><strong>AI Features:</strong> When using Cloud AI, queries are sent to your chosen provider</span>
              </li>
              <li className="flex items-start gap-2">
                <span>🌐</span>
                <span><strong>Chrome AI:</strong> All processing happens locally - no data leaves your device</span>
              </li>
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* AI Privacy */}
      <Card>
        <CardHeader>
          <CardTitle>AI Features & Privacy</CardTitle>
          <CardDescription>How AI features handle your data</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <h4 className="font-medium text-green-800 flex items-center gap-2">
                <span>🌐</span> Chrome AI (Recommended)
              </h4>
              <ul className="mt-2 text-sm text-green-700 space-y-1">
                <li>• 100% local processing</li>
                <li>• No data sent to servers</li>
                <li>• No API keys needed</li>
                <li>• Works offline</li>
              </ul>
            </div>
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <h4 className="font-medium text-blue-800 flex items-center gap-2">
                <span>☁️</span> Cloud AI
              </h4>
              <ul className="mt-2 text-sm text-blue-700 space-y-1">
                <li>• Queries sent to AI provider</li>
                <li>• Subject to provider's privacy policy</li>
                <li>• Your API key, your account</li>
                <li>• More powerful capabilities</li>
              </ul>
            </div>
          </div>
          <p className="text-sm text-muted-foreground">
            When using Cloud AI providers (OpenAI, Anthropic, Google, Mistral), your queries and 
            any included data context are sent to their servers. Review each provider's privacy 
            policy for details on how they handle data.
          </p>
        </CardContent>
      </Card>

      {/* Local Storage */}
      <Card>
        <CardHeader>
          <CardTitle>Browser Storage</CardTitle>
          <CardDescription>Data stored in your browser</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm">Bijmantra stores the following in your browser:</p>
          <ul className="space-y-2 text-sm">
            <li className="flex items-start gap-2">
              <span>🔑</span>
              <span><strong>Authentication token:</strong> To keep you logged in</span>
            </li>
            <li className="flex items-start gap-2">
              <span>⚙️</span>
              <span><strong>AI settings:</strong> Your AI provider configuration (API key stored locally)</span>
            </li>
            <li className="flex items-start gap-2">
              <span>🎨</span>
              <span><strong>UI preferences:</strong> Sidebar state, theme preferences</span>
            </li>
            <li className="flex items-start gap-2">
              <span>📝</span>
              <span><strong>Feedback:</strong> Any feedback you submit (stored locally until backend available)</span>
            </li>
          </ul>
          <div className="p-3 bg-muted rounded-lg mt-4">
            <p className="text-sm">
              <strong>Clear your data:</strong> You can clear all locally stored data by clearing 
              your browser's site data for this domain, or by logging out.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Third Parties */}
      <Card>
        <CardHeader>
          <CardTitle>Third-Party Services</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm">Bijmantra may interact with these third-party services:</p>
          <ul className="space-y-2 text-sm">
            <li className="flex items-start gap-2">
              <span>🤖</span>
              <span><strong>AI Providers:</strong> OpenAI, Anthropic, Google, Mistral (only if you configure them)</span>
            </li>
            <li className="flex items-start gap-2">
              <span>🗺️</span>
              <span><strong>Map Services:</strong> OpenStreetMap for location maps (no personal data sent)</span>
            </li>
            <li className="flex items-start gap-2">
              <span>🐙</span>
              <span><strong>GitHub:</strong> For source code and issue tracking (external links only)</span>
            </li>
          </ul>
        </CardContent>
      </Card>

      {/* Your Rights */}
      <Card>
        <CardHeader>
          <CardTitle>Your Rights</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm">You have full control over your data:</p>
          <ul className="space-y-2 text-sm">
            <li className="flex items-start gap-2">
              <span>📤</span>
              <span><strong>Export:</strong> Export all your data at any time via Import/Export</span>
            </li>
            <li className="flex items-start gap-2">
              <span>🗑️</span>
              <span><strong>Delete:</strong> Delete your data from the system</span>
            </li>
            <li className="flex items-start gap-2">
              <span>🔄</span>
              <span><strong>Portability:</strong> Data is in standard BrAPI format for easy migration</span>
            </li>
            <li className="flex items-start gap-2">
              <span>🔒</span>
              <span><strong>Security:</strong> Self-hosted deployments give you full control</span>
            </li>
          </ul>
        </CardContent>
      </Card>

      {/* Contact */}
      <Card className="border-blue-200 bg-blue-50">
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <span className="text-3xl">❓</span>
              <div>
                <h3 className="font-semibold text-blue-800">Questions?</h3>
                <p className="text-sm text-blue-700">
                  If you have questions about privacy, please reach out
                </p>
              </div>
            </div>
            <Link to="/contact">
              <Button variant="outline">Contact Us</Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
