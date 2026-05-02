/**
 * About Page - Professional & Mission-Driven Redesign
 * "One Seed. Infinite Worlds."
 */
import { Card, CardContent } from '@/components/ui/card'
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
    <div className="animate-fade-in max-w-7xl mx-auto px-6 pb-24 space-y-32">
      
      {/* 1. HERO SECTION - Visionary & Cinematic */}
      <section className="text-center pt-32 pb-16 relative">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1000px] h-[500px] bg-gradient-to-r from-emerald-500/10 via-teal-500/5 to-cyan-500/10 blur-[100px] rounded-full -z-10 pointer-events-none dark:from-emerald-900/20 dark:via-teal-900/10 dark:to-cyan-900/20"></div>
        
        <Badge variant="outline" className="mb-8 px-6 py-2 border-emerald-500/30 text-emerald-700 dark:text-emerald-400 bg-emerald-50/50 dark:bg-emerald-900/10 backdrop-blur-md uppercase tracking-widest text-xs font-semibold">
          Established MMXXV
        </Badge>
        
        <h1 className="text-6xl md:text-8xl lg:text-[7rem] font-black tracking-tighter text-foreground mb-8 leading-[0.9]">
          One Seed.<br/>
          <span className="bg-gradient-to-r from-emerald-600 via-teal-500 to-cyan-600 bg-clip-text text-transparent drop-shadow-sm">
            Infinite Worlds.
          </span>
        </h1>
        
        <p className="text-xl md:text-3xl text-muted-foreground max-w-3xl mx-auto font-light leading-relaxed tracking-wide">
          An open-source research sanctuary designed to unify the fragmented world of agricultural science.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-6 mt-12">
          <Link to="/features">
            <Button size="lg" className="h-14 px-10 text-lg rounded-full bg-emerald-600 hover:bg-emerald-700 text-white shadow-xl shadow-emerald-500/20 transition-all hover:scale-105">
              Enter the Platform
            </Button>
          </Link>
          <Link to="https://github.com/denishdholaria/bijmantra" target="_blank" aria-label="View Source on Github">
            <Button variant="outline" size="lg" className="h-14 px-10 text-lg rounded-full border-2 hover:bg-muted transition-all">
              Inspect Source
            </Button>
          </Link>
        </div>
      </section>

      {/* 2. THE ORIGIN - Epic Narrative */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-16 items-center">
        <div className="lg:col-span-7 space-y-8">
          <h2 className="text-4xl md:text-5xl font-extrabold tracking-tight">Forged in the Fields</h2>
          <div className="prose prose-xl dark:prose-invert text-muted-foreground leading-relaxed">
            <p>
              The architecture of Bijmantra was conceived long before the first line of code was compiled. It began in the sun-baked cotton fields of Gujarat, India, observing the ancient, quiet rhythm of the harvest.
            </p>
            <p>
              Witnessing the meticulous selection of cotton hybrids, a profound truth emerged: science is not merely the aggregation of data. It is patience. It is acute observation. It is the heavy, sacred responsibility of choosing which seeds possess the strength to feed the future.
            </p>
            <blockquote className="border-l-4 border-emerald-500 pl-6 italic text-foreground my-8 text-2xl font-serif">
              "The seeds we protect today are the quiet architects of tomorrow's survival."
            </blockquote>
            <p>
              Decades later, after rigorous academic trials across Australia and relentless professional practice, that same ancestral responsibility now powers the engine of Bijmantra.
            </p>
          </div>
        </div>
        
        <div className="lg:col-span-5 relative pl-10 border-l-2 border-muted space-y-16 py-8">
          <div className="relative">
            <div className="absolute -left-[49px] bg-background border-2 border-emerald-500 p-1.5 rounded-full shadow-[0_0_15px_rgba(16,185,129,0.5)]">
              <span className="block w-3 h-3 bg-emerald-500 rounded-full"></span>
            </div>
            <span className="text-sm font-mono text-emerald-600 dark:text-emerald-400 mb-2 block tracking-wider uppercase">Genesis • Gujarat</span>
            <h3 className="text-2xl font-bold text-foreground">The Art of Selection</h3>
            <p className="text-muted-foreground mt-2 text-lg">Internalizing the weight of agricultural responsibility at the root level.</p>
          </div>
          <div className="relative">
            <div className="absolute -left-[49px] bg-background border-2 border-blue-500 p-1.5 rounded-full shadow-[0_0_15px_rgba(59,130,246,0.5)]">
            <span className="block w-3 h-3 bg-blue-500 rounded-full"></span>
            </div>
            <span className="text-sm font-mono text-blue-600 dark:text-blue-400 mb-2 block tracking-wider uppercase">Crucible • Australia</span>
            <h3 className="text-2xl font-bold text-foreground">Theoretical Mastery</h3>
            <p className="text-muted-foreground mt-2 text-lg">Monash, Adelaide, Melbourne — deciphering the complex languages of genetics and biotechnology.</p>
          </div>
          <div className="relative">
            <div className="absolute -left-[49px] bg-background border-2 border-purple-500 p-1.5 rounded-full shadow-[0_0_15px_rgba(168,85,247,0.5)]">
            <span className="block w-3 h-3 bg-purple-500 rounded-full"></span>
            </div>
            <span className="text-sm font-mono text-purple-600 dark:text-purple-400 mb-2 block tracking-wider uppercase">Synthesis • 2025</span>
            <h3 className="text-2xl font-bold text-foreground">Bijmantra Awakens</h3>
            <p className="text-muted-foreground mt-2 text-lg">Fusing biology and digital infrastructure into an unbreakable, open platform.</p>
          </div>
        </div>
      </section>

      <Separator className="opacity-50" />

      {/* 3. THE CREATOR PROFILE - The Architect */}
      <section>
        <div className="text-center max-w-4xl mx-auto mb-20">
          <h2 className="text-4xl md:text-5xl font-extrabold tracking-tight mb-6">The Architect</h2>
          <p className="text-xl text-muted-foreground font-light">
            Engineered independently over 20+ months. Zero external funding. No corporate oversight. A pure distillation of purpose.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Main Profile Card */}
          <Card className="lg:col-span-5 border border-muted/50 shadow-2xl bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-950 overflow-hidden relative">
            <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/10 rounded-full blur-3xl -mr-10 -mt-10 pointer-events-none"></div>
            <CardContent className="pt-12 pb-10 text-center relative z-10">
              <div className="w-32 h-32 mx-auto bg-slate-200 dark:bg-slate-800 rounded-full flex items-center justify-center text-5xl mb-6 shadow-inner ring-4 ring-background">
                👨‍💻
              </div>
              <h3 className="text-4xl font-black tracking-tight">Hare Krishna</h3>
              <p className="text-lg font-mono text-muted-foreground mt-2 tracking-wide">(Denish Dholaria)</p>
              <div className="mt-8 flex flex-wrap justify-center gap-3">
                <Badge variant="secondary" className="px-4 py-1.5 text-sm">Founder</Badge>
                <Badge variant="secondary" className="px-4 py-1.5 text-sm">Lead Architect</Badge>
                <Badge variant="secondary" className="px-4 py-1.5 text-sm">Plant Scientist</Badge>
              </div>
              <Separator className="my-8 opacity-50 w-2/3 mx-auto" />
              <div className="text-left space-y-4 text-base text-muted-foreground px-4 md:px-8">
                <p className="flex items-center gap-3"><span className="text-xl">📍</span> Architecting Global Research Infrastructure</p>
                <p className="flex items-center gap-3"><span className="text-xl">💼</span> Agricultural Scientist by Day</p>
                <p className="flex items-center gap-3"><span className="text-xl">🌙</span> Open Source Maintainer by Night</p>
              </div>
            </CardContent>
          </Card>

          {/* Education Array */}
          <div className="lg:col-span-7 flex flex-col justify-center space-y-6">
            <h4 className="text-sm font-bold uppercase tracking-widest text-muted-foreground mb-2 pl-2">Academic Foundation</h4>
            {education.map((edu, i) => (
              <div key={i} className="group flex items-center gap-6 p-6 rounded-2xl border border-muted/50 bg-card hover:border-emerald-500/30 hover:shadow-lg transition-all duration-300">
                <div className="text-4xl p-4 bg-muted/30 rounded-xl border border-muted/50 group-hover:bg-emerald-500/10 group-hover:scale-110 transition-all duration-300">
                  {edu.icon}
                </div>
                <div>
                  <h4 className="font-bold text-2xl text-foreground">{edu.degree}</h4>
                  <p className="text-base text-muted-foreground mt-1 font-medium">{edu.school} <span className="mx-2">•</span> {edu.year}</p>
                  <p className="text-sm text-muted-foreground mt-2 opacity-80">{edu.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 4. MANIFESTO - The Soul of the Project */}
      <section className="relative overflow-hidden rounded-[2.5rem] bg-slate-950 text-white p-10 md:p-24 text-center shadow-2xl border border-slate-800">
        <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/stardust.png')] opacity-20 pointer-events-none mix-blend-overlay"></div>
        <div className="absolute top-0 left-0 w-full h-full opacity-30 pointer-events-none">
          <div className="absolute -right-20 -top-20 w-[500px] h-[500px] bg-blue-600 rounded-full filter blur-[150px]"></div>
          <div className="absolute -left-20 -bottom-20 w-[500px] h-[500px] bg-emerald-600 rounded-full filter blur-[150px]"></div>
        </div>

        <div className="relative z-10 max-w-5xl mx-auto space-y-10">
          <h2 className="text-4xl md:text-6xl font-black tracking-tighter leading-tight drop-shadow-md">
             This is not a complaint.<br/>
             <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">
               It is a necessity for human survival.
             </span>
          </h2>
          <p className="text-xl md:text-3xl text-slate-300 font-light leading-relaxed max-w-4xl mx-auto">
            Agricultural resilience is the ultimate mission of our era. Building this open infrastructure is the standard of greatness we must achieve to secure the world's food supply.
          </p>
          <div className="pt-12">
            <p className="text-sm font-mono text-slate-400 uppercase tracking-[0.3em] mb-8">Deployed For</p>
            <div className="flex flex-wrap justify-center gap-4 text-sm md:text-base">
              <span className="px-6 py-3 rounded-full border border-slate-700 bg-slate-800/80 backdrop-blur-sm text-slate-200">Researchers in Niger</span>
              <span className="px-6 py-3 rounded-full border border-slate-700 bg-slate-800/80 backdrop-blur-sm text-slate-200">Breeders in Cambodia</span>
              <span className="px-6 py-3 rounded-full border border-slate-700 bg-slate-800/80 backdrop-blur-sm text-slate-200">Curators in Peru</span>
              <span className="px-6 py-3 rounded-full border border-emerald-900 bg-emerald-950/80 backdrop-blur-sm text-emerald-300 font-semibold shadow-[0_0_15px_rgba(16,185,129,0.2)]">Everyone. Everywhere.</span>
            </div>
          </div>
        </div>
      </section>

      {/* 5. ETHICS - The Unbreakable Red Line */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-12 p-10 md:p-16 rounded-3xl bg-red-50/30 dark:bg-red-950/10 border border-red-100 dark:border-red-900/30">
         <div className="lg:col-span-1 space-y-6">
           <h3 className="text-3xl font-black text-red-600 dark:text-red-500 tracking-tight uppercase">The Red Line</h3>
           <p className="text-lg text-muted-foreground leading-relaxed">
             Technology is never neutral. The tools we build dictate how power is distributed in the future. Bijmantra draws an unbreakable ethical line.
           </p>
         </div>
         <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-4">
           {['Terminator Technology', 'GURTs (Genetic Restriction)', 'Traitor Tech', 'Seed Sterilization'].map((item) => (
             <div key={item} className="flex items-center gap-4 p-5 border border-red-200 dark:border-red-900/50 bg-white/50 dark:bg-red-950/30 rounded-xl shadow-sm backdrop-blur-sm">
               <span className="text-2xl drop-shadow-sm">🚫</span>
               <span className="font-bold text-red-950 dark:text-red-200 text-lg">{item}</span>
             </div>
           ))}
           <div className="sm:col-span-2 text-center pt-8">
             <p className="text-xl font-serif italic text-foreground border-t border-red-200 dark:border-red-900/50 pt-8">
               "Seeds are a gift of nature belonging to all humanity, not proprietary features to be engineered away for profit."
             </p>
           </div>
         </div>
      </section>

      {/* 6. INSPIRATION & CTA - The Future */}
      <section className="text-center space-y-10 pt-16 pb-12">
        <div className="max-w-3xl mx-auto space-y-6">
          <blockquote className="text-2xl md:text-3xl font-serif italic text-foreground leading-relaxed">
            "The good you do today, people will often forget tomorrow. Do good anyway.<br/>
            Give the world the best you have, and it may never be enough. Give the best you've got anyway."
          </blockquote>
          <p className="text-sm font-bold uppercase tracking-[0.2em] text-muted-foreground">— Kent M. Keith</p>
        </div>
        
        <div className="pt-16 flex flex-col items-center gap-8">
          <p className="text-2xl font-bold tracking-tight">Are you ready to build the future?</p>
          <div className="flex flex-col sm:flex-row gap-5">
            <Link to="/vision">
              <Button size="lg" className="h-14 px-10 text-lg rounded-full">Read the 100-Year Vision</Button>
            </Link>
            <Link to="/dashboard">
              <Button size="lg" variant="secondary" className="h-14 px-10 text-lg rounded-full border-2">Enter Dashboard</Button>
            </Link>
          </div>
          <div className="mt-16 flex flex-col items-center gap-2">
            <div className="w-12 h-1 bg-emerald-500 rounded-full mb-4"></div>
            <p className="text-sm font-medium text-muted-foreground uppercase tracking-widest">
              © 2025 Bijmantra
            </p>
            <p className="text-xs text-muted-foreground opacity-70">
              Open Source • Built with 💚 for the World
            </p>
          </div>
        </div>
      </section>

    </div>
  )
}