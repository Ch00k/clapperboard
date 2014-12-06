from setuptools import setup, find_packages

setup(
    name='clapperboard',
    version='0.0.1',
    author='Andriy Yurchuk',
    author_email='ayurchuk@minuteware.net',
    url='https://github.com/Ch00k/clapperboard',

    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'cb_manage = clapperboard.manager.manage:main'
        ]
    },
    install_requires=[
        'celery',
        'flask',
        'flask-cors',
        'flask-migrate',
        'flask-restful',
        'flask-sqlalchemy',
        'webargs',
        'requests',
        'pymysql',
        'xmltodict',
        'IMDbPY'
    ]
)
