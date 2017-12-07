from subprocess import Popen
from docker_helpers import montagu_registry

import versions


def start(port, hostname, use_fake_db_annex, project_name):
    run("up -d", port, hostname, use_fake_db_annex, project_name)


def stop(port, hostname, persist_volumes, use_fake_db_annex, project_name):
    command = "down" if persist_volumes else "down --volumes"
    run(command, port, hostname, use_fake_db_annex, project_name)


def pull(port, hostname, project_name):
    # NOTE: passing use_fake_db_annex = False here because it does not
    # affect the pull (the fake db annex uses the main montagu-db
    # container)
    run("pull", port, hostname, False, project_name)


def run(args, port, hostname, use_fake_db_annex, project_name):
    prefix = 'docker-compose --project-name {} '.format(project_name)
    if use_fake_db_annex:
        # NOTE: it's surprising that the '../' is needed here, but
        # docker-compose apparently looks like git through parent
        # directories until it finds a docker-compose file!
        prefix += '-f ../docker-compose.yml -f ../docker-compose-annex.yml '
    cmd = prefix + args
    p = Popen(cmd, env=get_env(port, hostname), shell=True)
    p.wait()
    if p.returncode != 0:
        raise Exception("An error occurred: docker-compose returned {}".format(p.returncode))


def get_env(port, hostname):
    return {
        'MONTAGU_REGISTRY': montagu_registry,

        'MONTAGU_PORT': str(port),
        'MONTAGU_HOSTNAME': hostname,

        'MONTAGU_API_VERSION': versions.api,
        'MONTAGU_REPORTING_API_VERSION': versions.reporting_api,
        'MONTAGU_DB_VERSION': versions.db,

        'MONTAGU_CONTRIB_PORTAL_VERSION': versions.contrib_portal,
        'MONTAGU_ADMIN_PORTAL_VERSION': versions.admin_portal,
        'MONTAGU_REPORT_PORTAL_VERSION': versions.report_portal,

        'MONTAGU_PROXY_VERSION': versions.proxy,

        'MONTAGU_ORDERLY_VERSION': versions.orderly
    }
