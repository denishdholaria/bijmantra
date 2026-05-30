package tui

import (
	"fmt"
	"strings"
	"time"

	"github.com/bijmantra/bij/internal/registry"
	"github.com/charmbracelet/bubbles/key"
	tea "github.com/charmbracelet/bubbletea"
)

type DashboardModel struct {
	Services []*registry.Service
	Events   []registry.StateEvent

	eventCh <-chan registry.StateEvent
	opts    Options
	width   int
	height  int
	start   time.Time
	keys    KeyMap
	styles  Styles
	help    bool
}

func NewDashboardModel(services []*registry.Service, events <-chan registry.StateEvent, opts Options) DashboardModel {
	width := 100
	return DashboardModel{
		Services: services,
		eventCh:  events,
		opts:     opts,
		width:    width,
		height:   30,
		start:    time.Now(),
		keys:     DefaultKeyMap(),
		styles:   NewStyles(opts.NoColor, width),
	}
}

func (m DashboardModel) Init() tea.Cmd {
	cmds := []tea.Cmd{tea.HideCursor}
	if m.eventCh != nil {
		cmds = append(cmds, waitForEvent(m.eventCh))
	}
	cmds = append(cmds, uptimeTick())
	return tea.Batch(cmds...)
}

func (m DashboardModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case StateChangedMsg:
		m.applyStateChange(registry.StateEvent(msg))
		if m.eventCh != nil {
			return m, waitForEvent(m.eventCh)
		}
		return m, nil
	case TickMsg:
		return m, uptimeTick()
	case tea.WindowSizeMsg:
		m.width, m.height = msg.Width, msg.Height
		m.styles = NewStyles(m.opts.NoColor, msg.Width)
		return m, nil
	case tea.KeyMsg:
		switch {
		case key.Matches(msg, m.keys.Quit):
			return m, tea.Batch(tea.ShowCursor, tea.Quit)
		case key.Matches(msg, m.keys.Refresh):
			return m, func() tea.Msg { return RefreshRequestedMsg{} }
		case key.Matches(msg, m.keys.Logs):
			return m, func() tea.Msg { return OpenLogsMsg{} }
		case key.Matches(msg, m.keys.Help):
			m.help = !m.help
			return m, nil
		}
	}
	return m, nil
}

func (m DashboardModel) View() string {
	var out []string
	healthy, total := healthySummary(m.Services)
	out = append(out, m.styles.RenderHeader(m.opts.Runtime, time.Since(m.start), healthy, total))
	out = append(out, "")
	out = append(out, "SERVICES")
	for _, svc := range m.Services {
		out = append(out, m.styles.RenderServiceRow(svc))
	}

	out = append(out, "")
	out = append(out, "LIVE EVENTS")
	for _, event := range m.Events {
		out = append(out, m.styles.RenderEvent(event))
	}
	if len(m.Events) == 0 {
		out = append(out, m.styles.RenderStatusBar("waiting for runtime events"))
	}

	if summary := coreSummary(m.Services); summary != "" {
		out = append(out, "", summary)
	}

	legend := "q quit   r refresh   l logs   ? help"
	if m.help {
		legend = "q quit   r refresh probes   l logs   ? toggle help"
	}
	out = append(out, "", m.styles.RenderStatusBar(legend))
	return strings.Join(out, "\n")
}

func (m *DashboardModel) applyStateChange(event registry.StateEvent) {
	for _, svc := range m.Services {
		if svc.Name != event.Service {
			continue
		}
		svc.State = event.To
		if event.To == registry.StateReady && !svc.StartedAt.IsZero() {
			svc.Duration = event.Time.Sub(svc.StartedAt)
		}
		break
	}

	m.Events = append(m.Events, event)
	if len(m.Events) > 8 {
		m.Events = m.Events[len(m.Events)-8:]
	}
}

func healthySummary(services []*registry.Service) (int, int) {
	healthy := 0
	for _, svc := range services {
		if svc.State == registry.StateReady {
			healthy++
		}
	}
	return healthy, len(services)
}

func coreSummary(services []*registry.Service) string {
	var frontend, backend *registry.Service
	for _, svc := range services {
		switch svc.Name {
		case "frontend":
			frontend = svc
		case "backend":
			backend = svc
		}
	}
	if frontend == nil || backend == nil || frontend.State != registry.StateReady || backend.State != registry.StateReady {
		return ""
	}
	return fmt.Sprintf("Frontend: http://localhost:%d   Backend: http://localhost:%d", frontend.Port, backend.Port)
}

func uptimeTick() tea.Cmd {
	return tea.Tick(time.Second, func(t time.Time) tea.Msg { return TickMsg(t) })
}
