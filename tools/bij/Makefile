VERSION := $(shell python3 -c 'import json, sys; print(json.load(sys.stdin)["version"]["app"])' < ../../metrics.json)
LDFLAGS := -ldflags "-X main.version=$(VERSION)"

.PHONY: bij bij-release clean

bij:
	go build $(LDFLAGS) -o bij ./cmd/bij

bij-release:
	mkdir -p dist
	GOOS=darwin GOARCH=arm64 go build $(LDFLAGS) -o dist/bij-darwin-arm64 ./cmd/bij
	GOOS=darwin GOARCH=amd64 go build $(LDFLAGS) -o dist/bij-darwin-amd64 ./cmd/bij
	GOOS=linux GOARCH=amd64 go build $(LDFLAGS) -o dist/bij-linux-amd64 ./cmd/bij

clean:
	rm -f bij dist/bij-*
