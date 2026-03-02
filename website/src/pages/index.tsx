import React from 'react';
import Layout from '@theme/Layout';

export default function Home() {
  return (
    <Layout
      title="BijMantra - Cross-Domain Agricultural Intelligence"
      description="The open-source breeding management platform for agricultural visionaries.">

      {/* The Abode (Backgrounds) */}
      <div className="font-sans text-samudra-900 dark:text-samudra-50 min-h-screen selection:bg-devi-500/30 selection:text-devi-100 overflow-x-hidden transition-colors duration-500">

        {/* Navaratna Lusters (Background Glows) */}
        <div className="ambient-glow-1 animate-blob opacity-60 dark:opacity-40"></div>
        <div className="ambient-glow-2 animate-blob [animation-delay:4s] opacity-40 dark:opacity-30"></div>

        {/* Hero Section (The Ratnagriha) */}
        <main
          className="w-full max-w-7xl mx-auto px-6 pt-32 pb-24 lg:pt-48 lg:pb-32 flex flex-col items-center text-center relative z-10">

          {/* Badge */}
          <div
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass-panel text-gold-600 dark:text-gold-400 text-xs font-semibold uppercase tracking-widest mb-8 animate-slide-up delay-100 border-gold-500/20 bg-gold-500/5">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-gold-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-gold-500"></span>
            </span>
            The Forge is Open
          </div>

          {/* Headline */}
          <h1
            className="font-heading font-extrabold text-5xl md:text-7xl lg:text-8xl tracking-tight leading-[1.1] mb-6 animate-slide-up delay-200">
            One Seed.<br />
            <span className="text-gradient-gold">Infinite Worlds.</span>
          </h1>

          {/* Subheadline */}
          <p className="max-w-2xl text-lg md:text-xl text-samudra-800 dark:text-slate-400 font-medium leading-relaxed mb-10 animate-slide-up delay-300">
            An impossibly ambitious endeavor to unify agricultural sciences into a single computational platform. Currently
            built by a solo developer who has realized this mountain is too tall to climb alone.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center gap-4 w-full sm:w-auto animate-slide-up delay-400">
            <a href="#the-reality"
              className="group relative inline-flex items-center justify-center w-full sm:w-auto px-10 py-4 text-sm font-bold text-white bg-devi-600 hover:bg-devi-500 rounded-full transition-all overflow-hidden shadow-lg shadow-devi-500/20">
              <span
                className="absolute w-0 h-0 transition-all duration-500 ease-out bg-white rounded-full group-hover:w-56 group-hover:h-56 opacity-10"></span>
              <span className="relative flex items-center gap-2 tracking-wide uppercase">
                <i className="ph-fill ph-book-open-text text-lg"></i>
                Read the Reality
              </span>
            </a>

            <a href="https://github.com/denishdholaria/bijmantra" target="_blank" rel="noopener"
              className="inline-flex items-center justify-center w-full sm:w-auto px-10 py-4 text-sm font-bold text-samudra-900 dark:text-white bg-white/50 dark:bg-samudra-900 glass-panel hover:bg-white/80 dark:hover:bg-samudra-800 rounded-full transition-all group border-slate-200 dark:border-white/5 uppercase tracking-wide">
              <i className="ph ph-github-logo text-lg mr-2 group-hover:scale-110 transition-transform"></i>
              View Source Code
            </a>
          </div>

          {/* Development Disclaimer */}
          <div className="mt-20 pt-8 border-t border-slate-200 dark:border-white/10 w-full max-w-2xl opacity-80 animate-slide-up delay-500">
            <p className="text-[0.65rem] text-slate-500 leading-relaxed text-center uppercase tracking-widest px-4 font-serif">
              * BijMantra is currently in active pre-alpha development. Features, modules, and BrAPI architecture described
              are aspirational or currently in progress. Access to the developer sandbox is for testing purposes only and does
              not represent a finished or production-ready product.
            </p>
          </div>
        </main>

        {/* The Reality Section */}
        <section id="the-reality" className="w-full max-w-7xl mx-auto px-6 py-24 relative z-10">
          <div className="text-center mb-16">
            <h2 className="font-heading font-bold text-3xl md:text-5xl text-samudra-900 dark:text-white mb-4">The Impossible Mission</h2>
            <p className="text-slate-600 dark:text-slate-400 max-w-3xl mx-auto text-lg leading-relaxed">When I initially conceptualized "Cross-Domain
              Agricultural Intelligence," I vastly underestimated the magnitude of the endeavor. As a solo developer, I am
              standing at the base of an insurmountable mountain. I am asking for help.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Card 1 */}
            <div className="feature-card glass-panel p-8 rounded-3xl flex flex-col items-start cursor-default border-slate-200 dark:border-white/5 bg-white/20 dark:bg-white/5">
              <div
                className="feature-icon-box w-14 h-14 rounded-2xl bg-devi-500/10 flex items-center justify-center text-devi-600 dark:text-devi-400 mb-6 font-bold shadow-sm">
                <i className="ph-fill ph-warning-circle text-2xl"></i>
              </div>
              <h3 className="font-heading font-semibold text-xl text-samudra-900 dark:text-white mb-3">The AI Illusion</h3>
              <p className="text-slate-600 dark:text-slate-400 leading-relaxed text-sm">I believed advanced artificial intelligence could bridge the
                massive gaps in agricultural data. I was wrong. Algorithms alone cannot synthesize biological truth. We
                desperately require rigorous, human scientific validation to anchor these models.</p>
            </div>

            {/* Card 2 */}
            <div className="feature-card glass-panel p-8 rounded-3xl flex flex-col items-start cursor-default border-slate-200 dark:border-white/5 bg-white/20 dark:bg-white/5">
              <div
                className="feature-icon-box w-14 h-14 rounded-2xl bg-blue-500/10 flex items-center justify-center text-blue-600 dark:text-blue-400 mb-6 font-bold shadow-sm">
                <i className="ph-fill ph-cloud-warning text-2xl"></i>
              </div>
              <h3 className="font-heading font-semibold text-xl text-samudra-900 dark:text-white mb-3">The Climate Imperative</h3>
              <p className="text-slate-600 dark:text-slate-400 leading-relaxed text-sm">The ultimate goal of this project is to build global
                agricultural resilience. Climate change is an existential threat that cannot be engineered around in
                isolation. We urgently need climatologists to integrate planetary-scale risk into field-level decisions.</p>
            </div>

            {/* Card 3 */}
            <div className="feature-card glass-panel p-8 rounded-3xl flex flex-col items-start cursor-default border-slate-200 dark:border-white/5 bg-white/20 dark:bg-white/5">
              <div
                className="feature-icon-box w-14 h-14 rounded-2xl bg-gold-500/10 flex items-center justify-center text-gold-600 dark:text-gold-500 mb-6 font-bold shadow-sm">
                <i className="ph-fill ph-users-three text-2xl"></i>
              </div>
              <h3 className="font-heading font-semibold text-xl text-samudra-900 dark:text-white mb-3">Multidisciplinary Complexity</h3>
              <p className="text-slate-600 dark:text-slate-400 leading-relaxed text-sm">True agriculture is the paramount intersection of
                sciences—biology, biochemistry, physics, genetics, agronomy, and macroeconomics. I do not possess this
                sprawling expertise. We need seasoned professors and industry veterans to architect the profound domain logic.
              </p>
            </div>

            {/* Card 4 */}
            <div className="feature-card glass-panel p-8 rounded-3xl flex flex-col items-start cursor-default border-slate-200 dark:border-white/5 bg-white/20 dark:bg-white/5">
              <div
                className="feature-icon-box w-14 h-14 rounded-2xl bg-emerald-500/10 flex items-center justify-center text-emerald-600 dark:text-emerald-500 mb-6 font-bold shadow-sm">
                <i className="ph-fill ph-hands-praying text-2xl"></i>
              </div>
              <h3 className="font-heading font-semibold text-xl text-samudra-900 dark:text-white mb-3">The Sustainability Crisis</h3>
              <p className="text-slate-600 dark:text-slate-400 leading-relaxed text-sm">I have been burning through personal funds to keep this
                platform alive, and it is entirely unsustainable. We are lightyears from the finished dream. To forge the
                profound scientific inventions this system demands, we urgently require visionary funding.</p>
            </div>
          </div>
        </section>

        {/* Contributor / Funding CTA */}
        <section id="contribute" className="w-full max-w-7xl mx-auto px-6 py-12 relative z-10">
          <div
            className="glass-panel p-10 rounded-3xl border-devi-500/30 bg-devi-500/5 dark:bg-devi-900/10 relative overflow-hidden flex flex-col md:flex-row items-center justify-between gap-8 shadow-xl">
            {/* Decorative Glow */}
            <div className="absolute -right-20 -top-20 w-64 h-64 bg-devi-500/10 dark:bg-devi-500/20 blur-[80px] rounded-full"></div>

            <div className="flex-1">
              <div
                className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-devi-500/20 text-devi-600 dark:text-devi-400 text-xs font-bold uppercase tracking-widest mb-4 border border-devi-500/20">
                <i className="ph-fill ph-hands-clapping text-devi-500"></i> We Urgently Need You
              </div>
              <h2 className="font-heading font-bold text-2xl md:text-3xl text-samudra-900 dark:text-white mb-3">Save the Open-Source Mission</h2>
              <p className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed max-w-2xl">
                I cannot build this entirely alone. To survive and scale, BijMantra urgently requires <span
                  className="text-devi-700 dark:text-devi-300 font-semibold">visionary institutional funding</span> to sustain development. We are
                actively seeking <span className="text-devi-700 dark:text-devi-300 font-semibold">passionate scientists across all
                  disciplines—especially climatology and genetics—</span> willing to volunteer
                their deep expertise to architect a globally resilient tomorrow.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-3 w-full md:w-auto shrink-0 relative z-10">
              <a href="mailto:hello@bijmantra.org?subject=I want to volunteer scientific expertise to BijMantra"
                className="inline-flex h-11 items-center justify-center px-6 bg-devi-600 text-white hover:bg-devi-500 font-bold text-sm rounded-xl transition-colors shadow-lg shadow-devi-500/20 uppercase tracking-widest">
                <i className="ph-fill ph-hand-heart mr-2 text-lg"></i> Volunteer
              </a>
              <a href="mailto:hello@bijmantra.org?subject=Funding and Sponsorship Inquiry"
                className="inline-flex h-11 items-center justify-center px-6 bg-white dark:bg-white/5 text-samudra-900 dark:text-white border border-slate-200 dark:border-white/10 hover:bg-slate-50 dark:hover:bg-white/10 font-bold text-sm rounded-xl transition-colors backdrop-blur-md uppercase tracking-widest">
                Sponsor
              </a>
            </div>
          </div>
        </section>

        {/* Final CTA */}
        <section id="waitlist" className="w-full max-w-4xl mx-auto px-6 py-24 relative z-10 text-center">
          <div className="glass-panel p-10 md:p-16 rounded-[2.5rem] relative overflow-hidden border-slate-200 dark:border-white/5 bg-white/40 dark:bg-white/5 shadow-2xl">
            {/* Subtle internal glow */}
            <div
              className="absolute inset-x-0 bottom-0 h-px w-full bg-gradient-to-r from-transparent via-gold-500/50 to-transparent">
            </div>

            <i className="ph-fill ph-plant text-4xl text-devi-500/60 mb-6 inline-block"></i>
            <h2 className="font-heading font-bold text-3xl md:text-4xl text-samudra-900 dark:text-white mb-4">Ready to plant the seed?</h2>

            <p className="text-slate-600 dark:text-slate-400 max-w-lg mx-auto mb-8 text-sm md:text-base font-serif">We are currently in active development to
              bring you the first truly compatible, open-source breeding management platform.</p>

            <a href="https://app.bijmantra.org/login"
              className="inline-flex h-12 items-center justify-center px-8 mb-12 bg-devi-600 text-white hover:bg-devi-500 font-bold text-sm rounded-xl transition-colors shadow-xl shadow-devi-500/30 uppercase tracking-widest">
              Access Developer Sandbox
            </a>

            <div className="w-full h-px bg-slate-200 dark:bg-white/10 mb-12 max-w-md mx-auto"></div>

            <p className="text-slate-600 dark:text-slate-400 max-w-lg mx-auto mb-6 text-sm font-medium uppercase tracking-widest text-gold-600 dark:text-gold-400">Join the Newsletter</p>

            <form id="waitlist-form" action="https://formspree.io/f/xdaoowvj" method="POST"
              className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
              <div className="relative flex-1">
                <i className="ph ph-envelope-simple absolute left-4 top-1/2 -translate-y-1/2 text-slate-500"></i>
                <input
                  type="email"
                  name="email"
                  placeholder="name@organisation.com"
                  required
                  className="w-full h-12 pl-12 pr-4 bg-white/50 dark:bg-samudra-950/50 border border-slate-200 dark:border-white/10 rounded-xl focus:ring-2 focus:ring-devi-500 outline-none transition-all placeholder:text-slate-400 text-samudra-900 dark:text-white"
                />
              </div>
              <button type="submit"
                className="h-12 px-8 bg-samudra-900 dark:bg-white text-white dark:text-samudra-900 hover:bg-samudra-800 dark:hover:bg-slate-100 font-bold text-sm rounded-xl transition-colors shrink-0 uppercase tracking-widest">
                Join
              </button>
            </form>

            <p className="mt-4 text-[0.6rem] text-slate-500 uppercase tracking-tighter">I will notify you only for significant scientific milestones.</p>
          </div>
        </section>

        {/* Footer */}
        <footer className="w-full border-t border-slate-200 dark:border-white/5 bg-slate-50/50 dark:bg-transparent">
          <div className="max-w-7xl mx-auto px-6 py-12 flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 p-1 glass-panel rounded-lg shadow-sm border-slate-200 dark:border-white/10">
                <img src="/img/logo.png" alt="BijMantra Logo" />
              </div>
              <span className="font-heading font-semibold text-slate-500 text-sm tracking-wide">BijMantra</span>
            </div>

            <p className="text-slate-500 text-[0.7rem] text-center max-w-md font-serif italic">
              "Thank you to all those who work in acres, not in hours." <br />
              <span className="block mt-2 font-bold text-slate-400 not-italic">© 2026 BijMantra. Built for the next 1,000 years.</span>
            </p>

            <div className="flex items-center gap-6">
              <a href="https://github.com/denishdholaria/bijmantra" target="_blank" rel="noopener"
                className="text-slate-400 hover:text-brand-500 transition-colors" aria-label="GitHub">
                <i className="ph-fill ph-github-logo text-xl"></i>
              </a>
              <a href="mailto:hello@bijmantra.org" className="text-slate-400 hover:text-brand-500 transition-colors"
                aria-label="Email">
                <i className="ph-fill ph-envelope-simple text-xl"></i>
              </a>
            </div>
          </div>
        </footer>

      </div>

    </Layout>
  );
}
