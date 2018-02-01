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
orderly = get_submodule_version("orderly")
shiny = get_submodule_version("shiny")

api = get_submodule_version("api")
reporting_api = get_submodule_version("reporting-api")

contrib_portal = get_submodule_version("contrib-portal")
admin_portal = get_submodule_version("admin-portal")
report_portal = get_submodule_version("report-portal")

proxy = get_submodule_version("proxy")
cert_tool = get_submodule_version("cert-tool")


def as_dict():
    return {
        'db': db,
        'orderly': orderly,
        'shiny': shiny,
        'api': api,
        'reporting_api': api,
        'contrib_portal': contrib_portal,
        'admin_portal': admin_portal,
        'report_portal': report_portal,
        'proxy': proxy,
        'cert_tool': cert_tool
    }
