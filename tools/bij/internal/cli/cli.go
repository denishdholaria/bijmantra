package cli

import (
	"bufio"
	"context"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/bijmantra/bij/internal/config"
	"github.com/bijmantra/bij/internal/logger"
	"github.com/bijmantra/bij/internal/orchestrator"
	"github.com/bijmantra/bij/internal/registry"
	"github.com/bijmantra/bij/internal/tui"
	"github.com/bijmantra/bij/internal/workspace"
	tea "github.com/charmbracelet/bubbletea"
)

type globalOptions struct {
	Workspace string
	NoColor   bool
}

type runtimeContext struct {
	Workspace string
	Podman    string
	Services  []*registry.Service
	Log       *logger.Logger
	Orch      *orchestrator.Orchestrator
}

func Run(args []string, stdout, stderr io.Writer, version string) int {
	if hasVersionFlag(args) {
		fmt.Fprintln(stdout, version)
		return 0
	}

	cmd, rest, opts, err := parseGlobalArgs(args)
	if err != nil {
		fmt.Fprintln(stderr, err)
		return 1
	}
	if cmd == "" {
		printHelp(stdout)
		return 0
	}

	switch cmd {
	case "dev":
		return runDev(rest, opts, stdout, stderr)
	case "status":
		return runStatus(rest, opts, stderr)
	case "logs":
		return runLogs(rest, opts, stdout, stderr)
	case "restart":
		return runRestart(rest, opts, stdout, stderr)
	case "stop":
		return runStop(rest, opts, stdout, stderr)
	default:
		fmt.Fprintf(stderr, "unknown command %q\n\n", cmd)
		printHelp(stderr)
		return 1
	}
}

func printHelp(w io.Writer) {
	fmt.Fprintln(w, "bij - BijMantra developer runtime")
	fmt.Fprintln(w)
	fmt.Fprintln(w, "Usage:")
	fmt.Fprintln(w, "  bij [--workspace PATH] [--no-color] <command> [flags]")
	fmt.Fprintln(w)
	fmt.Fprintln(w, "Commands:")
	fmt.Fprintln(w, "  dev       Start the product development stack")
	fmt.Fprintln(w, "  status    Show a live service dashboard")
	fmt.Fprintln(w, "  logs      Tail service logs")
	fmt.Fprintln(w, "  restart   Restart one service")
	fmt.Fprintln(w, "  stop      Stop managed services")
	fmt.Fprintln(w)
	fmt.Fprintln(w, "Flags:")
	fmt.Fprintln(w, "  --workspace PATH  Override workspace root")
	fmt.Fprintln(w, "  --no-color        Disable ANSI colors")
	fmt.Fprintln(w, "  --version         Print version")
}

func parseGlobalArgs(args []string) (string, []string, globalOptions, error) {
	var opts globalOptions
	command := ""
	rest := make([]string, 0, len(args))

	for i := 0; i < len(args); i++ {
		arg := args[i]
		switch arg {
		case "--no-color":
			opts.NoColor = true
		case "--workspace":
			i++
			if i >= len(args) {
				return "", nil, opts, fmt.Errorf("--workspace requires a path")
			}
			opts.Workspace = args[i]
		default:
			if command == "" && !strings.HasPrefix(arg, "-") {
				command = arg
				continue
			}
			rest = append(rest, arg)
		}
	}

	return command, rest, opts, nil
}

func runDev(args []string, opts globalOptions, stdout, stderr io.Writer) int {
	profile := string(registry.ServiceGroupInfra)
	for i := 0; i < len(args); i++ {
		if args[i] != "--profile" {
			continue
		}
		i++
		if i >= len(args) {
			fmt.Fprintln(stderr, "--profile requires core, infra, or autonomy")
			return 1
		}
		if _, err := registry.ParseServiceGroup(args[i]); err != nil {
			fmt.Fprintln(stderr, err)
			return 1
		}
		profile = args[i]
	}

	rt, err := prepareRuntime(opts, true)
	if err != nil {
		fmt.Fprintln(stderr, err)
		return 1
	}
	defer rt.Log.Close()

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	model := tui.NewModel(rt.Services, rt.Orch.Events, tui.Options{
		NoColor: opts.NoColor,
		Runtime: "dev",
	})
	program := tea.NewProgram(model, tea.WithAltScreen())
	go rt.Orch.Boot(ctx, profile)
	if _, err := program.Run(); err != nil {
		fmt.Fprintln(stderr, err)
		return 1
	}
	if err := rt.Orch.Stop(context.Background(), false); err != nil {
		fmt.Fprintln(stderr, err)
		return 1
	}
	fmt.Fprintln(stdout, "bij dev stopped")
	return 0
}

func runStatus(args []string, opts globalOptions, stderr io.Writer) int {
	rt, err := prepareRuntime(opts, false)
	if err != nil {
		fmt.Fprintln(stderr, err)
		return 1
	}
	defer rt.Log.Close()

	rt.Orch.ProbeAll(context.Background())
	model := tui.NewModel(rt.Services, rt.Orch.Events, tui.Options{
		NoColor:  opts.NoColor,
		ReadOnly: true,
		Runtime:  "status",
		ProbeAll: rt.Orch.ProbeAll,
	})
	program := tea.NewProgram(model, tea.WithAltScreen())
	if _, err := program.Run(); err != nil {
		fmt.Fprintln(stderr, err)
		return 1
	}
	return 0
}

func runLogs(args []string, opts globalOptions, stdout, stderr io.Writer) int {
	lines := 50
	follow := true
	serviceName := ""

	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--follow":
			follow = true
		case "--no-follow":
			follow = false
		case "--lines":
			i++
			if i >= len(args) {
				fmt.Fprintln(stderr, "--lines requires a number")
				return 1
			}
			value, err := strconv.Atoi(args[i])
			if err != nil || value < 0 {
				fmt.Fprintf(stderr, "invalid --lines value %q\n", args[i])
				return 1
			}
			lines = value
		default:
			if strings.HasPrefix(args[i], "-") {
				fmt.Fprintf(stderr, "unknown logs flag %q\n", args[i])
				return 1
			}
			serviceName = args[i]
		}
	}

	rt, err := prepareRuntime(opts, false)
	if err != nil {
		fmt.Fprintln(stderr, err)
		return 1
	}
	defer rt.Log.Close()

	if serviceName != "" {
		svc := registry.Find(rt.Services, serviceName)
		if svc == nil {
			fmt.Fprintf(stderr, "unknown service %q; valid services: %s\n", serviceName, strings.Join(registry.Names(rt.Services), ", "))
			return 1
		}
		if !follow {
			return printLogTail(svc, lines, stdout, stderr)
		}
		return runLogPane(svc, lines, opts, stderr)
	}

	if !follow {
		fmt.Fprintln(stderr, "bij logs --no-follow requires a service name")
		return 1
	}
	return runLogPicker(rt.Services, lines, opts, stderr)
}

func runRestart(args []string, opts globalOptions, stdout, stderr io.Writer) int {
	if len(args) != 1 {
		fmt.Fprintln(stderr, "usage: bij restart <service>")
		return 1
	}
	rt, err := prepareRuntime(opts, true)
	if err != nil {
		fmt.Fprintln(stderr, err)
		return 1
	}
	defer rt.Log.Close()

	name := args[0]
	if registry.Find(rt.Services, name) == nil {
		fmt.Fprintf(stderr, "unknown service %q; valid services: %s\n", name, strings.Join(registry.Names(rt.Services), ", "))
		return 1
	}
	fmt.Fprintf(stdout, "restarting %s\n", name)
	if err := runWithProgress(stdout, rt.Orch.Events, func() error {
		return rt.Orch.Restart(context.Background(), name)
	}); err != nil {
		fmt.Fprintf(stderr, "restart failed for %s: %v\ntry: bij logs %s\n", name, err, name)
		return 1
	}
	fmt.Fprintf(stdout, "%s ready\n", name)
	return 0
}

func runStop(args []string, opts globalOptions, stdout, stderr io.Writer) int {
	for _, arg := range args {
		if arg != "--force" {
			fmt.Fprintf(stderr, "unknown stop flag %q\n", arg)
			return 1
		}
	}
	force := contains(args, "--force")
	rt, err := prepareRuntime(opts, true)
	if err != nil {
		fmt.Fprintln(stderr, err)
		return 1
	}
	defer rt.Log.Close()

	for _, svc := range rt.Services {
		rt.Orch.MarkManaged(svc.Name)
	}
	if err := runWithProgress(stdout, rt.Orch.Events, func() error {
		return rt.Orch.Stop(context.Background(), force)
	}); err != nil {
		fmt.Fprintf(stderr, "stop completed with warnings: %v\n", err)
		return 1
	}
	fmt.Fprintln(stdout, "all BijMantra services stopped")
	return 0
}

func runLogPane(svc *registry.Service, lines int, opts globalOptions, stderr io.Writer) int {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	model := tui.NewLogPaneModel(svc, tui.Options{NoColor: opts.NoColor, Runtime: "logs"})
	program := tea.NewProgram(model, tea.WithAltScreen())
	go forwardLogLines(ctx, program, svc, lines, stderr)
	if _, err := program.Run(); err != nil {
		fmt.Fprintln(stderr, err)
		return 1
	}
	return 0
}

func runLogPicker(services []*registry.Service, lines int, opts globalOptions, stderr io.Writer) int {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	var program *tea.Program
	model := tui.NewModel(services, nil, tui.Options{
		NoColor: opts.NoColor,
		Runtime: "logs",
		LogStream: func(svc *registry.Service) tea.Cmd {
			return func() tea.Msg {
				go forwardLogLines(ctx, program, svc, lines, stderr)
				return nil
			}
		},
	})
	program = tea.NewProgram(model, tea.WithAltScreen())
	if _, err := program.Run(); err != nil {
		fmt.Fprintln(stderr, err)
		return 1
	}
	return 0
}

func runWithProgress(stdout io.Writer, events <-chan registry.StateEvent, fn func() error) error {
	done := make(chan error, 1)
	go func() { done <- fn() }()

	for {
		select {
		case event := <-events:
			printEvent(stdout, event)
		case err := <-done:
			drainEvents(stdout, events)
			return err
		}
	}
}

func drainEvents(stdout io.Writer, events <-chan registry.StateEvent) {
	for {
		select {
		case event := <-events:
			printEvent(stdout, event)
		default:
			return
		}
	}
}

func printEvent(stdout io.Writer, event registry.StateEvent) {
	if event.Service == "" {
		return
	}
	if event.Message != "" {
		fmt.Fprintf(stdout, "%s: %s -> %s (%s)\n", event.Service, event.From, event.To, event.Message)
		return
	}
	fmt.Fprintf(stdout, "%s: %s -> %s\n", event.Service, event.From, event.To)
}

func forwardLogLines(ctx context.Context, program *tea.Program, svc *registry.Service, lines int, stderr io.Writer) {
	if svc == nil || svc.LogSource == nil || program == nil {
		return
	}
	ch, err := svc.LogSource.Stream(ctx, lines)
	if err != nil {
		program.Send(tui.LogLineMsg{Service: svc.Name, Line: "log stream error: " + err.Error()})
		return
	}
	for {
		select {
		case <-ctx.Done():
			return
		case line, ok := <-ch:
			if !ok {
				return
			}
			program.Send(tui.LogLineMsg{Service: svc.Name, Line: line})
		}
	}
}

func prepareRuntime(opts globalOptions, verifyCompose bool) (*runtimeContext, error) {
	root, err := workspace.ResolveWorkspace(opts.Workspace)
	if err != nil {
		return nil, err
	}
	podman, err := workspace.DetectPodman()
	if err != nil {
		return nil, err
	}
	cfg, err := config.Load(root)
	if err != nil {
		return nil, err
	}
	if cfg.Podman != "" {
		podman = cfg.Podman
	}
	if verifyCompose {
		if err := workspace.VerifyCompose(podman); err != nil {
			return nil, err
		}
	}
	services := registry.DefaultRegistry(root, podman)
	registry.Apply(services, cfg)
	log, err := logger.New(filepath.Join(root, "logs", "bij-runtime.log"))
	if err != nil {
		return nil, err
	}
	orch := orchestrator.New(services, podman, root, log)
	return &runtimeContext{Workspace: root, Podman: podman, Services: services, Log: log, Orch: orch}, nil
}

func printLogTail(svc *registry.Service, lines int, stdout, stderr io.Writer) int {
	if svc.LogSource == nil {
		fmt.Fprintf(stderr, "service %s has no log source\n", svc.Name)
		return 1
	}
	switch source := svc.LogSource.(type) {
	case registry.FileLogSource:
		tail, err := readFileTail(source.Path, lines)
		if err != nil {
			fmt.Fprintln(stderr, err)
			return 1
		}
		for _, line := range tail {
			fmt.Fprintln(stdout, line)
		}
		return 0
	default:
		ctx, cancel := context.WithTimeout(context.Background(), 300*time.Millisecond)
		defer cancel()
		ch, err := svc.LogSource.Stream(ctx, lines)
		if err != nil {
			fmt.Fprintln(stderr, err)
			return 1
		}
		for line := range ch {
			fmt.Fprintln(stdout, line)
		}
		return 0
	}
}

func readFileTail(path string, lines int) ([]string, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	if lines <= 0 {
		return nil, nil
	}
	recent := make([]string, 0, lines)
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		if len(recent) == lines {
			copy(recent, recent[1:])
			recent = recent[:lines-1]
		}
		recent = append(recent, scanner.Text())
	}
	if err := scanner.Err(); err != nil {
		return nil, err
	}
	return recent, nil
}

func hasVersionFlag(args []string) bool {
	return contains(args, "--version")
}

func contains(values []string, target string) bool {
	for _, value := range values {
		if value == target {
			return true
		}
	}
	return false
}
