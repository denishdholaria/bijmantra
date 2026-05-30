package tui

import "github.com/charmbracelet/bubbles/key"

type KeyMap struct {
	Quit        key.Binding
	Refresh     key.Binding
	Logs        key.Binding
	Help        key.Binding
	ScrollUp    key.Binding
	ScrollDown  key.Binding
	Top         key.Binding
	Bottom      key.Binding
	Filter      key.Binding
	ClearFilter key.Binding
	NextService key.Binding
	Select      key.Binding
}

func DefaultKeyMap() KeyMap {
	return KeyMap{
		Quit:        key.NewBinding(key.WithKeys("q", "ctrl+c", "esc"), key.WithHelp("q", "quit")),
		Refresh:     key.NewBinding(key.WithKeys("r"), key.WithHelp("r", "refresh")),
		Logs:        key.NewBinding(key.WithKeys("l"), key.WithHelp("l", "logs")),
		Help:        key.NewBinding(key.WithKeys("?"), key.WithHelp("?", "help")),
		ScrollUp:    key.NewBinding(key.WithKeys("up", "k"), key.WithHelp("k/up", "up")),
		ScrollDown:  key.NewBinding(key.WithKeys("down", "j"), key.WithHelp("j/down", "down")),
		Top:         key.NewBinding(key.WithKeys("g"), key.WithHelp("g", "top")),
		Bottom:      key.NewBinding(key.WithKeys("G"), key.WithHelp("G", "bottom")),
		Filter:      key.NewBinding(key.WithKeys("/"), key.WithHelp("/", "filter")),
		ClearFilter: key.NewBinding(key.WithKeys("esc"), key.WithHelp("esc", "clear")),
		NextService: key.NewBinding(key.WithKeys("tab"), key.WithHelp("tab", "next")),
		Select:      key.NewBinding(key.WithKeys("enter"), key.WithHelp("enter", "select")),
	}
}

func (k KeyMap) ShortHelp() []key.Binding {
	return []key.Binding{k.Quit, k.Refresh, k.Logs, k.Help}
}

func (k KeyMap) FullHelp() [][]key.Binding {
	return [][]key.Binding{
		{k.Quit, k.Refresh, k.Logs, k.Help},
		{k.ScrollUp, k.ScrollDown, k.Top, k.Bottom, k.Filter, k.ClearFilter, k.NextService},
	}
}
