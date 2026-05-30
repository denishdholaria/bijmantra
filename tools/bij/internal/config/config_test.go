package config

import (
	"os"
	"path/filepath"
	"testing"
)

func TestLoadMergesEnvThenYAML(t *testing.T) {
	workspace := t.TempDir()
	writeFile(t, filepath.Join(workspace, ".env"), "BACKEND_PORT=8100\nFRONTEND_PORT=5657\n")
	writeFile(t, filepath.Join(workspace, ".bij.yaml"), `
podman: /custom/podman
services:
  backend:
    port: 8200
    cmd: ["uv", "run", "custom"]
`)

	cfg, err := Load(workspace)
	if err != nil {
		t.Fatalf("Load returned error: %v", err)
	}

	if cfg.Podman != "/custom/podman" {
		t.Fatalf("cfg.Podman = %q, want /custom/podman", cfg.Podman)
	}
	if got := cfg.Services["backend"].Port; got != 8200 {
		t.Fatalf("backend port = %d, want YAML override 8200", got)
	}
	if got := cfg.Services["frontend"].Port; got != 5657 {
		t.Fatalf("frontend port = %d, want .env override 5657", got)
	}
	if got := cfg.Services["backend"].Cmd; len(got) != 3 || got[2] != "custom" {
		t.Fatalf("backend cmd = %#v, want YAML command override", got)
	}
}

func TestLoadIgnoresShellEnvWhenDotEnvMissing(t *testing.T) {
	workspace := t.TempDir()
	t.Setenv("BACKEND_PORT", "9999")

	cfg, err := Load(workspace)
	if err != nil {
		t.Fatalf("Load returned error: %v", err)
	}
	if _, ok := cfg.Services["backend"]; ok {
		t.Fatalf("cfg.Services[backend] exists from shell env, want shell env ignored without .env")
	}
}

func TestLoadReturnsYAMLError(t *testing.T) {
	workspace := t.TempDir()
	writeFile(t, filepath.Join(workspace, ".bij.yaml"), "services:\n  backend: [")

	_, err := Load(workspace)
	if err == nil {
		t.Fatal("Load error = nil, want YAML parse error")
	}
}

func TestLoadSupportsLivePortAliases(t *testing.T) {
	workspace := t.TempDir()
	writeFile(t, filepath.Join(workspace, ".env"), "OPENCLAW_GATEWAY_PORT=18791\nBEINGBIJMANTRA_SURREAL_PORT=8085\n")

	cfg, err := Load(workspace)
	if err != nil {
		t.Fatalf("Load returned error: %v", err)
	}

	if got := cfg.Services["chloe-gateway"].Port; got != 18791 {
		t.Fatalf("chloe-gateway port = %d, want OPENCLAW_GATEWAY_PORT 18791", got)
	}
	if got := cfg.Services["beingbijmantra"].Port; got != 8085 {
		t.Fatalf("beingbijmantra port = %d, want BEINGBIJMANTRA_SURREAL_PORT 8085", got)
	}
}

func writeFile(t *testing.T, path, contents string) {
	t.Helper()
	if err := os.WriteFile(path, []byte(contents), 0o644); err != nil {
		t.Fatalf("write %s: %v", path, err)
	}
}
