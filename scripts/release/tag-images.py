#!/usr/bin/env python3
"""Tags images used in a particular release and pushes the tags into
our local docker registrty at docker.montagu.dide.ic.ac.uk:5000.  If
run with the "publish" option it will also publish images to
https://hub.docker.com/u/vimc

Usage:
  tag-images.py tag [--publish] <version>
  tag-images.py publish <version>
"""
import docker
import docopt
from subprocess import run
import os
import re
import git_helpers

os.chdir("../..")
tag = "v0.8.0"

# This feels like something we should have elsewhere; it's a map of
# the name of the *repo* (the key here) with the name of the submodule
# *subdirectory* (the value, which then maps onto the docker compose
# container name).  It's easy enough to lift this out later though
container_repo_map = {
    "montagu-api": "api",
    "montagu-reporting-api": "reporting-api",
    "montagu-db": "db",
    "montagu-contrib-portal": "contrib-portal",
    "montagu-admin-portal": "admin-portal",
    "montagu-report-portal": "report-portal",
    "montagu-reverse-proxy": "proxy",
    "montagu-orderly": "orderly"
}

registry = "docker.montagu.dide.ic.ac.uk:5000"

def set_image_tag(name, version):
    repo_name = container_repo_map[name]
    sha = git_helpers.get_past_submodule_version(repo_name, version)
    d = docker.client.from_env()
    img = d.images.pull("{}/{}:{}".format(registry, name, sha))
    tag_and_push(img, registry, name, version)

def set_image_tags(version):
    print("Setting image tags")
    for name in container_repo_map.keys():
        print("  - " + name)
        set_image_tag(name, version)

def publish_images(version):
    d = docker.client.from_env()
    print("Pushing release to docker hub")
    for name in container_repo_map.keys():
        img = d.images.get("{}/{}:{}".format(registry, name, version))
        tag_and_push(img, "vimc", name, version)

# NOTE: Using subprocess here and not the python docker module because
# the latter does not support streaming as nicely as the CLI
def tag_and_push(img, registry, name, tag):
    repo = "{}/{}".format(registry, name)
    img.tag(repo, tag)
    run(["docker", "push", "{}:{}".format(repo, tag)], check = True)

def get_past_submodule_versions(master_repo_version):
    return {k: get_past_submodule_version(k, master_repo_version)
            for k in os.listdir("submodules")}

if __name__ == "__main__":
    args = docopt.docopt(__doc__)
    version = args["<version>"]
    release_tag_pattern = re.compile(r"^v\d+\.\d+\.\d+(-RC\d)?$")
    if not release_tag_pattern.match(version):
        raise Exception("Invalid tag")
    if args["tag"]:
        set_image_tags(version)
        if args["--publish"]:
            publish_images(version)
    elif args["publish"]:
        publish_images(version)
