package registry

import (
	"path/filepath"
	"reflect"
	"testing"

	"github.com/bijmantra/bij/internal/config"
)

func TestDefaultRegistryDefinesBijMantraServices(t *testing.T) {
	workspace := t.TempDir()
	services := DefaultRegistry(workspace, "/bin/podman")

	wantNames := []string{
		"postgres",
		"redis",
		"minio",
		"meilisearch",
		"beingbijmantra",
		"backend",
		"frontend",
		"chloe-gateway",
		"chloe-cli",
		"chloe-sandbox",
	}
	if got := serviceNames(services); !reflect.DeepEqual(got, wantNames) {
		t.Fatalf("service names = %#v, want %#v", got, wantNames)
	}

	backend := findService(t, services, "backend")
	if backend.Type != ProcessService {
		t.Fatalf("backend type = %v, want ProcessService", backend.Type)
	}
	if backend.Port != 8000 {
		t.Fatalf("backend port = %d, want 8000", backend.Port)
	}
	if backend.WorkDir != filepath.Join(workspace, "backend") {
		t.Fatalf("backend WorkDir = %q, want workspace/backend", backend.WorkDir)
	}
	if got, ok := backend.Probe.(HTTPProbe); !ok || got.URL != "http://localhost:8000/health" {
		t.Fatalf("backend probe = %#v, want HTTPProbe for /health", backend.Probe)
	}
	if got, ok := backend.LogSource.(FileLogSource); !ok || got.Path != filepath.Join(workspace, "logs", "backend.log") {
		t.Fatalf("backend log source = %#v, want backend.log FileLogSource", backend.LogSource)
	}

	frontend := findService(t, services, "frontend")
	if frontend.Port != 5656 {
		t.Fatalf("frontend port = %d, want live default 5656", frontend.Port)
	}

	postgres := findService(t, services, "postgres")
	if postgres.ComposeService != "postgres" || postgres.ContainerName != "bijmantra-postgres" {
		t.Fatalf("postgres compose/container = %q/%q, want postgres/bijmantra-postgres", postgres.ComposeService, postgres.ContainerName)
	}

	being := findService(t, services, "beingbijmantra")
	if being.ComposeService != "beingbijmantra-surrealdb" || being.ContainerName != "beingbijmantra-surrealdb" {
		t.Fatalf("beingbijmantra compose/container = %q/%q, want beingbijmantra-surrealdb", being.ComposeService, being.ContainerName)
	}

	chloe := findService(t, services, "chloe-gateway")
	if chloe.Port != 18790 {
		t.Fatalf("chloe-gateway port = %d, want live default 18790", chloe.Port)
	}
	if got, ok := chloe.Probe.(HTTPProbe); !ok || got.URL != "http://127.0.0.1:18790/healthz" {
		t.Fatalf("chloe-gateway probe = %#v, want HTTPProbe on 18790", chloe.Probe)
	}

	if being.Group != ServiceGroupAutonomy || !being.Experimental {
		t.Fatalf("beingbijmantra classification = group %q experimental %v, want autonomy experimental", being.Group, being.Experimental)
	}
	if chloe.Group != ServiceGroupAutonomy || !chloe.Experimental {
		t.Fatalf("chloe-gateway classification = group %q experimental %v, want autonomy experimental", chloe.Group, chloe.Experimental)
	}
}

func TestApplyOverridesPortsAndCommandsWithoutClobberingDefaults(t *testing.T) {
	workspace := t.TempDir()
	services := DefaultRegistry(workspace, "/bin/podman")
	cfg := &config.Config{
		Services: map[string]config.ServiceOverride{
			"backend": {
				Port: 8200,
				Cmd:  []string{"uv", "run", "custom"},
			},
			"frontend": {
				Port: 5660,
			},
		},
	}

	Apply(services, cfg)

	backend := findService(t, services, "backend")
	if backend.Port != 8200 {
		t.Fatalf("backend port = %d, want override 8200", backend.Port)
	}
	if got := backend.Cmd; !reflect.DeepEqual(got, []string{"uv", "run", "custom"}) {
		t.Fatalf("backend cmd = %#v, want command override", got)
	}
	if got, ok := backend.Probe.(HTTPProbe); !ok || got.URL != "http://localhost:8200/health" {
		t.Fatalf("backend probe = %#v, want port-adjusted HTTPProbe", backend.Probe)
	}

	frontend := findService(t, services, "frontend")
	if frontend.Port != 5660 {
		t.Fatalf("frontend port = %d, want override 5660", frontend.Port)
	}
	if got := frontend.Cmd; !reflect.DeepEqual(got, []string{"bun", "run", "dev"}) {
		t.Fatalf("frontend cmd = %#v, want default command preserved", got)
	}
}

func TestServicesForGroupKeepsAutonomyExplicit(t *testing.T) {
	workspace := t.TempDir()
	services := DefaultRegistry(workspace, "/bin/podman")

	tests := []struct {
		name     string
		group    ServiceGroup
		services []string
		profiles []string
	}{
		{
			name:     "core",
			group:    ServiceGroupCore,
			services: []string{"postgres", "backend", "frontend"},
			profiles: []string{},
		},
		{
			name:     "infra",
			group:    ServiceGroupInfra,
			services: []string{"postgres", "redis", "minio", "meilisearch", "backend", "frontend"},
			profiles: []string{"infra"},
		},
		{
			name:     "autonomy",
			group:    ServiceGroupAutonomy,
			services: []string{"postgres", "redis", "minio", "meilisearch", "beingbijmantra", "backend", "frontend", "chloe-gateway", "chloe-cli", "chloe-sandbox"},
			profiles: []string{"infra", "beingbijmantra", "chloe"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			gotServices := serviceNames(ServicesForGroup(services, tt.group))
			if !reflect.DeepEqual(gotServices, tt.services) {
				t.Fatalf("ServicesForGroup(%q) = %#v, want %#v", tt.group, gotServices, tt.services)
			}

			gotProfiles := ComposeProfilesForGroup(services, tt.group)
			if !reflect.DeepEqual(gotProfiles, tt.profiles) {
				t.Fatalf("ComposeProfilesForGroup(%q) = %#v, want %#v", tt.group, gotProfiles, tt.profiles)
			}
		})
	}
}

func TestParseServiceGroup(t *testing.T) {
	got, err := ParseServiceGroup("infra")
	if err != nil {
		t.Fatalf("ParseServiceGroup returned error: %v", err)
	}
	if got != ServiceGroupInfra {
		t.Fatalf("ParseServiceGroup = %q, want infra", got)
	}

	if _, err := ParseServiceGroup("chloe"); err == nil {
		t.Fatal("ParseServiceGroup(\"chloe\") error = nil, want invalid group error")
	}
}

func serviceNames(services []*Service) []string {
	names := make([]string, 0, len(services))
	for _, svc := range services {
		names = append(names, svc.Name)
	}
	return names
}

func findService(t *testing.T, services []*Service, name string) *Service {
	t.Helper()
	for _, svc := range services {
		if svc.Name == name {
			return svc
		}
	}
	t.Fatalf("service %q not found", name)
	return nil
}
