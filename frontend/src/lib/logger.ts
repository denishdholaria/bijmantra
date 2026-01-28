/**
 * Centralized Logging Utility
 * Provides a structured logging system with different log levels
 */

export enum LogLevel {
  DEBUG = 'DEBUG',
  INFO = 'INFO',
  WARN = 'WARN',
  ERROR = 'ERROR',
}

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  context?: Record<string, any>;
  error?: Error;
}

interface LoggerConfig {
  minLevel?: LogLevel;
  enableConsole?: boolean;
  enableFile?: boolean;
  isDevelopment?: boolean;
}

class Logger {
  private minLevel: LogLevel = LogLevel.DEBUG;
  private enableConsole: boolean = true;
  private enableFile: boolean = false;
  private isDevelopment: boolean = import.meta.env.DEV;
  private logs: LogEntry[] = [];

  constructor(config: LoggerConfig = {}) {
    this.minLevel = config.minLevel ?? LogLevel.DEBUG;
    this.enableConsole = config.enableConsole ?? true;
    this.enableFile = config.enableFile ?? false;
    this.isDevelopment = config.isDevelopment ?? this.isDevelopment;
  }

  /**
   * Check if a log level should be processed
   */
  private shouldLog(level: LogLevel): boolean {
    const levels = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARN, LogLevel.ERROR];
    const minLevelIndex = levels.indexOf(this.minLevel);
    const currentLevelIndex = levels.indexOf(level);
    return currentLevelIndex >= minLevelIndex;
  }

  /**
   * Format timestamp in ISO 8601 format
   */
  private getTimestamp(): string {
    return new Date().toISOString();
  }

  /**
   * Create a formatted log entry
   */
  private createLogEntry(
    level: LogLevel,
    message: string,
    context?: Record<string, any>,
    error?: Error
  ): LogEntry {
    return {
      timestamp: this.getTimestamp(),
      level,
      message,
      context,
      error,
    };
  }

  /**
   * Format log entry for console output
   */
  private formatForConsole(entry: LogEntry): string {
    const { timestamp, level, message, context } = entry;
    let output = `[${timestamp}] [${level}] ${message}`;

    if (context && Object.keys(context).length > 0) {
      output += `\n${JSON.stringify(context, null, 2)}`;
    }

    if (entry.error) {
      output += `\nError: ${entry.error.message}\n${entry.error.stack}`;
    }

    return output;
  }

  /**
   * Output log to console based on level
   */
  private outputToConsole(entry: LogEntry): void {
    if (!this.enableConsole) return;

    const formatted = this.formatForConsole(entry);

    switch (entry.level) {
      case LogLevel.DEBUG:
        console.debug(formatted);
        break;
      case LogLevel.INFO:
        console.info(formatted);
        break;
      case LogLevel.WARN:
        console.warn(formatted);
        break;
      case LogLevel.ERROR:
        console.error(formatted);
        break;
    }
  }

  /**
   * Store log in memory (for potential file export later)
   */
  private storeLog(entry: LogEntry): void {
    this.logs.push(entry);
    // Keep only last 1000 logs in memory
    if (this.logs.length > 1000) {
      this.logs.shift();
    }
  }

  /**
   * Process and output a log entry
   */
  private log(
    level: LogLevel,
    message: string,
    context?: Record<string, any>,
    error?: Error
  ): void {
    if (!this.shouldLog(level)) return;

    const entry = this.createLogEntry(level, message, context, error);

    this.outputToConsole(entry);
    this.storeLog(entry);
  }

  /**
   * Log a debug message
   */
  public debug(message: string, context?: Record<string, any>): void {
    this.log(LogLevel.DEBUG, message, context);
  }

  /**
   * Log an info message
   */
  public info(message: string, context?: Record<string, any>): void {
    this.log(LogLevel.INFO, message, context);
  }

  /**
   * Log a warning message
   */
  public warn(message: string, context?: Record<string, any>): void {
    this.log(LogLevel.WARN, message, context);
  }

  /**
   * Log an error message
   */
  public error(message: string, error?: Error, context?: Record<string, any>): void {
    this.log(LogLevel.ERROR, message, context, error);
  }

  /**
   * Get all logged entries
   */
  public getLogs(): LogEntry[] {
    return [...this.logs];
  }

  /**
   * Clear all stored logs
   */
  public clearLogs(): void {
    this.logs = [];
  }

  /**
   * Export logs as JSON
   */
  public exportLogsAsJSON(): string {
    return JSON.stringify(this.logs, null, 2);
  }

  /**
   * Get logs filtered by level
   */
  public getLogsByLevel(level: LogLevel): LogEntry[] {
    return this.logs.filter((entry) => entry.level === level);
  }

  /**
   * Configure logger settings
   */
  public configure(config: LoggerConfig): void {
    if (config.minLevel !== undefined) this.minLevel = config.minLevel;
    if (config.enableConsole !== undefined) this.enableConsole = config.enableConsole;
    if (config.enableFile !== undefined) this.enableFile = config.enableFile;
    if (config.isDevelopment !== undefined) this.isDevelopment = config.isDevelopment;
  }
}

// Create and export a singleton instance
export const logger = new Logger({
  minLevel: (import.meta.env.VITE_LOG_LEVEL as LogLevel) ?? LogLevel.INFO,
  isDevelopment: import.meta.env.DEV,
});

export default logger;
