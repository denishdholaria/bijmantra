package registry

import (
	"context"
	"fmt"
	"io"
	"net"
	"net/http"
	"os/exec"
	"strconv"
	"strings"
	"time"
)

func (p TCPProbe) Check(ctx context.Context) error {
	if p.Port <= 0 {
		return fmt.Errorf("tcp probe: invalid port %d", p.Port)
	}

	host := p.Host
	if host == "" {
		host = "localhost"
	}

	ctx = usableContext(ctx)
	dialer := &net.Dialer{}
	conn, err := dialer.DialContext(ctx, "tcp", net.JoinHostPort(host, strconv.Itoa(p.Port)))
	if err != nil {
		return fmt.Errorf("tcp probe %s:%d: %w", host, p.Port, err)
	}
	_ = conn.Close()
	return nil
}

func (p HTTPProbe) Check(ctx context.Context) error {
	if p.URL == "" {
		return fmt.Errorf("http probe: URL is empty")
	}

	ctx = usableContext(ctx)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, p.URL, nil)
	if err != nil {
		return fmt.Errorf("http probe %s: %w", p.URL, err)
	}

	client := &http.Client{Timeout: 2 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("http probe %s: %w", p.URL, err)
	}
	defer resp.Body.Close()
	_, _ = io.Copy(io.Discard, resp.Body)

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("http probe %s: status %d", p.URL, resp.StatusCode)
	}

	return nil
}

func (p ExecProbe) Check(ctx context.Context) error {
	if p.Runtime == "" {
		return fmt.Errorf("exec probe: runtime is empty")
	}
	if p.Container == "" {
		return fmt.Errorf("exec probe: container is empty")
	}
	if len(p.Cmd) == 0 {
		return fmt.Errorf("exec probe %s: command is empty", p.Container)
	}

	args := append([]string{"exec", p.Container}, p.Cmd...)
	cmd := exec.CommandContext(usableContext(ctx), p.Runtime, args...)
	output, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("exec probe %s: %s", p.Container, probeOutput(output, err))
	}

	return nil
}

func (p ContainerRunningProbe) Check(ctx context.Context) error {
	if p.Runtime == "" {
		return fmt.Errorf("container running probe: runtime is empty")
	}
	if p.Container == "" {
		return fmt.Errorf("container running probe: container is empty")
	}

	cmd := exec.CommandContext(
		usableContext(ctx),
		p.Runtime,
		"ps",
		"--filter",
		"name="+p.Container,
		"--format",
		"{{.Names}}",
	)
	output, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("container running probe %s: %s", p.Container, probeOutput(output, err))
	}

	for _, line := range strings.Split(string(output), "\n") {
		if strings.TrimSpace(line) == p.Container {
			return nil
		}
	}

	return fmt.Errorf("container running probe %s: container not running", p.Container)
}

func usableContext(ctx context.Context) context.Context {
	if ctx == nil {
		return context.Background()
	}
	return ctx
}

func probeOutput(output []byte, err error) string {
	message := strings.TrimSpace(string(output))
	if message == "" {
		message = err.Error()
	}
	return message
}
