package config

import (
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"

	"github.com/joho/godotenv"
	"gopkg.in/yaml.v3"
)

type Config struct {
	Podman   string                     `yaml:"podman"`
	Services map[string]ServiceOverride `yaml:"services"`
}

type ServiceOverride struct {
	Port int      `yaml:"port"`
	Cmd  []string `yaml:"cmd"`
}

var servicePortEnv = map[string][]string{
	"postgres":       {"POSTGRES_PORT"},
	"redis":          {"REDIS_PORT"},
	"minio":          {"MINIO_PORT"},
	"meilisearch":    {"MEILISEARCH_PORT"},
	"beingbijmantra": {"BEINGBIJMANTRA_PORT", "BEINGBIJMANTRA_SURREAL_PORT"},
	"backend":        {"BACKEND_PORT"},
	"frontend":       {"FRONTEND_PORT"},
	"chloe-gateway":  {"CHLOE_GATEWAY_PORT", "OPENCLAW_GATEWAY_PORT"},
}

// Load reads .env and .bij.yaml from the workspace and merges their overrides.
func Load(workspace string) (*Config, error) {
	cfg := &Config{Services: map[string]ServiceOverride{}}

	if err := applyDotEnv(cfg, filepath.Join(workspace, ".env")); err != nil {
		return nil, err
	}

	if err := applyYAML(cfg, filepath.Join(workspace, ".bij.yaml")); err != nil {
		return nil, err
	}

	return cfg, nil
}

func applyDotEnv(cfg *Config, path string) error {
	values, err := godotenv.Read(path)
	if err != nil {
		return nil
	}

	for service, keys := range servicePortEnv {
		for _, key := range keys {
			raw, ok := values[key]
			if !ok || strings.TrimSpace(raw) == "" {
				continue
			}
			port, err := strconv.Atoi(raw)
			if err != nil {
				return fmt.Errorf("load .env: invalid %s=%q: %w", key, raw, err)
			}
			override := cfg.Services[service]
			override.Port = port
			cfg.Services[service] = override
			break
		}
	}

	return nil
}

func applyYAML(cfg *Config, path string) error {
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return nil
		}
		return fmt.Errorf("load .bij.yaml: %w", err)
	}

	fileCfg := &Config{}
	if err := yaml.Unmarshal(data, fileCfg); err != nil {
		return fmt.Errorf("load .bij.yaml: %w", err)
	}

	merge(cfg, fileCfg)
	return nil
}

func merge(base, override *Config) {
	if override.Podman != "" {
		base.Podman = override.Podman
	}

	if base.Services == nil {
		base.Services = map[string]ServiceOverride{}
	}
	for name, next := range override.Services {
		current := base.Services[name]
		if next.Port != 0 {
			current.Port = next.Port
		}
		if next.Cmd != nil {
			current.Cmd = cloneStrings(next.Cmd)
		}
		base.Services[name] = current
	}
}

func cloneStrings(values []string) []string {
	if values == nil {
		return nil
	}
	out := make([]string, len(values))
	copy(out, values)
	return out
}
