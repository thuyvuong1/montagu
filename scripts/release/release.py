#!/usr/bin/env python3
import re

from helpers import run

release_tag_pattern = re.compile(r"^v\d\.\d\.\d(-RC\d)?$")


def get_latest_release_tag():
    tags = run("git tag").split('\n')
    release_tags = sorted(t for t in tags if release_tag_pattern.match(t))
    return release_tags[-1]


def git_is_clean():
    return not run("git status -s")


if __name__ == "__main__":
    if not git_is_clean():
        print("Git status reports as not clean; aborting release")
    else:
        print("The latest release was: " + get_latest_release_tag())
        new_tag = input("What should the new release tag be? ")
