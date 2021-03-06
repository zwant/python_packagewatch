from setuptools import setup

setup(
    name='PyPI Package Watch',
    version='1.0',
    long_description=__doc__,
    packages=['package_monitor'],
    include_package_data=True,
    zip_safe=False,
    install_requires=['flask',
                      'Flask-WTF',
                      'requests',
                      'psycopg2',
                      'SQLAlchemy',
                      'Flask-SQLAlchemy',
                      'pytz']
)