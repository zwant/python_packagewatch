import re
import requests

PYPI_URL_TEMPLATE = 'https://pypi.python.org/pypi/{0}/json'
requirements_parsing_regexp = re.compile(r'([^\<\=\>\s]*)\s?[\<\=\>]{1,2}\s?([0-9\.]*)')

def cmp(a, b):
    return (a > b) - (a < b)

def compare_package_versions(first, other):
    def normalize(v):
        return [int(x) for x in re.sub(r'(\.0+)*$','', v).split(".")]
    return cmp(normalize(first), normalize(other))

def check_if_package_exists_on_pypi(package_name):
    print('Checking if package {0} exists on PyPI'.format(package_name))
    r = requests.head(PYPI_URL_TEMPLATE.format(package_name))
    return r.status_code == requests.codes.ok

def get_package_info_from_pypi(package_name):
    print('Getting package information for {0} from PyPI'.format(package_name))
    r = requests.get(PYPI_URL_TEMPLATE.format(package_name))
    if r.status_code == requests.codes.ok:
        return r.json()['info']

    return None

def parse_line_from_requirements(line):
    matching = requirements_parsing_regexp.match(line)
    if matching:
        return (matching.group(1), matching.group(2))
    return None
