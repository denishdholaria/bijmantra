package tui

import (
	"github.com/bijmantra/bij/internal/registry"
	"github.com/charmbracelet/bubbles/key"
	"github.com/charmbracelet/bubbles/list"
	tea "github.com/charmbracelet/bubbletea"
)

type PickerModel struct {
	Services []*registry.Service
	List     list.Model
	opts     Options
	keys     KeyMap
}

type serviceItem struct {
	service *registry.Service
}

func (i serviceItem) FilterValue() string { return i.Title() }
func (i serviceItem) Title() string {
	if i.service.Label != "" {
		return i.service.Label
	}
	return i.service.Name
}
func (i serviceItem) Description() string {
	return logSourceLabel(i.service)
}

func NewPickerModel(services []*registry.Service, opts Options) PickerModel {
	items := make([]list.Item, 0, len(services))
	logServices := make([]*registry.Service, 0, len(services))
	for _, svc := range services {
		if svc.LogSource == nil {
			continue
		}
		items = append(items, serviceItem{service: svc})
		logServices = append(logServices, svc)
	}
	delegate := list.NewDefaultDelegate()
	model := list.New(items, delegate, 80, 20)
	model.Title = "Select service log"
	model.SetShowStatusBar(false)
	model.SetFilteringEnabled(true)
	return PickerModel{
		Services: logServices,
		List:     model,
		opts:     opts,
		keys:     DefaultKeyMap(),
	}
}

func (m PickerModel) Init() tea.Cmd {
	return nil
}

func (m PickerModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.List.SetSize(msg.Width, msg.Height)
		return m, nil
	case tea.KeyMsg:
		if key.Matches(msg, m.keys.Quit) {
			return m, tea.Batch(tea.ShowCursor, tea.Quit)
		}
		if key.Matches(msg, m.keys.Select) {
			if item, ok := m.List.SelectedItem().(serviceItem); ok && item.service != nil {
				return m, func() tea.Msg { return ServiceSelectedMsg{Service: item.service.Name} }
			}
		}
	}

	var cmd tea.Cmd
	m.List, cmd = m.List.Update(msg)
	return m, cmd
}

func (m PickerModel) View() string {
	return m.List.View()
}
