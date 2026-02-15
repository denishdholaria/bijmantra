/**
 * About Page - Professional & Mission-Driven Redesign
 * "One Seed. Infinite Worlds."
 */
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Link } from 'react-router-dom'
import { Separator } from '@/components/ui/separator'

export function About() {
  const education = [
    { 
      degree: "BSc Biotechnology", 
      school: "Monash University", 
      year: "2010", 
      icon: "🧬",
      desc: "Foundational genetics & molecular biology"
    },
    { 
      degree: "MSc Plant Breeding & Biotech", 
      school: "University of Adelaide", 
      year: "2012", 
      icon: "🌾",
      desc: "Advanced crop improvement & quantitative genetics"
    },
    { 
      degree: "Agricultural Science", 
      school: "University of Melbourne", 
      year: "2024", 
      icon: "🎓",
      desc: "Precision agriculture, extension & marketing"
    }
  ]

  return (
    <div className="animate-fade-in max-w-6xl mx-auto px-4 pb-20 space-y-24">
      
      {/* 1. HERO SECTION - High Impact, Minimalist */}
      <section className="text-center pt-20 pb-10 relative">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[400px] bg-gradient-to-r from-emerald-500/10 via-green-500/5 to-teal-500/10 blur-3xl rounded-full -z-10 dark:from-emerald-900/20 dark:via-green-900/10 dark:to-teal-900/20 pointer-events-none"></div>
        
        <Badge variant="outline" className="mb-6 px-4 py-1 border-emerald-500/30 text-emerald-700 dark:text-emerald-400 bg-emerald-50/50 dark:bg-emerald-900/10 backdrop-blur-sm">
          Since 2025
        </Badge>
        
        <h1 className="text-6xl md:text-7xl lg:text-8xl font-black tracking-tight text-foreground mb-6">
          One Seed.<br/>
          <span className="bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">Infinite Worlds.</span>
        </h1>
        
        <p className="text-xl md:text-2xl text-muted-foreground max-w-2xl mx-auto font-light leading-relaxed">
          Bijmantra is an open-source research infrastructure designed to unify the fragmented world of agricultural science.
        </p>

        <div className="flex items-center justify-center gap-4 mt-8">
          <Link to="/features">
            <Button size="lg" className="h-12 px-8 text-lg rounded-full bg-emerald-600 hover:bg-emerald-700 text-white shadow-lg shadow-emerald-500/20">
              Explore the Platform
            </Button>
          </Link>
          <Link to="https://github.com/denishdholaria/bijmantra" target="_blank">
            <Button variant="outline" size="lg" className="h-12 px-8 text-lg rounded-full border-2">
              View Source
            </Button>
          </Link>
        </div>
      </section>

      {/* 2. THE ORIGIN - Narrative Timeline */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        <div className="space-y-6">
          <h2 className="text-3xl font-bold tracking-tight">Rooted in the Fields</h2>
          <div className="prose prose-lg dark:prose-invert text-muted-foreground">
            <p>
              The seed for Bijmantra was planted long before any code was written. It began in the cotton fields of Gujarat, India, 
              where a 12-year-old boy walked alongside his father, <strong className="text-foreground">Dr. T.L. Dholaria</strong>.
            </p>
            <p>
              Watching his father—a PhD in Plant Breeding—meticulously select cotton hybrids, he learned that 
              science isn't just data. It's patience. It's observation. It's the profound responsibility 
              of choosing which seeds will feed the future.
            </p>
            <blockquote className="border-l-4 border-emerald-500 pl-4 italic text-foreground my-6">
              "The seeds we plant today determine the harvest our children will reap tomorrow."
            </blockquote>
            <p>
              Decades later, after academic rigor in Australia and professional practice in the field, 
              that same responsibility now drives the code behind Bijmantra.
            </p>
          </div>
        </div>
        
        <div className="relative pl-8 border-l border-border space-y-12 py-4">
          <div className="relative">
            <div className="absolute -left-[39px] bg-background border border-border p-1.5 rounded-full">
              <span className="block w-2.5 h-2.5 bg-emerald-500 rounded-full"></span>
            </div>
            <span className="text-sm font-mono text-emerald-600 dark:text-emerald-400 mb-1 block">The Beginning (Gujarat)</span>
            <h3 className="text-xl font-semibold">Field Observation</h3>
            <p className="text-muted-foreground mt-1">Learning the art of selection and the weight of scientific responsibility.</p>
          </div>
          <div className="relative">
            <div className="absolute -left-[39px] bg-background border border-border p-1.5 rounded-full">
            <span className="block w-2.5 h-2.5 bg-blue-500 rounded-full"></span>
            </div>
            <span className="text-sm font-mono text-blue-600 dark:text-blue-400 mb-1 block">Academic Rigor (Australia)</span>
            <h3 className="text-xl font-semibold">Theoretical Foundation</h3>
            <p className="text-muted-foreground mt-1">Monash, Adelaide, Melbourne — mastering the science of genetics and biotechnology.</p>
          </div>
          <div className="relative">
            <div className="absolute -left-[39px] bg-background border border-border p-1.5 rounded-full">
            <span className="block w-2.5 h-2.5 bg-purple-500 rounded-full"></span>
            </div>
            <span className="text-sm font-mono text-purple-600 dark:text-purple-400 mb-1 block">The Synthesis (2025)</span>
            <h3 className="text-xl font-semibold">Bijmantra Born</h3>
            <p className="text-muted-foreground mt-1">Unifying biology and technology into a single, open platform.</p>
          </div>
        </div>
      </section>

      <Separator />

      {/* 3. THE CREATOR PROFILE - Professional & Dignified */}
      <section>
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl font-bold tracking-tight mb-4">The Team of One</h2>
          <p className="text-lg text-muted-foreground">
            Built independently over 20+ months. No funding. No team. Just clear purpose.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Main Profile Card */}
          <Card className="md:col-span-1 border-0 shadow-lg bg-gradient-to-b from-slate-50 to-white dark:from-slate-900 dark:to-slate-950">
            <CardContent className="pt-8 text-center">
              <div className="w-24 h-24 mx-auto bg-slate-200 dark:bg-slate-800 rounded-full flex items-center justify-center text-4xl mb-4 shadow-inner">
                👨‍💻
              </div>
              <h3 className="text-2xl font-bold">Hare Krishna</h3>
              <p className="text-sm font-mono text-muted-foreground mt-1">(Denish Dholaria)</p>
              <div className="mt-4 flex flex-wrap justify-center gap-2">
                <Badge variant="secondary">Creator</Badge>
                <Badge variant="secondary">Lead Dev</Badge>
                <Badge variant="secondary">Plant Scientist</Badge>
              </div>
              <div className="mt-8 text-left space-y-3 text-sm text-muted-foreground pb-4">
                <p>📍 Architecting Global Research Infrastructure</p>
                <p>💼 Agricultural Scientist by Day</p>
                <p>🌙 Open Source Maintainer by Night</p>
              </div>
            </CardContent>
          </Card>

          {/* Education & Mentorship */}
          <div className="md:col-span-2 space-y-6">
            <div className="grid grid-cols-1 gap-4">
              {education.map((edu, i) => (
                <div key={i} className="flex items-start gap-4 p-4 rounded-xl border bg-card hover:bg-accent/50 transition-colors">
                  <div className="text-3xl p-2 bg-background rounded-lg border shadow-sm">{edu.icon}</div>
                  <div>
                    <h4 className="font-semibold text-lg">{edu.degree}</h4>
                    <p className="text-sm text-muted-foreground">{edu.school} • {edu.year}</p>
                    <p className="text-xs text-muted-foreground mt-1 opacity-80">{edu.desc}</p>
                  </div>
                </div>
              ))}
            </div>

            <div className="p-6 rounded-xl bg-amber-50/50 dark:bg-amber-900/10 border border-amber-200/50 dark:border-amber-800/30">
              <h4 className="text-sm font-semibold uppercase tracking-wider text-amber-800 dark:text-amber-500 mb-2">Primary Mentorship</h4>
              <p className="text-lg font-medium text-foreground">Dr. T. L. Dholaria</p>
              <p className="text-muted-foreground">PhD, Plant Breeding & Genetics • Pioneer in Cotton Hybrid Development</p>
            </div>
          </div>
        </div>
      </section>

      {/* 4. MANIFESTO - The Soul of the Project */}
      <section className="relative overflow-hidden rounded-3xl bg-slate-900 text-white p-8 md:p-16 text-center">
        {/* Abstract background pattern */}
        <div className="absolute top-0 left-0 w-full h-full opacity-10 pointer-events-none">
          <div className="absolute right-0 top-0 w-96 h-96 bg-blue-500 rounded-full filter blur-[128px]"></div>
          <div className="absolute left-0 bottom-0 w-96 h-96 bg-emerald-500 rounded-full filter blur-[128px]"></div>
        </div>

        <div className="relative z-10 max-w-4xl mx-auto space-y-8">
          <h2 className="text-3xl md:text-5xl font-black tracking-tight leading-tight">
             This is not a complaint.<br/>
             It is a necessity for the survival of future generations.
          </h2>
          <p className="text-xl md:text-2xl text-slate-300 font-light leading-relaxed">
            Agricultural resilience is the mission of our age. Building this infrastructure is the standard of 
            greatness we must achieve to secure the world's food supply.
          </p>
          <div className="pt-8">
            <p className="text-sm font-mono text-slate-400 uppercase tracking-widest mb-6">Built For</p>
            <div className="flex flex-wrap justify-center gap-3">
              <span className="px-4 py-2 rounded-full border border-slate-700 bg-slate-800/50">Researchers in Niger</span>
              <span className="px-4 py-2 rounded-full border border-slate-700 bg-slate-800/50">Breeders in Cambodia</span>
              <span className="px-4 py-2 rounded-full border border-slate-700 bg-slate-800/50">Curators in Peru</span>
              <span className="px-4 py-2 rounded-full border border-slate-700 bg-slate-800/50">Everyone. Everywhere.</span>
            </div>
          </div>
        </div>
      </section>

      {/* 5. ETHICS - The Red Line */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-8">
         <div className="md:col-span-1">
           <h3 className="text-2xl font-bold mb-4 text-red-600 dark:text-red-400">Ethical Hardline</h3>
           <p className="text-muted-foreground">
             Technology is not neutral. What we build determines how power is distributed. Bijmantra draws a clear line in the sand.
           </p>
         </div>
         <div className="md:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-4">
           {['Terminator Technology', 'GURTs (Genetic Restriction)', 'Traitor Tech', 'Seed Sterilization'].map((item) => (
             <div key={item} className="flex items-center gap-3 p-4 border border-red-200 dark:border-red-900/50 bg-red-50/50 dark:bg-red-950/10 rounded-lg">
               <span className="text-red-500">🚫</span>
               <span className="font-medium text-red-900 dark:text-red-200">{item}</span>
             </div>
           ))}
           <div className="sm:col-span-2 text-center pt-2">
             <p className="text-sm italic text-muted-foreground">
               "Seeds are a gift of nature belonging to all humanity, not features to be engineered away for profit."
             </p>
           </div>
         </div>
      </section>

      {/* 6. INSPIRATION & CTA - The Future */}
      <section className="text-center space-y-8 pt-10">
        <blockquote className="text-xl font-serif italic text-muted-foreground max-w-2xl mx-auto">
          "The good you do today, people will often forget tomorrow. Do good anyway.<br/>
          Give the world the best you have, and it may never be enough. Give the best you've got anyway."
        </blockquote>
        <p className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">— Kent M. Keith</p>
        
        <div className="pt-12 flex flex-col items-center gap-6">
          <p className="text-lg">Ready to contribute to the mission?</p>
          <div className="flex gap-4">
            <Link to="/vision">
              <Button size="lg" variant="default">See the 100-Year Vision</Button>
            </Link>
            <Link to="/dashboard">
              <Button size="lg" variant="secondary">Go to Dashboard</Button>
            </Link>
          </div>
          <p className="text-xs text-muted-foreground mt-8">
            © 2025 Bijmantra • Open Source • Built with 💚 for the World
          </p>
        </div>
      </section>

    </div>
  )
}

