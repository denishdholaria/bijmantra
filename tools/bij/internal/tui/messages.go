package tui

import (
	"time"

	"github.com/bijmantra/bij/internal/registry"
)

type StateChangedMsg registry.StateEvent

type TickMsg time.Time

type LogLineMsg struct {
	Service string
	Line    string
}

type RefreshRequestedMsg struct{}

type OpenLogsMsg struct{}

type SwitchServiceMsg struct {
	Service string
}

type ServiceSelectedMsg struct {
	Service string
}

func waitForEvent(ch <-chan registry.StateEvent) Cmd {
	return func() Msg {
		event, ok := <-ch
		if !ok {
			return nil
		}
		return StateChangedMsg(event)
	}
}
