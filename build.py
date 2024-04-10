from __future__ import annotations

import re
import subprocess
import sys

# Grab Version from __init__.py
version = ''
with open('__init__.py') as file:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', file.read(), re.MULTILINE).group(1)  # type:ignore

if not version:
    raise RuntimeError("version is not set")

# Grab Version from `CHANGELOG.md`
with open("CHANGELOG.md") as changelog:
    changelog_data = changelog.read()
    split_data = changelog_data.split("\n")
    ver_data = split_data[0]  # Version - *.*.*** (commit hash)
    ver_data = ver_data.split(" ")
    last_commit: str = ver_data[-1][1:8]
    cl_ver: str = ver_data[-3]
    changelog.close()

# Compare CHANGELOG.md and __init__.py Versions.
if version == cl_ver:
    raise ValueError(f"Version has not been updated `__init__.py`: {version} == `CHANGELOG.md`: {cl_ver}")

# Verify that the current branch is `developer`.
output: bytes = subprocess.check_output(["git", "branch"])
branch: str = output.decode("utf-8").strip("*").strip().split("\n")[0]
if branch != "developer":
    raise RuntimeError(f"Current branch is not `developer`: {branch}")

# Verify that there are new commits.
output = subprocess.check_output(["git", "log"])
new_commit = output.decode("utf-8").split("\n")[0][7:14]
if new_commit == last_commit:
    raise RuntimeError(f"No new commits since last version: {last_commit} == {new_commit}")

# Format the git log data into a dictionary for Changelog.
output = subprocess.check_output(['git', 'log', '--format="%B"', last_commit + "..HEAD"])
files: dict[str, list[str]] = {}
cur_data = output.decode("utf-8")
cur_data = cur_data.strip().strip('"')
cur_data = cur_data.split("\n")
for entry in cur_data:
    if len(entry) == 0 or len(entry) == 1:
        continue

    if entry.startswith('"'):
        entry = entry.strip('"')

    elif entry.startswith("#"):
        file_name = entry[1:].strip()
        if file_name not in files:
            files[file_name] = []

    else:
        if entry.startswith("--"):
            entry = "\t-" + entry[2:]
        files[file_name].append(entry)


# Format the data into the `CHANGELOG.md`
user = "k8thekat"
project = "GatekeeperV2"
set_version = f"## Version - {version} - [{new_commit[:7]}](https://github.com/{user}/{project}/commit/{new_commit})\n"
data = set_version
for file_name, file_changes in files.items():
    data: str = data + "#### " + file_name + "\n" + "\n".join(file_changes) + "\n\n"

data = data + changelog_data
with open("CHANGELOG.md", "w") as changelog:
    changelog.write(data)
    changelog.close()

# git merge --no-ff and tag the merge to main.
