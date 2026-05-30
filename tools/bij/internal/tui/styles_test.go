package tui

import (
	"strings"
	"testing"
	"time"

	"github.com/bijmantra/bij/internal/registry"
)

func TestNoColorStylesRenderPlainText(t *testing.T) {
	styles := NewStyles(true, 100)
	service := &registry.Service{
		Label:    "Backend API",
		State:    registry.StateReady,
		Port:     8000,
		Duration: 3 * time.Second,
	}

	header := styles.RenderHeader("dev", 5*time.Second, 1, 2)
	row := styles.RenderServiceRow(service)

	for _, value := range []string{header, row} {
		if strings.Contains(value, "\x1b[") {
			t.Fatalf("rendered text contains ANSI sequence: %q", value)
		}
	}
	if !strings.Contains(row, "Backend API") || !strings.Contains(row, "READY") || !strings.Contains(row, "8000") {
		t.Fatalf("service row = %q, want service, state, and port", row)
	}
}

func TestCompactStylesDropHeaderBorder(t *testing.T) {
	styles := NewStyles(false, 60)
	header := styles.RenderHeader("status", 0, 0, 10)

	if strings.Contains(header, "+") || strings.Contains(header, "|") {
		t.Fatalf("compact header = %q, want no border", header)
	}
	if !styles.Compact {
		t.Fatal("styles.Compact = false, want true below width threshold")
	}
}

func TestStateIconsAreStableASCII(t *testing.T) {
	tests := map[registry.ServiceState]string{
		registry.StateReady:    "OK",
		registry.StateDegraded: "!!",
		registry.StateFailed:   "XX",
		registry.StateWaiting:  "--",
	}

	for state, want := range tests {
		if got := stateIcon(state); got != want {
			t.Fatalf("stateIcon(%q) = %q, want %q", state, got, want)
		}
	}
}
