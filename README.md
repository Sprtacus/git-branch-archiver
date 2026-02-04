# Git Branch Archiver

A small Python tool that exports all branches (and optionally tags) from a Git repository into separate folders and then archives them as `.zip` and `.tar` files. The generated archives are stored inside the specified output directory. This is useful for creating backups on SMB shares or external storage so branches can be deleted safely without losing information.

Usage:

```bash
python archiver.py --repo https://github.com/example/project.git --out ~/backups/project_backup
```

Options:
- `--include-tags`: also export tags
- `--keep-temp`: do not remove the temporary clone
- `--tmp <dir>`: directory to place temporary clones
- `-v`: verbose logging

---

## Example repository for testing

A small example repository is included in `example_repo` with multiple branches and a tag. You can test the archiver locally using:

```bash
python archiver.py --repo ./example_repo --out ./example_repo_backup --include-tags
```

This will create a folder for each branch in `./example_repo_backup` and place the `.zip` and `.tar` archives there.
