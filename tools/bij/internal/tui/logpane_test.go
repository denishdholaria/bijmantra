package tui

import (
	"strings"
	"testing"

	"github.com/bijmantra/bij/internal/registry"
	tea "github.com/charmbracelet/bubbletea"
)

func TestLogPaneAppendsAndCapsRingBuffer(t *testing.T) {
	model := NewLogPaneModel(&registry.Service{Name: "backend"}, Options{NoColor: true})

	for i := 0; i < maxLogLines+5; i++ {
		model.Append("line")
	}
	if len(model.Lines) != maxLogLines {
		t.Fatalf("line count = %d, want %d", len(model.Lines), maxLogLines)
	}
}

func TestLogPaneFilterShowsMatchingLines(t *testing.T) {
	model := NewLogPaneModel(&registry.Service{Name: "backend"}, Options{NoColor: true})
	model.Lines = []string{"alpha seed", "beta field", "gamma seed"}
	model.Filter.SetValue("seed")

	view := model.View()
	if !strings.Contains(view, "alpha seed") || !strings.Contains(view, "gamma seed") {
		t.Fatalf("filtered view = %q, want matching lines", view)
	}
	if strings.Contains(view, "beta field") {
		t.Fatalf("filtered view = %q, did not expect nonmatching line", view)
	}
}

func TestLogPaneTabRequestsNextService(t *testing.T) {
	model := NewLogPaneModel(&registry.Service{Name: "backend"}, Options{NoColor: true})

	_, cmd := model.Update(tea.KeyMsg{Type: tea.KeyTab})
	msg, ok := cmd().(SwitchServiceMsg)
	if !ok {
		t.Fatalf("tab command = %#v, want SwitchServiceMsg", cmd())
	}
	if msg.Service != "backend" {
		t.Fatalf("switch service = %q, want backend", msg.Service)
	}
}
