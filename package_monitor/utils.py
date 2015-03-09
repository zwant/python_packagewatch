import re
import requests
from package_monitor import db, models
from pip._vendor.packaging.version import parse, Version, LegacyVersion
PYPI_URL_TEMPLATE = 'https://pypi.python.org/pypi/{0}/json'

def compare_package_versions(first, other):
    """ 
    Normal version-strings work fine:
    >>> compare_package_versions('1.5.0', '1.6.0')
    -1
    >>> compare_package_versions('1.6.0', '1.5.0')
    1

    pip version objects work:
    >>> compare_package_versions(Version('1.6.0'), Version('1.5.0'))
    1
    >>> compare_package_versions(LegacyVersion('1.6.0'), LegacyVersion('1.5.0'))
    1
    >>> compare_package_versions(Version('1.6.0b2'), Version('1.6.0b1'))
    1
    >>> compare_package_versions(Version('1.6.0b2'), Version('1.6.0b2'))
    0
    """
    return cmp(first, other)

def check_if_package_exists_on_pypi(package_name):
    print('Checking if package {0} exists on PyPI'.format(package_name))
    r = requests.head(PYPI_URL_TEMPLATE.format(package_name))
    return r.status_code == requests.codes.ok

def get_package_info_from_pypi(package_name):
    print('Getting package information for {0} from PyPI'.format(package_name))
    r = requests.get(PYPI_URL_TEMPLATE.format(package_name))
    if r.status_code == requests.codes.ok:
        data = r.json()['info']
        data['python3_compat'] = check_python3_compat(data)
        return data

    return None

def check_python3_compat(info):
    """
    >>> check_python3_compat({'classifiers': ['Programming Language :: Python :: 3']})
    True
    >>> check_python3_compat({})
    False
    >>> check_python3_compat({'classifiers': ['Programming Language :: Python :: 3', 'Programming Language :: Python :: 2']})
    True
    """
    if "classifiers" in info and "Programming Language :: Python :: 3" in info['classifiers']:
        return True
    return False

def parse_line_from_requirements(line):
    """ 
    Normal version specifiers work:
    >>> parse_line_from_requirements('Django==1.6.0')
    ('Django', <Version('1.6.0')>)
    >>> parse_line_from_requirements('Django>=1.6.0')
    ('Django', <Version('1.6.0')>)
    >>> parse_line_from_requirements('Django<=1.6.0')
    ('Django', <Version('1.6.0')>)

    Version or package versions with spaces around separators work:
    >>> parse_line_from_requirements(' Django <= 1.6.0')
    ('Django', <Version('1.6.0')>)

    Beta and pre-release version work:
    >>> parse_line_from_requirements('Django<=1.6.0b1')
    ('Django', <Version('1.6.0b1')>)
    >>> parse_line_from_requirements('html5lib==1.0b3')
    ('html5lib', <Version('1.0b3')>)

    >>> package,version = parse_line_from_requirements('html5lib==1.0b3')
    >>> print str(version)
    1.0b3
    >>> Version(str(version))
    <Version('1.0b3')>

    Invalid requirements-lines returns None:
    >>> parse_line_from_requirements('Django 1.6.0b1')
    (None, None)
    >>> parse_line_from_requirements('Django')
    (None, None)

    """
    split_result = re.split('[==|<=|>=]+', line)
    if len(split_result) != 2:
        return None, None
    package, version = split_result
    parsed_version = parse(version.strip())
    return package.strip(), parsed_version

def delete_package(user, package_name):
    package_to_delete = models.WatchedPackage.query \
           .join(models.User) \
           .filter(models.User.email == user) \
           .filter(models.WatchedPackage.package_name == package_name) \
           .first()
    if package_to_delete:
        db.session.delete(package_to_delete)
        db.session.commit()
    else:
        db.session.rollback()

def update_package_version(user, package_name, new_version):
    package = models.WatchedPackage.query \
                                   .join(models.User) \
                                   .filter(models.User.email == user) \
                                   .filter(models.WatchedPackage.package_name == package_name) \
                                   .first()
    if package:
        package.version = new_version
        db.session.commit()
    else:
        db.session.rollback()



def add_package(user, package_name, version):
    # Check that the package exists
    if check_if_package_exists_on_pypi(package_name):
        package = models.Package.query.filter_by(package_name=package_name).first()
        # New package that we have never seen before :)
        if not package:
            package_info = get_package_info_from_pypi(package_name)
            if package_info:
                package = models.Package.from_pypi_package_info(package_info)
                db.session.add(package)
        watched_package = models.WatchedPackage(package_name=package.package_name,
                                                version=version)
        if not watched_package in user.watched_packages:
            user.watched_packages.append(watched_package)
        db.session.commit()

        return True
    else:
        return None

