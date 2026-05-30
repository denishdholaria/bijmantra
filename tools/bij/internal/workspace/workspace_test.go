package workspace

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestResolveWorkspaceWalksUpToComposeYaml(t *testing.T) {
	root := t.TempDir()
	nested := filepath.Join(root, "backend", "app")
	mustMkdirAll(t, nested)
	mustWriteFile(t, filepath.Join(root, "compose.yaml"), "services: {}\n")

	original, err := os.Getwd()
	if err != nil {
		t.Fatalf("get cwd: %v", err)
	}
	t.Cleanup(func() { _ = os.Chdir(original) })

	if err := os.Chdir(nested); err != nil {
		t.Fatalf("chdir nested: %v", err)
	}

	got, err := ResolveWorkspace("")
	if err != nil {
		t.Fatalf("ResolveWorkspace returned error: %v", err)
	}
	want := canonicalPath(t, root)
	if got != want {
		t.Fatalf("ResolveWorkspace() = %q, want %q", got, want)
	}
}

func TestResolveWorkspaceReturnsErrorWhenComposeYamlMissing(t *testing.T) {
	root := t.TempDir()

	original, err := os.Getwd()
	if err != nil {
		t.Fatalf("get cwd: %v", err)
	}
	t.Cleanup(func() { _ = os.Chdir(original) })

	if err := os.Chdir(root); err != nil {
		t.Fatalf("chdir temp root: %v", err)
	}

	_, err = ResolveWorkspace("")
	if err == nil {
		t.Fatal("ResolveWorkspace() error = nil, want missing compose.yaml error")
	}
	if !strings.Contains(err.Error(), "compose.yaml") {
		t.Fatalf("ResolveWorkspace() error = %q, want compose.yaml context", err)
	}
}

func TestResolveWorkspaceOverrideUsesExplicitPath(t *testing.T) {
	root := t.TempDir()
	override := filepath.Join(root, "explicit")
	other := filepath.Join(root, "other", "nested")
	mustMkdirAll(t, override)
	mustMkdirAll(t, other)
	mustWriteFile(t, filepath.Join(root, "compose.yaml"), "services: {}\n")
	mustWriteFile(t, filepath.Join(override, "compose.yaml"), "services: {}\n")

	original, err := os.Getwd()
	if err != nil {
		t.Fatalf("get cwd: %v", err)
	}
	t.Cleanup(func() { _ = os.Chdir(original) })

	if err := os.Chdir(other); err != nil {
		t.Fatalf("chdir other: %v", err)
	}

	got, err := ResolveWorkspace(override)
	if err != nil {
		t.Fatalf("ResolveWorkspace override returned error: %v", err)
	}
	if got != override {
		t.Fatalf("ResolveWorkspace(%q) = %q, want %q", override, got, override)
	}
}

func TestResolveWorkspaceOverrideRequiresComposeYaml(t *testing.T) {
	override := t.TempDir()

	_, err := ResolveWorkspace(override)
	if err == nil {
		t.Fatal("ResolveWorkspace override error = nil, want missing compose.yaml error")
	}
	if !strings.Contains(err.Error(), "compose.yaml") {
		t.Fatalf("ResolveWorkspace override error = %q, want compose.yaml context", err)
	}
}

func TestDetectPodmanUsesContainerRuntimeFirst(t *testing.T) {
	fake := writeExecutable(t, t.TempDir(), "custom-podman", "#!/bin/sh\nexit 0\n")
	t.Setenv("CONTAINER_RUNTIME", fake)

	got, err := DetectPodman()
	if err != nil {
		t.Fatalf("DetectPodman returned error: %v", err)
	}
	if got != fake {
		t.Fatalf("DetectPodman() = %q, want CONTAINER_RUNTIME %q", got, fake)
	}
}

func TestDetectPodmanUsesDefaultPathBeforePATH(t *testing.T) {
	defaultFake := writeExecutable(t, t.TempDir(), "podman-default", "#!/bin/sh\nexit 0\n")
	pathDir := t.TempDir()
	pathFake := writeExecutable(t, pathDir, "podman", "#!/bin/sh\nexit 0\n")
	t.Setenv("CONTAINER_RUNTIME", "")
	t.Setenv("PATH", pathDir)

	originalDefault := defaultPodmanPath
	defaultPodmanPath = defaultFake
	t.Cleanup(func() { defaultPodmanPath = originalDefault })

	got, err := DetectPodman()
	if err != nil {
		t.Fatalf("DetectPodman returned error: %v", err)
	}
	if got != defaultFake {
		t.Fatalf("DetectPodman() = %q, want default path %q before PATH %q", got, defaultFake, pathFake)
	}
}

func TestDetectPodmanFallsBackToPATH(t *testing.T) {
	pathDir := t.TempDir()
	pathFake := writeExecutable(t, pathDir, "podman", "#!/bin/sh\nexit 0\n")
	t.Setenv("CONTAINER_RUNTIME", "")
	t.Setenv("PATH", pathDir)

	originalDefault := defaultPodmanPath
	defaultPodmanPath = filepath.Join(t.TempDir(), "missing-podman")
	t.Cleanup(func() { defaultPodmanPath = originalDefault })

	got, err := DetectPodman()
	if err != nil {
		t.Fatalf("DetectPodman returned error: %v", err)
	}
	if got != pathFake {
		t.Fatalf("DetectPodman() = %q, want PATH podman %q", got, pathFake)
	}
}

func TestDetectPodmanErrorsWhenMissing(t *testing.T) {
	t.Setenv("CONTAINER_RUNTIME", "")
	t.Setenv("PATH", "")

	originalDefault := defaultPodmanPath
	defaultPodmanPath = filepath.Join(t.TempDir(), "missing-podman")
	t.Cleanup(func() { defaultPodmanPath = originalDefault })

	_, err := DetectPodman()
	if err == nil {
		t.Fatal("DetectPodman() error = nil, want missing podman error")
	}
	if !strings.Contains(err.Error(), "podman") {
		t.Fatalf("DetectPodman() error = %q, want podman context", err)
	}
}

func TestVerifyComposeRunsPodmanComposeVersion(t *testing.T) {
	fake := writeExecutable(t, t.TempDir(), "podman", `#!/bin/sh
if [ "$1" = "compose" ] && [ "$2" = "version" ]; then
  exit 0
fi
exit 1
`)

	if err := VerifyCompose(fake); err != nil {
		t.Fatalf("VerifyCompose returned error: %v", err)
	}
}

func TestVerifyComposeReturnsErrorOnFailure(t *testing.T) {
	fake := writeExecutable(t, t.TempDir(), "podman", "#!/bin/sh\nexit 42\n")

	err := VerifyCompose(fake)
	if err == nil {
		t.Fatal("VerifyCompose() error = nil, want compose failure")
	}
	if !strings.Contains(err.Error(), "compose") {
		t.Fatalf("VerifyCompose() error = %q, want compose context", err)
	}
}

func mustMkdirAll(t *testing.T, path string) {
	t.Helper()
	if err := os.MkdirAll(path, 0o755); err != nil {
		t.Fatalf("mkdir %s: %v", path, err)
	}
}

func mustWriteFile(t *testing.T, path, contents string) {
	t.Helper()
	if err := os.WriteFile(path, []byte(contents), 0o644); err != nil {
		t.Fatalf("write %s: %v", path, err)
	}
}

func writeExecutable(t *testing.T, dir, name, contents string) string {
	t.Helper()
	path := filepath.Join(dir, name)
	if err := os.WriteFile(path, []byte(contents), 0o755); err != nil {
		t.Fatalf("write executable %s: %v", path, err)
	}
	return path
}

func canonicalPath(t *testing.T, path string) string {
	t.Helper()
	resolved, err := filepath.EvalSymlinks(path)
	if err != nil {
		t.Fatalf("canonicalize %s: %v", path, err)
	}
	return resolved
}
