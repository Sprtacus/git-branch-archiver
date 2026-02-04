# Git Branch Archiver

A lightweight CLI tool to export all branches (and optionally tags) from a Git repository into separate folders and archive them as `.zip` and `.tar` files. Useful for backups and other workflows. Works with local repositories or remote URLs and writes the archives into the specified output directory.

Usage:

```bash
python archiver.py --repo https://github.com/example/project.git --out ~/backups/project_backup
```

Options:
- `--include-tags`  Export tags as well
- `--keep-temp`     Keep the temporary clone for inspection
- `--tmp <dir>`     Directory for temporary clones
- `-v`              Verbose logging

## Installation & Requirements

- **Requirements:** Python 3 (recommended 3.8+), and **Git** available on PATH.
- **No external Python dependencies.** `requirements.txt` is intentionally empty.

Quick install (optional virtualenv):

```bash
git clone https://github.com/yourname/git-branch-archiver.git
cd git-branch-archiver
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

---

## Example

Export a repository's branches (local path or remote URL) and archive them:

```bash
python archiver.py --repo /path/to/repo --out /path/to/backups/project_backup --include-tags
```

This creates one folder per branch inside the output directory and writes `.zip` and `.tar` archives there.

Tip: Works well as part of periodic backups (cronjob, CI task, etc.).
