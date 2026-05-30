package logger

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"
)

var maxLogSizeBytes int64 = 10 * 1024 * 1024

type Logger struct {
	mu   sync.Mutex
	path string
	file *os.File
}

type Event struct {
	Time    time.Time `json:"time"`
	Type    string    `json:"type"`
	Service string    `json:"service"`
	From    string    `json:"from"`
	To      string    `json:"to"`
	Message string    `json:"message,omitempty"`
}

func New(path string) (*Logger, error) {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return nil, fmt.Errorf("create log directory: %w", err)
	}

	file, err := openLog(path)
	if err != nil {
		return nil, err
	}

	return &Logger{path: path, file: file}, nil
}

func (l *Logger) Write(e Event) error {
	line, err := json.Marshal(e)
	if err != nil {
		return fmt.Errorf("marshal log event: %w", err)
	}
	line = append(line, '\n')

	l.mu.Lock()
	defer l.mu.Unlock()

	if err := l.rotateIfNeeded(int64(len(line))); err != nil {
		return err
	}
	if _, err := l.file.Write(line); err != nil {
		return fmt.Errorf("write log event: %w", err)
	}
	if err := l.file.Sync(); err != nil {
		return fmt.Errorf("flush log event: %w", err)
	}

	return nil
}

func (l *Logger) Recent(n int) []Event {
	if n <= 0 {
		return nil
	}

	l.mu.Lock()
	if l.file != nil {
		_ = l.file.Sync()
	}
	path := l.path
	l.mu.Unlock()

	file, err := os.Open(path)
	if err != nil {
		return nil
	}
	defer file.Close()

	recent := make([]Event, 0, n)
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		var event Event
		if err := json.Unmarshal(scanner.Bytes(), &event); err != nil {
			continue
		}
		if len(recent) == n {
			copy(recent, recent[1:])
			recent = recent[:n-1]
		}
		recent = append(recent, event)
	}

	return recent
}

func (l *Logger) Close() error {
	l.mu.Lock()
	defer l.mu.Unlock()

	if l.file == nil {
		return nil
	}
	err := l.file.Close()
	l.file = nil
	return err
}

func (l *Logger) rotateIfNeeded(incoming int64) error {
	if maxLogSizeBytes <= 0 || l.file == nil {
		return nil
	}

	info, err := l.file.Stat()
	if err != nil {
		return fmt.Errorf("stat log file: %w", err)
	}
	if info.Size() == 0 || info.Size()+incoming <= maxLogSizeBytes {
		return nil
	}

	if err := l.file.Close(); err != nil {
		return fmt.Errorf("close log before rotation: %w", err)
	}
	l.file = nil

	rotatedPath := fmt.Sprintf("%s.%s", l.path, time.Now().UTC().Format("20060102T150405.000000000Z"))
	if err := os.Rename(l.path, rotatedPath); err != nil {
		return fmt.Errorf("rotate log file: %w", err)
	}

	file, err := openLog(l.path)
	if err != nil {
		return err
	}
	l.file = file
	return nil
}

func openLog(path string) (*os.File, error) {
	file, err := os.OpenFile(path, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		return nil, fmt.Errorf("open log file: %w", err)
	}
	return file, nil
}
