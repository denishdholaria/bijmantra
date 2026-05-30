package tui

import (
	"context"

	"github.com/bijmantra/bij/internal/registry"
	tea "github.com/charmbracelet/bubbletea"
)

type Options struct {
	NoColor   bool
	ReadOnly  bool
	Runtime   string
	ProbeAll  func(context.Context)
	LogStream func(*registry.Service) tea.Cmd
}
