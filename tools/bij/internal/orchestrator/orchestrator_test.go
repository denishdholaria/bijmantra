package orchestrator

import (
	"context"
	"errors"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/bijmantra/bij/internal/logger"
	"github.com/bijmantra/bij/internal/registry"
)

func TestContainerLifecycleCommandsUseComposeFileAndServiceName(t *testing.T) {
	dir := t.TempDir()
	argsFile := filepath.Join(dir, "args.txt")
	podman := writeExecutable(t, dir, "podman", "#!/bin/sh\nprintf '%s\\n' \"$*\" >> "+shellQuote(argsFile)+"\n")
	composeFile := filepath.Join(dir, "compose.yaml")
	if err := os.WriteFile(composeFile, []byte("services: {}\n"), 0o644); err != nil {
		t.Fatalf("write compose file: %v", err)
	}

	svc := &registry.Service{
		Name:           "postgres",
		Type:           registry.ContainerService,
		ContainerName:  "bijmantra-postgres",
		ComposeService: "postgres",
	}

	if err := StartContainer(context.Background(), podman, composeFile, svc); err != nil {
		t.Fatalf("StartContainer returned error: %v", err)
	}
	if err := StopContainer(context.Background(), podman, composeFile, svc); err != nil {
		t.Fatalf("StopContainer returned error: %v", err)
	}
	if err := RestartContainer(context.Background(), podman, composeFile, svc); err != nil {
		t.Fatalf("RestartContainer returned error: %v", err)
	}

	got := readText(t, argsFile)
	want := strings.Join([]string{
		"compose --file " + composeFile + " up -d postgres",
		"compose --file " + composeFile + " stop postgres",
		"compose --file " + composeFile + " restart postgres",
		"",
	}, "\n")
	if got != want {
		t.Fatalf("podman args = %q, want %q", got, want)
	}
}

func TestStartAndStopProcessWritesLogAndClearsPID(t *testing.T) {
	dir := t.TempDir()
	logDir := filepath.Join(dir, "logs")
	process := writeExecutable(t, dir, "backend-process", "#!/bin/sh\necho process-started\nexec sleep 30\n")
	svc := &registry.Service{
		Name:    "backend",
		Type:    registry.ProcessService,
		Cmd:     []string{process},
		WorkDir: dir,
	}

	if err := StartProcess(context.Background(), svc, logDir); err != nil {
		t.Fatalf("StartProcess returned error: %v", err)
	}
	if svc.PID == 0 || svc.Process == nil {
		t.Fatalf("process tracking = pid %d process %#v, want live process", svc.PID, svc.Process)
	}

	waitForContains(t, filepath.Join(logDir, "backend.log"), "process-started")

	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	if err := StopProcess(ctx, svc, false); err != nil {
		t.Fatalf("StopProcess returned error: %v", err)
	}
	if svc.PID != 0 || svc.Process != nil {
		t.Fatalf("process tracking after stop = pid %d process %#v, want cleared", svc.PID, svc.Process)
	}
}

func TestWaitReadyEmitsReadyEventAndWritesLog(t *testing.T) {
	dir := t.TempDir()
	log, err := logger.New(filepath.Join(dir, "bij-runtime.log"))
	if err != nil {
		t.Fatalf("logger.New returned error: %v", err)
	}
	defer log.Close()

	probe := &flakyProbe{failures: 1}
	svc := &registry.Service{Name: "backend", State: registry.StateStarting, Probe: probe}
	orch := New([]*registry.Service{svc}, "/bin/podman", dir, log)

	if ok := orch.WaitReady(context.Background(), svc, time.Second); !ok {
		t.Fatal("WaitReady = false, want true")
	}
	if svc.State != registry.StateReady {
		t.Fatalf("service state = %q, want ready", svc.State)
	}

	select {
	case event := <-orch.Events:
		if event.Service != "backend" || event.To != registry.StateReady {
			t.Fatalf("event = %#v, want backend ready", event)
		}
	case <-time.After(time.Second):
		t.Fatal("timed out waiting for state event")
	}

	recent := log.Recent(1)
	if len(recent) != 1 || recent[0].Service != "backend" || recent[0].To != string(registry.StateReady) {
		t.Fatalf("recent log events = %#v, want backend ready event", recent)
	}
}

func TestBootCoreStartsOnlyCoreServices(t *testing.T) {
	workspace := t.TempDir()
	for _, dir := range []string{"backend", "frontend"} {
		if err := os.MkdirAll(filepath.Join(workspace, dir), 0o755); err != nil {
			t.Fatalf("create %s dir: %v", dir, err)
		}
	}
	if err := os.WriteFile(filepath.Join(workspace, "compose.yaml"), []byte("services: {}\n"), 0o644); err != nil {
		t.Fatalf("write compose file: %v", err)
	}

	binDir := filepath.Join(workspace, "bin")
	if err := os.MkdirAll(binDir, 0o755); err != nil {
		t.Fatalf("create bin dir: %v", err)
	}
	uvArgs := filepath.Join(workspace, "uv-args.txt")
	writeExecutable(t, binDir, "uv", "#!/bin/sh\nprintf '%s\\n' \"$*\" >> "+shellQuote(uvArgs)+"\n")
	t.Setenv("PATH", binDir+string(os.PathListSeparator)+os.Getenv("PATH"))

	podmanArgs := filepath.Join(workspace, "podman-args.txt")
	podman := writeExecutable(t, workspace, "podman", "#!/bin/sh\nprintf '%s\\n' \"$*\" >> "+shellQuote(podmanArgs)+"\n")
	process := writeExecutable(t, workspace, "sleep-process", "#!/bin/sh\nexec sleep 30\n")

	services := registry.DefaultRegistry(workspace, podman)
	for _, svc := range services {
		svc.Probe = successProbe{}
		if svc.Type == registry.ProcessService {
			svc.Cmd = []string{process}
		}
	}

	orch := New(services, podman, workspace, nil)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	orch.Boot(ctx, "core")
	waitForState(t, orch.Events, "frontend", registry.StateReady)

	if err := orch.Stop(context.Background(), false); err != nil {
		t.Fatalf("Stop returned error: %v", err)
	}

	args := readText(t, podmanArgs)
	if !strings.Contains(args, "compose --file "+filepath.Join(workspace, "compose.yaml")+" up -d postgres") {
		t.Fatalf("podman args = %q, want postgres start", args)
	}
	for _, unexpected := range []string{"redis", "minio", "meilisearch", "beingbijmantra", "chloe"} {
		if strings.Contains(args, unexpected) {
			t.Fatalf("podman args = %q, did not expect %s in core profile", args, unexpected)
		}
	}

	if got := readText(t, uvArgs); got != "run alembic upgrade head\n" {
		t.Fatalf("uv args = %q, want migration command", got)
	}
}

func TestProbeAllUpdatesServiceStates(t *testing.T) {
	services := []*registry.Service{
		{Name: "ready", State: registry.StateWaiting, Probe: successProbe{}},
		{Name: "degraded", State: registry.StateReady, Probe: errorProbe{}},
	}
	orch := New(services, "/bin/podman", t.TempDir(), nil)

	orch.ProbeAll(context.Background())

	if services[0].State != registry.StateReady {
		t.Fatalf("ready service state = %q, want ready", services[0].State)
	}
	if services[1].State != registry.StateDegraded {
		t.Fatalf("degraded service state = %q, want degraded", services[1].State)
	}
}

func TestRestartReturnsErrorForUnknownService(t *testing.T) {
	orch := New(nil, "/bin/podman", t.TempDir(), nil)

	if err := orch.Restart(context.Background(), "missing"); err == nil {
		t.Fatal("Restart error = nil, want unknown service error")
	}
}

type flakyProbe struct {
	failures int
	calls    int
}

func (p *flakyProbe) Check(context.Context) error {
	p.calls++
	if p.calls <= p.failures {
		return errors.New("not ready")
	}
	return nil
}

type successProbe struct{}

func (successProbe) Check(context.Context) error {
	return nil
}

type errorProbe struct{}

func (errorProbe) Check(context.Context) error {
	return errors.New("probe failed")
}

func writeExecutable(t *testing.T, dir, name, body string) string {
	t.Helper()
	path := filepath.Join(dir, name)
	if err := os.WriteFile(path, []byte(body), 0o755); err != nil {
		t.Fatalf("write executable %s: %v", name, err)
	}
	return path
}

func readText(t *testing.T, path string) string {
	t.Helper()
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("read %s: %v", path, err)
	}
	return string(data)
}

func waitForContains(t *testing.T, path, needle string) {
	t.Helper()
	deadline := time.Now().Add(2 * time.Second)
	for time.Now().Before(deadline) {
		data, err := os.ReadFile(path)
		if err == nil && strings.Contains(string(data), needle) {
			return
		}
		time.Sleep(25 * time.Millisecond)
	}
	t.Fatalf("timed out waiting for %s to contain %q", path, needle)
}

func waitForState(t *testing.T, events <-chan registry.StateEvent, service string, state registry.ServiceState) {
	t.Helper()
	deadline := time.After(5 * time.Second)
	for {
		select {
		case event := <-events:
			if event.Service == service && event.To == state {
				return
			}
		case <-deadline:
			t.Fatalf("timed out waiting for %s to reach %s", service, state)
		}
	}
}

func shellQuote(value string) string {
	return "'" + strings.ReplaceAll(value, "'", "'\\''") + "'"
}
