#!/usr/bin/env python3
"""Sandbox policy manager for BijMantra autonomous agents.

Enforces NemoClaw-style deny-by-default policies:
 - Network egress restrictions (only allowed endpoints)
 - Filesystem path restrictions (read-only / read-write / blocked)
 - Dynamic policy updates for running sessions
 - Policy validation and auditing

Usage:
    # Validate policy file
    python ops-private/claw-runtime/scripts/sandbox_policy_manager.py validate

    # Show what the policy allows
    python ops-private/claw-runtime/scripts/sandbox_policy_manager.py show

    # Test a URL against the policy
    python ops-private/claw-runtime/scripts/sandbox_policy_manager.py test-url https://api.github.com

    # Test a file path against the policy
    python ops-private/claw-runtime/scripts/sandbox_policy_manager.py test-path /workspace/backend/app/main.py

    # Export policy as Docker network rules
    python ops-private/claw-runtime/scripts/sandbox_policy_manager.py export-docker
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_POLICY = ROOT / "ops-private" / "claw-runtime" / "policies" / "bijmantra-sandbox.yaml"

logger = logging.getLogger("sandbox-policy-manager")


# ── Policy Data Model ────────────────────────────────────────────────

@dataclass
class Endpoint:
    host: str
    port: int
    protocol: str = "rest"
    enforcement: str = "enforce"
    tls: str = ""
    rules: list[dict[str, Any]] = field(default_factory=list)
    access: str = ""


@dataclass
class NetworkPolicy:
    name: str
    endpoints: list[Endpoint] = field(default_factory=list)
    binaries: list[str] = field(default_factory=list)


@dataclass
class FilesystemPolicy:
    include_workdir: bool = True
    read_only: list[str] = field(default_factory=list)
    read_write: list[str] = field(default_factory=list)
    blocked: list[str] = field(default_factory=list)


@dataclass
class SandboxPolicy:
    version: int = 1
    filesystem: FilesystemPolicy = field(default_factory=FilesystemPolicy)
    network_policies: dict[str, NetworkPolicy] = field(default_factory=dict)
    landlock_compat: str = "best_effort"
    run_as_user: str = "sandbox"
    run_as_group: str = "sandbox"


# ── Policy Loading ───────────────────────────────────────────────────

def load_policy(path: Path) -> SandboxPolicy:
    """Load and parse a NemoClaw sandbox policy YAML file."""
    if not HAS_YAML:
        raise RuntimeError("PyYAML is required: pip install pyyaml")
    if not path.exists():
        raise FileNotFoundError(f"Policy file not found: {path}")

    with open(path, encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}

    policy = SandboxPolicy(version=raw.get("version", 1))

    # Filesystem policy
    fs_raw = raw.get("filesystem_policy", {})
    policy.filesystem = FilesystemPolicy(
        include_workdir=fs_raw.get("include_workdir", True),
        read_only=fs_raw.get("read_only", []),
        read_write=fs_raw.get("read_write", []),
        blocked=fs_raw.get("blocked", []),
    )

    # Landlock
    landlock = raw.get("landlock", {})
    policy.landlock_compat = landlock.get("compatibility", "best_effort")

    # Process
    process = raw.get("process", {})
    policy.run_as_user = process.get("run_as_user", "sandbox")
    policy.run_as_group = process.get("run_as_group", "sandbox")

    # Network policies
    for name, np_raw in raw.get("network_policies", {}).items():
        endpoints = []
        for ep_raw in np_raw.get("endpoints", []):
            endpoints.append(Endpoint(
                host=ep_raw.get("host", ""),
                port=ep_raw.get("port", 443),
                protocol=ep_raw.get("protocol", "rest"),
                enforcement=ep_raw.get("enforcement", "enforce"),
                tls=ep_raw.get("tls", ""),
                rules=ep_raw.get("rules", []),
                access=ep_raw.get("access", ""),
            ))
        binaries = [b.get("path", "") for b in np_raw.get("binaries", [])]
        policy.network_policies[name] = NetworkPolicy(
            name=np_raw.get("name", name),
            endpoints=endpoints,
            binaries=binaries,
        )

    return policy


# ── Policy Evaluation ────────────────────────────────────────────────

def check_url_allowed(policy: SandboxPolicy, url: str) -> tuple[bool, str]:
    """Check if a URL is allowed by the policy. Returns (allowed, reason)."""
    parsed = urlparse(url)
    host = parsed.hostname or ""
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    method = "GET"
    path = parsed.path or "/"

    for name, np in policy.network_policies.items():
        for ep in np.endpoints:
            if ep.host == host and ep.port == port:
                # Full access means everything is allowed
                if ep.access == "full":
                    return True, f"allowed by policy '{name}' (full access)"
                # Check rules
                for rule in ep.rules:
                    allow = rule.get("allow", {})
                    rule_method = allow.get("method", "")
                    rule_path = allow.get("path", "")
                    if rule_method in ("*", method):
                        if rule_path == "/**" or path.startswith(rule_path.rstrip("*")):
                            return True, f"allowed by policy '{name}' rule: {method} {rule_path}"
                # Endpoint matched but no rule allowed it
                if not ep.rules:
                    return True, f"allowed by policy '{name}' (no explicit rules = allow all)"
                return False, f"endpoint matched in '{name}' but no rule allows {method} {path}"

    return False, f"no policy allows {host}:{port} (deny by default)"


def check_path_allowed(policy: SandboxPolicy, filepath: str) -> tuple[str, str]:
    """Check file path access. Returns (access_level, reason).

    access_level: 'read-write', 'read-only', 'blocked', 'denied'
    """
    resolved = str(Path(filepath).resolve()) if not filepath.startswith("/") else filepath

    # Check blocked first
    for blocked in policy.filesystem.blocked:
        if resolved.startswith(blocked) or re.match(blocked.replace("*", ".*"), resolved):
            return "blocked", f"explicitly blocked by pattern: {blocked}"

    # Check read-write
    for rw in policy.filesystem.read_write:
        if resolved.startswith(rw):
            return "read-write", f"read-write via: {rw}"

    # Check read-only
    for ro in policy.filesystem.read_only:
        if resolved.startswith(ro):
            return "read-only", f"read-only via: {ro}"

    return "denied", f"path not covered by any policy rule (deny by default)"


# ── Path Guard ───────────────────────────────────────────────────────

class PathGuard:
    """Enforces file path restrictions for autonomous agents.

    Used by the bridge/watchdog to validate that agents only touch files
    within their allowed scope (from job cards).
    """

    def __init__(
        self,
        allowed_patterns: list[str] | None = None,
        blocked_patterns: list[str] | None = None,
        workspace_root: str = str(ROOT),
    ):
        self.workspace_root = Path(workspace_root)
        self.allowed_patterns = allowed_patterns or ["**"]
        self.blocked_patterns = blocked_patterns or [
            ".env*",
            "docker-compose*.yml",
            "*.key",
            "*.pem",
            ".git/config",
            ".ssh/**",
        ]

    def is_allowed(self, filepath: str) -> tuple[bool, str]:
        """Check if a file path is allowed for modification."""
        path = Path(filepath)

        # Make relative to workspace if absolute
        try:
            rel = path.relative_to(self.workspace_root)
        except ValueError:
            return False, f"path outside workspace: {filepath}"

        rel_str = str(rel)

        # Check blocked patterns first
        for pattern in self.blocked_patterns:
            if self._matches_glob(rel_str, pattern):
                return False, f"blocked by pattern: {pattern}"

        # Check allowed patterns
        for pattern in self.allowed_patterns:
            if self._matches_glob(rel_str, pattern):
                return True, f"allowed by pattern: {pattern}"

        return False, f"not matched by any allowed pattern"

    @staticmethod
    def _matches_glob(path_str: str, pattern: str) -> bool:
        """Simple glob matching for path patterns."""
        # Convert glob pattern to regex
        regex = pattern.replace(".", r"\.")
        regex = regex.replace("**/", "(.*/)?")
        regex = regex.replace("**", ".*")
        regex = regex.replace("*", "[^/]*")
        regex = f"^{regex}$"
        return bool(re.match(regex, path_str))

    @classmethod
    def from_job_card(cls, job: dict, workspace_root: str = str(ROOT)) -> PathGuard:
        """Create a PathGuard from an overnight-queue.json job card."""
        return cls(
            allowed_patterns=job.get("allowedPaths", ["**"]),
            blocked_patterns=job.get("blockedPaths", [
                ".env*", "docker-compose*.yml", "*.key", "*.pem",
            ]),
            workspace_root=workspace_root,
        )


# ── Docker Export ────────────────────────────────────────────────────

def export_docker_network_rules(policy: SandboxPolicy) -> dict[str, Any]:
    """Export policy as Docker-compatible network configuration.

    Generates iptables rules and Docker network labels for enforcement
    by the container runtime.
    """
    rules: list[dict[str, Any]] = []

    for name, np in policy.network_policies.items():
        for ep in np.endpoints:
            rules.append({
                "policy": name,
                "action": "ACCEPT",
                "destination": ep.host,
                "port": ep.port,
                "protocol": "tcp",
                "comment": f"bijmantra-sandbox: {name}",
            })

    # Default deny rule
    rules.append({
        "policy": "default",
        "action": "DROP",
        "destination": "0.0.0.0/0",
        "port": 0,
        "protocol": "all",
        "comment": "bijmantra-sandbox: deny-by-default",
    })

    return {
        "version": 1,
        "generatedBy": "bijmantra-sandbox-policy-manager",
        "rules": rules,
        "dns": {
            "allowed": list({
                ep.host
                for np in policy.network_policies.values()
                for ep in np.endpoints
            }),
        },
    }


# ── Validation ───────────────────────────────────────────────────────

def validate_policy(policy: SandboxPolicy) -> list[str]:
    """Validate a policy for common issues. Returns list of warnings."""
    warnings: list[str] = []

    if policy.version != 1:
        warnings.append(f"Unknown policy version: {policy.version}")

    if not policy.filesystem.read_write:
        warnings.append("No read-write paths defined; agent cannot modify any files")

    if not policy.network_policies:
        warnings.append("No network policies; agent has no network access at all")

    # Check for overly permissive rules
    for name, np in policy.network_policies.items():
        for ep in np.endpoints:
            if ep.access == "full" and ep.host not in ("localhost", "127.0.0.1"):
                warnings.append(
                    f"Policy '{name}' grants full access to {ep.host}:{ep.port} — "
                    "consider adding specific rules"
                )
            if not np.binaries:
                warnings.append(
                    f"Policy '{name}' has no binary restrictions — "
                    "any process can use these endpoints"
                )

    if policy.run_as_user == "root":
        warnings.append("Policy runs as root — strongly consider using a non-root user")

    return warnings


# ── CLI ──────────────────────────────────────────────────────────────

def cmd_validate(args: argparse.Namespace) -> int:
    policy = load_policy(args.policy)
    warnings = validate_policy(policy)
    if warnings:
        print(f"⚠  {len(warnings)} warning(s):")
        for w in warnings:
            print(f"   • {w}")
    else:
        print("✓ Policy is valid with no warnings")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    policy = load_policy(args.policy)
    print(f"Policy version: {policy.version}")
    print(f"Run as: {policy.run_as_user}:{policy.run_as_group}")
    print(f"Landlock: {policy.landlock_compat}")
    print()
    print("── Filesystem ──────────────────────────")
    print(f"  Read-only:  {', '.join(policy.filesystem.read_only) or '(none)'}")
    print(f"  Read-write: {', '.join(policy.filesystem.read_write) or '(none)'}")
    print(f"  Blocked:    {', '.join(policy.filesystem.blocked) or '(none)'}")
    print()
    print("── Network Policies ────────────────────")
    for name, np in policy.network_policies.items():
        endpoints_str = ", ".join(f"{ep.host}:{ep.port}" for ep in np.endpoints)
        binaries_str = ", ".join(np.binaries) or "(any)"
        print(f"  {name}: {endpoints_str} [binaries: {binaries_str}]")
    return 0


def cmd_test_url(args: argparse.Namespace) -> int:
    policy = load_policy(args.policy)
    allowed, reason = check_url_allowed(policy, args.url)
    symbol = "✓" if allowed else "✗"
    print(f"{symbol} {args.url}: {reason}")
    return 0 if allowed else 1


def cmd_test_path(args: argparse.Namespace) -> int:
    policy = load_policy(args.policy)
    access, reason = check_path_allowed(policy, args.path)
    symbols = {"read-write": "✓", "read-only": "◎", "blocked": "✗", "denied": "✗"}
    print(f"{symbols.get(access, '?')} {args.path}: {access} — {reason}")
    return 0 if access in ("read-write", "read-only") else 1


def cmd_export_docker(args: argparse.Namespace) -> int:
    policy = load_policy(args.policy)
    rules = export_docker_network_rules(policy)
    output = json.dumps(rules, indent=2)
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Wrote Docker network rules to {args.output}")
    else:
        print(output)
    return 0


def cmd_test_job_paths(args: argparse.Namespace) -> int:
    """Test file paths against a job card's path restrictions."""
    queue_path = ROOT / ".agent" / "jobs" / "overnight-queue.json"
    queue = json.loads(queue_path.read_text(encoding="utf-8"))

    job = next((j for j in queue["jobs"] if j["jobId"] == args.job_id), None)
    if not job:
        print(f"✗ Job not found: {args.job_id}")
        return 1

    guard = PathGuard.from_job_card(job)
    all_ok = True
    for path in args.paths:
        allowed, reason = guard.is_allowed(path)
        symbol = "✓" if allowed else "✗"
        print(f"{symbol} {path}: {reason}")
        if not allowed:
            all_ok = False
    return 0 if all_ok else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--policy", type=Path, default=DEFAULT_POLICY,
        help="Path to sandbox policy YAML",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("validate", help="Validate the policy file")
    sub.add_parser("show", help="Show policy summary")

    url_p = sub.add_parser("test-url", help="Test URL against policy")
    url_p.add_argument("url", help="URL to test")

    path_p = sub.add_parser("test-path", help="Test file path against policy")
    path_p.add_argument("path", help="File path to test")

    docker_p = sub.add_parser("export-docker", help="Export as Docker network rules")
    docker_p.add_argument("--output", help="Output file (default: stdout)")

    job_p = sub.add_parser("test-job-paths", help="Test paths against job card restrictions")
    job_p.add_argument("job_id", help="Job ID from overnight-queue.json")
    job_p.add_argument("paths", nargs="+", help="File paths to test")

    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    commands = {
        "validate": cmd_validate,
        "show": cmd_show,
        "test-url": cmd_test_url,
        "test-path": cmd_test_path,
        "export-docker": cmd_export_docker,
        "test-job-paths": cmd_test_job_paths,
    }
    return commands[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
