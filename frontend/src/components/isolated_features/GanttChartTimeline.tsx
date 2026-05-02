import React, { useMemo } from 'react';
import {
  format,
  eachMonthOfInterval,
  differenceInDays,
  startOfMonth,
  endOfMonth,
  isWithinInterval,
  startOfDay
} from 'date-fns';
import {
  Milestone,
  Info,
  Sprout,
  Search,
  CheckCircle,
  Leaf,
  Sparkles
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

/**
 * GanttChartTimeline component for Breeding Cycle Planning.
 * Isolated component for visualizing breeding stages and milestones over time.
 */

export interface GanttTask {
  id: string;
  name: string;
  start: Date;
  end: Date;
  status: 'planned' | 'in-progress' | 'completed' | 'delayed';
  progress: number;
  assignee?: string;
  type?: string;
}

export interface GanttMilestone {
  id: string;
  name: string;
  date: Date;
  type: 'harvest' | 'planting' | 'evaluation' | 'selection' | 'default';
}

export interface GanttChartTimelineProps {
  tasks: GanttTask[];
  milestones?: GanttMilestone[];
  startDate: Date;
  endDate: Date;
  className?: string;
}

const statusColors = {
  planned: 'bg-blue-100 border-blue-300 text-blue-700 dark:bg-blue-900/30 dark:border-blue-800 dark:text-blue-400',
  'in-progress': 'bg-green-100 border-green-300 text-green-700 dark:bg-green-900/30 dark:border-green-800 dark:text-green-400',
  completed: 'bg-gray-100 border-gray-300 text-gray-700 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-400',
  delayed: 'bg-red-100 border-red-300 text-red-700 dark:bg-red-900/30 dark:border-red-800 dark:text-red-400',
};

const milestoneIcons: Record<string, React.ReactNode> = {
  harvest: <Leaf className="w-3 h-3 -rotate-45" />,
  planting: <Sprout className="w-3 h-3 -rotate-45" />,
  evaluation: <Search className="w-3 h-3 -rotate-45" />,
  selection: <CheckCircle className="w-3 h-3 -rotate-45" />,
  default: <Milestone className="w-3 h-3 -rotate-45" />,
};

export const GanttChartTimeline: React.FC<GanttChartTimelineProps> = ({
  tasks,
  milestones = [],
  startDate,
  endDate,
  className,
}) => {
  const months = useMemo(() => {
    return eachMonthOfInterval({
      start: startOfMonth(startDate),
      end: endOfMonth(endDate),
    });
  }, [startDate, endDate]);

  const timelineStart = startOfMonth(startDate);
  const timelineEnd = endOfMonth(endDate);
  const totalDays = useMemo(() => {
    return differenceInDays(timelineEnd, timelineStart) + 1;
  }, [timelineStart, timelineEnd]);

  const today = useMemo(() => new Date(), []);
  const showToday = useMemo(() => {
    return isWithinInterval(today, { start: timelineStart, end: timelineEnd });
  }, [today, timelineStart, timelineEnd]);

  const getPosition = (date: Date) => {
    const daysFromStart = differenceInDays(startOfDay(date), timelineStart);
    return (daysFromStart / totalDays) * 100;
  };

  const getWidth = (start: Date, end: Date) => {
    const duration = differenceInDays(startOfDay(end), startOfDay(start)) + 1;
    return (duration / totalDays) * 100;
  };

  return (
    <TooltipProvider>
      <div className={cn("flex flex-col w-full h-full border rounded-lg bg-background overflow-hidden shadow-sm", className)}>
        {/* Header */}
        <div className="p-4 border-b bg-card flex justify-between items-center">
          <div>
            <h3 className="text-lg font-semibold tracking-tight">Breeding Cycle Timeline</h3>
            <p className="text-sm text-muted-foreground">
              {format(startDate, 'MMMM yyyy')} - {format(endDate, 'MMMM yyyy')}
            </p>
          </div>
          <div className="flex gap-2">
            <div className="flex items-center gap-4 text-xs">
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 bg-blue-500 rounded-sm" />
                <span>Planned</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 bg-green-500 rounded-sm" />
                <span>In Progress</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 bg-gray-400 rounded-sm" />
                <span>Completed</span>
              </div>
            </div>
          </div>
        </div>

        {/* Gantt Content */}
        <div className="flex-1 overflow-auto">
          <div className="min-w-max">
            {/* Timeline Header (Months) */}
            <div className="flex border-b bg-muted/30 sticky top-0 z-20">
              <div className="w-64 flex-shrink-0 border-r p-3 font-medium text-sm">
                Stages / Activities
              </div>
              <div className="flex flex-1">
                {months.map((month, idx) => {
                  const daysInMonth = differenceInDays(endOfMonth(month), startOfMonth(month)) + 1;
                  const widthPercent = (daysInMonth / totalDays) * 100;
                  return (
                    <div
                      key={idx}
                      className="border-r px-2 py-3 text-xs font-medium text-muted-foreground text-center overflow-hidden"
                      style={{ width: `${widthPercent}%`, minWidth: '100px' }}
                    >
                      {format(month, 'MMM yyyy')}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Gantt Body */}
            <div className="relative">
              {/* Today Marker */}
              {showToday && (
                <div
                  className="absolute top-0 bottom-0 w-px bg-red-500 z-30 pointer-events-none flex flex-col items-center"
                  style={{ left: `${getPosition(today)}%` }}
                >
                  <div className="bg-red-500 text-white text-[8px] px-1 rounded-sm -mt-2">Today</div>
                </div>
              )}

              {/* Vertical Grid Lines */}
              <div className="absolute inset-0 flex pointer-events-none">
                <div className="w-64 flex-shrink-0 border-r h-full bg-muted/5" />
                <div className="flex flex-1 h-full">
                  {months.map((month, idx) => {
                    const daysInMonth = differenceInDays(endOfMonth(month), startOfMonth(month)) + 1;
                    const widthPercent = (daysInMonth / totalDays) * 100;
                    return (
                      <div
                        key={idx}
                        className="border-r h-full"
                        style={{ width: `${widthPercent}%`, minWidth: '100px' }}
                      />
                    );
                  })}
                </div>
              </div>

              {/* Tasks Rows */}
              <div className="relative z-10">
                {tasks.length === 0 && (
                  <div className="flex border-b h-32 items-center justify-center text-muted-foreground italic text-sm">
                    No tasks planned for this cycle.
                  </div>
                )}
                {tasks.map((task) => (
                  <div key={task.id} className="flex border-b group hover:bg-muted/30 transition-colors">
                    <div className="w-64 flex-shrink-0 border-r p-3 flex flex-col justify-center">
                      <span className="text-sm font-medium leading-none mb-1">{task.name}</span>
                      <span className="text-[10px] text-muted-foreground">
                        {format(task.start, 'MMM d')} - {format(task.end, 'MMM d')}
                      </span>
                    </div>
                    <div className="flex-1 relative h-16 flex items-center">
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <div
                            className={cn(
                              "absolute h-8 rounded-md border shadow-sm flex items-center px-3 cursor-help transition-all group-hover:shadow-md",
                              statusColors[task.status]
                            )}
                            style={{
                              left: `${getPosition(task.start)}%`,
                              width: `${getWidth(task.start, task.end)}%`
                            }}
                          >
                            <span className="text-[10px] font-bold truncate">
                              {task.progress}%
                            </span>
                          </div>
                        </TooltipTrigger>
                        <TooltipContent>
                          <div className="text-xs space-y-1">
                            <p className="font-bold">{task.name}</p>
                            <p>{format(task.start, 'PP')} - {format(task.end, 'PP')}</p>
                            <p>Status: <span className="capitalize">{task.status}</span></p>
                            <p>Progress: {task.progress}%</p>
                            {task.assignee && <p>Lead: {task.assignee}</p>}
                          </div>
                        </TooltipContent>
                      </Tooltip>
                    </div>
                  </div>
                ))}

                {/* Milestones Layer */}
                <div className="flex">
                  <div className="w-64 flex-shrink-0 border-r p-3 italic text-xs text-muted-foreground flex items-center">
                    <Milestone className="w-3 h-3 mr-2" /> Key Milestones
                  </div>
                  <div className="flex-1 relative h-12">
                    {milestones.map((milestone) => (
                      <Tooltip key={milestone.id}>
                        <TooltipTrigger asChild>
                          <div
                            className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 cursor-help group"
                            style={{ left: `${getPosition(milestone.date)}%` }}
                          >
                            <div className="bg-primary text-primary-foreground p-1 rounded-full rotate-45 border-2 border-background shadow-sm group-hover:scale-125 transition-transform">
                              {milestoneIcons[milestone.type] || milestoneIcons.default}
                            </div>
                            <div className="absolute top-full mt-1 left-1/2 -translate-x-1/2 whitespace-nowrap text-[10px] font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                              {milestone.name}
                            </div>
                          </div>
                        </TooltipTrigger>
                        <TooltipContent>
                          <div className="text-xs">
                            <p className="font-bold">{milestone.name}</p>
                            <p>{format(milestone.date, 'PPPP')}</p>
                            <p className="capitalize text-muted-foreground">{milestone.type}</p>
                          </div>
                        </TooltipContent>
                      </Tooltip>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* AI Insight Footer (REEVU Canonical) */}
        <div className="p-3 bg-indigo-50 dark:bg-indigo-950/20 border-t flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-indigo-500" />
          <span className="text-xs font-medium text-indigo-700 dark:text-indigo-300">
            REEVU Insight: Cycle efficiency is optimized for the current climate forecast.
          </span>
          <Tooltip>
            <TooltipTrigger asChild>
              <Info className="w-3 h-3 text-indigo-400 cursor-help" />
            </TooltipTrigger>
            <TooltipContent side="top">
              <p className="max-w-xs text-[10px]">
                REEVU analyzes historical breeding data and real-time weather to suggest optimal planting windows.
              </p>
            </TooltipContent>
          </Tooltip>
        </div>
      </div>
    </TooltipProvider>
  );
};

export default GanttChartTimeline;
