"""Click/Rich presentation. The library itself neither prints nor owns an event loop."""

import asyncio
import json
import shlex
import signal
from contextlib import contextmanager
from dataclasses import asdict, replace
from importlib.metadata import version
from pathlib import Path

import click
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from . import state
from .backend import RcloneBackend
from .config import load_config
from .demo import create_demo
from .events import Event
from .runner import Runner


def config_option(function):
    return click.option(
        "--config",
        "config_path",
        type=click.Path(path_type=Path, exists=True, dir_okay=False),
        default="backup.toml",
        show_default=True,
    )(function)


@contextmanager
def friendly_errors():
    try:
        yield
    except (OSError, ValueError, RuntimeError) as exc:
        raise click.ClickException(str(exc)) from exc


@contextmanager
def display(plain: bool, json_events: bool):
    console = Console(stderr=True)
    tasks = {}
    progress = Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
        refresh_per_second=4,
        disable=plain or json_events or not console.is_terminal,
    )

    def emit(event: Event):
        if json_events:
            click.echo(json.dumps(asdict(event)))
        elif progress.disable:
            if event.phase not in {"transfer", "archive"}:
                click.echo(f"{event.task}: {event.phase} {event.message}".rstrip(), err=True)
        else:
            if event.task not in tasks:
                tasks[event.task] = progress.add_task(event.task, total=None)
            task_id = tasks[event.task]
            if event.phase == "started":
                progress.reset(task_id, total=None, completed=0)
            if event.phase in {"transfer", "archive"}:
                progress.update(task_id, completed=event.completed, total=event.total)
            if event.phase in {"done", "failed"}:
                progress.update(task_id, description=f"{event.task}: {event.phase}")
                progress.stop_task(task_id)
            if event.phase in {"failed", "retry"}:
                console.print(f"{event.task}: {event.message}", markup=False)

    with progress:
        yield emit


def finish(result, json_events: bool):
    if json_events:
        click.echo(json.dumps({"type": "result", **asdict(result)}, default=str))
    else:
        click.echo(f"{result.run_id}: {result.status}")
        if result.archive:
            click.echo(f"ZIP: {result.archive}")
        for error in result.errors:
            click.echo(error, err=True)
    if not result.success:
        raise click.exceptions.Exit(1)


def run_async(operation):
    """Give SIGTERM the same cleanup path as task cancellation, then exit 143."""
    terminated = False

    async def execute():
        loop = asyncio.get_running_loop()
        task = asyncio.current_task()
        previous = signal.getsignal(signal.SIGTERM)

        def terminate():
            nonlocal terminated
            # Repeated signals must not interrupt subprocess/thread cleanup.
            if not terminated:
                terminated = True
                task.cancel()

        loop.add_signal_handler(signal.SIGTERM, terminate)
        try:
            return await operation
        finally:
            loop.remove_signal_handler(signal.SIGTERM)
            signal.signal(signal.SIGTERM, previous)

    try:
        return asyncio.run(execute())
    except asyncio.CancelledError:
        if not terminated:
            raise
        click.echo("Terminated.", err=True)
        raise SystemExit(128 + signal.SIGTERM) from None


@click.group()
@click.version_option(version=version("stashfleet"))
def main():
    """Pull server folders, create one ZIP, optionally upload it to the cloud."""


@main.command()
@config_option
@click.option("--parallel-hosts", type=click.IntRange(min=1))
@click.option("--plain", is_flag=True, help="Use plain logs suitable for systemd.")
@click.option("--json-events", is_flag=True, help="Emit newline-delimited JSON events.")
@click.option("--dry-run", is_flag=True, help="Print the plan without network or writes.")
def run(config_path, parallel_hosts, plain, json_events, dry_run):
    """Run all configured backups once."""
    with friendly_errors():
        config = load_config(config_path)
        if parallel_hosts is not None:
            config = replace(config, parallel_hosts=parallel_hosts)
        if dry_run:
            show_plan(config, json_events)
            return
        with display(plain, json_events) as emit:
            result = run_async(Runner(config, emit=emit).run())
        finish(result, json_events)


def show_plan(config, json_events=False):
    backend = RcloneBackend(config)
    run_directory = config.destination / "runs" / "<run-id>"
    archive = run_directory / "stashfleet-<run-id>.zip"
    target = config.cloud.target(archive.name) if config.cloud.enabled else None
    plan = {
        "type": "plan",
        "dry_run": True,
        "parallel_hosts": config.parallel_hosts,
        "transfers_per_host": config.transfers,
        "pulls": [],
        "archive": {
            "path": str(archive),
            "compression": config.archive.compression,
            "level": config.archive.options()[1],
        },
        "upload": backend.arguments("copyto", str(archive), target, "--immutable")
        if target
        else None,
        "retention": {"keep_local": config.keep_local, "keep_cloud": config.keep_cloud},
    }
    for job in config.jobs:
        destination = run_directory / "data" / job.host / job.name
        plan["pulls"].append(backend.pull_arguments(config.hosts[job.host], job, destination))
    if json_events:
        click.echo(json.dumps(plan))
        return
    click.echo("DRY RUN: no connections, command execution, or backup writes.")
    click.echo(f"Parallel hosts: {config.parallel_hosts}; file transfers/host: {config.transfers}")
    for command in plan["pulls"]:
        click.echo(f"Pull: {shlex.join(command)}")
    click.echo(f"ZIP: {archive}")
    click.echo(f"Compression: {config.archive.compression}; level={plan['archive']['level']}")
    click.echo(f"Upload: {shlex.join(plan['upload']) if target else 'disabled'}")
    local = f"keep newest {config.keep_local} completed runs" if config.keep_local else "keep all"
    cloud = f"keep newest {config.keep_cloud} uploaded ZIPs" if config.keep_cloud else "keep all"
    click.echo(f"Retention: local={local}; cloud={cloud if target else 'disabled'}")
    click.echo(
        "ZIP/upload require all pulls to succeed. File changes and deletions are not evaluated."
    )


@main.command()
@config_option
def doctor(config_path):
    """Validate config and local dependencies; never connect to servers or Drive."""
    with friendly_errors():
        config = load_config(config_path)
        RcloneBackend(config).validate()
        click.echo("Configuration and executable paths OK. SSH/Drive access is untested.")


@main.command("retry-upload")
@click.argument("run_id")
@config_option
@click.option("--plain", is_flag=True)
@click.option("--json-events", is_flag=True)
def retry_upload(run_id, config_path, plain, json_events):
    """Upload an existing verified ZIP without pulling servers again."""
    with friendly_errors():
        config = load_config(config_path)
        with display(plain, json_events) as emit:
            result = run_async(Runner(config, emit=emit).retry_upload(run_id))
        finish(result, json_events)


@main.command()
@config_option
@click.option("--limit", type=click.IntRange(min=1), default=10, show_default=True)
def status(config_path, limit):
    """Print recent local run manifests as JSON."""
    with friendly_errors():
        config = load_config(config_path)
        click.echo(json.dumps(state.history(config.destination)[:limit], indent=2))


@main.command()
@click.option(
    "--directory",
    type=click.Path(path_type=Path),
    required=True,
    help="A NEW directory for disposable fixtures and fake cloud output.",
)
@click.option("--plain", is_flag=True)
@click.option("--json-events", is_flag=True)
def demo(directory, plain, json_events):
    """Exercise pull -> ZIP -> upload using local fake data only. No SSH/rclone needed."""
    with friendly_errors():
        config, backend = create_demo(directory.expanduser().resolve())
        with display(plain, json_events) as emit:
            result = run_async(Runner(config, backend=backend, emit=emit).run())
        finish(result, json_events)
