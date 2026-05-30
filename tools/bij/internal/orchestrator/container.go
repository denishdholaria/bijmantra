package orchestrator

import (
	"context"
	"fmt"
	"os/exec"
	"strings"

	"github.com/bijmantra/bij/internal/registry"
)

func StartContainer(ctx context.Context, podman, composeFile string, svc *registry.Service) error {
	target, err := composeTarget(svc)
	if err != nil {
		return err
	}
	return runCompose(ctx, podman, composeFile, "up", "-d", target)
}

func StopContainer(ctx context.Context, podman, composeFile string, svc *registry.Service) error {
	target, err := composeTarget(svc)
	if err != nil {
		return err
	}
	return runCompose(ctx, podman, composeFile, "stop", target)
}

func RestartContainer(ctx context.Context, podman, composeFile string, svc *registry.Service) error {
	target, err := composeTarget(svc)
	if err != nil {
		return err
	}
	return runCompose(ctx, podman, composeFile, "restart", target)
}

func runCompose(ctx context.Context, podman, composeFile string, args ...string) error {
	if podman == "" {
		return fmt.Errorf("podman path is empty")
	}
	if composeFile == "" {
		return fmt.Errorf("compose file path is empty")
	}

	fullArgs := append([]string{"compose", "--file", composeFile}, args...)
	cmd := exec.CommandContext(usableContext(ctx), podman, fullArgs...)
	output, err := cmd.CombinedOutput()
	if err != nil {
		message := strings.TrimSpace(string(output))
		if message == "" {
			message = err.Error()
		}
		return fmt.Errorf("podman %s: %s", strings.Join(fullArgs, " "), message)
	}
	return nil
}

func composeTarget(svc *registry.Service) (string, error) {
	if svc == nil {
		return "", fmt.Errorf("service is nil")
	}
	if svc.ComposeService != "" {
		return svc.ComposeService, nil
	}
	if svc.Name != "" {
		return svc.Name, nil
	}
	if svc.ContainerName != "" {
		return svc.ContainerName, nil
	}
	return "", fmt.Errorf("service has no compose target")
}
