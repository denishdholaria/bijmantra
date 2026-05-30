package tui

import (
	"fmt"
	"strconv"
	"strings"
	"time"

	"github.com/bijmantra/bij/internal/registry"
	"github.com/charmbracelet/lipgloss"
)

const compactWidth = 80

type Styles struct {
	NoColor         bool
	Compact         bool
	Header          lipgloss.Style
	HeaderText      lipgloss.Style
	ServiceRow      lipgloss.Style
	EventRow        lipgloss.Style
	StatusBar       lipgloss.Style
	LogPaneBorder   lipgloss.Style
	Dim             lipgloss.Style
	Highlight       lipgloss.Style
	stateTextStyles map[registry.ServiceState]lipgloss.Style
}

func NewStyles(noColor bool, width int) Styles {
	compact := width > 0 && width < compactWidth
	base := Styles{
		NoColor:         noColor,
		Compact:         compact,
		stateTextStyles: map[registry.ServiceState]lipgloss.Style{},
	}
	if noColor {
		return base
	}

	border := lipgloss.Border{
		Top: "-", Bottom: "-", Left: "|", Right: "|",
		TopLeft: "+", TopRight: "+", BottomLeft: "+", BottomRight: "+",
	}
	if !compact {
		base.Header = lipgloss.NewStyle().Border(border).Padding(0, 1)
		base.LogPaneBorder = lipgloss.NewStyle().Border(border).Padding(0, 1)
	}
	base.HeaderText = lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("86"))
	base.ServiceRow = lipgloss.NewStyle()
	base.EventRow = lipgloss.NewStyle().Foreground(lipgloss.Color("244"))
	base.StatusBar = lipgloss.NewStyle().Foreground(lipgloss.Color("110"))
	base.Dim = lipgloss.NewStyle().Foreground(lipgloss.Color("240"))
	base.Highlight = lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("229")).Background(lipgloss.Color("57"))
	base.stateTextStyles[registry.StateReady] = lipgloss.NewStyle().Foreground(lipgloss.Color("82")).Bold(true)
	base.stateTextStyles[registry.StateDegraded] = lipgloss.NewStyle().Foreground(lipgloss.Color("214")).Bold(true)
	base.stateTextStyles[registry.StateFailed] = lipgloss.NewStyle().Foreground(lipgloss.Color("196")).Bold(true)
	base.stateTextStyles[registry.StateStarting] = lipgloss.NewStyle().Foreground(lipgloss.Color("75")).Bold(true)
	base.stateTextStyles[registry.StateStopping] = lipgloss.NewStyle().Foreground(lipgloss.Color("75")).Bold(true)
	base.stateTextStyles[registry.StateWaiting] = lipgloss.NewStyle().Foreground(lipgloss.Color("244"))
	base.stateTextStyles[registry.StateStopped] = lipgloss.NewStyle().Foreground(lipgloss.Color("244"))
	return base
}

func (s Styles) RenderHeader(runtime string, uptime time.Duration, healthy, total int) string {
	if runtime == "" {
		runtime = "dev"
	}
	content := fmt.Sprintf("BIJMANTRA  runtime: %s  uptime: %s  %d/%d healthy", runtime, formatDuration(uptimeFloor(uptime)), healthy, total)
	if s.NoColor || s.Compact {
		return content
	}
	return s.Header.Render(s.HeaderText.Render(content))
}

func (s Styles) RenderServiceRow(svc *registry.Service) string {
	if svc == nil {
		return ""
	}
	name := svc.Label
	if name == "" {
		name = svc.Name
	}
	if s.Compact && len(name) > 12 {
		name = strings.TrimSpace(name[:12])
	}
	state := strings.ToUpper(string(svc.State))
	if state == "" {
		state = strings.ToUpper(string(registry.StateWaiting))
	}
	port := "-"
	if svc.Port > 0 {
		port = strconv.Itoa(svc.Port)
	}
	duration := "-"
	if svc.Duration > 0 {
		duration = formatDuration(svc.Duration)
	}

	if s.Compact {
		return fmt.Sprintf("%-12s %-2s %-10s %5s", name, stateIcon(svc.State), state, port)
	}
	row := fmt.Sprintf("%-18s %-2s %-10s %5s %8s", name, stateIcon(svc.State), state, port, duration)
	return s.renderState(row, svc.State)
}

func (s Styles) RenderEvent(event registry.StateEvent) string {
	if event.Time.IsZero() {
		event.Time = time.Now()
	}
	line := fmt.Sprintf("[%s] %-9s %-14s %s", event.Time.Format("15:04:05"), strings.ToUpper(string(event.To)), event.Service, event.Message)
	if s.NoColor {
		return line
	}
	return s.EventRow.Render(line)
}

func (s Styles) RenderStatusBar(parts ...string) string {
	line := strings.Join(nonEmpty(parts), "   ")
	if s.NoColor {
		return line
	}
	return s.StatusBar.Render(line)
}

func (s Styles) RenderLogPane(title, body, footer string) string {
	content := strings.TrimRight(body, "\n")
	if title != "" {
		content = title + "\n" + content
	}
	if footer != "" {
		content += "\n" + footer
	}
	if s.NoColor || s.Compact {
		return content
	}
	return s.LogPaneBorder.Render(content)
}

func (s Styles) HighlightMatch(line, filter string) string {
	if filter == "" || !strings.Contains(strings.ToLower(line), strings.ToLower(filter)) {
		if filter != "" && !s.NoColor {
			return s.Dim.Render(line)
		}
		return line
	}
	if s.NoColor {
		return line
	}
	return s.Highlight.Render(line)
}

func (s Styles) renderState(value string, state registry.ServiceState) string {
	if s.NoColor {
		return value
	}
	if style, ok := s.stateTextStyles[state]; ok {
		return style.Render(value)
	}
	return value
}

func stateIcon(state registry.ServiceState) string {
	switch state {
	case registry.StateReady:
		return "OK"
	case registry.StateDegraded:
		return "!!"
	case registry.StateFailed:
		return "XX"
	case registry.StateStarting, registry.StateStopping:
		return ".."
	default:
		return "--"
	}
}

func formatDuration(duration time.Duration) string {
	if duration < 0 {
		duration = 0
	}
	duration = uptimeFloor(duration)
	if duration < time.Minute {
		return fmt.Sprintf("%ds", int(duration.Seconds()))
	}
	if duration < time.Hour {
		return fmt.Sprintf("%dm%02ds", int(duration.Minutes()), int(duration.Seconds())%60)
	}
	return fmt.Sprintf("%dh%02dm", int(duration.Hours()), int(duration.Minutes())%60)
}

func uptimeFloor(duration time.Duration) time.Duration {
	return duration.Truncate(time.Second)
}

func nonEmpty(values []string) []string {
	out := make([]string, 0, len(values))
	for _, value := range values {
		if value != "" {
			out = append(out, value)
		}
	}
	return out
}
