/**
 * Terms of Service Page
 * Terms and conditions for using Bijmantra
 */
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export function Terms() {
  return (
    <div className="space-y-6 animate-fade-in max-w-4xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Terms of Service</h1>
          <p className="text-muted-foreground mt-1">Last updated: December 1, 2025</p>
        </div>
        <Link to="/privacy">
          <Button variant="outline">🔒 Privacy Policy</Button>
        </Link>
      </div>

      {/* Summary */}
      <Card className="border-blue-200 bg-blue-50">
        <CardContent className="pt-6">
          <div className="flex items-start gap-4">
            <span className="text-3xl">📜</span>
            <div>
              <h3 className="font-semibold text-blue-800">Open Source Software</h3>
              <p className="text-sm text-blue-700 mt-1">
                Bijmantra is open-source software. You are free to use, modify, and distribute it 
                according to the license terms. These terms apply to the hosted version and services.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Acceptance */}
      <Card>
        <CardHeader>
          <CardTitle>1. Acceptance of Terms</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p>
            By accessing or using Bijmantra, you agree to be bound by these Terms of Service. 
            If you do not agree to these terms, please do not use the application.
          </p>
          <p>
            We may update these terms from time to time. Continued use of the application after 
            changes constitutes acceptance of the new terms.
          </p>
        </CardContent>
      </Card>

      {/* License */}
      <Card>
        <CardHeader>
          <CardTitle>2. License</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p>
            Bijmantra is released under an open-source license. You are granted a non-exclusive, 
            worldwide, royalty-free license to:
          </p>
          <ul className="list-disc list-inside space-y-1 ml-4">
            <li>Use the software for any purpose</li>
            <li>Study how the software works and modify it</li>
            <li>Redistribute copies of the software</li>
            <li>Distribute modified versions</li>
          </ul>
          <p>
            The full license text is available in the project repository on GitHub.
          </p>
        </CardContent>
      </Card>

      {/* Use of Service */}
      <Card>
        <CardHeader>
          <CardTitle>3. Use of Service</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p>You agree to use Bijmantra only for lawful purposes and in accordance with these terms. You agree not to:</p>
          <ul className="list-disc list-inside space-y-1 ml-4">
            <li>Use the service in any way that violates applicable laws or regulations</li>
            <li>Attempt to gain unauthorized access to any part of the service</li>
            <li>Interfere with or disrupt the service or servers</li>
            <li>Use the service to transmit malware or harmful code</li>
            <li>Impersonate any person or entity</li>
          </ul>
        </CardContent>
      </Card>

      {/* Your Data */}
      <Card>
        <CardHeader>
          <CardTitle>4. Your Data</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p>
            You retain all rights to your data. Bijmantra does not claim ownership of any data 
            you input into the system.
          </p>
          <p>
            You are responsible for:
          </p>
          <ul className="list-disc list-inside space-y-1 ml-4">
            <li>Maintaining backups of your data</li>
            <li>Ensuring you have the right to use and store the data</li>
            <li>Complying with any applicable data protection regulations</li>
            <li>Securing your account credentials</li>
          </ul>
        </CardContent>
      </Card>

      {/* AI Services */}
      <Card>
        <CardHeader>
          <CardTitle>5. AI Services</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p>
            Bijmantra integrates with third-party AI services. When using these features:
          </p>
          <ul className="list-disc list-inside space-y-1 ml-4">
            <li>You are responsible for providing your own API keys</li>
            <li>Usage is subject to the terms of the respective AI provider</li>
            <li>AI responses are provided "as is" without warranty</li>
            <li>You should verify AI-generated recommendations before acting on them</li>
          </ul>
          <p className="mt-3">
            Chrome Built-in AI (Gemini Nano) runs locally and is subject to Google's terms for 
            Chrome and its built-in features.
          </p>
        </CardContent>
      </Card>

      {/* Disclaimer */}
      <Card>
        <CardHeader>
          <CardTitle>6. Disclaimer of Warranties</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p className="uppercase font-medium">
            THE SERVICE IS PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND, 
            EITHER EXPRESS OR IMPLIED.
          </p>
          <p>
            We do not warrant that:
          </p>
          <ul className="list-disc list-inside space-y-1 ml-4">
            <li>The service will be uninterrupted or error-free</li>
            <li>Defects will be corrected</li>
            <li>The service is free of viruses or harmful components</li>
            <li>The results obtained from using the service will be accurate or reliable</li>
          </ul>
        </CardContent>
      </Card>

      {/* Limitation of Liability */}
      <Card>
        <CardHeader>
          <CardTitle>7. Limitation of Liability</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p>
            To the maximum extent permitted by law, in no event shall the developers or contributors 
            be liable for any indirect, incidental, special, consequential, or punitive damages, 
            including but not limited to:
          </p>
          <ul className="list-disc list-inside space-y-1 ml-4">
            <li>Loss of profits, data, or goodwill</li>
            <li>Service interruption or computer damage</li>
            <li>Cost of substitute services</li>
            <li>Any damages arising from your use of the service</li>
          </ul>
        </CardContent>
      </Card>

      {/* Indemnification */}
      <Card>
        <CardHeader>
          <CardTitle>8. Indemnification</CardTitle>
        </CardHeader>
        <CardContent className="text-sm">
          <p>
            You agree to indemnify and hold harmless the developers, contributors, and affiliates 
            from any claims, damages, losses, or expenses arising from your use of the service 
            or violation of these terms.
          </p>
        </CardContent>
      </Card>

      {/* Governing Law */}
      <Card>
        <CardHeader>
          <CardTitle>9. Governing Law</CardTitle>
        </CardHeader>
        <CardContent className="text-sm">
          <p>
            These terms shall be governed by and construed in accordance with applicable laws, 
            without regard to conflict of law principles.
          </p>
        </CardContent>
      </Card>

      {/* Changes */}
      <Card>
        <CardHeader>
          <CardTitle>10. Changes to Terms</CardTitle>
        </CardHeader>
        <CardContent className="text-sm">
          <p>
            We reserve the right to modify these terms at any time. Changes will be posted on 
            this page with an updated revision date. Your continued use of the service after 
            changes constitutes acceptance of the modified terms.
          </p>
        </CardContent>
      </Card>

      {/* Contact */}
      <Card className="border-green-200 bg-green-50">
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <span className="text-3xl">❓</span>
              <div>
                <h3 className="font-semibold text-green-800">Questions about these terms?</h3>
                <p className="text-sm text-green-700">
                  Contact us if you have any questions
                </p>
              </div>
            </div>
            <Link to="/contact">
              <Button>Contact Us</Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
