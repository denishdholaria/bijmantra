package tui

import (
	"fmt"
	"strings"

	"github.com/bijmantra/bij/internal/registry"
	"github.com/charmbracelet/bubbles/key"
	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
)

const maxLogLines = 1000

type LogPaneModel struct {
	Service    *registry.Service
	Lines      []string
	Filter     textinput.Model
	Filtering  bool
	Scroll     int
	AutoFollow bool

	opts   Options
	width  int
	height int
	keys   KeyMap
	styles Styles
}

func NewLogPaneModel(svc *registry.Service, opts Options) LogPaneModel {
	width := 100
	input := textinput.New()
	input.Prompt = "/"
	input.CharLimit = 120
	return LogPaneModel{
		Service:    svc,
		Filter:     input,
		AutoFollow: true,
		opts:       opts,
		width:      width,
		height:     30,
		keys:       DefaultKeyMap(),
		styles:     NewStyles(opts.NoColor, width),
	}
}

func (m LogPaneModel) Init() tea.Cmd {
	return tea.HideCursor
}

func (m LogPaneModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case LogLineMsg:
		if m.Service == nil || msg.Service == "" || msg.Service == m.Service.Name {
			m.Append(msg.Line)
		}
		return m, nil
	case tea.WindowSizeMsg:
		m.width, m.height = msg.Width, msg.Height
		m.styles = NewStyles(m.opts.NoColor, msg.Width)
		return m, nil
	case tea.KeyMsg:
		if m.Filtering {
			if key.Matches(msg, m.keys.ClearFilter) {
				m.Filtering = false
				m.Filter.Blur()
				m.Filter.SetValue("")
				return m, nil
			}
			if msg.Type == tea.KeyEnter {
				m.Filtering = false
				m.Filter.Blur()
				m.Scroll = 0
				m.AutoFollow = false
				return m, nil
			}
			var cmd tea.Cmd
			m.Filter, cmd = m.Filter.Update(msg)
			return m, cmd
		}

		switch {
		case key.Matches(msg, m.keys.Quit):
			return m, tea.Batch(tea.ShowCursor, tea.Quit)
		case key.Matches(msg, m.keys.Filter):
			m.Filtering = true
			m.Filter.Focus()
			return m, textinput.Blink
		case key.Matches(msg, m.keys.ClearFilter):
			m.Filter.SetValue("")
			m.AutoFollow = true
			return m, nil
		case key.Matches(msg, m.keys.ScrollUp):
			m.Scroll--
			if m.Scroll < 0 {
				m.Scroll = 0
			}
			m.AutoFollow = false
			return m, nil
		case key.Matches(msg, m.keys.ScrollDown):
			m.Scroll++
			m.AutoFollow = false
			return m, nil
		case key.Matches(msg, m.keys.Top):
			m.Scroll = 0
			m.AutoFollow = false
			return m, nil
		case key.Matches(msg, m.keys.Bottom):
			m.AutoFollow = true
			return m, nil
		case key.Matches(msg, m.keys.NextService):
			name := ""
			if m.Service != nil {
				name = m.Service.Name
			}
			return m, func() tea.Msg { return SwitchServiceMsg{Service: name} }
		}
	}
	return m, nil
}

func (m LogPaneModel) View() string {
	name := "logs"
	if m.Service != nil {
		name = m.Service.Name
	}
	lines := m.visibleLines()
	body := strings.Join(lines, "\n")
	filter := m.Filter.Value()
	if m.Filtering || filter != "" {
		body += "\n" + m.Filter.View()
	}

	footer := m.styles.RenderStatusBar(logSourceLabel(m.Service), "Tab: next", "q: quit")
	return m.styles.RenderLogPane(name, body, footer)
}

func (m *LogPaneModel) Append(line string) {
	m.Lines = append(m.Lines, line)
	if len(m.Lines) > maxLogLines {
		m.Lines = m.Lines[len(m.Lines)-maxLogLines:]
	}
	if m.AutoFollow {
		m.Scroll = len(m.filteredLines())
	}
}

func (m LogPaneModel) visibleLines() []string {
	filtered := m.filteredLines()
	limit := m.height - 5
	if limit <= 0 {
		limit = 10
	}
	if len(filtered) == 0 {
		return []string{"waiting for log output"}
	}

	start := m.Scroll
	if m.AutoFollow || start > len(filtered)-limit {
		start = len(filtered) - limit
	}
	if start < 0 {
		start = 0
	}
	end := start + limit
	if end > len(filtered) {
		end = len(filtered)
	}

	filter := m.Filter.Value()
	out := make([]string, 0, end-start)
	for _, line := range filtered[start:end] {
		out = append(out, m.styles.HighlightMatch(line, filter))
	}
	return out
}

func (m LogPaneModel) filteredLines() []string {
	filter := strings.ToLower(m.Filter.Value())
	if filter == "" {
		return append([]string(nil), m.Lines...)
	}
	out := make([]string, 0, len(m.Lines))
	for _, line := range m.Lines {
		if strings.Contains(strings.ToLower(line), filter) {
			out = append(out, line)
		}
	}
	return out
}

func logSourceLabel(svc *registry.Service) string {
	if svc == nil || svc.LogSource == nil {
		return ""
	}
	switch source := svc.LogSource.(type) {
	case registry.FileLogSource:
		return source.Path
	case registry.PodmanLogSource:
		return fmt.Sprintf("podman logs %s", source.Container)
	default:
		return svc.Name
	}
}
