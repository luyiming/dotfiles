#!/usr/bin/env python3

import argparse
import hashlib
import json
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

SUPPORTED_FISH_MAJOR = 4
MINIMUM_PYTHON = (3, 8)
GITHUB_API = "https://api.github.com/repos"


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    dependencies: Tuple[str, ...] = ()


TOOLS = (
    ToolSpec("ripgrep", "Fast recursive text search"),
    ToolSpec("fd", "Fast and friendly file finder"),
    ToolSpec("eza", "Modern replacement for ls"),
    ToolSpec("fzf", "Command-line fuzzy finder"),
    ToolSpec("rust", "Rust toolchain managed by rustup"),
    ToolSpec("fnm", "Fast Node.js version manager"),
    ToolSpec("bat", "cat clone with syntax highlighting"),
    ToolSpec("zoxide", "Smarter cd command"),
    ToolSpec("fish", "Friendly interactive shell"),
    ToolSpec("neovim", "Extensible text editor"),
    ToolSpec("gdu", "Fast disk usage analyzer"),
    ToolSpec("dust", "Intuitive du replacement"),
    ToolSpec("duf", "Disk usage/free utility"),
    ToolSpec("nvtop", "GPU process monitor"),
    ToolSpec("uv", "Python package and project manager"),
    ToolSpec("gpustat", "NVIDIA GPU status utility", ("uv",)),
)
TOOL_BY_NAME = {tool.name: tool for tool in TOOLS}


class InstallerError(Exception):
    def __init__(
        self,
        tool: str,
        phase: str,
        detail: str,
        hint: Optional[str] = None,
    ) -> None:
        super().__init__(detail)
        self.tool = tool
        self.phase = phase
        self.detail = detail
        self.hint = hint


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


class CommandRunner:
    def run(
        self,
        args: Sequence[str],
        tool: str,
        phase: str,
        *,
        capture: bool = False,
        check: bool = True,
        env: Optional[Mapping[str, str]] = None,
    ) -> CommandResult:
        command = [str(arg) for arg in args]
        if not capture:
            print("+ " + shlex.join(command))

        command_env = os.environ.copy()
        command_env["LC_ALL"] = "C"
        if env:
            command_env.update(env)

        try:
            completed = subprocess.run(
                command,
                check=False,
                text=True,
                stdout=subprocess.PIPE if capture else None,
                stderr=subprocess.PIPE if capture else None,
                env=command_env,
            )
        except OSError as exc:
            raise InstallerError(tool, phase, str(exc)) from exc

        result = CommandResult(
            completed.returncode,
            completed.stdout or "",
            completed.stderr or "",
        )
        if check and result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip()
            if not detail:
                detail = "command exited with status {}".format(result.returncode)
            raise InstallerError(tool, phase, detail)
        return result

    def run_root(
        self,
        args: Sequence[str],
        tool: str,
        phase: str,
        *,
        capture: bool = False,
    ) -> CommandResult:
        command = list(args)
        if os.geteuid() != 0:
            sudo = shutil.which("sudo")
            if sudo is None:
                raise InstallerError(
                    tool,
                    phase,
                    "root privileges are required, but sudo is not installed",
                )
            command = [sudo, "--"] + command
        return self.run(command, tool, phase, capture=capture)


@dataclass(frozen=True)
class Asset:
    name: str
    url: str
    sha256: Optional[str]


@dataclass(frozen=True)
class Release:
    tag: str
    version: str
    assets: Tuple[Asset, ...]

    def require_asset(self, tool: str, pattern: str) -> Asset:
        regex = re.compile(pattern)
        matches = [asset for asset in self.assets if regex.fullmatch(asset.name)]
        if len(matches) != 1:
            names = ", ".join(asset.name for asset in self.assets)
            raise InstallerError(
                tool,
                "release metadata",
                "expected exactly one asset matching {!r}, found {} (assets: {})".format(
                    pattern,
                    len(matches),
                    names,
                ),
            )
        asset = matches[0]
        if asset.sha256 is None:
            raise InstallerError(
                tool,
                "release metadata",
                "selected asset {} has no valid SHA-256 digest".format(asset.name),
            )
        return asset


class HttpClient:
    def __init__(self, github_token: Optional[str]) -> None:
        self.github_token = github_token

    def _request(self, url: str) -> urllib.request.Request:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "dotfiles-manage-tools",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.github_token and url.startswith("https://api.github.com/"):
            headers["Authorization"] = "Bearer {}".format(self.github_token)
        return urllib.request.Request(url, headers=headers)

    def json(self, url: str, tool: str, phase: str) -> Dict[str, Any]:
        try:
            with urllib.request.urlopen(self._request(url), timeout=30) as response:
                data = json.load(response)
        except (OSError, ValueError, urllib.error.URLError) as exc:
            raise InstallerError(tool, phase, "failed to fetch {}: {}".format(url, exc)) from exc
        if not isinstance(data, dict):
            raise InstallerError(tool, phase, "expected a JSON object from {}".format(url))
        return data

    def download(
        self,
        url: str,
        destination: Path,
        tool: str,
        phase: str,
        expected_sha256: Optional[str] = None,
    ) -> None:
        digest = hashlib.sha256()
        try:
            with urllib.request.urlopen(self._request(url), timeout=30) as response:
                with destination.open("wb") as output:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        output.write(chunk)
                        digest.update(chunk)
        except (OSError, urllib.error.URLError) as exc:
            raise InstallerError(tool, phase, "failed to download {}: {}".format(url, exc)) from exc

        if expected_sha256 and digest.hexdigest() != expected_sha256:
            raise InstallerError(
                tool,
                phase,
                "SHA-256 mismatch for {}: expected {}, got {}".format(
                    url,
                    expected_sha256,
                    digest.hexdigest(),
                ),
            )


@dataclass(frozen=True)
class PlatformInfo:
    distro: str
    version_id: str

    @property
    def major_version(self) -> int:
        match = re.match(r"^(\d+)", self.version_id)
        if match is None:
            raise ValueError("invalid VERSION_ID: {}".format(self.version_id))
        return int(match.group(1))


def parse_os_release(contents: str) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for raw_line in contents.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if value.startswith(('"', "'")) and value.endswith(value[0]):
            value = value[1:-1]
        values[key] = value
    return values


def detect_platform() -> PlatformInfo:
    if platform.machine().lower() not in {"x86_64", "amd64"}:
        raise InstallerError(
            "platform",
            "preflight",
            "unsupported architecture: {} (expected x86_64)".format(platform.machine()),
        )

    os_release_path = Path("/etc/os-release")
    try:
        values = parse_os_release(os_release_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise InstallerError("platform", "preflight", str(exc)) from exc

    distro = values.get("ID", "")
    version_id = values.get("VERSION_ID", "")
    if distro not in {"ubuntu", "debian"}:
        raise InstallerError(
            "platform",
            "preflight",
            "unsupported distribution {!r}; expected Ubuntu or Debian".format(distro),
        )

    info = PlatformInfo(distro, version_id)
    try:
        major = info.major_version
    except ValueError as exc:
        raise InstallerError("platform", "preflight", str(exc)) from exc

    minimum = 22 if distro == "ubuntu" else 12
    if major < minimum:
        raise InstallerError(
            "platform",
            "preflight",
            "unsupported {} {}; minimum supported version is {}".format(
                distro,
                version_id,
                minimum,
            ),
        )
    if shutil.which("apt-get") is None or shutil.which("dpkg-query") is None:
        raise InstallerError(
            "platform",
            "preflight",
            "apt-get and dpkg-query are required",
        )
    return info


def extract_version(value: str) -> str:
    match = re.search(r"(?<!\d)(\d+(?:\.\d+){1,3})(?!\d)", value)
    if match is None:
        raise ValueError("could not parse version from {!r}".format(value.strip()))
    return match.group(1)


def version_tuple(value: str) -> Tuple[int, ...]:
    return tuple(int(part) for part in extract_version(value).split("."))


def compare_versions(left: str, right: str) -> int:
    left_parts = version_tuple(left)
    right_parts = version_tuple(right)
    width = max(len(left_parts), len(right_parts))
    padded_left = left_parts + (0,) * (width - len(left_parts))
    padded_right = right_parts + (0,) * (width - len(right_parts))
    return (padded_left > padded_right) - (padded_left < padded_right)


def normalize_release(data: Mapping[str, Any], tool: str) -> Release:
    tag = data.get("tag_name")
    raw_assets = data.get("assets")
    if not isinstance(tag, str) or not tag:
        raise InstallerError(tool, "release metadata", "release has no valid tag_name")
    if data.get("draft") or data.get("prerelease"):
        raise InstallerError(tool, "release metadata", "latest release is not stable")
    if not isinstance(raw_assets, list):
        raise InstallerError(tool, "release metadata", "release has no asset list")

    try:
        version = extract_version(tag)
    except ValueError as exc:
        raise InstallerError(tool, "release metadata", str(exc)) from exc

    assets: List[Asset] = []
    for raw_asset in raw_assets:
        if not isinstance(raw_asset, dict):
            raise InstallerError(tool, "release metadata", "invalid release asset")
        name = raw_asset.get("name")
        url = raw_asset.get("browser_download_url")
        digest = raw_asset.get("digest")
        if not isinstance(name, str) or not isinstance(url, str):
            raise InstallerError(tool, "release metadata", "asset has no name or URL")
        sha256 = None
        if isinstance(digest, str) and re.fullmatch(r"sha256:[0-9a-fA-F]{64}", digest):
            sha256 = digest.split(":", 1)[1].lower()
        assets.append(Asset(name, url, sha256))
    return Release(tag, version, tuple(assets))


def expand_dependencies(selected: Iterable[str]) -> List[str]:
    requested = list(selected)
    result: List[str] = []
    visiting: set = set()
    visited: set = set()

    def visit(name: str) -> None:
        if name in visited:
            return
        if name in visiting:
            raise ValueError("dependency cycle involving {}".format(name))
        visiting.add(name)
        for dependency in TOOL_BY_NAME[name].dependencies:
            visit(dependency)
        visiting.remove(name)
        visited.add(name)
        result.append(name)

    for tool_name in requested:
        visit(tool_name)
    return result


def safe_extract_tar(archive_path: Path, destination: Path, tool: str) -> None:
    try:
        with tarfile.open(archive_path, "r:*") as archive:
            destination_root = destination.resolve()
            for member in archive.getmembers():
                member_path = (destination / member.name).resolve()
                try:
                    common = os.path.commonpath([str(destination_root), str(member_path)])
                except ValueError as exc:
                    raise InstallerError(tool, "extract", str(exc)) from exc
                if common != str(destination_root):
                    raise InstallerError(
                        tool,
                        "extract",
                        "archive member escapes destination: {}".format(member.name),
                    )
                if member.issym() or member.islnk():
                    link_path = (member_path.parent / member.linkname).resolve()
                    if os.path.commonpath([str(destination_root), str(link_path)]) != str(destination_root):
                        raise InstallerError(
                            tool,
                            "extract",
                            "archive link escapes destination: {}".format(member.name),
                        )
            archive.extractall(destination)
    except (OSError, tarfile.TarError) as exc:
        raise InstallerError(tool, "extract", str(exc)) from exc


class Installer:
    def __init__(
        self,
        platform_info: PlatformInfo,
        work_dir: Path,
        check_only: bool,
        runner: Optional[CommandRunner] = None,
        http: Optional[HttpClient] = None,
        home: Optional[Path] = None,
    ) -> None:
        self.platform = platform_info
        self.work_dir = work_dir
        self.check_only = check_only
        self.runner = runner or CommandRunner()
        self.http = http or HttpClient(os.environ.get("GITHUB_TOKEN"))
        self.home = home or Path.home()
        self.local_bin = self.home / ".local/bin"
        self.local_man1 = self.home / ".local/share/man/man1"
        self.release_cache: Dict[str, Release] = {}

    def run(self, tool: str) -> None:
        handler = getattr(self, "_run_{}".format(tool))
        handler()

    def _latest_release(self, tool: str, repository: str) -> Release:
        if repository not in self.release_cache:
            data = self.http.json(
                "{}/{}/releases/latest".format(GITHUB_API, repository),
                tool,
                "release metadata",
            )
            self.release_cache[repository] = normalize_release(data, tool)
        return self.release_cache[repository]

    def _temporary_path(self, name: str) -> Path:
        return self.work_dir / name

    def _command_output(
        self,
        path: Path,
        args: Sequence[str],
        tool: str,
        phase: str,
    ) -> str:
        result = self.runner.run([str(path)] + list(args), tool, phase, capture=True)
        return result.stdout.strip() or result.stderr.strip()

    def _binary_version(
        self,
        path: Path,
        args: Sequence[str],
        tool: str,
        identity: Optional[str] = None,
    ) -> str:
        output = self._command_output(path, args, tool, "version check")
        if identity and identity.lower() not in output.lower():
            raise InstallerError(
                tool,
                "conflict check",
                "{} does not identify itself as {}: {!r}".format(path, identity, output),
            )
        try:
            return extract_version(output)
        except ValueError as exc:
            raise InstallerError(tool, "version check", str(exc)) from exc

    def _managed_binary_version(
        self,
        tool: str,
        command: str,
        target: Path,
        args: Sequence[str] = ("--version",),
        identity: Optional[str] = None,
    ) -> Optional[str]:
        found = shutil.which(command)
        target_exists = target.exists() or target.is_symlink()
        if not target_exists:
            if found:
                raise InstallerError(
                    tool,
                    "conflict check",
                    "{} is already provided by {}".format(command, found),
                    "Remove or externally manage the existing installation before rerunning.",
                )
            return None

        if target.is_symlink() or not target.is_file():
            raise InstallerError(
                tool,
                "conflict check",
                "expected a regular file at {}, found a different file type".format(target),
            )
        if found and Path(found).resolve() != target.resolve():
            raise InstallerError(
                tool,
                "conflict check",
                "{} exists at {}, but the managed target is {}".format(command, found, target),
                "Remove the duplicate installation or fix PATH ordering before rerunning.",
            )
        return self._binary_version(target, args, tool, identity)

    def _document_target(self, tool: str, target: Path) -> None:
        if target.is_symlink() or (target.exists() and not target.is_file()):
            raise InstallerError(
                tool,
                "conflict check",
                "expected a regular documentation file at {}".format(target),
            )

    def _atomic_install_file(self, source: Path, target: Path, mode: int, tool: str) -> None:
        self._atomic_install_files(((source, target, mode),), tool)

    def _atomic_install_files(
        self,
        files: Sequence[Tuple[Path, Path, int]],
        tool: str,
    ) -> None:
        staged: List[Tuple[Path, Path]] = []
        backups: List[Tuple[Path, Path]] = []
        installed: List[Path] = []
        try:
            for source, target, mode in files:
                target.parent.mkdir(parents=True, exist_ok=True)
                staging = target.parent / ".{}.new-{}".format(
                    target.name,
                    uuid.uuid4().hex,
                )
                shutil.copyfile(source, staging)
                os.chmod(staging, mode)
                staged.append((staging, target))

            for _, target in staged:
                if target.exists() or target.is_symlink():
                    backup = target.parent / ".{}.old-{}".format(
                        target.name,
                        uuid.uuid4().hex,
                    )
                    os.replace(target, backup)
                    backups.append((backup, target))

            for staging, target in staged:
                os.replace(staging, target)
                installed.append(target)
        except OSError as exc:
            for target in reversed(installed):
                if target.exists() or target.is_symlink():
                    target.unlink()
            for backup, target in reversed(backups):
                if backup.exists() or backup.is_symlink():
                    os.replace(backup, target)
            raise InstallerError(tool, "install", str(exc)) from exc
        finally:
            for staging, _ in staged:
                if staging.exists() or staging.is_symlink():
                    staging.unlink()
            for backup, _ in backups:
                if backup.exists() or backup.is_symlink():
                    backup.unlink()

    def _atomic_symlink(self, target: Path, link: Path, tool: str) -> None:
        link.parent.mkdir(parents=True, exist_ok=True)
        staging = link.parent / ".{}.new-{}".format(link.name, uuid.uuid4().hex)
        try:
            staging.symlink_to(target)
            os.replace(staging, link)
        except OSError as exc:
            raise InstallerError(tool, "install", str(exc)) from exc
        finally:
            if staging.exists() or staging.is_symlink():
                staging.unlink()

    def _download_asset(self, tool: str, asset: Asset) -> Path:
        destination = self._temporary_path("{}-{}".format(tool, asset.name))
        self.http.download(
            asset.url,
            destination,
            tool,
            "download",
            asset.sha256,
        )
        return destination

    def _dpkg_version(self, package: str, tool: str) -> Optional[str]:
        result = self.runner.run(
            ["dpkg-query", "-W", "-f=${Version}", package],
            tool,
            "package query",
            capture=True,
            check=False,
        )
        if result.returncode != 0:
            return None
        version = result.stdout.strip()
        return version or None

    def _package_owns_command(self, package: str, command_path: Path, tool: str) -> bool:
        result = self.runner.run(
            ["dpkg-query", "-S", str(command_path)],
            tool,
            "conflict check",
            capture=True,
            check=False,
        )
        if result.returncode != 0:
            return False
        for line in result.stdout.splitlines():
            owner = line.split(":", 1)[0]
            if owner == package or owner.startswith(package + ":"):
                return True
        return False

    def _package_version_and_conflict(
        self,
        tool: str,
        package: str,
        command: str,
    ) -> Optional[str]:
        package_version = self._dpkg_version(package, tool)
        found = shutil.which(command)
        if package_version is None:
            if found:
                raise InstallerError(
                    tool,
                    "conflict check",
                    "{} is installed at {}, but dpkg package {} is not installed".format(
                        command,
                        found,
                        package,
                    ),
                    "Remove or externally manage the conflicting command before rerunning.",
                )
            return None

        if found and not self._package_owns_command(package, Path(found), tool):
            raise InstallerError(
                tool,
                "conflict check",
                "{} from {} shadows the installed dpkg package {}".format(
                    command,
                    found,
                    package,
                ),
                "Remove the shadowing command or fix PATH ordering before rerunning.",
            )
        return package_version

    def _ensure_commands(self, tool: str, requirements: Mapping[str, str]) -> None:
        missing_packages = sorted(
            {package for command, package in requirements.items() if shutil.which(command) is None}
        )
        if not missing_packages:
            return
        self.runner.run_root(["apt-get", "update"], tool, "install prerequisites")
        self.runner.run_root(
            ["apt-get", "install", "-y"] + missing_packages,
            tool,
            "install prerequisites",
        )

    def _release_deb(
        self,
        tool: str,
        repository: str,
        package: str,
        command: str,
        asset_pattern: str,
    ) -> None:
        installed = self._package_version_and_conflict(tool, package, command)
        release = self._latest_release(tool, repository)
        if installed is not None and compare_versions(installed, release.version) >= 0:
            print("[current] {} {}".format(tool, extract_version(installed)))
            return
        if self.check_only:
            if installed is None:
                print("[missing] {} (latest {})".format(tool, release.version))
            else:
                print(
                    "[update] {} {} -> {}".format(
                        tool,
                        extract_version(installed),
                        release.version,
                    )
                )
            return

        pattern = asset_pattern.format(version=re.escape(release.version))
        asset = release.require_asset(tool, pattern)
        package_path = self._download_asset(tool, asset)
        action = "Installing" if installed is None else "Updating"
        print("{} {} to {}".format(action, tool, release.version))
        self.runner.run_root(
            ["apt-get", "install", "-y", str(package_path)],
            tool,
            "package install",
        )
        installed_after = self._dpkg_version(package, tool)
        if installed_after is None or compare_versions(installed_after, release.version) < 0:
            raise InstallerError(
                tool,
                "verify",
                "dpkg did not report the expected version {}".format(release.version),
            )
        print("[installed] {} {}".format(tool, release.version))

    def _apt_source_texts(self) -> List[Tuple[Path, str]]:
        candidates = [Path("/etc/apt/sources.list")]
        source_dir = Path("/etc/apt/sources.list.d")
        if source_dir.is_dir():
            candidates.extend(sorted(source_dir.glob("*.list")))
            candidates.extend(sorted(source_dir.glob("*.sources")))
        result: List[Tuple[Path, str]] = []
        for path in candidates:
            try:
                result.append((path, path.read_text(encoding="utf-8", errors="replace")))
            except FileNotFoundError:
                continue
            except OSError as exc:
                raise InstallerError("apt", "source inspection", str(exc)) from exc
        return result

    def _matching_apt_sources(self, needles: Sequence[str]) -> List[Tuple[Path, str]]:
        return [(path, text) for path, text in self._apt_source_texts() if any(needle in text for needle in needles)]

    def _install_root_file(self, source: Path, target: Path, tool: str) -> None:
        self.runner.run_root(
            ["install", "-D", "-m", "0644", str(source), str(target)],
            tool,
            "repository configuration",
        )

    def _configure_ppa(
        self,
        tool: str,
        ppa: str,
        family_needles: Sequence[str],
        expected_needle: str,
        *,
        configure: bool = True,
    ) -> bool:
        matches = self._matching_apt_sources(family_needles)
        if matches:
            if not all(expected_needle in text for _, text in matches):
                paths = ", ".join(str(path) for path, _ in matches)
                raise InstallerError(
                    tool,
                    "repository conflict",
                    "conflicting APT source found in {}".format(paths),
                    "Remove or reconcile the existing source manually before rerunning.",
                )
            return True
        if not configure:
            return False
        self._ensure_commands(tool, {"add-apt-repository": "software-properties-common"})
        self.runner.run_root(
            ["add-apt-repository", "-y", ppa],
            tool,
            "repository configuration",
        )
        return True

    def _run_ripgrep(self) -> None:
        self._release_deb(
            "ripgrep",
            "BurntSushi/ripgrep",
            "ripgrep",
            "rg",
            r"ripgrep_{version}-.+_amd64\.deb",
        )

    def _run_fd(self) -> None:
        self._release_deb(
            "fd",
            "sharkdp/fd",
            "fd",
            "fd",
            r"fd_{version}_amd64\.deb",
        )

    def _run_bat(self) -> None:
        self._release_deb(
            "bat",
            "sharkdp/bat",
            "bat",
            "bat",
            r"bat_{version}_amd64\.deb",
        )

    def _run_dust(self) -> None:
        self._release_deb(
            "dust",
            "bootandy/dust",
            "du-dust",
            "dust",
            r"du-dust_{version}-.+_amd64\.deb",
        )

    def _run_duf(self) -> None:
        self._release_deb(
            "duf",
            "muesli/duf",
            "duf",
            "duf",
            r"duf_{version}_linux_amd64\.deb",
        )

    def _run_eza(self) -> None:
        tool = "eza"
        installed = self._package_version_and_conflict(tool, "eza", "eza")
        if installed is not None:
            print("[apt-managed] eza {} (use apt to update)".format(installed))
            return
        source_path = Path("/etc/apt/sources.list.d/gierens.list")
        key_path = Path("/etc/apt/keyrings/gierens.gpg")
        source_line = "deb [arch=amd64 signed-by=/etc/apt/keyrings/gierens.gpg] http://deb.gierens.de stable main\n"
        source_exists = source_path.exists()
        key_exists = key_path.exists()
        try:
            source_matches = source_exists and source_path.read_text() == source_line
        except OSError as exc:
            raise InstallerError(tool, "repository conflict", str(exc)) from exc
        family_matches = self._matching_apt_sources(("deb.gierens.de",))
        expected_matches = [path for path, _ in family_matches if path == source_path]
        configured = source_matches and key_exists and len(expected_matches) == 1
        if source_exists or key_exists or family_matches:
            if not configured or len(family_matches) != 1:
                paths = ", ".join(str(path) for path, _ in family_matches) or str(source_path)
                raise InstallerError(
                    tool,
                    "repository conflict",
                    "partial or conflicting eza repository configuration exists in {}".format(paths),
                    "Reconcile {} and {} manually before rerunning.".format(
                        source_path,
                        key_path,
                    ),
                )
        if self.check_only:
            suffix = " (repository configured)" if configured else ""
            print("[missing] eza{}".format(suffix))
            return

        self._ensure_commands(tool, {"gpg": "gpg"})
        if not configured:
            armored_key = self._temporary_path("eza-deb.asc")
            binary_key = self._temporary_path("eza-deb.gpg")
            source_file = self._temporary_path("gierens.list")
            self.http.download(
                "https://raw.githubusercontent.com/eza-community/eza/main/deb.asc",
                armored_key,
                tool,
                "repository key download",
            )
            self.runner.run(
                [
                    "gpg",
                    "--batch",
                    "--yes",
                    "--dearmor",
                    "--output",
                    str(binary_key),
                    str(armored_key),
                ],
                tool,
                "repository key conversion",
            )
            source_file.write_text(source_line, encoding="utf-8")
            self._install_root_file(binary_key, key_path, tool)
            self._install_root_file(source_file, source_path, tool)

        self.runner.run_root(["apt-get", "update"], tool, "repository refresh")
        self.runner.run_root(["apt-get", "install", "-y", "eza"], tool, "package install")
        if self._dpkg_version("eza", tool) is None:
            raise InstallerError(tool, "verify", "eza package is not installed")
        print("[installed] eza (future updates are managed by apt)")

    def _run_fzf(self) -> None:
        tool = "fzf"
        target = self.local_bin / "fzf"
        man_target = self.local_man1 / "fzf.1"
        installed = self._managed_binary_version(tool, "fzf", target)
        self._document_target(tool, man_target)
        release = self._latest_release(tool, "junegunn/fzf")
        if installed is not None and compare_versions(installed, release.version) >= 0:
            print("[current] fzf {}".format(installed))
            return
        if self.check_only:
            if installed is None:
                print("[missing] fzf (latest {})".format(release.version))
            else:
                print("[update] fzf {} -> {}".format(installed, release.version))
            return

        asset = release.require_asset(
            tool,
            r"fzf-{}-linux_amd64\.tar\.gz".format(re.escape(release.version)),
        )
        archive = self._download_asset(tool, asset)
        extract_dir = self._temporary_path("fzf-extract")
        extract_dir.mkdir()
        safe_extract_tar(archive, extract_dir, tool)
        binary = extract_dir / "fzf"
        if not binary.is_file():
            raise InstallerError(tool, "extract", "fzf binary not found in release archive")
        os.chmod(binary, 0o755)
        downloaded_version = self._binary_version(binary, ("--version",), tool)
        if compare_versions(downloaded_version, release.version) != 0:
            raise InstallerError(tool, "verify", "downloaded fzf version does not match release")

        man_source = self._temporary_path("fzf.1")
        self.http.download(
            "https://raw.githubusercontent.com/junegunn/fzf/refs/tags/{}/man/man1/fzf.1".format(release.tag),
            man_source,
            tool,
            "man page download",
        )
        try:
            man_contents = man_source.read_text(encoding="utf-8")
        except OSError as exc:
            raise InstallerError(tool, "verify", str(exc)) from exc
        if "fzf {}".format(release.version) not in man_contents:
            raise InstallerError(tool, "verify", "fzf man page version does not match release")

        self._atomic_install_files(
            (
                (binary, target, 0o755),
                (man_source, man_target, 0o644),
            ),
            tool,
        )
        print("[installed] fzf {}".format(release.version))

    def _run_rust(self) -> None:
        tool = "rust"
        candidates = [
            shutil.which("rustup"),
            shutil.which("rustc"),
            str(self.home / ".cargo/bin/rustup") if (self.home / ".cargo/bin/rustup").exists() else None,
            str(self.home / ".cargo/bin/rustc") if (self.home / ".cargo/bin/rustc").exists() else None,
        ]
        installed = next((candidate for candidate in candidates if candidate), None)
        if installed:
            print("[manual] rust is already installed via {}; use rustup to update".format(installed))
            return
        if self.check_only:
            print("[missing] rust (first install uses rustup.rs)")
            return

        self._ensure_commands(tool, {"curl": "curl"})
        installer = self._temporary_path("rustup-init.sh")
        self.http.download("https://sh.rustup.rs", installer, tool, "installer download")
        self.runner.run(
            ["sh", str(installer), "-y", "--no-modify-path"],
            tool,
            "install",
        )
        if not (self.home / ".cargo/bin/rustup").is_file():
            raise InstallerError(tool, "verify", "rustup was not installed to ~/.cargo/bin")
        print("[installed] rust (future updates are managed manually by rustup)")

    def _run_fnm(self) -> None:
        tool = "fnm"
        target = self.local_bin / "fnm"
        installed = self._managed_binary_version(tool, "fnm", target, identity="fnm")
        release = self._latest_release(tool, "Schniz/fnm")
        if installed is not None and compare_versions(installed, release.version) >= 0:
            print("[current] fnm {}".format(installed))
            return
        if self.check_only:
            if installed is None:
                print("[missing] fnm (latest {})".format(release.version))
            else:
                print("[update] fnm {} -> {}".format(installed, release.version))
            return

        self._ensure_commands(tool, {"curl": "curl", "unzip": "unzip"})
        installer = self._temporary_path("fnm-install.sh")
        self.http.download("https://fnm.vercel.app/install", installer, tool, "installer download")
        self.runner.run(
            [
                "bash",
                str(installer),
                "--skip-shell",
                "--install-dir",
                str(self.local_bin),
            ],
            tool,
            "install",
        )
        installed_after = self._binary_version(target, ("--version",), tool, "fnm")
        if compare_versions(installed_after, release.version) < 0:
            raise InstallerError(tool, "verify", "fnm installer did not install the latest release")
        print("[installed] fnm {}".format(installed_after))

    def _run_zoxide(self) -> None:
        tool = "zoxide"
        target = self.local_bin / "zoxide"
        installed = self._managed_binary_version(tool, "zoxide", target, identity="zoxide")
        release = self._latest_release(tool, "ajeetdsouza/zoxide")
        if installed is not None and compare_versions(installed, release.version) >= 0:
            print("[current] zoxide {}".format(installed))
            return
        if self.check_only:
            if installed is None:
                print("[missing] zoxide (latest {})".format(release.version))
            else:
                print("[update] zoxide {} -> {}".format(installed, release.version))
            return

        self._ensure_commands(tool, {"curl": "curl"})
        installer = self._temporary_path("zoxide-install.sh")
        self.http.download(
            "https://raw.githubusercontent.com/ajeetdsouza/zoxide/main/install.sh",
            installer,
            tool,
            "installer download",
        )
        self.runner.run(
            [
                "sh",
                str(installer),
                "--bin-dir",
                str(self.local_bin),
                "--man-dir",
                str(self.home / ".local/share/man"),
            ],
            tool,
            "install",
        )
        installed_after = self._binary_version(target, ("--version",), tool, "zoxide")
        if compare_versions(installed_after, release.version) < 0:
            raise InstallerError(tool, "verify", "zoxide installer did not install the latest release")
        print("[installed] zoxide {}".format(installed_after))

    def _run_fish(self) -> None:
        tool = "fish"
        installed = self._package_version_and_conflict(tool, "fish", "fish")
        if installed is not None:
            installed_major = version_tuple(installed)[0]
            if installed_major != SUPPORTED_FISH_MAJOR:
                raise InstallerError(
                    tool,
                    "major version gate",
                    "installed fish major version is {}, but this script supports {}.x".format(
                        installed_major,
                        SUPPORTED_FISH_MAJOR,
                    ),
                    "Review the major upgrade manually before changing SUPPORTED_FISH_MAJOR.",
                )

        release = self._latest_release(tool, "fish-shell/fish-shell")
        upstream_major = version_tuple(release.version)[0]
        if upstream_major != SUPPORTED_FISH_MAJOR:
            raise InstallerError(
                tool,
                "major version gate",
                "latest stable fish is {}, but this script supports {}.x".format(
                    release.version,
                    SUPPORTED_FISH_MAJOR,
                ),
                "Review the fish release and configuration compatibility, then update the script manually.",
            )
        if installed is not None:
            print("[apt-managed] fish {} (use apt to update)".format(installed))
            return

        if self.platform.distro == "ubuntu":
            expected = "fish-shell/release-{}".format(SUPPORTED_FISH_MAJOR)
            repository_configured = self._configure_ppa(
                tool,
                "ppa:fish-shell/release-{}".format(SUPPORTED_FISH_MAJOR),
                ("fish-shell/", "shells:/fish:", "shells:fish:"),
                expected,
                configure=not self.check_only,
            )
        else:
            repository_configured = self._configure_fish_debian(configure=not self.check_only)

        if self.check_only:
            suffix = " (repository configured)" if repository_configured else ""
            print(
                "[missing] fish {}.x (latest {}){}".format(
                    SUPPORTED_FISH_MAJOR,
                    release.version,
                    suffix,
                )
            )
            return

        self.runner.run_root(["apt-get", "update"], tool, "repository refresh")
        self.runner.run_root(["apt-get", "install", "-y", "fish"], tool, "package install")
        installed_after = self._dpkg_version("fish", tool)
        if installed_after is None or version_tuple(installed_after)[0] != SUPPORTED_FISH_MAJOR:
            raise InstallerError(
                tool,
                "verify",
                "fish {}.x was not installed".format(SUPPORTED_FISH_MAJOR),
            )
        print("[installed] fish {} (future updates are managed by apt)".format(installed_after))

    def _configure_fish_debian(self, *, configure: bool = True) -> bool:
        tool = "fish"
        major = SUPPORTED_FISH_MAJOR
        debian_major = self.platform.major_version
        repository_url = ("https://download.opensuse.org/repositories/shells:/fish:/release:/{}/Debian_{}/").format(
            major, debian_major
        )
        key_path = Path("/etc/apt/keyrings/shells_fish_release_{}.gpg".format(major))
        source_path = Path("/etc/apt/sources.list.d/shells_fish_release_{}.list".format(major))
        source_line = "deb [arch=amd64 signed-by={}] {} /\n".format(key_path, repository_url)

        family_matches = self._matching_apt_sources(("shells:/fish:", "shells:fish:", "fish-shell/"))
        unexpected_paths = [path for path, _ in family_matches if path != source_path]
        if family_matches and (
            unexpected_paths
            or len(family_matches) != 1
            or not all(repository_url in text for _, text in family_matches)
        ):
            paths = ", ".join(str(path) for path, _ in family_matches)
            raise InstallerError(
                tool,
                "repository conflict",
                "conflicting fish APT source found in {}".format(paths),
            )

        source_exists = source_path.exists()
        key_exists = key_path.exists()
        if source_exists or key_exists:
            try:
                source_matches = source_exists and source_path.read_text() == source_line
            except OSError as exc:
                raise InstallerError(tool, "repository conflict", str(exc)) from exc
            if not source_matches or not key_exists:
                raise InstallerError(
                    tool,
                    "repository conflict",
                    "partial or conflicting Debian fish repository configuration exists",
                )
            return True

        if not configure:
            return False

        self._ensure_commands(tool, {"gpg": "gpg"})
        armored_key = self._temporary_path("fish-release.key")
        binary_key = self._temporary_path("fish-release.gpg")
        source_file = self._temporary_path("fish-release.list")
        self.http.download(
            repository_url + "Release.key",
            armored_key,
            tool,
            "repository key download",
        )
        self.runner.run(
            [
                "gpg",
                "--batch",
                "--yes",
                "--dearmor",
                "--output",
                str(binary_key),
                str(armored_key),
            ],
            tool,
            "repository key conversion",
        )
        source_file.write_text(source_line, encoding="utf-8")
        self._install_root_file(binary_key, key_path, tool)
        self._install_root_file(source_file, source_path, tool)
        return True

    def _run_neovim(self) -> None:
        tool = "neovim"
        managed_dir = self.home / ".local/opt/nvim"
        command_link = self.local_bin / "nvim"
        managed_binary = managed_dir / "bin/nvim"
        man_link = self.local_man1 / "nvim.1"
        managed_man = managed_dir / "share/man/man1/nvim.1"

        command_exists = command_link.exists() or command_link.is_symlink()
        if command_exists:
            if not command_link.is_symlink() or command_link.resolve() != managed_binary.resolve():
                raise InstallerError(
                    tool,
                    "conflict check",
                    "{} is not the managed Neovim tarball symlink".format(command_link),
                    "Move or remove the existing AppImage/installation manually, then rerun.",
                )
            if not managed_binary.is_file():
                raise InstallerError(tool, "conflict check", "managed Neovim binary is missing")
        else:
            found = shutil.which("nvim")
            if found:
                raise InstallerError(
                    tool,
                    "conflict check",
                    "nvim is already installed at {}".format(found),
                    "Remove or externally manage the existing installation before rerunning.",
                )
            if managed_dir.exists():
                raise InstallerError(
                    tool,
                    "conflict check",
                    "{} exists without the expected command symlink".format(managed_dir),
                )

        if man_link.exists() or man_link.is_symlink():
            if not man_link.is_symlink() or man_link.resolve() != managed_man.resolve():
                raise InstallerError(tool, "conflict check", "conflicting Neovim man page exists")

        installed = None
        if managed_binary.is_file():
            installed = self._binary_version(managed_binary, ("--version",), tool, "NVIM")
        release = self._latest_release(tool, "neovim/neovim")
        if installed is not None and compare_versions(installed, release.version) >= 0:
            print("[current] neovim {}".format(installed))
            return
        if self.check_only:
            if installed is None:
                print("[missing] neovim (latest {})".format(release.version))
            else:
                print("[update] neovim {} -> {}".format(installed, release.version))
            return

        asset = release.require_asset(tool, r"nvim-linux-x86_64\.tar\.gz")
        archive = self._download_asset(tool, asset)
        extract_dir = self._temporary_path("neovim-extract")
        extract_dir.mkdir()
        safe_extract_tar(archive, extract_dir, tool)
        extracted_root = extract_dir / "nvim-linux-x86_64"
        new_binary = extracted_root / "bin/nvim"
        new_man = extracted_root / "share/man/man1/nvim.1"
        if not new_binary.is_file() or not new_man.is_file():
            raise InstallerError(tool, "extract", "Neovim archive is missing binary or man page")
        downloaded_version = self._binary_version(new_binary, ("--version",), tool, "NVIM")
        if compare_versions(downloaded_version, release.version) != 0:
            raise InstallerError(tool, "verify", "downloaded Neovim version does not match release")

        managed_dir.parent.mkdir(parents=True, exist_ok=True)
        staging_dir = managed_dir.parent / ".nvim.new-{}".format(uuid.uuid4().hex)
        old_dir = managed_dir.parent / ".nvim.old-{}".format(uuid.uuid4().hex)
        shutil.copytree(extracted_root, staging_dir, symlinks=True)
        moved_old = False
        had_command_link = command_link.exists() or command_link.is_symlink()
        had_man_link = man_link.exists() or man_link.is_symlink()
        try:
            if managed_dir.exists():
                managed_dir.rename(old_dir)
                moved_old = True
            staging_dir.rename(managed_dir)
            self._atomic_symlink(managed_binary, command_link, tool)
            self._atomic_symlink(managed_man, man_link, tool)
        except (OSError, InstallerError) as exc:
            if not had_command_link and (command_link.exists() or command_link.is_symlink()):
                command_link.unlink()
            if not had_man_link and (man_link.exists() or man_link.is_symlink()):
                man_link.unlink()
            if managed_dir.exists():
                shutil.rmtree(managed_dir)
            if moved_old and old_dir.exists():
                old_dir.rename(managed_dir)
            if isinstance(exc, InstallerError):
                raise
            raise InstallerError(tool, "install", str(exc)) from exc
        finally:
            if staging_dir.exists():
                shutil.rmtree(staging_dir)
        if old_dir.exists():
            shutil.rmtree(old_dir)
        print("[installed] neovim {}".format(release.version))

    def _run_gdu(self) -> None:
        tool = "gdu"
        target = self.local_bin / "gdu"
        man_target = self.local_man1 / "gdu.1"
        installed = self._managed_binary_version(tool, "gdu", target)
        self._document_target(tool, man_target)
        release = self._latest_release(tool, "dundee/gdu")
        if installed is not None and compare_versions(installed, release.version) >= 0:
            print("[current] gdu {}".format(installed))
            return
        if self.check_only:
            if installed is None:
                print("[missing] gdu (latest {})".format(release.version))
            else:
                print("[update] gdu {} -> {}".format(installed, release.version))
            return

        binary_asset = release.require_asset(tool, r"gdu_linux_amd64\.tgz")
        man_asset = release.require_asset(tool, r"gdu\.1\.tgz")
        binary_archive = self._download_asset(tool, binary_asset)
        man_archive = self._download_asset(tool, man_asset)
        extract_dir = self._temporary_path("gdu-extract")
        extract_dir.mkdir()
        safe_extract_tar(binary_archive, extract_dir, tool)
        safe_extract_tar(man_archive, extract_dir, tool)
        binary = extract_dir / "gdu_linux_amd64"
        man_source = extract_dir / "gdu.1"
        if not binary.is_file() or not man_source.is_file():
            raise InstallerError(tool, "extract", "gdu archive is missing binary or man page")
        os.chmod(binary, 0o755)
        downloaded_version = self._binary_version(binary, ("--version",), tool, "gdu")
        if compare_versions(downloaded_version, release.version) != 0:
            raise InstallerError(tool, "verify", "downloaded gdu version does not match release")
        self._atomic_install_files(
            (
                (binary, target, 0o755),
                (man_source, man_target, 0o644),
            ),
            tool,
        )
        print("[installed] gdu {}".format(release.version))

    def _run_nvtop(self) -> None:
        if self.platform.distro == "ubuntu":
            self._run_nvtop_ubuntu()
        else:
            self._run_nvtop_debian()

    def _run_nvtop_ubuntu(self) -> None:
        tool = "nvtop"
        installed = self._package_version_and_conflict(tool, "nvtop", "nvtop")
        if installed is not None:
            print("[apt-managed] nvtop {} (use apt to update)".format(installed))
            return
        repository_configured = self._configure_ppa(
            tool,
            "ppa:quentiumyt/nvtop",
            ("quentiumyt/nvtop",),
            "quentiumyt/nvtop",
            configure=not self.check_only,
        )
        if self.check_only:
            suffix = " (repository configured)" if repository_configured else ""
            print("[missing] nvtop{}".format(suffix))
            return
        self.runner.run_root(["apt-get", "update"], tool, "repository refresh")
        self.runner.run_root(["apt-get", "install", "-y", "nvtop"], tool, "package install")
        if self._dpkg_version("nvtop", tool) is None:
            raise InstallerError(tool, "verify", "nvtop package is not installed")
        print("[installed] nvtop (future updates are managed by apt)")

    def _run_nvtop_debian(self) -> None:
        tool = "nvtop"
        target = self.local_bin / "nvtop"
        installed = self._managed_binary_version(tool, "nvtop", target, identity="nvtop")
        release = self._latest_release(tool, "Syllo/nvtop")
        if installed is not None and compare_versions(installed, release.version) >= 0:
            print("[current] nvtop {}".format(installed))
            return
        if self.check_only:
            if installed is None:
                print("[missing] nvtop (latest {})".format(release.version))
            else:
                print("[update] nvtop {} -> {}".format(installed, release.version))
            return

        asset = release.require_asset(
            tool,
            r"nvtop-{}-x86_64\.AppImage".format(re.escape(release.version)),
        )
        appimage = self._download_asset(tool, asset)
        os.chmod(appimage, 0o755)
        downloaded_version = self._binary_version(appimage, ("--version",), tool, "nvtop")
        if compare_versions(downloaded_version, release.version) != 0:
            raise InstallerError(tool, "verify", "downloaded nvtop version does not match release")
        self._atomic_install_file(appimage, target, 0o755, tool)
        print("[installed] nvtop {}".format(release.version))

    def _run_uv(self) -> None:
        tool = "uv"
        target = self.local_bin / "uv"
        companion = self.local_bin / "uvx"
        found = shutil.which("uv")
        found_companion = shutil.which("uvx")
        target_exists = target.exists() or target.is_symlink()
        if found and target_exists and Path(found).resolve() != target.resolve():
            raise InstallerError(
                tool,
                "conflict check",
                "uv exists at {} and {}".format(found, target),
                "Remove the duplicate installation or fix PATH ordering before rerunning.",
            )
        if found and not target_exists:
            print("[external] uv is managed by {}".format(found))
            return
        if target_exists:
            if target.is_symlink() or not target.is_file():
                raise InstallerError(tool, "conflict check", "managed uv target is not a regular file")
            if not companion.exists():
                raise InstallerError(
                    tool,
                    "conflict check",
                    "managed uv exists, but its uvx companion is missing at {}".format(companion),
                )
            if found_companion and Path(found_companion).resolve() != companion.resolve():
                raise InstallerError(
                    tool,
                    "conflict check",
                    "uvx at {} shadows the managed companion at {}".format(
                        found_companion,
                        companion,
                    ),
                )
            args = [str(target), "self", "update"]
            if self.check_only:
                args.append("--dry-run")
            env = {"UV_NO_MODIFY_PATH": "1"}
            github_token = os.environ.get("GITHUB_TOKEN")
            if github_token:
                env["UV_GITHUB_TOKEN"] = github_token
            result = self.runner.run(
                args,
                tool,
                "self update" if not self.check_only else "update check",
                capture=True,
                check=False,
                env=env,
            )
            output = (result.stdout + "\n" + result.stderr).strip()
            if result.returncode != 0:
                if "Self-update is only available" in output or "not installed via" in output:
                    print("[external] uv at {} is not a standalone installation".format(target))
                    return
                raise InstallerError(tool, "update check", output or "uv self update failed")
            print(output)
            print("[managed] uv standalone installation")
            return
        if companion.exists() or companion.is_symlink() or found_companion:
            location = found_companion or str(companion)
            raise InstallerError(
                tool,
                "conflict check",
                "uvx already exists at {}, but uv is not installed".format(location),
                "Remove or externally manage the partial installation before rerunning.",
            )
        if self.check_only:
            print("[missing] uv")
            return

        self._ensure_commands(tool, {"curl": "curl"})
        installer = self._temporary_path("uv-install.sh")
        self.http.download("https://astral.sh/uv/install.sh", installer, tool, "installer download")
        self.runner.run(
            ["sh", str(installer)],
            tool,
            "install",
            env={
                "UV_INSTALL_DIR": str(self.local_bin),
                "UV_NO_MODIFY_PATH": "1",
            },
        )
        installed_version = self._binary_version(target, ("--version",), tool, "uv")
        print("[installed] uv {}".format(installed_version))

    def _uv_path(self) -> Optional[Path]:
        found = shutil.which("uv")
        if found:
            return Path(found)
        target = self.local_bin / "uv"
        if target.is_file() and not target.is_symlink():
            return target
        return None

    def _gpustat_version(self, uv: Path) -> Optional[str]:
        result = self.runner.run(
            [str(uv), "tool", "list"],
            "gpustat",
            "tool query",
            capture=True,
        )
        match = re.search(r"^gpustat\s+v([^\s]+)", result.stdout, re.MULTILINE)
        if match is None:
            return None
        try:
            return extract_version(match.group(1))
        except ValueError as exc:
            raise InstallerError("gpustat", "tool query", str(exc)) from exc

    def _uv_tool_binary(self, uv: Path, command: str) -> Path:
        result = self.runner.run(
            [str(uv), "tool", "dir", "--bin"],
            "gpustat",
            "tool query",
            capture=True,
        )
        bin_directory = result.stdout.strip()
        if not bin_directory:
            raise InstallerError("gpustat", "tool query", "uv returned no tool bin directory")
        return Path(bin_directory) / command

    def _run_gpustat(self) -> None:
        tool = "gpustat"
        uv = self._uv_path()
        if uv is None:
            if self.check_only:
                print("[missing] gpustat (uv is not installed)")
                return
            raise InstallerError(tool, "dependency", "uv is not available after dependency installation")

        installed = self._gpustat_version(uv)
        found = shutil.which("gpustat")
        if installed is None:
            if found:
                raise InstallerError(
                    tool,
                    "conflict check",
                    "gpustat is provided by {}, but is not managed by uv".format(found),
                )
        else:
            managed_command = self._uv_tool_binary(uv, "gpustat")
            if not managed_command.exists():
                raise InstallerError(
                    tool,
                    "conflict check",
                    "uv lists gpustat, but {} is missing".format(managed_command),
                )
            if found and Path(found).resolve() != managed_command.resolve():
                raise InstallerError(
                    tool,
                    "conflict check",
                    "{} shadows the uv-managed gpustat at {}".format(found, managed_command),
                    "Remove the duplicate installation or fix PATH ordering before rerunning.",
                )
        data = self.http.json("https://pypi.org/pypi/gpustat/json", tool, "PyPI metadata")
        info = data.get("info")
        latest_value = info.get("version") if isinstance(info, dict) else None
        if not isinstance(latest_value, str):
            raise InstallerError(tool, "PyPI metadata", "gpustat has no valid latest version")
        try:
            latest = extract_version(latest_value)
        except ValueError as exc:
            raise InstallerError(tool, "PyPI metadata", str(exc)) from exc

        if installed is not None and compare_versions(installed, latest) >= 0:
            print("[current] gpustat {}".format(installed))
            return
        if self.check_only:
            if installed is None:
                print("[missing] gpustat (latest {})".format(latest))
            else:
                print("[update] gpustat {} -> {}".format(installed, latest))
            return

        if installed is None:
            command = [str(uv), "tool", "install", "gpustat@latest"]
            phase = "install"
        else:
            command = [str(uv), "tool", "upgrade", "gpustat"]
            phase = "update"
        self.runner.run(command, tool, phase)
        installed_after = self._gpustat_version(uv)
        if installed_after is None or compare_versions(installed_after, latest) < 0:
            raise InstallerError(tool, "verify", "uv did not install the latest gpustat")
        print("[installed] gpustat {}".format(installed_after))


def interactive_selection() -> List[str]:
    print("Select tools to install or update:")
    for index, tool in enumerate(TOOLS, start=1):
        dependency_note = " (also installs {})".format(", ".join(tool.dependencies)) if tool.dependencies else ""
        print("{:>2}. {:<10} {}{}".format(index, tool.name, tool.description, dependency_note))
    response = input("Enter numbers separated by commas, or 'all': ").strip().lower()
    if response == "all":
        return [tool.name for tool in TOOLS]
    if not response:
        raise ValueError("no tools selected")

    selected: List[str] = []
    for value in response.split(","):
        value = value.strip()
        if not value.isdigit():
            raise ValueError("invalid selection: {!r}".format(value))
        index = int(value)
        if index < 1 or index > len(TOOLS):
            raise ValueError("selection out of range: {}".format(index))
        name = TOOLS[index - 1].name
        if name not in selected:
            selected.append(name)
    return selected


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Install and update selected command-line tools on Ubuntu or Debian.",
    )
    parser.add_argument("tools", nargs="*", metavar="TOOL")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--all", action="store_true", help="select every tool")
    mode.add_argument("--interactive", action="store_true", help="choose tools interactively")
    parser.add_argument(
        "--check",
        action="store_true",
        help="report updates without changing the system",
    )
    parser.add_argument("--list", action="store_true", help="list available tools and exit")
    return parser


def select_tools(args: argparse.Namespace, parser: argparse.ArgumentParser) -> List[str]:
    unknown = sorted(set(args.tools) - set(TOOL_BY_NAME))
    if unknown:
        parser.error(
            "unknown tool(s): {}; choose from {}".format(
                ", ".join(unknown),
                ", ".join(sorted(TOOL_BY_NAME)),
            )
        )
    if args.list:
        if args.tools or args.all or args.interactive or args.check:
            parser.error("--list cannot be combined with other arguments")
        for tool in TOOLS:
            print("{:<10} {}".format(tool.name, tool.description))
        return []
    if args.all:
        if args.tools:
            parser.error("--all cannot be combined with tool names")
        selected = [tool.name for tool in TOOLS]
    elif args.interactive:
        if args.tools:
            parser.error("--interactive cannot be combined with tool names")
        try:
            selected = interactive_selection()
        except (EOFError, ValueError) as exc:
            parser.error(str(exc))
    elif args.tools:
        selected = args.tools
    elif sys.stdin.isatty() and sys.stdout.isatty():
        try:
            selected = interactive_selection()
        except (EOFError, ValueError) as exc:
            parser.error(str(exc))
    else:
        parser.error("select tools, use --all, or run --interactive in a terminal")
    return expand_dependencies(selected)


def main(argv: Optional[Sequence[str]] = None) -> int:
    if sys.version_info < MINIMUM_PYTHON:
        print("Python 3.8 or newer is required.", file=sys.stderr)
        return 2

    parser = build_parser()
    args = parser.parse_args(argv)
    selected = select_tools(args, parser)
    if args.list:
        return 0

    current_tool = "platform"
    try:
        platform_info = detect_platform()
        with tempfile.TemporaryDirectory(prefix="install-tools-") as temporary_directory:
            installer = Installer(
                platform_info,
                Path(temporary_directory),
                args.check,
            )
            for tool in selected:
                current_tool = tool
                print("\n==> {}".format(tool))
                installer.run(tool)
    except InstallerError as exc:
        print("\nFAILED", file=sys.stderr)
        print("  tool:  {}".format(exc.tool), file=sys.stderr)
        print("  phase: {}".format(exc.phase), file=sys.stderr)
        print("  error: {}".format(exc.detail), file=sys.stderr)
        if exc.hint:
            print("  hint:  {}".format(exc.hint), file=sys.stderr)
        return 1
    except OSError as exc:
        print("\nFAILED", file=sys.stderr)
        print("  tool:  {}".format(current_tool), file=sys.stderr)
        print("  phase: filesystem operation", file=sys.stderr)
        print("  error: {}".format(exc), file=sys.stderr)
        return 1

    verb = "Checked" if args.check else "Completed"
    print("\n{}: {}".format(verb, ", ".join(selected)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
