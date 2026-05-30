package orchestrator

import (
	"context"
	"fmt"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"github.com/bijmantra/bij/internal/logger"
	"github.com/bijmantra/bij/internal/registry"
)

type Orchestrator struct {
	Services []*registry.Service
	Events   chan registry.StateEvent

	podman      string
	workspace   string
	composeFile string
	log         *logger.Logger
	mu          sync.Mutex
	managed     map[string]bool
}

func New(services []*registry.Service, podman, workspace string, log *logger.Logger) *Orchestrator {
	return &Orchestrator{
		Services:    services,
		Events:      make(chan registry.StateEvent, 256),
		podman:      podman,
		workspace:   workspace,
		composeFile: filepath.Join(workspace, "compose.yaml"),
		log:         log,
		managed:     map[string]bool{},
	}
}

func (o *Orchestrator) Boot(ctx context.Context, profile string) {
	go o.boot(usableContext(ctx), profile)
}

func (o *Orchestrator) Stop(ctx context.Context, force bool) error {
	ctx = usableContext(ctx)
	var firstErr error

	for i := len(bootOrder) - 1; i >= 0; i-- {
		var wg sync.WaitGroup
		var mu sync.Mutex
		for _, name := range bootOrder[i] {
			if name == migrationsStep {
				continue
			}
			svc := o.findService(name)
			if svc == nil || !o.isManaged(svc.Name) {
				continue
			}

			wg.Add(1)
			go func(svc *registry.Service) {
				defer wg.Done()

				o.transition(svc, registry.StateStopping, "stopping service")
				serviceCtx, cancel := context.WithTimeout(ctx, 15*time.Second)
				defer cancel()

				var err error
				switch svc.Type {
				case registry.ContainerService:
					err = o.StopContainer(serviceCtx, svc)
				case registry.ProcessService:
					err = StopProcess(serviceCtx, svc, force)
				}
				if err != nil {
					o.transition(svc, registry.StateFailed, err.Error())
					mu.Lock()
					if firstErr == nil {
						firstErr = err
					}
					mu.Unlock()
					return
				}

				o.setManaged(svc.Name, false)
				o.transition(svc, registry.StateStopped, "service stopped")
			}(svc)
		}
		wg.Wait()
	}

	return firstErr
}

func (o *Orchestrator) Restart(ctx context.Context, name string) error {
	svc := o.findService(name)
	if svc == nil {
		return fmt.Errorf("unknown service %q", name)
	}

	if svc.Type == registry.ContainerService && !o.isManaged(svc.Name) {
		o.transition(svc, registry.StateStarting, "restarting service")
		if err := o.RestartContainer(ctx, svc); err != nil {
			o.transition(svc, registry.StateFailed, err.Error())
			return err
		}
		o.setManaged(svc.Name, true)
		if !o.WaitReady(ctx, svc, 60*time.Second) {
			return fmt.Errorf("service %s did not become ready", svc.Name)
		}
		return nil
	}

	if o.isManaged(svc.Name) {
		o.transition(svc, registry.StateStopping, "restarting service")
		var err error
		switch svc.Type {
		case registry.ContainerService:
			err = o.StopContainer(ctx, svc)
		case registry.ProcessService:
			err = StopProcess(ctx, svc, false)
		}
		if err != nil {
			o.transition(svc, registry.StateFailed, err.Error())
			return err
		}
		o.setManaged(svc.Name, false)
		o.transition(svc, registry.StateStopped, "service stopped")
	}

	return o.startService(usableContext(ctx), svc, true)
}

func (o *Orchestrator) MarkManaged(name string) {
	o.setManaged(name, true)
}

func (o *Orchestrator) ProbeAll(ctx context.Context) {
	ctx = usableContext(ctx)
	var wg sync.WaitGroup
	for _, svc := range o.Services {
		if svc.Probe == nil {
			continue
		}
		wg.Add(1)
		go func(svc *registry.Service) {
			defer wg.Done()
			if err := svc.Probe.Check(ctx); err != nil {
				o.transition(svc, registry.StateDegraded, err.Error())
				return
			}
			o.transition(svc, registry.StateReady, "health probe passed")
		}(svc)
	}
	wg.Wait()
}

func (o *Orchestrator) StartContainer(ctx context.Context, svc *registry.Service) error {
	return StartContainer(ctx, o.podman, o.composeFile, svc)
}

func (o *Orchestrator) StopContainer(ctx context.Context, svc *registry.Service) error {
	return StopContainer(ctx, o.podman, o.composeFile, svc)
}

func (o *Orchestrator) RestartContainer(ctx context.Context, svc *registry.Service) error {
	return RestartContainer(ctx, o.podman, o.composeFile, svc)
}

func (o *Orchestrator) WaitReady(ctx context.Context, svc *registry.Service, timeout time.Duration) bool {
	if svc == nil {
		return false
	}
	ctx = usableContext(ctx)
	if timeout <= 0 {
		timeout = 60 * time.Second
	}

	deadline := time.NewTimer(timeout)
	defer deadline.Stop()

	ticker := time.NewTicker(300 * time.Millisecond)
	defer ticker.Stop()

	for {
		if svc.Probe == nil || svc.Probe.Check(ctx) == nil {
			o.transition(svc, registry.StateReady, "health probe passed")
			return true
		}

		select {
		case <-ctx.Done():
			o.transition(svc, registry.StateFailed, ctx.Err().Error())
			return false
		case <-deadline.C:
			o.transition(svc, registry.StateFailed, "health probe timed out")
			return false
		case <-ticker.C:
		}
	}
}

func (o *Orchestrator) boot(ctx context.Context, profile string) {
	group := registry.ServiceGroupInfra
	if profile != "" {
		parsed, err := registry.ParseServiceGroup(profile)
		if err != nil {
			o.emit(registry.StateEvent{
				Time:    time.Now(),
				Service: "orchestrator",
				From:    registry.StateWaiting,
				To:      registry.StateFailed,
				Message: err.Error(),
			})
			return
		}
		group = parsed
	}

	selected := map[string]bool{}
	for _, svc := range registry.ServicesForGroup(o.Services, group) {
		selected[svc.Name] = true
	}

	migrationsOK := true
	for _, tier := range bootOrder {
		if len(tier) == 1 && tier[0] == migrationsStep {
			if selected["backend"] {
				migrationsOK = o.runMigrations(ctx)
				if !migrationsOK {
					if backend := o.findService("backend"); backend != nil {
						o.transition(backend, registry.StateFailed, "database migrations failed")
					}
				}
			}
			continue
		}

		var wg sync.WaitGroup
		for _, name := range tier {
			if !selected[name] {
				continue
			}
			if !migrationsOK && (name == "backend" || name == "frontend") {
				continue
			}
			svc := o.findService(name)
			if svc == nil {
				continue
			}

			wg.Add(1)
			go func(svc *registry.Service) {
				defer wg.Done()
				_ = o.startService(ctx, svc, true)
			}(svc)
		}
		wg.Wait()
	}
}

func (o *Orchestrator) startService(ctx context.Context, svc *registry.Service, wait bool) error {
	o.transition(svc, registry.StateStarting, "starting service")

	var err error
	switch svc.Type {
	case registry.ContainerService:
		err = o.StartContainer(ctx, svc)
	case registry.ProcessService:
		err = StartProcess(ctx, svc, filepath.Join(o.workspace, "logs"))
	default:
		err = fmt.Errorf("service %s has unknown type", svc.Name)
	}
	if err != nil {
		o.transition(svc, registry.StateFailed, err.Error())
		return err
	}

	o.setManaged(svc.Name, true)
	if wait && !o.WaitReady(ctx, svc, 60*time.Second) {
		return fmt.Errorf("service %s did not become ready", svc.Name)
	}
	if svc.Type == registry.ProcessService {
		go o.watchProcess(ctx, svc)
	}
	return nil
}

func (o *Orchestrator) runMigrations(ctx context.Context) bool {
	cmd := exec.CommandContext(usableContext(ctx), "uv", "run", "alembic", "upgrade", "head")
	cmd.Dir = filepath.Join(o.workspace, "backend")
	output, err := cmd.CombinedOutput()
	if err != nil {
		message := strings.TrimSpace(string(output))
		if message == "" {
			message = err.Error()
		}
		o.emit(registry.StateEvent{
			Time:    time.Now(),
			Service: migrationsStep,
			From:    registry.StateStarting,
			To:      registry.StateFailed,
			Message: message,
		})
		return false
	}
	o.emit(registry.StateEvent{
		Time:    time.Now(),
		Service: migrationsStep,
		From:    registry.StateStarting,
		To:      registry.StateReady,
		Message: "database migrations complete",
	})
	return true
}

func (o *Orchestrator) watchProcess(ctx context.Context, svc *registry.Service) {
	for {
		done := svc.ProcessDone
		if done == nil {
			return
		}

		select {
		case <-usableContext(ctx).Done():
			return
		case <-done:
		}

		if o.serviceState(svc) == registry.StateStopping || o.serviceState(svc) == registry.StateStopped {
			return
		}

		o.transition(svc, registry.StateDegraded, "process exited unexpectedly")
		if svc.FailCount >= 3 {
			o.transition(svc, registry.StateFailed, "process crashed repeatedly")
			return
		}

		select {
		case <-usableContext(ctx).Done():
			return
		case <-time.After(2 * time.Second):
		}

		if err := StartProcess(ctx, svc, filepath.Join(o.workspace, "logs")); err != nil {
			o.transition(svc, registry.StateFailed, err.Error())
			return
		}
		o.transition(svc, registry.StateStarting, "restarting process")
		if !o.WaitReady(ctx, svc, 60*time.Second) {
			return
		}
	}
}

func (o *Orchestrator) emit(event registry.StateEvent) {
	if event.Time.IsZero() {
		event.Time = time.Now()
	}
	if o.log != nil {
		_ = o.log.Write(logger.Event{
			Time:    event.Time,
			Type:    "state_change",
			Service: event.Service,
			From:    string(event.From),
			To:      string(event.To),
			Message: event.Message,
		})
	}

	select {
	case o.Events <- event:
	default:
	}
}

func (o *Orchestrator) transition(svc *registry.Service, to registry.ServiceState, message string) {
	now := time.Now()

	o.mu.Lock()
	from := svc.State
	svc.State = to
	if to == registry.StateStarting {
		svc.StartedAt = now
		svc.Duration = 0
	}
	if !svc.StartedAt.IsZero() {
		svc.Duration = now.Sub(svc.StartedAt)
	}
	switch to {
	case registry.StateFailed, registry.StateDegraded:
		svc.FailCount++
		svc.LastFailAt = now
	case registry.StateReady:
		if svc.LastFailAt.IsZero() || now.Sub(svc.LastFailAt) > 60*time.Second {
			svc.FailCount = 0
		}
	}
	o.mu.Unlock()

	o.emit(registry.StateEvent{
		Time:    now,
		Service: svc.Name,
		From:    from,
		To:      to,
		Message: message,
	})
}

func (o *Orchestrator) findService(name string) *registry.Service {
	for _, svc := range o.Services {
		if svc.Name == name {
			return svc
		}
	}
	return nil
}

func (o *Orchestrator) setManaged(name string, managed bool) {
	o.mu.Lock()
	defer o.mu.Unlock()
	if managed {
		o.managed[name] = true
		return
	}
	delete(o.managed, name)
}

func (o *Orchestrator) isManaged(name string) bool {
	o.mu.Lock()
	defer o.mu.Unlock()
	return o.managed[name]
}

func (o *Orchestrator) serviceState(svc *registry.Service) registry.ServiceState {
	o.mu.Lock()
	defer o.mu.Unlock()
	return svc.State
}

func usableContext(ctx context.Context) context.Context {
	if ctx == nil {
		return context.Background()
	}
	return ctx
}

const migrationsStep = "_migrations"

var bootOrder = [][]string{
	{"postgres"},
	{"redis", "minio", "meilisearch"},
	{migrationsStep},
	{"backend"},
	{"frontend"},
	{"beingbijmantra", "chloe-gateway", "chloe-cli", "chloe-sandbox"},
}
