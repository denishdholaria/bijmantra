/**
 * LoginForm Component
 * 
 * Inspirational multilingual login experience featuring wisdom from
 * agricultural cultures worldwide, displayed in their original languages
 * with English translations.
 * 
 * "One Seed. Infinite Worlds."
 */

import { ArrowRight, Eye, EyeOff, LockKeyhole, Mail, Orbit, Play, ShieldCheck, Sprout, Volume2, VolumeX } from 'lucide-react'
import { useAuth } from './useAuth'
import { quotes, regionColors } from './quotes'
import type { PlatformSignal, TrustMarker } from './types'

function formatRegionLabel(region: string) {
  return region
    .split('-')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

export function LoginForm() {
  const auth = useAuth()

  const quote = quotes[auth.currentQuote]
  const regionColor = regionColors[quote.region] || regionColors['global']
  const regionLabel = formatRegionLabel(quote.region)
  const activeThoughtLensLabel = auth.inferredThoughtRegion
    ? formatRegionLabel(auth.inferredThoughtRegion)
    : 'Worldwide'

  const arrivalToneStatus = !auth.isStartupAudioAvailable
    ? 'Tone unavailable in this browser.'
    : auth.isStartupAudioPlaying
      ? 'Playing after successful sign-in.'
      : auth.isStartupAudioEnabled
        ? auth.hasPlayedStartupAudio
          ? 'Played after sign-in. Replay any time.'
          : 'Plays after a successful sign-in.'
        : auth.isStartupAudioQuietByDefault
          ? 'Quiet by default on Data Saver.'
          : 'Muted on this browser.'

  const arrivalToneBadgeLabel = !auth.isStartupAudioAvailable
    ? 'Unavailable'
    : auth.isStartupAudioPlaying
      ? 'Playing'
      : auth.isStartupAudioEnabled
        ? auth.hasPlayedStartupAudio
          ? 'Played'
          : 'Ready'
        : auth.isStartupAudioQuietByDefault
          ? 'Quiet'
          : 'Muted'

  const arrivalToneBadgeClass = !auth.isStartupAudioAvailable
    ? 'border-slate-300/80 bg-slate-100 text-slate-600 dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-300'
    : auth.isStartupAudioPlaying
      ? 'border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-200'
      : auth.isStartupAudioEnabled
        ? 'border-cyan-200 bg-cyan-50 text-cyan-800 dark:border-cyan-500/20 dark:bg-cyan-500/10 dark:text-cyan-200'
        : 'border-slate-300/80 bg-slate-100 text-slate-600 dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-300'

  const arrivalToneVisualizerClass = auth.isStartupAudioPlaying
    ? 'border-emerald-200/90 bg-emerald-50/95 shadow-[0_0_0_6px_rgba(16,185,129,0.06)] dark:border-emerald-500/20 dark:bg-emerald-500/10'
    : auth.isStartupAudioEnabled
      ? 'border-cyan-200/80 bg-cyan-50/90 dark:border-cyan-500/20 dark:bg-cyan-500/10'
      : 'border-slate-200/80 bg-white/75 dark:border-white/10 dark:bg-white/5'

  const arrivalToneBarClass = auth.isStartupAudioPlaying
    ? 'bg-emerald-500 dark:bg-emerald-300'
    : auth.isStartupAudioEnabled
      ? 'bg-cyan-500/75 dark:bg-cyan-300/80'
      : 'bg-slate-300 dark:bg-slate-600'

  const arrivalToneToggleLabel = `Arrival tone ${auth.isStartupAudioEnabled ? 'on' : 'off'}`
  const replayToneLabel = auth.hasPlayedStartupAudio ? 'Replay arrival tone' : 'Preview arrival tone'

  const platformSignals: PlatformSignal[] = [
    {
      label: 'Wisdom',
      value: 'Civilizational memory',
      accent: 'from-prakruti-sona/25 to-amber-500/15',
    },
    {
      label: 'Impact',
      value: 'Food, climate, livelihoods',
      accent: 'from-prakruti-neela/25 to-cyan-500/15',
    },
    {
      label: 'Interop',
      value: 'BrAPI compatible',
      accent: 'from-prakruti-patta/25 to-emerald-500/15',
    },
  ]

  const trustMarkers: TrustMarker[] = [
    {
      icon: ShieldCheck,
      title: 'Sovereignty first',
      detail: 'External exchange is explicit and intentional, not ambient.',
    },
    {
      icon: Orbit,
      title: 'Cross-domain by design',
      detail: 'Genetics, agronomy, climate, soil, and economics stay connected.',
    },
    {
      icon: Sprout,
      title: 'Built for living agriculture',
      detail: 'Research, seed work, and field operations share the same surface.',
    },
  ]

  return (
    <div className="relative min-h-screen overflow-hidden bg-[radial-gradient(circle_at_top_left,rgba(245,215,66,0.18),transparent_26%),radial-gradient(circle_at_bottom_right,rgba(45,90,39,0.16),transparent_30%),linear-gradient(180deg,#f8f5ee_0%,#f1ede2_48%,#edf3ea_100%)] dark:bg-[radial-gradient(circle_at_top_left,rgba(212,160,18,0.14),transparent_24%),radial-gradient(circle_at_bottom_right,rgba(45,90,39,0.14),transparent_28%),linear-gradient(180deg,#07130e_0%,#0f1714_44%,#101923_100%)]">
      <div className="pointer-events-none absolute inset-0 opacity-40 dark:opacity-20">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.35)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.35)_1px,transparent_1px)] [background-size:72px_72px] dark:bg-[linear-gradient(to_right,rgba(255,255,255,0.06)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.06)_1px,transparent_1px)]" />
      </div>
      <div className="pointer-events-none absolute left-1/2 top-0 h-[420px] w-[420px] -translate-x-1/2 rounded-full bg-prakruti-sona/10 blur-[140px] dark:bg-prakruti-sona/10" />
      <div className="relative mx-auto flex min-h-screen max-w-[1600px] items-stretch px-4 py-4 sm:px-6 lg:px-8 lg:py-8">
        <div className="grid w-full overflow-hidden rounded-[32px] border border-black/5 bg-white/55 shadow-[0_30px_120px_rgba(40,33,18,0.16)] backdrop-blur-xl dark:border-white/10 dark:bg-slate-950/55 lg:grid-cols-[minmax(0,1.18fr)_minmax(420px,0.82fr)]">

          {/* Desktop Quote Panel */}
          <div
            className="relative hidden overflow-hidden text-white lg:flex"
            onMouseEnter={auth.pauseAutoRotation}
            onMouseLeave={auth.resumeAutoRotation}
            onFocusCapture={auth.pauseAutoRotation}
            onBlurCapture={auth.handleQuoteSurfaceBlur}
          >
            <div className="absolute inset-0 bg-[linear-gradient(135deg,#082319_0%,#0b3a2d_38%,#15483a_62%,#1f2d22_100%)]" />
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_16%_18%,rgba(245,215,66,0.18),transparent_22%),radial-gradient(circle_at_84%_82%,rgba(59,138,196,0.16),transparent_26%)]" />
            <div className="absolute inset-0 opacity-[0.08] [background-image:radial-gradient(circle_at_center,white_1px,transparent_1px)] [background-size:24px_24px]" />
            <div className={`absolute -left-20 top-16 h-80 w-80 rounded-full bg-gradient-to-br ${regionColor} blur-3xl transition-colors duration-1000`} />
            <div className="absolute bottom-[-10%] right-[-6%] h-[28rem] w-[28rem] rounded-full bg-gradient-to-br from-prakruti-neela/20 to-transparent blur-3xl" />
            <div className="absolute inset-y-10 right-12 w-px bg-gradient-to-b from-transparent via-white/25 to-transparent" />

            <div className="relative z-10 flex w-full flex-col justify-between p-10 xl:p-14">
              <div className="space-y-10">
                <div className="flex items-start justify-between gap-6">
                  <div className="flex items-center gap-4">
                    <div className="flex h-16 w-16 items-center justify-center rounded-[22px] border border-white/15 bg-white/10 p-3 shadow-2xl backdrop-blur-md">
                      <img src="/icons/icon-192x192.png" alt="Bijmantra" className="h-full w-full object-contain drop-shadow-md" />
                    </div>
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-[0.35em] text-emerald-100/70">BijMantra</p>
                      <p className="mt-2 text-sm text-emerald-50/72">One Seed. Infinite Worlds.</p>
                    </div>
                  </div>
                  <div className="rounded-full border border-white/12 bg-white/8 px-5 py-3 text-right shadow-lg backdrop-blur-md">
                    <p className="text-[10px] uppercase tracking-[0.3em] text-emerald-100/55">Thought Lens</p>
                    <p className="mt-1 text-sm font-semibold text-white">{activeThoughtLensLabel}</p>
                  </div>
                </div>

                <div className="max-w-3xl space-y-6">
                  <div className="inline-flex items-center gap-2 rounded-full border border-white/12 bg-white/8 px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.28em] text-emerald-100/78 backdrop-blur-sm">
                    Cross-domain agricultural intelligence
                  </div>
                  <div className="space-y-4">
                    <h1 className="max-w-3xl text-5xl font-bold leading-[0.92] tracking-[-0.04em] text-white xl:text-6xl [font-family:'Space_Grotesk',var(--prakruti-font-display)]">
                      Every agricultural decision carries soil, climate, genetic, and market consequences.
                    </h1>
                    <p className="max-w-2xl text-base leading-7 text-emerald-50/74 xl:text-lg">
                      BijMantra brings breeding, seed systems, climate, soil, and economic context into one operating surface while keeping agricultural wisdom visibly human.
                    </p>
                  </div>
                </div>

                <div className="flex flex-wrap gap-3">
                  {platformSignals.map((signal) => (
                    <div
                      key={signal.label}
                      className="min-w-[180px] flex-1 rounded-[20px] border border-white/10 bg-white/7 px-4 py-3 shadow-lg backdrop-blur-md"
                    >
                      <div className={`mb-3 h-1 rounded-full bg-gradient-to-r ${signal.accent}`} />
                      <p className="text-[10px] uppercase tracking-[0.28em] text-emerald-100/55">{signal.label}</p>
                      <p className="mt-2 text-sm font-semibold leading-6 text-white">{signal.value}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="my-10 flex-1">
                <div
                  className={`rounded-[30px] border border-white/12 bg-white/8 p-8 shadow-[0_30px_80px_rgba(0,0,0,0.22)] backdrop-blur-xl transition-all duration-700 ease-out xl:p-10 ${
                    auth.isQuoteFading ? 'translate-y-8 opacity-0 blur-sm' : 'translate-y-0 opacity-100 blur-0'
                  }`}
                >
                  <div className="flex items-start justify-between gap-6">
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-[0.32em] text-emerald-100/60">Thought For This Moment</p>
                      <p className="mt-2 text-sm text-emerald-100/65">{regionLabel} • {quote.culture}</p>
                    </div>
                    <span className="text-5xl drop-shadow-2xl xl:text-6xl">{quote.icon}</span>
                  </div>

                  <blockquote className="mt-10 max-w-3xl text-3xl font-medium leading-[1.15] text-white xl:text-[3.25rem] font-serif">
                    "{quote.original}"
                  </blockquote>

                  <p className="mt-6 max-w-2xl text-lg italic leading-8 text-emerald-50/84 xl:text-xl">
                    {quote.translation}
                  </p>

                  <div className="mt-8 flex flex-wrap items-center gap-3 text-sm text-emerald-50/80">
                    <span className="rounded-full border border-white/15 bg-white/10 px-4 py-1.5 font-medium text-white">
                      {quote.culture}
                    </span>
                    <span className="text-emerald-100/70">{quote.source}</span>
                  </div>
                </div>
              </div>

              <div className="space-y-6">
                <div className="flex items-center justify-between gap-4 rounded-[28px] border border-white/12 bg-black/10 px-5 py-4 shadow-lg backdrop-blur-md">
                  <div>
                    <p className="text-[10px] uppercase tracking-[0.28em] text-emerald-100/50">Now</p>
                    <p className="mt-2 text-sm font-medium text-emerald-50/82">{auth.currentQuote + 1} of {quotes.length}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      onClick={auth.handlePreviousQuote}
                      disabled={auth.pastQuotes.length === 0}
                      className="rounded-full border border-white/12 bg-white/8 px-5 py-2.5 text-sm font-medium text-white transition-all hover:bg-white/14 disabled:cursor-not-allowed disabled:opacity-30"
                    >
                      Previous
                    </button>
                    <button
                      type="button"
                      onClick={auth.handleNextQuote}
                      className="rounded-full border border-emerald-100/80 bg-emerald-50 px-5 py-2.5 text-sm font-semibold text-emerald-950 shadow-[0_12px_28px_rgba(255,255,255,0.12)] transition-all hover:bg-white dark:border-emerald-100/80 dark:bg-emerald-50 dark:text-emerald-950"
                    >
                      Next
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Form Section */}
          <div className="relative flex items-center justify-center px-6 py-8 sm:px-8 lg:px-10 xl:px-14">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,255,255,0.72),transparent_28%),radial-gradient(circle_at_bottom_left,rgba(212,160,18,0.14),transparent_24%)] dark:bg-[radial-gradient(circle_at_top_right,rgba(255,255,255,0.08),transparent_24%),radial-gradient(circle_at_bottom_left,rgba(212,160,18,0.08),transparent_24%)]" />
            <div className="absolute inset-0 opacity-50 [background-image:radial-gradient(circle_at_center,rgba(15,23,42,0.08)_1px,transparent_1px)] [background-size:18px_18px] dark:opacity-15" />

            <div className="relative z-10 w-full max-w-[540px]">
              {/* Mobile Header */}
              <div className="lg:hidden mb-8 text-center">
                <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-[26px] bg-gradient-to-br from-emerald-950 to-emerald-800 p-4 shadow-[0_18px_60px_rgba(8,35,25,0.35)]">
                  <img src="/icons/icon-192x192.png" alt="Bijmantra" className="h-full w-full object-contain drop-shadow-md" />
                </div>
                <p className="mt-5 text-[11px] font-semibold uppercase tracking-[0.35em] text-slate-500 dark:text-slate-400">BijMantra</p>
                <h1 className="mt-3 text-4xl font-bold tracking-[-0.04em] text-slate-950 dark:text-white [font-family:'Space_Grotesk',var(--prakruti-font-display)]">
                  Enter the agricultural intelligence workspace.
                </h1>
                <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  Cross-domain research and operational context, shaped for seed, climate, and field work.
                </p>
              </div>

              {/* Mobile Quote Card */}
              <div
                className="lg:hidden mb-8 overflow-hidden rounded-[28px] border border-emerald-950/10 bg-emerald-950 text-white shadow-[0_24px_60px_rgba(8,35,25,0.28)]"
                onFocusCapture={auth.pauseAutoRotation}
                onBlurCapture={auth.handleQuoteSurfaceBlur}
              >
                <div className={`bg-gradient-to-br ${regionColor} p-[1px]`}>
                  <div className="bg-[linear-gradient(135deg,#082319_0%,#0b3a2d_46%,#1f2d22_100%)] px-5 py-6">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-emerald-100/60">Thought For This Moment</p>
                        <p className="mt-2 text-xs text-emerald-100/72">{activeThoughtLensLabel}</p>
                      </div>
                      <span className="text-4xl leading-none">{quote.icon}</span>
                    </div>

                    <blockquote className="mt-6 text-2xl font-medium leading-snug text-white font-serif">
                      "{quote.original}"
                    </blockquote>

                    <p className="mt-4 text-sm italic leading-7 text-emerald-50/84">
                      {quote.translation}
                    </p>

                    <div className="mt-5 flex flex-wrap items-center gap-2 text-xs text-emerald-50/78">
                      <span className="rounded-full border border-white/15 bg-white/10 px-3 py-1 text-white">
                        {quote.culture}
                      </span>
                      <span>{quote.source}</span>
                    </div>

                    <div className="mt-6 flex items-center justify-between border-t border-white/10 pt-4">
                      <button
                        type="button"
                        onClick={auth.handlePreviousQuote}
                        disabled={auth.pastQuotes.length === 0}
                        className="rounded-full border border-white/15 bg-white/5 px-4 py-2 text-sm font-medium text-white transition-all hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-30"
                      >
                        Previous
                      </button>
                      <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-emerald-100/58">
                        {auth.currentQuote + 1} / {quotes.length}
                      </p>
                      <button
                        type="button"
                        onClick={auth.handleNextQuote}
                        className="rounded-full border border-emerald-100/80 bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-950 shadow-sm transition-all hover:bg-white dark:border-emerald-100/80 dark:bg-emerald-50 dark:text-emerald-950"
                      >
                        Next
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Login Form Card */}
              <div className="rounded-[32px] border border-white/70 bg-white/82 p-6 shadow-[0_24px_80px_rgba(15,23,42,0.12)] backdrop-blur-xl dark:border-white/10 dark:bg-slate-900/78 sm:p-8">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.3em] text-slate-500 dark:text-slate-400">Welcome Back</p>
                    <h2 className="mt-3 text-3xl font-bold tracking-[-0.04em] text-slate-950 dark:text-white [font-family:'Space_Grotesk',var(--prakruti-font-display)]">
                      Enter your workspace.
                    </h2>
                    <p className="mt-3 max-w-md text-sm leading-6 text-slate-600 dark:text-slate-300">Sign in to continue.</p>
                  </div>
                  <div className="hidden rounded-full border border-emerald-200/70 bg-emerald-50/90 px-4 py-2 text-right shadow-sm dark:border-emerald-500/20 dark:bg-emerald-500/10 sm:block">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-emerald-700 dark:text-emerald-300">Preview</p>
                  </div>
                </div>

                {auth.error && (
                  <div className="mt-8 rounded-[22px] border border-red-200/70 bg-red-50/90 px-4 py-4 shadow-sm dark:border-red-500/20 dark:bg-red-500/10">
                    <div className="flex items-start gap-3">
                      <span className="mt-0.5 text-lg text-red-600 dark:text-red-300">⚠️</span>
                      <div>
                        <p className="text-[11px] font-semibold uppercase tracking-[0.25em] text-red-700 dark:text-red-300">Authentication issue</p>
                        <p className="mt-2 text-sm leading-6 text-red-700 dark:text-red-200">{auth.error}</p>
                      </div>
                    </div>
                  </div>
                )}

                <form onSubmit={auth.handleSubmit} className="mt-8 space-y-5" autoComplete="on">
                  <div className="space-y-2">
                    <label htmlFor="email" className="ml-1 block text-[11px] font-semibold uppercase tracking-[0.26em] text-slate-500 dark:text-slate-400">
                      Email Address
                    </label>
                    <div className="group relative">
                      <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 transition-colors group-focus-within:text-emerald-600 dark:group-focus-within:text-emerald-300">
                        <Mail className="h-4 w-4" />
                      </span>
                      <input
                        id="email"
                        type="email"
                        value={auth.email}
                        onChange={(e) => auth.setEmail(e.target.value)}
                        required
                        autoComplete="email"
                        className="w-full rounded-[22px] border border-slate-200/80 bg-white/90 py-4 pl-12 pr-4 text-slate-950 shadow-sm transition-all placeholder:text-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-4 focus:ring-emerald-500/10 dark:border-white/10 dark:bg-slate-950/60 dark:text-white dark:placeholder:text-slate-500"
                        placeholder="breeder@example.com"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label htmlFor="password" className="ml-1 block text-[11px] font-semibold uppercase tracking-[0.26em] text-slate-500 dark:text-slate-400">
                      Password
                    </label>
                    <div className="group relative">
                      <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 transition-colors group-focus-within:text-emerald-600 dark:group-focus-within:text-emerald-300">
                        <LockKeyhole className="h-4 w-4" />
                      </span>
                      <input
                        id="password"
                        type={auth.showPassword ? 'text' : 'password'}
                        value={auth.password}
                        onChange={(e) => auth.setPassword(e.target.value)}
                        required
                        autoComplete="current-password"
                        className="w-full rounded-[22px] border border-slate-200/80 bg-white/90 py-4 pl-12 pr-12 text-slate-950 shadow-sm transition-all placeholder:text-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-4 focus:ring-emerald-500/10 dark:border-white/10 dark:bg-slate-950/60 dark:text-white dark:placeholder:text-slate-500"
                        placeholder="••••••••"
                      />
                      <button
                        type="button"
                        onClick={() => auth.setShowPassword(!auth.showPassword)}
                        className="absolute right-4 top-1/2 -translate-y-1/2 rounded-full p-1 text-slate-400 transition-colors hover:text-slate-700 dark:hover:text-slate-200"
                        aria-label={auth.showPassword ? 'Hide password' : 'Show password'}
                      >
                        {auth.showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={auth.isLoading}
                    className="group w-full rounded-[22px] bg-[linear-gradient(135deg,#124c38_0%,#1f6f52_52%,#d4a012_140%)] px-6 py-4 text-base font-semibold text-white shadow-[0_16px_36px_rgba(18,76,56,0.28)] transition-all hover:-translate-y-0.5 hover:shadow-[0_22px_40px_rgba(18,76,56,0.32)] disabled:translate-y-0 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {auth.isLoading ? (
                      <span className="flex items-center justify-center gap-3">
                        <svg className="h-5 w-5 animate-spin" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                        Signing in...
                      </span>
                    ) : (
                      <span className="flex items-center justify-center gap-2">
                        Enter BijMantra
                        <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                      </span>
                    )}
                  </button>
                </form>

                {/* Demo Credentials */}
                <div className="mt-6 rounded-[26px] border border-amber-200/60 bg-[linear-gradient(135deg,rgba(255,251,235,0.88)_0%,rgba(255,255,255,0.96)_100%)] p-4 shadow-sm dark:border-amber-500/20 dark:bg-[linear-gradient(135deg,rgba(120,53,15,0.16)_0%,rgba(113,63,18,0.06)_100%)]">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-[0.26em] text-amber-800 dark:text-amber-200">Demo Organization</p>
                      <p className="mt-2 text-sm font-medium text-amber-950 dark:text-amber-100">Try the sandbox workspace.</p>
                      <p className="mt-1 text-xs leading-5 text-amber-700 dark:text-amber-200/70">Demo credentials for a quick look around.</p>
                    </div>
                    <button
                      type="button"
                      onClick={auth.handleDemoCredentials}
                      className="shrink-0 rounded-full border border-amber-300 bg-white/70 px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-amber-900 transition-colors hover:bg-white dark:border-amber-400/20 dark:bg-amber-100/10 dark:text-amber-100 dark:hover:bg-amber-100/15"
                    >
                      Use Demo
                    </button>
                  </div>
                </div>

                {/* Trust Markers */}
                <div className="mt-6 space-y-3">
                  {trustMarkers.map(({ icon: Icon, title, detail }) => (
                    <div
                      key={title}
                      className="flex items-start gap-4 rounded-[22px] border border-slate-200/70 bg-slate-50/90 p-4 shadow-sm dark:border-white/10 dark:bg-slate-950/45"
                    >
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300">
                        <Icon className="h-4 w-4" />
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-slate-900 dark:text-white">{title}</p>
                        <p className="mt-1 text-xs leading-5 text-slate-600 dark:text-slate-300">{detail}</p>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Audio Controls */}
                <div className="mt-6 flex items-center justify-between gap-3 rounded-[20px] border border-slate-200/70 bg-[linear-gradient(135deg,rgba(248,250,252,0.88)_0%,rgba(255,255,255,0.66)_100%)] px-4 py-3 shadow-sm dark:border-white/10 dark:bg-[linear-gradient(135deg,rgba(15,23,42,0.32)_0%,rgba(15,23,42,0.18)_100%)]">
                  <div className="flex min-w-0 items-center gap-3">
                    <div className={`flex h-10 w-10 items-end justify-center gap-1 rounded-2xl border px-2 pb-2 pt-1 transition-all ${arrivalToneVisualizerClass}`}>
                      {['h-2.5', 'h-4', 'h-3'].map((barClass) => (
                        <span
                          key={barClass}
                          className={`w-1 rounded-full transition-colors duration-500 ${barClass} ${arrivalToneBarClass}`}
                        />
                      ))}
                    </div>
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="text-[10px] font-semibold uppercase tracking-[0.26em] text-slate-500 dark:text-slate-400">Arrival Tone</p>
                        <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[9px] font-semibold uppercase tracking-[0.18em] ${arrivalToneBadgeClass}`}>
                          {arrivalToneBadgeLabel}
                        </span>
                      </div>
                      <p aria-live="polite" className="mt-1 truncate text-xs leading-5 text-slate-600 dark:text-slate-300">{arrivalToneStatus}</p>
                    </div>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <button
                      type="button"
                      onClick={auth.handleStartupAudioToggle}
                      className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 bg-white/85 text-slate-700 transition-colors hover:bg-white dark:border-white/10 dark:bg-white/5 dark:text-slate-200 dark:hover:bg-white/10"
                      aria-label={arrivalToneToggleLabel}
                      title={auth.isStartupAudioEnabled ? 'Mute arrival tone' : 'Enable arrival tone'}
                    >
                      {auth.isStartupAudioEnabled ? <Volume2 className="h-4 w-4" /> : <VolumeX className="h-4 w-4" />}
                    </button>
                    <button
                      type="button"
                      onClick={() => auth.playStartupAudio(true, false)}
                      disabled={!auth.isStartupAudioEnabled || !auth.isStartupAudioAvailable}
                      className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-emerald-200/80 bg-emerald-50/90 text-emerald-800 transition-colors hover:bg-emerald-100 disabled:cursor-not-allowed disabled:opacity-40 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-200 dark:hover:bg-emerald-500/15"
                      aria-label={replayToneLabel}
                      title={replayToneLabel}
                    >
                      <Play className="ml-0.5 h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>

                {/* Footer Badges */}
                <div className="mt-8 flex flex-wrap items-center justify-between gap-3 border-t border-slate-200/70 pt-5 text-xs text-slate-500 dark:border-white/10 dark:text-slate-400">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-full border border-slate-200 bg-white/80 px-3 py-1 dark:border-white/10 dark:bg-white/5">Secure</span>
                    <span className="rounded-full border border-slate-200 bg-white/80 px-3 py-1 dark:border-white/10 dark:bg-white/5">PWA</span>
                    <span className="rounded-full border border-slate-200 bg-white/80 px-3 py-1 dark:border-white/10 dark:bg-white/5">BrAPI</span>
                  </div>
                  <p className="text-[11px] uppercase tracking-[0.2em]">Preview</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
