package tui

import (
	"strings"
	"testing"

	"github.com/bijmantra/bij/internal/registry"
	tea "github.com/charmbracelet/bubbletea"
)

func TestRootModelSwitchesFromDashboardToPickerAndLogPane(t *testing.T) {
	services := []*registry.Service{
		{Name: "backend", Label: "Backend", LogSource: registry.FileLogSource{Path: "backend.log"}},
		{Name: "frontend", Label: "Frontend", LogSource: registry.FileLogSource{Path: "frontend.log"}},
	}
	model := NewModel(services, nil, Options{NoColor: true})

	next, _ := model.Update(OpenLogsMsg{})
	model = next.(Model)
	if model.ActiveView != ViewPicker {
		t.Fatalf("active view = %v, want picker", model.ActiveView)
	}

	next, _ = model.Update(ServiceSelectedMsg{Service: "frontend"})
	model = next.(Model)
	if model.ActiveView != ViewLogPane || model.LogPane.Service.Name != "frontend" {
		t.Fatalf("active/log service = %v/%v, want log pane frontend", model.ActiveView, model.LogPane.Service)
	}
}

func TestRootModelRoutesLogLinesToLogPane(t *testing.T) {
	services := []*registry.Service{
		{Name: "backend", Label: "Backend", LogSource: registry.FileLogSource{Path: "backend.log"}},
	}
	model := NewModel(services, nil, Options{NoColor: true})

	next, _ := model.Update(LogLineMsg{Service: "backend", Line: "server ready"})
	model = next.(Model)

	if !strings.Contains(model.LogPane.View(), "server ready") {
		t.Fatalf("log pane view = %q, want routed log line", model.LogPane.View())
	}
}

func TestRootModelDashboardKeyCanOpenLogs(t *testing.T) {
	services := []*registry.Service{
		{Name: "backend", Label: "Backend", LogSource: registry.FileLogSource{Path: "backend.log"}},
	}
	model := NewModel(services, nil, Options{NoColor: true})

	next, cmd := model.Update(tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune("l")})
	model = next.(Model)
	msg := cmd()
	next, _ = model.Update(msg)
	model = next.(Model)

	if model.ActiveView != ViewLogPane {
		t.Fatalf("active view = %v, want log pane for single log service", model.ActiveView)
	}
}
