/**
 * FAQ Page
 *
 * Frequently asked questions.
 */

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface FAQItem {
  question: string;
  answer: string;
  category: string;
}

export function FAQ() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  const faqs: FAQItem[] = [
    { question: 'How do I create a new breeding program?', answer: 'Navigate to Plant Sciences > Programs and click "New Program". Fill in the program name, objective, and other details.', category: 'Getting Started' },
    { question: 'Can I use Bijmantra offline?', answer: 'Yes! Bijmantra is a PWA that works offline. Data is stored locally and syncs automatically when you reconnect.', category: 'Features' },
    { question: 'How do I register a new accession in the seed bank?', answer: 'Go to Seed Bank > Accessions and click "Register Accession". Enter the taxonomy, collection info, and storage details.', category: 'Seed Bank' },
    { question: 'What is BrAPI and why does it matter?', answer: 'BrAPI (Breeding API) is a standard for plant breeding data exchange. It allows Bijmantra to interoperate with other breeding platforms.', category: 'Technical' },
    { question: 'How do I export my data?', answer: 'Most list pages have an export button. You can export to CSV, Excel, or BrAPI-compatible JSON format.', category: 'Data' },
    { question: 'Can multiple users work on the same program?', answer: 'Yes, Bijmantra supports multi-user collaboration with role-based access control (RBAC).', category: 'Collaboration' },
    { question: 'How is my data secured?', answer: 'Data is encrypted in transit (HTTPS) and at rest. We use JWT authentication and row-level security in the database.', category: 'Security' },
    { question: 'What browsers are supported?', answer: 'Bijmantra works best on Chrome, Firefox, Safari, and Edge. Mobile browsers are also supported.', category: 'Technical' },
  ];

  const categories = [...new Set(faqs.map((f) => f.category))];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-foreground">Frequently Asked Questions</h1>
        <p className="text-muted-foreground mt-1">Common questions and answers</p>
      </div>

      <div className="space-y-4">
        {faqs.map((faq, index) => (
          <Card key={index} className="cursor-pointer" onClick={() => setOpenIndex(openIndex === index ? null : index)}>
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs px-2 py-0.5 bg-muted text-muted-foreground rounded">{faq.category}</span>
                  </div>
                  <h3 className="font-medium mt-2 text-foreground">{faq.question}</h3>
                  {openIndex === index && (
                    <p className="text-muted-foreground mt-3 text-sm">{faq.answer}</p>
                  )}
                </div>
                <span className="text-muted-foreground text-xl">{openIndex === index ? '−' : '+'}</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

export default FAQ;
