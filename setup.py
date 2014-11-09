from setuptools import setup

setup(
      name = 'clapperboard',
      author = 'Andriy Yurchuk',
      author_email = 'ayurchuk@minuteware.net',
      url = 'https://github.com/Ch00k/clapperboard',

      packages = ['clapperboard'],
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