from subprocess import run

import os
import os.path
import paths

import versions
from docker_helpers import docker_cp
from service import orderly_name, orderly_volume_name

from settings import get_secret, save_secret
from service import orderly_volume_name

from database import VaultPassword

orderly_ssh_keypath = ""

def configure_orderly(initialise_volume, settings):
    ## Run this one first because we might need to use the ssh keys to
    ## clone:
    configure_orderly_ssh(settings)
    ## Then this requires an empty directory:
    if initialise_volume and settings["initial_data_source"] != "restore":
        print("Setting up orderly store")
        initialise_orderly_store(settings)
    ## Then set up some passwords
    configure_orderly_envir(settings)
    ## And we're off
    print("Sending orderly go signal")
    args = ["docker", "exec", orderly_name, "touch", "/orderly_go"]
    run(args)

def configure_orderly_envir(settings):
    envir = orderly_prepare_envir(settings['password_group'])
    docker_cp(envir, orderly_name, "/orderly")

def initialise_orderly_store(settings):
    if settings['clone_reports']:
        print("creating orderly store by cloning montagu-reports")
        cmd = ["git", "clone", "git@github.com:vimc/montagu-reports.git",
               "/orderly"]
    else:
        print("creating empty orderly store")
        cmd = ["/usr/bin/orderly_init", "/orderly"]
    run(["docker", "exec", orderly_name] + cmd, check = True)

def configure_orderly_ssh(settings):
    needs_ssh = settings['clone_reports'] or \
                settings['initial_data_source'] == 'restore'
    if not needs_ssh:
        return
    ssh = paths.orderly + "/.ssh"
    if not os.path.exists(ssh):
        print("preparing orderly ssh")
        os.makedirs(ssh)
        save_secret("vimc-robot/id_rsa.pub", ssh + "/id_rsa.pub")
        save_secret("vimc-robot/id_rsa", ssh + "/id_rsa")
        os.chmod(ssh + "/id_rsa", 0o600)
        with open(ssh + "/known_hosts", 'w') as output:
            run(["ssh-keyscan", "github.com"], stdout = output, check = True)
    docker_cp(ssh, orderly_name, "/root/.ssh")

def orderly_prepare_envir(password_group):
    print("preparing orderly configuration")
    dest = paths.orderly + "/orderly_envir.yml"
    user = "orderly"
    password = VaultPassword(password_group, user).get()
    envir = [
        "MONTAGU_PASSWORD: {password}".format(password = password),
        "MONTAGU_HOST: db",
        "MONTAGU_PORT: 5432",
        "MONTAGU_USER: {user}".format(user = user)]
    if not os.path.exists(paths.orderly):
        os.makedirs(paths.orderly)
    with open(dest, 'w') as output:
        for e in envir:
            output.write(e + '\n')
    return dest
