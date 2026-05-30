package tui

import (
	"testing"

	"github.com/bijmantra/bij/internal/registry"
	tea "github.com/charmbracelet/bubbletea"
)

func TestPickerSelectsCurrentService(t *testing.T) {
	services := []*registry.Service{
		{Name: "backend", Label: "Backend", LogSource: registry.FileLogSource{Path: "backend.log"}},
		{Name: "frontend", Label: "Frontend", LogSource: registry.FileLogSource{Path: "frontend.log"}},
	}
	model := NewPickerModel(services, Options{NoColor: true})

	_, cmd := model.Update(tea.KeyMsg{Type: tea.KeyEnter})
	msg, ok := cmd().(ServiceSelectedMsg)
	if !ok {
		t.Fatalf("enter command = %#v, want ServiceSelectedMsg", cmd())
	}
	if msg.Service != "backend" {
		t.Fatalf("selected service = %q, want backend", msg.Service)
	}
}

func TestPickerOnlyListsServicesWithLogSources(t *testing.T) {
	services := []*registry.Service{
		{Name: "backend", LogSource: registry.FileLogSource{Path: "backend.log"}},
		{Name: "no-log"},
	}
	model := NewPickerModel(services, Options{NoColor: true})

	if len(model.Services) != 1 || model.Services[0].Name != "backend" {
		t.Fatalf("picker services = %#v, want only backend", model.Services)
	}
}
