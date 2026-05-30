package tui

import (
	"context"
	"time"

	"github.com/bijmantra/bij/internal/registry"
	tea "github.com/charmbracelet/bubbletea"
)

type ViewType int

const (
	ViewDashboard ViewType = iota
	ViewPicker
	ViewLogPane
)

type Model struct {
	ActiveView ViewType
	Services   []*registry.Service
	Dashboard  DashboardModel
	LogPane    LogPaneModel
	Picker     PickerModel
	opts       Options
	current    int
}

func NewModel(services []*registry.Service, events <-chan registry.StateEvent, opts Options) Model {
	dashboard := NewDashboardModel(services, events, opts)
	picker := NewPickerModel(services, opts)
	first := firstLogService(services)
	logPane := NewLogPaneModel(first, opts)
	return Model{
		ActiveView: ViewDashboard,
		Services:   services,
		Dashboard:  dashboard,
		LogPane:    logPane,
		Picker:     picker,
		opts:       opts,
		current:    indexOfService(services, first),
	}
}

func (m Model) Init() tea.Cmd {
	cmds := []tea.Cmd{m.Dashboard.Init()}
	if m.opts.ReadOnly {
		cmds = append(cmds, statusTick())
	}
	return tea.Batch(cmds...)
}

func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case StateChangedMsg:
		next, cmd := m.Dashboard.Update(msg)
		if dashboard, ok := next.(DashboardModel); ok {
			m.Dashboard = dashboard
		}
		return m, cmd
	case TickMsg:
		var cmds []tea.Cmd
		next, cmd := m.Dashboard.Update(msg)
		if dashboard, ok := next.(DashboardModel); ok {
			m.Dashboard = dashboard
		}
		cmds = append(cmds, cmd)
		if m.opts.ReadOnly && m.opts.ProbeAll != nil {
			cmds = append(cmds, func() tea.Msg {
				m.opts.ProbeAll(context.Background())
				return nil
			}, statusTick())
		}
		return m, tea.Batch(cmds...)
	case RefreshRequestedMsg:
		if m.opts.ProbeAll == nil {
			return m, nil
		}
		return m, func() tea.Msg {
			m.opts.ProbeAll(context.Background())
			return nil
		}
	case OpenLogsMsg:
		if len(m.Picker.Services) == 1 {
			m.ActiveView = ViewLogPane
			m.LogPane = NewLogPaneModel(m.Picker.Services[0], m.opts)
			m.current = indexOfService(m.Services, m.Picker.Services[0])
			return m, m.startLogStream(m.Picker.Services[0])
		}
		m.ActiveView = ViewPicker
		return m, nil
	case ServiceSelectedMsg:
		svc := findService(m.Services, msg.Service)
		if svc != nil {
			m.ActiveView = ViewLogPane
			m.LogPane = NewLogPaneModel(svc, m.opts)
			m.current = indexOfService(m.Services, svc)
			return m, m.startLogStream(svc)
		}
		return m, nil
	case SwitchServiceMsg:
		cmd := m.switchToNextLogService()
		return m, cmd
	case LogLineMsg:
		next, cmd := m.LogPane.Update(msg)
		if pane, ok := next.(LogPaneModel); ok {
			m.LogPane = pane
		}
		return m, cmd
	}

	switch m.ActiveView {
	case ViewDashboard:
		next, cmd := m.Dashboard.Update(msg)
		if dashboard, ok := next.(DashboardModel); ok {
			m.Dashboard = dashboard
		}
		return m, cmd
	case ViewPicker:
		next, cmd := m.Picker.Update(msg)
		if picker, ok := next.(PickerModel); ok {
			m.Picker = picker
		}
		return m, cmd
	case ViewLogPane:
		next, cmd := m.LogPane.Update(msg)
		if pane, ok := next.(LogPaneModel); ok {
			m.LogPane = pane
		}
		return m, cmd
	default:
		return m, nil
	}
}

func (m Model) View() string {
	switch m.ActiveView {
	case ViewPicker:
		return m.Picker.View()
	case ViewLogPane:
		return m.LogPane.View()
	default:
		return m.Dashboard.View()
	}
}

func (m *Model) switchToNextLogService() tea.Cmd {
	if len(m.Services) == 0 {
		return nil
	}
	for i := 1; i <= len(m.Services); i++ {
		idx := (m.current + i) % len(m.Services)
		if m.Services[idx].LogSource == nil {
			continue
		}
		m.current = idx
		m.LogPane = NewLogPaneModel(m.Services[idx], m.opts)
		m.ActiveView = ViewLogPane
		return m.startLogStream(m.Services[idx])
	}
	return nil
}

func (m Model) startLogStream(svc *registry.Service) tea.Cmd {
	if svc == nil || m.opts.LogStream == nil {
		return nil
	}
	return m.opts.LogStream(svc)
}

func firstLogService(services []*registry.Service) *registry.Service {
	for _, svc := range services {
		if svc.LogSource != nil {
			return svc
		}
	}
	return nil
}

func findService(services []*registry.Service, name string) *registry.Service {
	for _, svc := range services {
		if svc.Name == name {
			return svc
		}
	}
	return nil
}

func indexOfService(services []*registry.Service, target *registry.Service) int {
	if target == nil {
		return 0
	}
	for i, svc := range services {
		if svc == target || svc.Name == target.Name {
			return i
		}
	}
	return 0
}

func statusTick() tea.Cmd {
	return tea.Tick(2*time.Second, func(t time.Time) tea.Msg { return TickMsg(t) })
}
