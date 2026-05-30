package registry

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestFileLogSourceStreamEmitsTailAndAppendedLines(t *testing.T) {
	path := filepath.Join(t.TempDir(), "backend.log")
	if err := os.WriteFile(path, []byte("one\ntwo\nthree\nfour\n"), 0o644); err != nil {
		t.Fatalf("write log: %v", err)
	}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	lines, err := (FileLogSource{Path: path}).Stream(ctx, 2)
	if err != nil {
		t.Fatalf("Stream returned error: %v", err)
	}

	if got := readLine(t, lines); got != "three" {
		t.Fatalf("first tail line = %q, want three", got)
	}
	if got := readLine(t, lines); got != "four" {
		t.Fatalf("second tail line = %q, want four", got)
	}

	file, err := os.OpenFile(path, os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		t.Fatalf("open append: %v", err)
	}
	if _, err := file.WriteString("five\n"); err != nil {
		t.Fatalf("append log: %v", err)
	}
	_ = file.Close()

	if got := readLine(t, lines); got != "five" {
		t.Fatalf("appended line = %q, want five", got)
	}

	cancel()
	expectChannelClosed(t, lines)
}

func TestFileLogSourceStreamReturnsErrorForMissingFile(t *testing.T) {
	_, err := (FileLogSource{Path: filepath.Join(t.TempDir(), "missing.log")}).Stream(context.Background(), 50)
	if err == nil {
		t.Fatal("Stream error = nil, want missing file error")
	}
}

func TestPodmanLogSourceStreamRunsPodmanLogsAndClosesOnCancel(t *testing.T) {
	argsFile := filepath.Join(t.TempDir(), "args.txt")
	fake := writeProbeExecutable(t, t.TempDir(), "podman", fmt.Sprintf(`#!/bin/sh
printf '%%s\n' "$*" > %q
printf 'container-line\n'
while true; do sleep 1; done
`, argsFile))

	ctx, cancel := context.WithCancel(context.Background())
	lines, err := (PodmanLogSource{Runtime: fake, Container: "bijmantra-postgres"}).Stream(ctx, 7)
	if err != nil {
		t.Fatalf("Stream returned error: %v", err)
	}

	if got := readLine(t, lines); got != "container-line" {
		t.Fatalf("podman line = %q, want container-line", got)
	}

	args := readFile(t, argsFile)
	want := "logs --follow --tail 7 bijmantra-postgres\n"
	if args != want {
		t.Fatalf("podman args = %q, want %q", args, want)
	}

	cancel()
	expectChannelClosed(t, lines)
}

func readLine(t *testing.T, lines <-chan string) string {
	t.Helper()
	select {
	case line, ok := <-lines:
		if !ok {
			t.Fatal("line channel closed before expected line")
		}
		return line
	case <-time.After(2 * time.Second):
		t.Fatal("timed out waiting for log line")
		return ""
	}
}

func expectChannelClosed(t *testing.T, lines <-chan string) {
	t.Helper()
	select {
	case _, ok := <-lines:
		if ok {
			t.Fatal("line channel still open after cancellation")
		}
	case <-time.After(2 * time.Second):
		t.Fatal("timed out waiting for channel close")
	}
}
