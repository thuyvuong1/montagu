import re
from os.path import join
from pathlib import Path
from subprocess import run, PIPE

montagu_root = str(Path(__file__).parent.parent)

def get_submodule_version(path):
    full_path = join(montagu_root, "submodules", path)
    result = run(["git", "-C", full_path, "rev-parse", "--short=7", "HEAD"],
                 stdout=PIPE, check=True, universal_newlines=True)
    return result.stdout.strip()


db = get_submodule_version("db")

api = get_submodule_version("api")

contrib_portal = get_submodule_version("contrib-portal")
admin_portal = get_submodule_version("admin-portal")

proxy = get_submodule_version("proxy")
cert_tool = get_submodule_version("cert-tool")

static = get_submodule_version("static")

task_queue = get_submodule_version("task-queue")

def as_dict():
    submodules = [
        'db', 'api', 'contrib-portal', 'admin-portal',
        'proxy', 'cert-tool', 'task-queue'
    ]
    return dict((k, get_submodule_version(k)) for k in submodules)
