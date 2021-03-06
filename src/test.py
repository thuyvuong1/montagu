#!/usr/bin/env python3

"""
Run integration tests on a deployed Montagu instance

Usage:
  test.py --run-tests [--simulate-restart]

Options:
  --run-tests         Required. This is included to prevent accidentally
                      running the tests in a live environment.
  --simulate-restart  Restart the Docker daemon before running the tests,
                      to simulate recovery from a system reboot.
"""

from subprocess import run
from docopt import docopt

import sys
import os
import celery
import requests

import versions
from docker_helpers import get_image_name, pull


def run_in_teamcity_block(name, work):
    print("##teamcity[blockOpened name='{name}']".format(name=name))
    try:
        work()
    finally:
        print("##teamcity[blockClosed name='{name}']".format(name=name))


def api_blackbox_tests():
    def work():
        image = get_image_name("montagu-api-blackbox-tests", versions.api)
        pull(image)
        run([
            "docker", "run",
            "--rm",
            "--network", "montagu_default",
            "-v", "montagu_emails:/tmp/montagu_emails",
            image
        ], check=True)

    run_in_teamcity_block("api_blackbox_tests", work)


def webapp_integration_tests():
    def run_suite(portal, version):
        image = "vimc/montagu-portal-integration-tests:{version}".format(
            version=version)
        pull(image)
        run([
            "docker", "run",
            "--rm",
            "--network", "montagu_default",
            "-v",
            "/opt/teamcity-agent/.docker/config.json:/root/.docker/config.json",
            "-v", "/var/run/docker.sock:/var/run/docker.sock",
            image,
            portal.title()
            # Tests expect capitalized first letter, e.g. "Admin"
        ], check=True)

    def work():
        run_suite("admin", versions.admin_portal)
        run_suite("contrib", versions.contrib_portal)

    run_in_teamcity_block("webapp_integration_tests", work)


def task_queue_integration_tests():
    def work():
        print("Running task queue integration tests")
        app = celery.Celery(broker="pyamqp://guest@localhost//",
                            backend="rpc://")
        sig = "run-diagnostic-reports"
        args = ["testGroup", "testDisease", "testTouchstone"]
        signature = app.signature(sig, args)
        versions = signature.delay().get()
        assert len(versions) == 1
        # check expected notification email was sent to fake smtp server
        emails = requests.get("http://localhost:1080/api/emails").json()
        assert len(emails) == 1
        s = "VIMC diagnostic report: testTouchstone - testGroup - testDisease"
        assert emails[0]["subject"] == s
        assert emails[0]["to"]["value"][0][
                   "address"] == "minimal_modeller@example.com"

    run_in_teamcity_block("task_queue_integration_tests", work)


def start_orderly_web():
    def add_user(email, image):
        run([
            "docker", "run", "-v", "orderly_volume:/orderly", image,
            "add-users", email
        ], check=True)

    def grant_permissions(email, image, permissions):
        run(["docker", "run", "-v", "orderly_volume:/orderly",
             image, "grant", email] + permissions, check=True)

    def work():
        cwd = os.getcwd()

        run(["docker", "volume", "create", "orderly_volume"], check=True)

        orderly_image = get_image_name("orderly.server", "master")
        pull(orderly_image)
        run([
            "docker", "run", "-d",
            "-p", "8321:8321",
            "--network", "montagu_default",
            "-v", "orderly_volume:/orderly",
            "-w", "/orderly",
            "--name", "montagu_orderly_orderly_1",
            orderly_image,
            "--port", "8321", "--go-signal", "/go_signal", "/orderly"
        ], check=True)

        run(["docker", "exec", "montagu_orderly_orderly_1", "Rscript", "-e",
             "orderly:::create_orderly_demo('/orderly')"], check=True)

        run(["docker", "exec", "montagu_orderly_orderly_1", "orderly",
             "rebuild", "--if-schema-changed"], check=True)

        run(["docker", "exec", "montagu_orderly_orderly_1", "touch",
             "/go_signal"],
            check=True)

        ow_image = get_image_name("orderly-web", "master")
        pull(ow_image)
        run([
            "docker", "run", "-d",
            "-p", "8888:8888",
            "--network", "montagu_default",
            "-v", "orderly_volume:/orderly",
            "-v", cwd + "/container_config/orderlyweb:/etc/orderly/web",
            "--name", "montagu_orderly_web_1",
            ow_image
        ], check=True)

        run(["docker", "exec", "montagu_orderly_web_1", "touch",
             "/etc/orderly/web/go_signal"],
            check=True)

        ow_migrate_image = get_image_name("orderlyweb-migrate", "master")
        pull(ow_migrate_image)
        run([
            "docker", "run", "--rm",
            "-v", "orderly_volume:/orderly",
            ow_migrate_image
        ], check=True)

        ow_cli_image = get_image_name("orderly-web-user-cli", "master")
        pull(ow_cli_image)

        # user for api blackbox tests
        add_user("user@test.com", ow_cli_image)
        grant_permissions("user@test.com", ow_cli_image, ["*/users.manage"])

        # add task q user
        add_user("montagu-task@imperial.ac.uk", ow_cli_image)
        grant_permissions("montagu-task@imperial.ac.uk", ow_cli_image,
                          ["*/reports.run", "*/reports.review", "*/reports.read"])

        # user for webapp tests
        add_user("test.user@example.com", ow_cli_image)
        grant_permissions("test.user@example.com", ow_cli_image, ["*/users.manage"])


    run_in_teamcity_block("start_orderly_web", work)


if __name__ == "__main__":
    args = docopt(__doc__)
    if args["--run-tests"]:
        if args["--simulate-restart"]:
            # Imitate a reboot of the system
            print("Restarting Docker", flush=True)
            run(["sudo", "/bin/systemctl", "restart", "docker"], check=True)
        start_orderly_web()
        api_blackbox_tests()
        webapp_integration_tests()
        task_queue_integration_tests()
    else:
        print(
            "Warning - these tests should not be run in a real environment. They will destroy or change data.")
        print("To run the tests, run ./tests.py --run-tests")
        exit(-1)
