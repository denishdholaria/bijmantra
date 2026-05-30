package tui

import (
	"strings"
	"testing"
	"time"

	"github.com/bijmantra/bij/internal/registry"
	tea "github.com/charmbracelet/bubbletea"
)

func TestDashboardAppliesStateChangesAndRendersSummary(t *testing.T) {
	services := []*registry.Service{
		{Name: "backend", Label: "Backend API", State: registry.StateStarting, Port: 8000, StartedAt: time.Now().Add(-3 * time.Second)},
		{Name: "frontend", Label: "Frontend", State: registry.StateStarting, Port: 5656, StartedAt: time.Now().Add(-2 * time.Second)},
	}
	model := NewDashboardModel(services, nil, Options{NoColor: true, Runtime: "test"})

	next, _ := model.Update(StateChangedMsg{Service: "backend", To: registry.StateReady, Time: time.Now(), Message: "ok"})
	model = next.(DashboardModel)
	next, _ = model.Update(StateChangedMsg{Service: "frontend", To: registry.StateReady, Time: time.Now(), Message: "ok"})
	model = next.(DashboardModel)

	view := model.View()
	if !strings.Contains(view, "2/2 healthy") {
		t.Fatalf("dashboard view = %q, want healthy count", view)
	}
	if !strings.Contains(view, "Frontend: http://localhost:5656") || !strings.Contains(view, "Backend: http://localhost:8000") {
		t.Fatalf("dashboard view = %q, want core URL summary", view)
	}
}

func TestDashboardKeyBindingsEmitCommands(t *testing.T) {
	model := NewDashboardModel(nil, nil, Options{NoColor: true})

	_, cmd := model.Update(tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune("r")})
	if _, ok := cmd().(RefreshRequestedMsg); !ok {
		t.Fatalf("refresh command message = %#v, want RefreshRequestedMsg", cmd())
	}

	_, cmd = model.Update(tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune("l")})
	if _, ok := cmd().(OpenLogsMsg); !ok {
		t.Fatalf("logs command message = %#v, want OpenLogsMsg", cmd())
	}
}
