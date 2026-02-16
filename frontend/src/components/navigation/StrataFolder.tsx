import { useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { LucideIcon, ArrowLeft, ChevronRight, Folder } from "lucide-react";
import { cn } from "@/lib/utils";

export interface StrataItem {
  id: string;
  label: string;
  icon?: LucideIcon;
  type: "folder" | "link";
  path?: string;
  description?: string;
  // Optional badge or status for items
  badge?: string;
  badgeColor?: string;
}

interface StrataFolderProps {
  title: string;
  icon?: LucideIcon;
  description?: string;
  items: StrataItem[];
  onItemClick: (item: StrataItem) => void;
  onBack?: () => void;
  isRoot?: boolean;
  className?: string;
}

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
    },
  },
  exit: {
    opacity: 0,
    transition: {
      duration: 0.2,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { type: "spring", stiffness: 300, damping: 24 },
  },
};

export function StrataFolder({
  title,
  icon: TitleIcon,
  description,
  items,
  onItemClick,
  onBack,
  isRoot = false,
  className,
}: StrataFolderProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  // Scroll to top on mount (when navigating into a new folder)
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = 0;
    }
  }, [items]);

  return (
    <div
      className={cn(
        "flex flex-col h-full bg-slate-50/50 dark:bg-slate-900/50",
        className,
      )}
    >
      {/* Header */}
      <div className="flex-none p-6 pb-2">
        {!isRoot && onBack && (
          <button
            onClick={onBack}
            className="group flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-slate-900 dark:hover:text-slate-100 mb-4 transition-colors"
          >
            <div className="p-1 rounded-full bg-slate-200/50 dark:bg-slate-800/50 group-hover:bg-slate-300 dark:group-hover:bg-slate-700 transition-colors">
              <ArrowLeft className="w-4 h-4" />
            </div>
            <span>Back</span>
          </button>
        )}

        <div className="flex items-start gap-4">
          {TitleIcon && (
            <div className="p-3 rounded-2xl bg-white dark:bg-slate-800 shadow-sm ring-1 ring-slate-900/5 dark:ring-slate-100/10">
              <TitleIcon className="w-8 h-8 text-primary" />
            </div>
          )}
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              {title}
            </h2>
            {description && (
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                {description}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Grid Content */}
      <motion.div
        ref={containerRef}
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        exit="exit"
        className="flex-1 overflow-y-auto p-6 pt-4"
      >
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          {items.map((item) => {
            const ItemIcon = item.icon || Folder;

            return (
              <motion.button
                key={item.id}
                variants={itemVariants}
                onClick={() => onItemClick(item)}
                className={cn(
                  "group relative flex flex-col items-start text-left p-4 rounded-xl",
                  "bg-white/40 dark:bg-slate-800/40 hover:bg-white dark:hover:bg-slate-800",
                  "border border-slate-200/50 dark:border-slate-700/50 hover:border-primary/20 dark:hover:border-primary/30",
                  "transition-all duration-200 shadow-sm hover:shadow-md hover:-translate-y-0.5",
                  "outline-none focus-visible:ring-2 focus-visible:ring-primary",
                )}
              >
                <div className="flex items-start justify-between w-full mb-3">
                  <div
                    className={cn(
                      "p-2.5 rounded-xl transition-colors",
                      item.type === "folder"
                        ? "bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400 group-hover:bg-blue-100 dark:group-hover:bg-blue-900/30"
                        : "bg-emerald-50 text-emerald-600 dark:bg-emerald-900/20 dark:text-emerald-400 group-hover:bg-emerald-100 dark:group-hover:bg-emerald-900/30",
                    )}
                  >
                    <ItemIcon className="w-6 h-6" />
                  </div>
                  {item.type === "folder" && (
                    <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-slate-600 dark:group-hover:text-slate-300 transition-transform group-hover:translate-x-0.5" />
                  )}
                </div>

                <div className="space-y-1">
                  <div className="font-semibold text-slate-900 dark:text-slate-100 group-hover:text-primary transition-colors">
                    {item.label}
                  </div>
                  {item.description && (
                    <div className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2">
                      {item.description}
                    </div>
                  )}
                </div>

                {item.badge && (
                  <div
                    className={cn(
                      "absolute top-3 right-3 px-1.5 py-0.5 text-[10px] font-medium rounded-full",
                      item.badgeColor ||
                        "bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300",
                    )}
                  >
                    {item.badge}
                  </div>
                )}
              </motion.button>
            );
          })}
        </div>
      </motion.div>
    </div>
  );
}
