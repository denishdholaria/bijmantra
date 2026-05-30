package tui

import (
	"testing"

	"github.com/charmbracelet/bubbles/key"
	tea "github.com/charmbracelet/bubbletea"
)

func TestDefaultKeyMapMatchesExpectedKeys(t *testing.T) {
	keys := DefaultKeyMap()

	if !key.Matches(tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune("q")}, keys.Quit) {
		t.Fatal("q did not match quit")
	}
	if !key.Matches(tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune("r")}, keys.Refresh) {
		t.Fatal("r did not match refresh")
	}
	if !key.Matches(tea.KeyMsg{Type: tea.KeyTab}, keys.NextService) {
		t.Fatal("tab did not match next service")
	}
}

func TestKeyMapHelpIsPopulated(t *testing.T) {
	keys := DefaultKeyMap()

	if len(keys.ShortHelp()) == 0 {
		t.Fatal("ShortHelp returned no bindings")
	}
	if len(keys.FullHelp()) != 2 {
		t.Fatalf("FullHelp group count = %d, want 2", len(keys.FullHelp()))
	}
}
