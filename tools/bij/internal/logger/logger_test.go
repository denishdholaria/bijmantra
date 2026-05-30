package logger

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestNewCreatesLogDirectory(t *testing.T) {
	path := filepath.Join(t.TempDir(), "nested", "bij-runtime.log")

	log, err := New(path)
	if err != nil {
		t.Fatalf("New returned error: %v", err)
	}
	defer log.Close()

	if _, err := os.Stat(filepath.Dir(path)); err != nil {
		t.Fatalf("log directory was not created: %v", err)
	}
}

func TestWriteProducesJSONLines(t *testing.T) {
	path := filepath.Join(t.TempDir(), "bij-runtime.log")
	log, err := New(path)
	if err != nil {
		t.Fatalf("New returned error: %v", err)
	}
	defer log.Close()

	event := Event{
		Time:    time.Date(2026, 5, 18, 12, 0, 0, 0, time.UTC),
		Type:    "state_change",
		Service: "backend",
		From:    "starting",
		To:      "ready",
		Message: "healthy",
	}
	if err := log.Write(event); err != nil {
		t.Fatalf("Write returned error: %v", err)
	}

	lines := readLogLines(t, path)
	if len(lines) != 1 {
		t.Fatalf("log line count = %d, want 1", len(lines))
	}

	var got Event
	if err := json.Unmarshal([]byte(lines[0]), &got); err != nil {
		t.Fatalf("unmarshal JSON line: %v", err)
	}
	if got.Service != "backend" || got.To != "ready" || got.Message != "healthy" {
		t.Fatalf("event = %#v, want backend ready healthy", got)
	}
}

func TestWriteRotatesAtLimit(t *testing.T) {
	originalLimit := maxLogSizeBytes
	maxLogSizeBytes = 120
	t.Cleanup(func() { maxLogSizeBytes = originalLimit })

	dir := t.TempDir()
	path := filepath.Join(dir, "bij-runtime.log")
	log, err := New(path)
	if err != nil {
		t.Fatalf("New returned error: %v", err)
	}
	defer log.Close()

	if err := log.Write(Event{Time: time.Now(), Type: "state_change", Service: "backend", To: "starting", Message: "first payload"}); err != nil {
		t.Fatalf("first Write returned error: %v", err)
	}
	if err := log.Write(Event{Time: time.Now(), Type: "state_change", Service: "frontend", To: "ready", Message: "second payload large enough to rotate"}); err != nil {
		t.Fatalf("second Write returned error: %v", err)
	}

	matches, err := filepath.Glob(filepath.Join(dir, "bij-runtime.log.*"))
	if err != nil {
		t.Fatalf("glob rotated logs: %v", err)
	}
	if len(matches) == 0 {
		t.Fatal("rotated log count = 0, want at least one rotated file")
	}
	if lines := readLogLines(t, path); len(lines) == 0 {
		t.Fatal("current log is empty after rotation, want newest event in active log")
	}
}

func TestRecentReturnsLastNEvents(t *testing.T) {
	path := filepath.Join(t.TempDir(), "bij-runtime.log")
	log, err := New(path)
	if err != nil {
		t.Fatalf("New returned error: %v", err)
	}
	defer log.Close()

	for i := 0; i < 5; i++ {
		if err := log.Write(Event{Time: time.Now(), Type: "state_change", Service: "svc", To: string(rune('0' + i))}); err != nil {
			t.Fatalf("Write %d returned error: %v", i, err)
		}
	}

	recent := log.Recent(2)
	if len(recent) != 2 {
		t.Fatalf("Recent(2) length = %d, want 2", len(recent))
	}
	if recent[0].To != "3" || recent[1].To != "4" {
		t.Fatalf("Recent(2) = %#v, want last two events in order", recent)
	}
}

func readLogLines(t *testing.T, path string) []string {
	t.Helper()
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("read log %s: %v", path, err)
	}
	var lines []string
	for _, line := range splitLines(string(data)) {
		if line != "" {
			lines = append(lines, line)
		}
	}
	return lines
}

func splitLines(value string) []string {
	var lines []string
	start := 0
	for i, ch := range value {
		if ch == '\n' {
			lines = append(lines, value[start:i])
			start = i + 1
		}
	}
	if start < len(value) {
		lines = append(lines, value[start:])
	}
	return lines
}
