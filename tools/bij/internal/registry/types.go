package registry

import (
	"context"
	"errors"
	"fmt"
	"os/exec"
	"time"
)

var (
	ErrProbeNotImplemented     = errors.New("health probe check not implemented")
	ErrLogSourceNotImplemented = errors.New("log source stream not implemented")
)

type ServiceType int

const (
	ContainerService ServiceType = iota
	ProcessService
)

type ServiceGroup string

const (
	ServiceGroupCore     ServiceGroup = "core"
	ServiceGroupInfra    ServiceGroup = "infra"
	ServiceGroupAutonomy ServiceGroup = "autonomy"
)

type ServiceState string

const (
	StateWaiting  ServiceState = "waiting"
	StateStarting ServiceState = "starting"
	StateReady    ServiceState = "ready"
	StateDegraded ServiceState = "degraded"
	StateFailed   ServiceState = "failed"
	StateStopping ServiceState = "stopping"
	StateStopped  ServiceState = "stopped"
)

type HealthProbe interface {
	Check(ctx context.Context) error
}

type LogSource interface {
	Stream(ctx context.Context, tailLines int) (<-chan string, error)
}

type Service struct {
	Name            string
	Label           string
	Type            ServiceType
	Group           ServiceGroup
	Experimental    bool
	Port            int
	ComposeService  string
	ContainerName   string
	ComposeProfiles []string
	Cmd             []string
	WorkDir         string
	Probe           HealthProbe
	LogSource       LogSource
	State           ServiceState
	StartedAt       time.Time
	Duration        time.Duration
	FailCount       int
	LastFailAt      time.Time
	PID             int
	Process         *exec.Cmd
	ProcessDone     <-chan struct{}
	ProcessErr      error
}

func ParseServiceGroup(value string) (ServiceGroup, error) {
	switch ServiceGroup(value) {
	case ServiceGroupCore:
		return ServiceGroupCore, nil
	case ServiceGroupInfra:
		return ServiceGroupInfra, nil
	case ServiceGroupAutonomy:
		return ServiceGroupAutonomy, nil
	default:
		return "", fmt.Errorf("unknown service group %q; expected core, infra, or autonomy", value)
	}
}

func ServicesForGroup(services []*Service, group ServiceGroup) []*Service {
	out := make([]*Service, 0, len(services))
	for _, svc := range services {
		if group.Includes(svc) {
			out = append(out, svc)
		}
	}
	return out
}

func ComposeProfilesForGroup(services []*Service, group ServiceGroup) []string {
	profiles := make([]string, 0)
	seen := map[string]bool{}
	for _, svc := range ServicesForGroup(services, group) {
		for _, profile := range svc.ComposeProfiles {
			if profile == "" || seen[profile] {
				continue
			}
			seen[profile] = true
			profiles = append(profiles, profile)
		}
	}
	return profiles
}

func Find(services []*Service, name string) *Service {
	for _, svc := range services {
		if svc.Name == name {
			return svc
		}
	}
	return nil
}

func Names(services []*Service) []string {
	names := make([]string, 0, len(services))
	for _, svc := range services {
		names = append(names, svc.Name)
	}
	return names
}

func (g ServiceGroup) Includes(svc *Service) bool {
	if svc == nil {
		return false
	}
	targetRank, ok := serviceGroupRank(g)
	if !ok {
		return false
	}
	serviceRank, ok := serviceGroupRank(svc.Group)
	if !ok {
		return false
	}
	return serviceRank <= targetRank
}

func serviceGroupRank(group ServiceGroup) (int, bool) {
	switch group {
	case ServiceGroupCore:
		return 0, true
	case ServiceGroupInfra:
		return 1, true
	case ServiceGroupAutonomy:
		return 2, true
	default:
		return 0, false
	}
}

type StateEvent struct {
	Time    time.Time
	Service string
	From    ServiceState
	To      ServiceState
	Message string
}

type TCPProbe struct {
	Host string
	Port int
}

type HTTPProbe struct {
	URL string
}

type ExecProbe struct {
	Container string
	Cmd       []string
	Runtime   string
}

type ContainerRunningProbe struct {
	Container string
	Runtime   string
}

type FileLogSource struct {
	Path string
}

type PodmanLogSource struct {
	Container string
	Runtime   string
}
