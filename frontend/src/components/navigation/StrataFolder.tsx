import { useRef, useEffect } from "react";
import { motion, Variants } from "framer-motion";
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

const containerVariants: Variants = {
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

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 10 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { type: "spring" as const, stiffness: 300, damping: 24 },
  },
} as any;

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
        "flex flex-col h-full bg-background",
        className,
      )}
    >
      {/* Header */}
      <div className="flex-none p-6 pb-2">
        {!isRoot && onBack && (
          <button
            onClick={onBack}
            className="group flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground mb-4 transition-colors"
          >
            <div className="p-1 rounded-full bg-muted/50 group-hover:bg-muted transition-colors">
              <ArrowLeft className="w-4 h-4" />
            </div>
            <span>Back</span>
          </button>
        )}

        <div className="flex items-start gap-4">
          {TitleIcon && (
            <div className="p-3 rounded-2xl bg-card shadow-sm ring-1 ring-border">
              <TitleIcon className="w-8 h-8 text-primary" />
            </div>
          )}
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-foreground">
              {title}
            </h2>
            {description && (
              <p className="text-sm text-muted-foreground mt-1">
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
                  "bg-card/40 hover:bg-card",
                  "border border-border/50 hover:border-primary/20",
                  "transition-all duration-200 shadow-sm hover:shadow-md hover:-translate-y-0.5",
                  "outline-none focus-visible:ring-2 focus-visible:ring-primary",
                )}
              >
                <div className="flex items-start justify-between w-full mb-3">
                  <div
                    className={cn(
                      "p-2.5 rounded-xl transition-colors",
                      item.type === "folder"
                        ? "bg-blue-100 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 group-hover:bg-blue-200 dark:group-hover:bg-blue-900/30"
                        : "bg-prakruti-patta-pale dark:bg-prakruti-patta/20 text-prakruti-patta dark:text-prakruti-patta-light group-hover:bg-prakruti-patta-100 dark:group-hover:bg-prakruti-patta/30",
                    )}
                  >
                    <ItemIcon className="w-6 h-6" />
                  </div>
                  {item.type === "folder" && (
                    <ChevronRight className="w-4 h-4 text-muted-foreground group-hover:text-foreground transition-transform group-hover:translate-x-0.5" />
                  )}
                </div>

                <div className="space-y-1">
                  <div className="font-semibold text-foreground group-hover:text-primary transition-colors">
                    {item.label}
                  </div>
                  {item.description && (
                    <div className="text-xs text-muted-foreground line-clamp-2">
                      {item.description}
                    </div>
                  )}
                </div>

                {item.badge && (
                  <div
                    className={cn(
                      "absolute top-3 right-3 px-1.5 py-0.5 text-[10px] font-medium rounded-full",
                      item.badgeColor ||
                      "bg-muted text-muted-foreground",
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
