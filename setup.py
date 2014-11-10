from setuptools import setup, find_packages

setup(
      name = 'clapperboard',
      version = '0.0.1',
      author = 'Andriy Yurchuk',
      author_email = 'ayurchuk@minuteware.net',
      url = 'https://github.com/Ch00k/clapperboard',

      packages = find_packages(),
      entry_points={'console_scripts': ['cb_workers = clapperboard.workers:main']},
      install_requires = [
          'flask',
          'flask-restful',
          'flask-sqlalchemy',
          'MySQL-python',
          'xmltodict',
          'apscheduler',
          'IMDbPY'
      ]
)