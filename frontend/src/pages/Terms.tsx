/**
 * Terms of Service Page
 * Bijmantra Source Available License (BSAL) v2.0
 */
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

export function Terms() {
  return (
    <div className="space-y-6 animate-fade-in max-w-4xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">License & Terms</h1>
          <p className="text-muted-foreground mt-1">Bijmantra Source Available License (BSAL) v2.0</p>
        </div>
        <Link to="/privacy">
          <Button variant="outline">🔒 Privacy Policy</Button>
        </Link>
      </div>

      {/* Summary Card */}
      <Card className="border-2 border-green-200 bg-gradient-to-br from-green-50 to-emerald-50">
        <CardContent className="pt-6">
          <div className="text-center mb-4">
            <span className="text-4xl">📜</span>
            <h2 className="text-xl font-bold text-green-800 mt-2">Free to Use, Pay to Sell</h2>
            <p className="text-green-700 mt-1">
              Bijmantra is free for everyone to use. Commercial license required only if you sell it.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Quick Summary */}
      <div className="grid md:grid-cols-3 gap-4">
        <Card className="border-green-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <span>✅</span> Free Use
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm space-y-1">
            <p>• Personal & educational use</p>
            <p>• Research & non-profit</p>
            <p>• Internal organizational use</p>
            <p>• Self-hosted deployments</p>
            <p>• Farmer cooperatives</p>
            <p>• Consulting services</p>
          </CardContent>
        </Card>

        <Card className="border-amber-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <span>💰</span> Commercial License
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm space-y-1">
            <p>• Selling the software</p>
            <p>• Paid SaaS/hosted service</p>
            <p>• White-labeling for resale</p>
            <p>• Bundling with products</p>
            <p className="text-amber-700 font-medium pt-2">Contact for pricing</p>
          </CardContent>
        </Card>

        <Card className="border-red-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <span>🚫</span> Prohibited
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm space-y-1">
            <p>• Terminator technology</p>
            <p>• GURT seed technologies</p>
            <p>• Seed termination tech</p>
            <p>• Removing attribution</p>
            <p className="text-red-700 font-medium pt-2">Zero tolerance</p>
          </CardContent>
        </Card>
      </div>

      {/* Free Use Details */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span>✅</span> Section 1: Free Use Grant
          </CardTitle>
          <CardDescription>No payment or permission required for these uses</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            {[
              { icon: '👤', title: 'Personal Use', desc: 'Learning, research, personal projects' },
              { icon: '🎓', title: 'Educational Use', desc: 'Students, teachers, universities, coursework' },
              { icon: '🔬', title: 'Research Use', desc: 'Academic research and publications' },
              { icon: '💚', title: 'Non-Profit Use', desc: 'NGOs, charities, foundations' },
              { icon: '🏛️', title: 'Government Use', desc: 'Public agencies, agricultural departments' },
              { icon: '🏢', title: 'Internal Use', desc: 'Any organization for their own operations' },
              { icon: '🌾', title: 'Farmer Cooperatives', desc: 'Even with nominal membership fees' },
              { icon: '👨‍💼', title: 'Consulting', desc: 'Charge for expertise, not the software' },
            ].map((item, i) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-green-50 rounded-lg">
                <span className="text-xl">{item.icon}</span>
                <div>
                  <h4 className="font-semibold text-green-800">{item.title}</h4>
                  <p className="text-sm text-green-700">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Commercial License */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span>💰</span> Section 2: Commercial License
          </CardTitle>
          <CardDescription>Required if you sell the software or offer it as a paid service</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="bg-amber-50 rounded-lg p-4 border border-amber-200">
            <h4 className="font-semibold text-amber-800 mb-2">When is a Commercial License Required?</h4>
            <ul className="space-y-2 text-sm text-amber-700">
              <li>• <strong>Selling the software</strong> — Rebranding and selling Bijmantra</li>
              <li>• <strong>SaaS/Hosted Service</strong> — Offering paid access to Bijmantra</li>
              <li>• <strong>White-labeling</strong> — Reselling under a different name</li>
              <li>• <strong>Bundling</strong> — Including in commercial products for sale</li>
            </ul>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <div className="p-4 bg-slate-50 rounded-lg">
              <h4 className="font-semibold mb-2">Commercial Terms</h4>
              <ul className="text-sm space-y-1">
                <li>• 90-day free evaluation period</li>
                <li>• 10% of SaaS subscription revenue</li>
                <li>• 15% of software sales revenue</li>
                <li>• $1,000 USD minimum annual fee</li>
              </ul>
            </div>
            <div className="p-4 bg-slate-50 rounded-lg">
              <h4 className="font-semibold mb-2">Special Programs</h4>
              <ul className="text-sm space-y-1">
                <li>• <strong>Startups</strong>: 2-year grace period (&lt;$100K revenue)</li>
                <li>• <strong>Developing countries</strong>: 50% discount</li>
                <li>• <strong>Public breeding</strong>: Exempt (free)</li>
              </ul>
            </div>
          </div>

          <div className="text-center pt-2">
            <a href="mailto:denishdholaria@gmail.com?subject=Bijmantra Commercial License Inquiry">
              <Button>
                <span className="mr-2">📧</span> Contact for Commercial License
              </Button>
            </a>
          </div>
        </CardContent>
      </Card>

      {/* Attribution */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span>📝</span> Section 3: Attribution Requirements
          </CardTitle>
          <CardDescription>Required for all use (free and commercial)</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm">
            All deployments must include visible attribution to the creator:
          </p>
          <div className="bg-slate-100 rounded-lg p-4 font-mono text-sm">
            "Powered by Bijmantra - Created by Denish Dholaria"
          </div>
          <p className="text-sm text-muted-foreground">
            Attribution must appear in the application UI, documentation, and source code.
            Academic use must include proper citation.
          </p>
        </CardContent>
      </Card>

      {/* Ethical Restrictions */}
      <Card className="border-2 border-red-200 bg-gradient-to-br from-red-50 to-orange-50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-red-800">
            <span>🚫</span> Section 4: Ethical Use Restrictions
          </CardTitle>
          <CardDescription className="text-red-700">Absolute prohibition — no exceptions</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-red-800">
            The use of Bijmantra is <strong>STRICTLY PROHIBITED</strong> for:
          </p>
          <div className="grid md:grid-cols-2 gap-3">
            {[
              { title: 'Terminator Technology', desc: 'Seeds engineered to be sterile' },
              { title: 'GURTs', desc: 'Genetic Use Restriction Technologies' },
              { title: 'Traitor Technology', desc: 'Chemical-dependent trait activation' },
              { title: 'Seed Termination', desc: 'Any tech preventing seed saving' },
            ].map((item, i) => (
              <div key={i} className="p-3 bg-red-100 rounded-lg border border-red-200">
                <h4 className="font-semibold text-red-800">{item.title}</h4>
                <p className="text-sm text-red-700">{item.desc}</p>
              </div>
            ))}
          </div>
          <div className="bg-white/70 rounded-lg p-4 text-center">
            <p className="text-red-800 italic">
              "Seeds are the foundation of life. The ability of seeds to reproduce is a gift of nature 
              that belongs to all humanity, not a feature to be engineered away for corporate profit."
            </p>
            <p className="text-red-600 font-semibold mt-2">— Denish Dholaria</p>
          </div>
        </CardContent>
      </Card>

      {/* No Warranty */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span>⚠️</span> Section 5: Disclaimer & Liability
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p className="uppercase font-medium text-muted-foreground">
            THE SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND.
          </p>
          <p>
            The creator is not liable for any damages arising from use of the software.
            You are responsible for your own data backups and compliance with applicable laws.
          </p>
        </CardContent>
      </Card>

      {/* Termination */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span>🔚</span> Section 6: Termination
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <ul className="space-y-2">
            <li>• License terminates automatically if you violate any terms</li>
            <li>• Ethical violations (Section 4) result in <strong>immediate termination</strong> with no cure period</li>
            <li>• Other violations have a 30-day cure period after written notice</li>
            <li>• Upon termination, you must cease all use and distribution</li>
          </ul>
        </CardContent>
      </Card>

      {/* Contact */}
      <Card className="border-green-200 bg-green-50">
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <span className="text-3xl">❓</span>
              <div>
                <h3 className="font-semibold text-green-800">Questions about licensing?</h3>
                <p className="text-sm text-green-700">
                  Contact us for clarification or commercial inquiries
                </p>
              </div>
            </div>
            <a href="mailto:denishdholaria@gmail.com">
              <Button>Contact Us</Button>
            </a>
          </div>
        </CardContent>
      </Card>

      {/* Footer */}
      <div className="text-center py-4 space-y-2">
        <p className="text-xs text-muted-foreground">
          Bijmantra Source Available License (BSAL) v2.0 • December 2025
        </p>
        <p className="text-xs text-muted-foreground">
          © 2025 Denish Dholaria • Supported by Solar Agrotech Private Limited
        </p>
        <div className="flex items-center justify-center gap-2 pt-2">
          <Badge variant="outline">Source Available</Badge>
          <Badge variant="outline">Free for Non-Commercial</Badge>
          <Badge variant="outline">Ethical Use Required</Badge>
        </div>
      </div>
    </div>
  )
}
