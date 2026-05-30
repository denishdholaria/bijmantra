package workspace

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

var defaultPodmanPath = "/opt/podman/bin/podman"

// ResolveWorkspace returns the workspace root containing compose.yaml.
func ResolveWorkspace(override string) (string, error) {
	if override != "" {
		return resolveOverride(override)
	}

	cwd, err := os.Getwd()
	if err != nil {
		return "", fmt.Errorf("resolve workspace: get current directory: %w", err)
	}

	dir, err := filepath.Abs(cwd)
	if err != nil {
		return "", fmt.Errorf("resolve workspace: absolutize %q: %w", cwd, err)
	}

	for {
		if hasComposeFile(dir) {
			return dir, nil
		}

		parent := filepath.Dir(dir)
		if parent == dir {
			break
		}
		dir = parent
	}

	return "", fmt.Errorf("resolve workspace: compose.yaml not found from %s upward", cwd)
}

// DetectPodman finds the Podman binary using repository runtime precedence.
func DetectPodman() (string, error) {
	if resolved, ok := resolveExecutable(os.Getenv("CONTAINER_RUNTIME")); ok {
		return resolved, nil
	}

	if isExecutable(defaultPodmanPath) {
		return defaultPodmanPath, nil
	}

	if resolved, err := exec.LookPath("podman"); err == nil && isExecutable(resolved) {
		return resolved, nil
	}

	return "", fmt.Errorf("podman not found; install Podman from https://podman.io")
}

// VerifyCompose confirms that podman compose is available.
func VerifyCompose(podman string) error {
	if podman == "" {
		return fmt.Errorf("verify podman compose: podman path is empty")
	}

	cmd := exec.Command(podman, "compose", "version")
	output, err := cmd.CombinedOutput()
	if err != nil {
		message := strings.TrimSpace(string(output))
		if message == "" {
			message = err.Error()
		}
		return fmt.Errorf("verify podman compose: %s", message)
	}

	return nil
}

func resolveOverride(override string) (string, error) {
	root, err := filepath.Abs(override)
	if err != nil {
		return "", fmt.Errorf("resolve workspace override %q: %w", override, err)
	}

	info, err := os.Stat(root)
	if err != nil {
		return "", fmt.Errorf("resolve workspace override %q: %w", root, err)
	}
	if !info.IsDir() {
		return "", fmt.Errorf("resolve workspace override %q: not a directory", root)
	}
	if !hasComposeFile(root) {
		return "", fmt.Errorf("resolve workspace override %q: compose.yaml not found", root)
	}

	return root, nil
}

func hasComposeFile(dir string) bool {
	info, err := os.Stat(filepath.Join(dir, "compose.yaml"))
	return err == nil && !info.IsDir()
}

func resolveExecutable(candidate string) (string, bool) {
	if candidate == "" {
		return "", false
	}

	if filepath.IsAbs(candidate) || strings.Contains(candidate, string(os.PathSeparator)) {
		abs, err := filepath.Abs(candidate)
		if err != nil {
			return "", false
		}
		if isExecutable(abs) {
			return abs, true
		}
		return "", false
	}

	resolved, err := exec.LookPath(candidate)
	if err != nil {
		return "", false
	}
	if !isExecutable(resolved) {
		return "", false
	}

	return resolved, true
}

func isExecutable(path string) bool {
	info, err := os.Stat(path)
	if err != nil || info.IsDir() {
		return false
	}
	return info.Mode()&0o111 != 0
}
