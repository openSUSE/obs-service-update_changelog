import sys
import os
import py
import pytz
import logging
from git import Repo
from datetime import datetime
from jinja2 import Environment, PackageLoader, select_autoescape

try:
    from shlex import quote as cmd_quote
except ImportError:
    from pipes import quote as cmd_quote


OSC_VC = "/usr/lib/build/vc"

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
log.addHandler(ch)


def get_template():
    env = Environment(
        loader=PackageLoader("updatechangelog", "templates"),
        autoescape=select_autoescape(["txt"]),
    )

    return env.get_template("header.txt")


def main():
    repo_path = py.path.local(os.getcwd()) / "salt-packaging"
    repo = Repo(repo_path.strpath)

    commit = repo.commit("HEAD")

    lastrevision = ""
    lastrevision_file = py.path.local("_lastrevision")
    if lastrevision_file.isfile():
        lastrevision = lastrevision_file.read().strip()

    lastrevision = lastrevision or commit.hexsha

    if not repo.git.merge_base(lastrevision, commit.hexsha):
        log.error(
            (
                "%s is not an ancestor of %s. "
                "Maybe force-push was used. "
                "Fix _lastrevision reference."
            )
            % (lastrevision, commt.hexsha)
        )
        sys.exit(1)

    existing_patches = set(
        [
            py.path.local(it.path).basename
            for it in repo.commit(lastrevision).tree["salt"]
            if it.path.endswith(".patch")
        ]
    )

    current_patches = set(
        [
            py.path.local(it.path).basename
            for it in repo.commit("HEAD").tree["salt"]
            if it.path.endswith(".patch")
        ]
    )

    deleted = existing_patches.difference(current_patches)
    added = current_patches.difference(existing_patches)
    modified = set(
        [
            py.path.local(it.a_path).basename
            for it in repo.commit("HEAD").diff(lastrevision)
            if it.a_path.endswith(".patch")
        ]
    ).difference(added.union(deleted))

    # Sort patches based the times of the commits
    _sort_function = lambda x: next(
        repo.iter_commits(paths=os.path.join("salt", x), max_count=1)
    ).committed_date
    added = sorted(added, key=_sort_function, reverse=True)
    modified = sorted(modified, key=_sort_function, reverse=True)
    deleted = sorted(deleted, key=_sort_function, reverse=True)

    template = get_template()

    current_dt = datetime.now().replace(tzinfo=pytz.utc)

    lastrevision_commit = repo.commit(lastrevision)
    ref = repo.commit("HEAD")
    messages = []
    while ref.hexsha != repo.commit(lastrevision).hexsha:
        for line in ref.message.split("\n"):
            if "[skip]" not in line and line:
                messages.append(line)
        ref = repo.commit(f"{ref.hexsha}^")

    if not messages:
        log.info("Nothing new.")
    else:
        changelog_entry = template.render(
            messages=messages,
            added=added,
            modified=modified,
            deleted=deleted,
        ).strip()

        cmd = "mailaddr={0} {1} -m {2}".format(
            cmd_quote(commit.author.email), OSC_VC, cmd_quote(changelog_entry)
        )
        os.system(cmd)

    try:
        with open("_lastrevision", "w") as f:
            f.write(commit.hexsha)
    except Exception as exc:
        log.error("Unable to update _lastrevision file: {}".format(exc))
        sys.exit(1)
