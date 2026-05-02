import { motion } from 'framer-motion';
import { useOSStore } from './store';
import { REGISTERED_APPS } from '../registry/moduleRegistry';
import { Sprout, Sun, CloudRain, Wind, ArrowRight, Activity } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useState, useEffect } from 'react';

export function Sanctuary() {
  const { openApp } = useOSStore();
  const [greeting, setGreeting] = useState('');

  useEffect(() => {
    const hour = new Date().getHours();
    if (hour < 12) setGreeting('Good Morning');
    else if (hour < 18) setGreeting('Good Afternoon');
    else setGreeting('Good Evening');
  }, []);

  // Animation variants
  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    },
    exit: { opacity: 0, y: -20, filter: 'blur(10px)', transition: { duration: 0.4 } }
  };

  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 300, damping: 24 } }
  };

  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="show"
      exit="exit"
      className="h-full w-full max-w-7xl mx-auto px-6 pt-[15vh] pb-32 overflow-y-auto no-scrollbar"
    >
      {/* Header Section */}
      <motion.div variants={item} className="mb-16">
        <h1 className="text-4xl md:text-6xl font-light tracking-tight text-prakruti-dhool-900 dark:text-prakruti-patta-100 font-serif">
          {greeting}, <span className="text-prakruti-patta-600 dark:text-prakruti-patta-400">Breeder.</span>
        </h1>
        <p className="mt-4 text-xl text-prakruti-dhool-600 dark:text-prakruti-dhool-300 max-w-2xl font-light">
          The fields are responding well to yesterday's rain. <br className="hidden sm:block"/>
          You have <span className="font-medium text-prakruti-dhool-900 dark:text-white">3 trials</span> requiring attention today.
        </p>
      </motion.div>

      {/* Insight Cards (Simulated) */}
      <motion.div variants={item} className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
        <InsightCard
          icon={Sun}
          label="Field Conditions"
          value="Optimal"
          sub="Soil moisture at 65%"
          color="bg-amber-100/50 text-amber-700 dark:bg-amber-900/20 dark:text-amber-300"
        />
        <InsightCard
          icon={Activity}
          label="Trial Progress"
          value="On Track"
          sub="Wheat-2024-A · 85% Complete"
          color="bg-emerald-100/50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-300"
        />
        <InsightCard
            icon={Wind}
            label="Genomic Analysis"
            value="Processing"
            sub="Batch #992 · Est. 2h left"
            color="bg-blue-100/50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-300"
        />
      </motion.div>

      {/* App Capabilities List */}
      <motion.div variants={item} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-8">
        {REGISTERED_APPS.map((app) => (
            <div
                key={app.id}
                onClick={() => openApp(app.id)}
                className="group cursor-pointer"
            >
                <div className="flex items-center gap-4 mb-3">
                    <div className={cn(
                        "p-3 rounded-2xl bg-white/50 dark:bg-white/5 backdrop-blur-sm border border-black/5 dark:border-white/5",
                        "group-hover:bg-prakruti-patta-50 dark:group-hover:bg-prakruti-patta-900/30 group-hover:scale-110 transition-all duration-300"
                    )}>
                        <app.icon className="w-6 h-6 text-prakruti-dhool-700 dark:text-prakruti-dhool-200 group-hover:text-prakruti-patta-600 dark:group-hover:text-prakruti-patta-400 stroke-[1.5]" />
                    </div>
                    <span className="text-lg font-medium text-prakruti-dhool-800 dark:text-prakruti-dhool-100 group-hover:translate-x-1 transition-transform">
                        {app.title}
                    </span>
                    <ArrowRight className="w-4 h-4 text-black/0 group-hover:text-prakruti-patta-500 -ml-2 group-hover:ml-0 opacity-0 group-hover:opacity-100 transition-all" />
                </div>
                <p className="text-sm text-prakruti-dhool-500 dark:text-prakruti-dhool-400 pl-[4.25rem] border-l border-black/5 dark:border-white/5">
                    {app.subtitle}
                </p>
            </div>
        ))}
      </motion.div>
    </motion.div>
  );
}

function InsightCard({ icon: Icon, label, value, sub, color }: any) {
    return (
        <div className="flex items-start gap-4 p-5 rounded-3xl bg-white/40 dark:bg-black/20 border border-white/20 dark:border-white/5 backdrop-blur-md hover:bg-white/60 dark:hover:bg-white/5 transition-colors cursor-default">
            <div className={cn("p-2.5 rounded-xl", color)}>
                <Icon className="w-5 h-5" />
            </div>
            <div>
                <p className="text-sm font-medium text-prakruti-dhool-500 dark:text-prakruti-dhool-400 mb-0.5">{label}</p>
                <p className="text-xl font-semibold text-prakruti-dhool-900 dark:text-prakruti-dhool-100 mb-1">{value}</p>
                <p className="text-xs text-prakruti-dhool-400 dark:text-prakruti-dhool-500">{sub}</p>
            </div>
        </div>
    )
}
