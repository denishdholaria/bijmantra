package cli

import (
	"bytes"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestRunVersionWinsBeforeWorkspaceResolution(t *testing.T) {
	var stdout, stderr bytes.Buffer

	code := Run([]string{"--version", "--workspace", filepath.Join(t.TempDir(), "missing")}, &stdout, &stderr, "1.2.3")

	if code != 0 {
		t.Fatalf("exit code = %d, want 0; stderr=%s", code, stderr.String())
	}
	if strings.TrimSpace(stdout.String()) != "1.2.3" {
		t.Fatalf("stdout = %q, want version", stdout.String())
	}
}

func TestRunNoArgsPrintsHelp(t *testing.T) {
	var stdout, stderr bytes.Buffer

	code := Run(nil, &stdout, &stderr, "1.2.3")

	if code != 0 {
		t.Fatalf("exit code = %d, want 0; stderr=%s", code, stderr.String())
	}
	if !strings.Contains(stdout.String(), "Commands:") || !strings.Contains(stdout.String(), "dev") {
		t.Fatalf("help output = %q, want command list", stdout.String())
	}
}

func TestRunUnknownCommandReturnsError(t *testing.T) {
	var stdout, stderr bytes.Buffer

	code := Run([]string{"missing"}, &stdout, &stderr, "1.2.3")

	if code != 1 {
		t.Fatalf("exit code = %d, want 1", code)
	}
	if !strings.Contains(stderr.String(), "unknown command") {
		t.Fatalf("stderr = %q, want unknown command", stderr.String())
	}
}

func TestLogsNoFollowPrintsFileTail(t *testing.T) {
	workspace := t.TempDir()
	if err := os.WriteFile(filepath.Join(workspace, "compose.yaml"), []byte("services: {}\n"), 0o644); err != nil {
		t.Fatalf("write compose: %v", err)
	}
	logDir := filepath.Join(workspace, "logs")
	if err := os.MkdirAll(logDir, 0o755); err != nil {
		t.Fatalf("create logs dir: %v", err)
	}
	if err := os.WriteFile(filepath.Join(logDir, "backend.log"), []byte("one\ntwo\nthree\n"), 0o644); err != nil {
		t.Fatalf("write backend log: %v", err)
	}
	podman := writeFakePodman(t, workspace)
	t.Setenv("CONTAINER_RUNTIME", podman)

	var stdout, stderr bytes.Buffer
	code := Run([]string{"--workspace", workspace, "logs", "backend", "--no-follow", "--lines", "2"}, &stdout, &stderr, "1.2.3")

	if code != 0 {
		t.Fatalf("exit code = %d, want 0; stderr=%s", code, stderr.String())
	}
	if stdout.String() != "two\nthree\n" {
		t.Fatalf("stdout = %q, want last two lines", stdout.String())
	}
}

func TestLogsUnknownServiceListsValidServices(t *testing.T) {
	workspace := t.TempDir()
	if err := os.WriteFile(filepath.Join(workspace, "compose.yaml"), []byte("services: {}\n"), 0o644); err != nil {
		t.Fatalf("write compose: %v", err)
	}
	podman := writeFakePodman(t, workspace)
	t.Setenv("CONTAINER_RUNTIME", podman)

	var stdout, stderr bytes.Buffer
	code := Run([]string{"--workspace", workspace, "logs", "missing", "--no-follow"}, &stdout, &stderr, "1.2.3")

	if code != 1 {
		t.Fatalf("exit code = %d, want 1", code)
	}
	if !strings.Contains(stderr.String(), "valid services") || !strings.Contains(stderr.String(), "backend") {
		t.Fatalf("stderr = %q, want valid services", stderr.String())
	}
}

func writeFakePodman(t *testing.T, dir string) string {
	t.Helper()
	path := filepath.Join(dir, "podman")
	body := "#!/bin/sh\nif [ \"$1 $2\" = \"compose version\" ]; then exit 0; fi\nexit 0\n"
	if err := os.WriteFile(path, []byte(body), 0o755); err != nil {
		t.Fatalf("write fake podman: %v", err)
	}
	return path
}
