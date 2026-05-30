package registry

import (
	"fmt"
	"path/filepath"

	"github.com/bijmantra/bij/internal/config"
)

// DefaultRegistry returns the built-in BijMantra development service registry.
func DefaultRegistry(workspace, podman string) []*Service {
	logDir := filepath.Join(workspace, "logs")

	return []*Service{
		{
			Name:           "postgres",
			Label:          "PostgreSQL",
			Type:           ContainerService,
			Group:          ServiceGroupCore,
			Port:           5432,
			ComposeService: "postgres",
			ContainerName:  "bijmantra-postgres",
			Probe: ExecProbe{
				Container: "bijmantra-postgres",
				Cmd:       []string{"pg_isready", "-U", "bijmantra_user", "-d", "bijmantra_db"},
				Runtime:   podman,
			},
			LogSource: PodmanLogSource{Container: "bijmantra-postgres", Runtime: podman},
			State:     StateWaiting,
		},
		{
			Name:            "redis",
			Label:           "Redis",
			Type:            ContainerService,
			Group:           ServiceGroupInfra,
			Port:            6379,
			ComposeService:  "redis",
			ContainerName:   "bijmantra-redis",
			ComposeProfiles: []string{"infra"},
			Probe: ExecProbe{
				Container: "bijmantra-redis",
				Cmd:       []string{"redis-cli", "ping"},
				Runtime:   podman,
			},
			LogSource: PodmanLogSource{Container: "bijmantra-redis", Runtime: podman},
			State:     StateWaiting,
		},
		{
			Name:            "minio",
			Label:           "MinIO",
			Type:            ContainerService,
			Group:           ServiceGroupInfra,
			Port:            9000,
			ComposeService:  "minio",
			ContainerName:   "bijmantra-minio",
			ComposeProfiles: []string{"infra"},
			Probe:           HTTPProbe{URL: "http://localhost:9000/minio/health/live"},
			LogSource:       PodmanLogSource{Container: "bijmantra-minio", Runtime: podman},
			State:           StateWaiting,
		},
		{
			Name:            "meilisearch",
			Label:           "Meilisearch",
			Type:            ContainerService,
			Group:           ServiceGroupInfra,
			Port:            7700,
			ComposeService:  "meilisearch",
			ContainerName:   "bijmantra-meilisearch",
			ComposeProfiles: []string{"infra"},
			Probe:           HTTPProbe{URL: "http://localhost:7700/health"},
			LogSource:       PodmanLogSource{Container: "bijmantra-meilisearch", Runtime: podman},
			State:           StateWaiting,
		},
		{
			Name:            "beingbijmantra",
			Label:           "BeingBijmantra",
			Type:            ContainerService,
			Group:           ServiceGroupAutonomy,
			Experimental:    true,
			Port:            8083,
			ComposeService:  "beingbijmantra-surrealdb",
			ContainerName:   "beingbijmantra-surrealdb",
			ComposeProfiles: []string{"beingbijmantra"},
			Probe:           TCPProbe{Host: "localhost", Port: 8083},
			LogSource:       PodmanLogSource{Container: "beingbijmantra-surrealdb", Runtime: podman},
			State:           StateWaiting,
		},
		{
			Name:      "backend",
			Label:     "Backend API",
			Type:      ProcessService,
			Group:     ServiceGroupCore,
			Port:      8000,
			Cmd:       backendCommand(8000),
			WorkDir:   filepath.Join(workspace, "backend"),
			Probe:     HTTPProbe{URL: "http://localhost:8000/health"},
			LogSource: FileLogSource{Path: filepath.Join(logDir, "backend.log")},
			State:     StateWaiting,
		},
		{
			Name:      "frontend",
			Label:     "Frontend",
			Type:      ProcessService,
			Group:     ServiceGroupCore,
			Port:      5656,
			Cmd:       []string{"bun", "run", "dev"},
			WorkDir:   filepath.Join(workspace, "frontend"),
			Probe:     HTTPProbe{URL: "http://localhost:5656/"},
			LogSource: FileLogSource{Path: filepath.Join(logDir, "frontend.log")},
			State:     StateWaiting,
		},
		{
			Name:            "chloe-gateway",
			Label:           "Chloe Gateway",
			Type:            ContainerService,
			Group:           ServiceGroupAutonomy,
			Experimental:    true,
			Port:            18790,
			ComposeService:  "chloe-gateway",
			ContainerName:   "bijmantra-chloe-gateway",
			ComposeProfiles: []string{"chloe"},
			Probe:           HTTPProbe{URL: "http://127.0.0.1:18790/healthz"},
			LogSource:       PodmanLogSource{Container: "bijmantra-chloe-gateway", Runtime: podman},
			State:           StateWaiting,
		},
		{
			Name:            "chloe-cli",
			Label:           "Chloe CLI",
			Type:            ContainerService,
			Group:           ServiceGroupAutonomy,
			Experimental:    true,
			ComposeService:  "chloe-cli",
			ContainerName:   "bijmantra-chloe-cli",
			ComposeProfiles: []string{"chloe"},
			Probe:           ContainerRunningProbe{Container: "bijmantra-chloe-cli", Runtime: podman},
			LogSource:       PodmanLogSource{Container: "bijmantra-chloe-cli", Runtime: podman},
			State:           StateWaiting,
		},
		{
			Name:            "chloe-sandbox",
			Label:           "Chloe Sandbox",
			Type:            ContainerService,
			Group:           ServiceGroupAutonomy,
			Experimental:    true,
			ComposeService:  "chloe-sandbox",
			ContainerName:   "bijmantra-chloe-sandbox",
			ComposeProfiles: []string{"chloe"},
			Probe:           ContainerRunningProbe{Container: "bijmantra-chloe-sandbox", Runtime: podman},
			LogSource:       PodmanLogSource{Container: "bijmantra-chloe-sandbox", Runtime: podman},
			State:           StateWaiting,
		},
	}
}

// Apply merges config overrides onto the service registry in-place.
func Apply(services []*Service, cfg *config.Config) {
	if cfg == nil {
		return
	}

	for _, svc := range services {
		override, ok := cfg.Services[svc.Name]
		if !ok {
			continue
		}
		hadCommandOverride := override.Cmd != nil

		if override.Port != 0 {
			svc.Port = override.Port
		}
		if hadCommandOverride {
			svc.Cmd = cloneStrings(override.Cmd)
		}
		if override.Port != 0 && !hadCommandOverride && svc.Name == "backend" {
			svc.Cmd = backendCommand(svc.Port)
		}

		refreshProbe(svc)
	}
}

func refreshProbe(svc *Service) {
	switch svc.Name {
	case "minio":
		svc.Probe = HTTPProbe{URL: fmt.Sprintf("http://localhost:%d/minio/health/live", svc.Port)}
	case "meilisearch":
		svc.Probe = HTTPProbe{URL: fmt.Sprintf("http://localhost:%d/health", svc.Port)}
	case "beingbijmantra":
		svc.Probe = TCPProbe{Host: "localhost", Port: svc.Port}
	case "backend":
		svc.Probe = HTTPProbe{URL: fmt.Sprintf("http://localhost:%d/health", svc.Port)}
	case "frontend":
		svc.Probe = HTTPProbe{URL: fmt.Sprintf("http://localhost:%d/", svc.Port)}
	case "chloe-gateway":
		svc.Probe = HTTPProbe{URL: fmt.Sprintf("http://127.0.0.1:%d/healthz", svc.Port)}
	}
}

func backendCommand(port int) []string {
	return []string{
		"uv",
		"run",
		"uvicorn",
		"app.main:app",
		"--reload",
		"--host",
		"0.0.0.0",
		"--port",
		fmt.Sprintf("%d", port),
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
