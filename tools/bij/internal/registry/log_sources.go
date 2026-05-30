package registry

import (
	"bufio"
	"context"
	"fmt"
	"io"
	"os"
	"os/exec"
	"strconv"
	"strings"
	"sync"
	"time"
)

func (s FileLogSource) Stream(ctx context.Context, tailLines int) (<-chan string, error) {
	if s.Path == "" {
		return nil, fmt.Errorf("file log source: path is empty")
	}

	history, offset, err := tailFile(s.Path, tailLines)
	if err != nil {
		return nil, err
	}

	ctx = usableContext(ctx)
	out := make(chan string, 256)
	go func() {
		defer close(out)

		for _, line := range history {
			if !sendLogLine(ctx, out, line) {
				return
			}
		}

		ticker := time.NewTicker(100 * time.Millisecond)
		defer ticker.Stop()

		pending := ""
		for {
			select {
			case <-ctx.Done():
				return
			case <-ticker.C:
				chunk, nextOffset, reset, err := readFromOffset(s.Path, offset)
				if err != nil {
					continue
				}
				if reset {
					pending = ""
				}
				offset = nextOffset
				lines, nextPending := completeLogLines(pending, string(chunk))
				pending = nextPending
				for _, line := range lines {
					if !sendLogLine(ctx, out, line) {
						return
					}
				}
			}
		}
	}()

	return out, nil
}

func (s PodmanLogSource) Stream(ctx context.Context, tailLines int) (<-chan string, error) {
	if s.Runtime == "" {
		return nil, fmt.Errorf("podman log source: runtime is empty")
	}
	if s.Container == "" {
		return nil, fmt.Errorf("podman log source: container is empty")
	}
	if tailLines < 0 {
		tailLines = 0
	}

	ctx = usableContext(ctx)
	cmd := exec.CommandContext(
		ctx,
		s.Runtime,
		"logs",
		"--follow",
		"--tail",
		strconv.Itoa(tailLines),
		s.Container,
	)

	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return nil, fmt.Errorf("podman log source %s: stdout pipe: %w", s.Container, err)
	}
	stderr, err := cmd.StderrPipe()
	if err != nil {
		return nil, fmt.Errorf("podman log source %s: stderr pipe: %w", s.Container, err)
	}
	if err := cmd.Start(); err != nil {
		return nil, fmt.Errorf("podman log source %s: start: %w", s.Container, err)
	}

	out := make(chan string, 256)
	go func() {
		defer close(out)

		var wg sync.WaitGroup
		wg.Add(2)
		go scanLogReader(ctx, &wg, stdout, out)
		go scanLogReader(ctx, &wg, stderr, out)

		done := make(chan error, 1)
		go func() { done <- cmd.Wait() }()

		select {
		case <-ctx.Done():
			<-done
		case <-done:
		}

		wg.Wait()
	}()

	return out, nil
}

func tailFile(path string, tailLines int) ([]string, int64, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, 0, fmt.Errorf("file log source %s: %w", path, err)
	}
	lines, pending := completeLogLines("", string(data))
	if pending != "" {
		lines = append(lines, pending)
	}
	if tailLines >= 0 && len(lines) > tailLines {
		lines = lines[len(lines)-tailLines:]
	}
	return lines, int64(len(data)), nil
}

func readFromOffset(path string, offset int64) ([]byte, int64, bool, error) {
	info, err := os.Stat(path)
	if err != nil {
		return nil, offset, false, err
	}

	reset := false
	if info.Size() < offset {
		offset = 0
		reset = true
	}
	if info.Size() == offset {
		return nil, offset, reset, nil
	}

	file, err := os.Open(path)
	if err != nil {
		return nil, offset, reset, err
	}
	defer file.Close()

	if _, err := file.Seek(offset, io.SeekStart); err != nil {
		return nil, offset, reset, err
	}
	data, err := io.ReadAll(file)
	if err != nil {
		return nil, offset, reset, err
	}

	return data, offset + int64(len(data)), reset, nil
}

func completeLogLines(pending, chunk string) ([]string, string) {
	if chunk == "" {
		return nil, pending
	}

	combined := pending + chunk
	parts := strings.Split(combined, "\n")
	if !strings.HasSuffix(combined, "\n") {
		return trimCR(parts[:len(parts)-1]), parts[len(parts)-1]
	}

	return trimCR(parts[:len(parts)-1]), ""
}

func trimCR(lines []string) []string {
	out := make([]string, len(lines))
	for i, line := range lines {
		out[i] = strings.TrimSuffix(line, "\r")
	}
	return out
}

func scanLogReader(ctx context.Context, wg *sync.WaitGroup, reader io.Reader, out chan<- string) {
	defer wg.Done()

	scanner := bufio.NewScanner(reader)
	scanner.Buffer(make([]byte, 0, 64*1024), 1024*1024)
	for scanner.Scan() {
		if !sendLogLine(ctx, out, scanner.Text()) {
			return
		}
	}
}

func sendLogLine(ctx context.Context, out chan<- string, line string) bool {
	select {
	case <-ctx.Done():
		return false
	case out <- line:
		return true
	}
}
