package orchestrator

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"syscall"
	"time"

	"github.com/bijmantra/bij/internal/registry"
)

func StartProcess(ctx context.Context, svc *registry.Service, logDir string) error {
	if svc == nil {
		return fmt.Errorf("service is nil")
	}
	if svc.Type != registry.ProcessService {
		return fmt.Errorf("service %s is not a process service", svc.Name)
	}
	if len(svc.Cmd) == 0 {
		return fmt.Errorf("service %s has no command", svc.Name)
	}
	if logDir == "" {
		return fmt.Errorf("log directory is empty")
	}
	if err := os.MkdirAll(logDir, 0o755); err != nil {
		return fmt.Errorf("create log directory: %w", err)
	}

	logPath := filepath.Join(logDir, svc.Name+".log")
	logFile, err := os.OpenFile(logPath, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		return fmt.Errorf("open process log %s: %w", logPath, err)
	}

	cmd := exec.CommandContext(usableContext(ctx), svc.Cmd[0], svc.Cmd[1:]...)
	cmd.Dir = svc.WorkDir
	cmd.Stdout = logFile
	cmd.Stderr = logFile

	if err := cmd.Start(); err != nil {
		_ = logFile.Close()
		return fmt.Errorf("start process %s: %w", svc.Name, err)
	}
	_ = logFile.Close()

	done := make(chan struct{})
	svc.Process = cmd
	svc.PID = cmd.Process.Pid
	svc.ProcessDone = done
	svc.ProcessErr = nil
	svc.StartedAt = time.Now()

	go func() {
		svc.ProcessErr = cmd.Wait()
		close(done)
	}()

	return nil
}

func StopProcess(ctx context.Context, svc *registry.Service, force bool) error {
	if svc == nil {
		return fmt.Errorf("service is nil")
	}
	ctx = usableContext(ctx)
	cmd := svc.Process
	if cmd == nil || cmd.Process == nil {
		clearProcess(svc)
		return nil
	}

	if force {
		_ = cmd.Process.Kill()
	} else {
		_ = cmd.Process.Signal(syscall.SIGTERM)
	}

	done := svc.ProcessDone
	if done == nil {
		done = closedProcessDone()
	}

	timer := time.NewTimer(10 * time.Second)
	defer timer.Stop()

	select {
	case <-done:
		clearProcess(svc)
		return nil
	case <-timer.C:
		_ = cmd.Process.Kill()
		<-done
		clearProcess(svc)
		return nil
	case <-ctx.Done():
		if force {
			_ = cmd.Process.Kill()
			<-done
			clearProcess(svc)
		}
		return ctx.Err()
	}
}

func clearProcess(svc *registry.Service) {
	svc.PID = 0
	svc.Process = nil
	svc.ProcessDone = nil
	svc.ProcessErr = nil
}

func closedProcessDone() <-chan struct{} {
	done := make(chan struct{})
	close(done)
	return done
}
