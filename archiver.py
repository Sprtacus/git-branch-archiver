#!/usr/bin/env python3
"""Simple Git branch archiver

Exports all branches (and optionally tags) from a given repo into separate
folders, then creates .zip and .tar archives for backup.

Usage:
  python archiver.py --repo <path-or-url> --out <output-dir>
"""

from __future__ import annotations
import argparse
import io
import logging
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


LOG = logging.getLogger("git-branch-archiver")


def run(cmd, cwd=None, capture_output=False):
    LOG.debug("Running: %s (cwd=%s)", cmd, cwd)
    return subprocess.run(cmd, cwd=cwd, check=True, stdout=subprocess.PIPE if capture_output else None)


def clone_repo_if_needed(repo: str, tmp_parent: Path) -> Path:
    """Return a path to a local repository to operate on.

    If `repo` is an existing directory with a `.git` it is used directly.
    Otherwise we clone the repository as a bare clone into a temporary dir.
    """
    p = Path(repo)
    if p.exists() and (p / ".git").exists():
        LOG.info("Using local repository: %s", p)
        return p

    tmp_dir = Path(tempfile.mkdtemp(prefix="git-archiver-", dir=tmp_parent))
    LOG.info("Cloning repository into temporary dir: %s", tmp_dir)
    # use --mirror so all refs are present
    run(["git", "clone", "--mirror", repo, str(tmp_dir)])
    return tmp_dir


def list_refs(repo_dir: Path, include_tags: bool) -> list[str]:
    """List branch and (optionally) tag refs in the repo."""
    # refs/heads and refs/remotes
    out = run(["git", "for-each-ref", "--format=%(refname)", "refs/heads", "refs/remotes"], cwd=str(repo_dir), capture_output=True)
    refs = [r.strip() for r in out.stdout.decode().splitlines() if r.strip()]
    if include_tags:
        out = run(["git", "for-each-ref", "--format=%(refname)", "refs/tags"], cwd=str(repo_dir), capture_output=True)
        refs += [r.strip() for r in out.stdout.decode().splitlines() if r.strip()]
    # Normalize and unique by short name
    seen = set()
    result: list[str] = []
    for r in refs:
        # remove leading refs/... to a stable short name
        if r.startswith("refs/heads/"):
            short = r[len("refs/heads/"):]
        elif r.startswith("refs/remotes/"):
            short = r[len("refs/remotes/"):]
        elif r.startswith("refs/tags/"):
            short = r[len("refs/tags/"):]
        else:
            short = r
        if short in seen:
            continue
        seen.add(short)
        result.append((r, short))
    # return list of strings as "<full_ref|short>" pairs in a formatted way
    return [f"{full}|{short}" for (full, short) in result]


def export_ref_to_folder(repo_dir: Path, refname: str, short_name: str, dest: Path):
    """Exports a single ref (branch or tag) into `dest` folder.
    Uses `git archive` to avoid checking out working trees.
    """
    dest.mkdir(parents=True, exist_ok=True)
    safe_name = short_name.replace("/", "__")
    LOG.info("Exporting %s -> %s", short_name, dest)
    # git archive expects a tree-ish; use full ref name when possible
    full = refname
    # create tar bytes
    proc = run(["git", "archive", "--format=tar", full], cwd=str(repo_dir), capture_output=True)
    data = proc.stdout
    # extract tar into dest
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:") as t:
        t.extractall(path=str(dest))


def archive_output_dir(output_dir: Path, base_name: Path):
    """Create .zip and .tar archives for the given output dir."""
    zip_path = shutil.make_archive(str(base_name), "zip", root_dir=str(output_dir))
    tar_path = shutil.make_archive(str(base_name), "tar", root_dir=str(output_dir))
    LOG.info("Created archives: %s, %s", zip_path, tar_path)
    return zip_path, tar_path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--repo", "-r", required=True, help="Path to local repo or remote URL")
    p.add_argument("--out", "-o", required=True, help="Output directory to store branch folders")
    p.add_argument("--include-tags", action="store_true", help="Also export tags")
    p.add_argument("--tmp", default=None, help="Directory to place temporary clones (defaults to system tmp)")
    p.add_argument("--keep-temp", action="store_true", help="Do not remove temporary clone")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")

    outdir = Path(args.out).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    tmp_parent = Path(args.tmp) if args.tmp else None
    repo_dir = clone_repo_if_needed(args.repo, tmp_parent)

    try:
        refs = list_refs(repo_dir, args.include_tags)
        if not refs:
            LOG.warning("No branches or tags found to export")
        for pair in refs:
            full, short = pair.split("|", 1)
            dest = outdir / short.replace("/", "__")
            try:
                export_ref_to_folder(repo_dir, full, short, dest)
            except subprocess.CalledProcessError:
                LOG.exception("Failed to export %s", short)

        # store archives inside the output directory so everything stays grouped
        base_name = outdir / (outdir.name + "_archive")
        zip_path, tar_path = archive_output_dir(outdir, base_name)
        LOG.info("Saved archives inside output dir: %s, %s", zip_path, tar_path)
        print(f"Created archives:\n - {zip_path}\n - {tar_path}")
        return 0
    finally:
        if (not args.keep_temp) and (not (Path(args.repo).exists() and (Path(args.repo) / ".git").exists())):
            # repo_dir was a temporary clone; remove it
            try:
                LOG.debug("Removing temporary repo: %s", repo_dir)
                shutil.rmtree(repo_dir)
            except Exception:
                LOG.exception("Failed to remove temporary dir %s", repo_dir)


if __name__ == "__main__":
    raise SystemExit(main())
