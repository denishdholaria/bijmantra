package registry

import (
	"context"
	"fmt"
	"net"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func TestTCPProbeCheckSucceedsWhenPortOpen(t *testing.T) {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("listen: %v", err)
	}
	defer listener.Close()

	port := listener.Addr().(*net.TCPAddr).Port
	probe := TCPProbe{Host: "127.0.0.1", Port: port}

	if err := probe.Check(context.Background()); err != nil {
		t.Fatalf("TCPProbe.Check returned error: %v", err)
	}
}

func TestTCPProbeCheckReturnsErrorWhenPortClosed(t *testing.T) {
	port := closedTCPPort(t)
	probe := TCPProbe{Host: "127.0.0.1", Port: port}

	if err := probe.Check(context.Background()); err == nil {
		t.Fatal("TCPProbe.Check error = nil, want closed port error")
	}
}

func TestHTTPProbeCheckSucceedsOn2xx(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.WriteHeader(http.StatusNoContent)
	}))
	defer server.Close()

	if err := (HTTPProbe{URL: server.URL}).Check(context.Background()); err != nil {
		t.Fatalf("HTTPProbe.Check returned error: %v", err)
	}
}

func TestHTTPProbeCheckReturnsErrorOnNon2xx(t *testing.T) {
	server := httptest.NewServer(http.NotFoundHandler())
	defer server.Close()

	err := (HTTPProbe{URL: server.URL}).Check(context.Background())
	if err == nil {
		t.Fatal("HTTPProbe.Check error = nil, want non-2xx error")
	}
	if !strings.Contains(err.Error(), "404") {
		t.Fatalf("HTTPProbe.Check error = %q, want status code context", err)
	}
}

func TestHTTPProbeCheckHonorsContextCancellation(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		time.Sleep(200 * time.Millisecond)
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Millisecond)
	defer cancel()

	err := (HTTPProbe{URL: server.URL}).Check(ctx)
	if err == nil {
		t.Fatal("HTTPProbe.Check error = nil, want context timeout")
	}
}

func TestExecProbeCheckRunsPodmanExec(t *testing.T) {
	argsFile := filepath.Join(t.TempDir(), "args.txt")
	fake := writeProbeExecutable(t, t.TempDir(), "podman", fmt.Sprintf(`#!/bin/sh
printf '%%s\n' "$*" > %q
exit 0
`, argsFile))

	probe := ExecProbe{Runtime: fake, Container: "bijmantra-postgres", Cmd: []string{"pg_isready", "-U", "bijmantra_user"}}
	if err := probe.Check(context.Background()); err != nil {
		t.Fatalf("ExecProbe.Check returned error: %v", err)
	}

	args := strings.TrimSpace(readFile(t, argsFile))
	want := "exec bijmantra-postgres pg_isready -U bijmantra_user"
	if args != want {
		t.Fatalf("exec args = %q, want %q", args, want)
	}
}

func TestExecProbeCheckReturnsErrorOnCommandFailure(t *testing.T) {
	fake := writeProbeExecutable(t, t.TempDir(), "podman", "#!/bin/sh\necho nope >&2\nexit 42\n")

	err := (ExecProbe{Runtime: fake, Container: "c", Cmd: []string{"cmd"}}).Check(context.Background())
	if err == nil {
		t.Fatal("ExecProbe.Check error = nil, want command failure")
	}
	if !strings.Contains(err.Error(), "nope") {
		t.Fatalf("ExecProbe.Check error = %q, want command output", err)
	}
}

func TestContainerRunningProbeCheckMatchesContainerName(t *testing.T) {
	fake := writeProbeExecutable(t, t.TempDir(), "podman", "#!/bin/sh\nprintf 'bijmantra-chloe-cli\\nother\\n'\n")

	probe := ContainerRunningProbe{Runtime: fake, Container: "bijmantra-chloe-cli"}
	if err := probe.Check(context.Background()); err != nil {
		t.Fatalf("ContainerRunningProbe.Check returned error: %v", err)
	}
}

func TestContainerRunningProbeCheckReturnsErrorWhenMissing(t *testing.T) {
	fake := writeProbeExecutable(t, t.TempDir(), "podman", "#!/bin/sh\nprintf 'other\\n'\n")

	err := (ContainerRunningProbe{Runtime: fake, Container: "bijmantra-chloe-cli"}).Check(context.Background())
	if err == nil {
		t.Fatal("ContainerRunningProbe.Check error = nil, want missing container error")
	}
}

func closedTCPPort(t *testing.T) int {
	t.Helper()
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("listen for closed port: %v", err)
	}
	port := listener.Addr().(*net.TCPAddr).Port
	if err := listener.Close(); err != nil {
		t.Fatalf("close listener: %v", err)
	}
	return port
}

func writeProbeExecutable(t *testing.T, dir, name, contents string) string {
	t.Helper()
	path := filepath.Join(dir, name)
	if err := os.WriteFile(path, []byte(contents), 0o755); err != nil {
		t.Fatalf("write executable %s: %v", path, err)
	}
	return path
}

func readFile(t *testing.T, path string) string {
	t.Helper()
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("read %s: %v", path, err)
	}
	return string(data)
}
