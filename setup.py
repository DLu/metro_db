from setuptools import setup, find_packages

from metro_db import __version__

extra_test = [
    'pytest>=4',
    'pytest-cov>=2',
]

setup(
    name='metro_db',
    version=__version__,
    url='https://github.com/DLu/metro_db',
    author='David V. Lu!!',
    author_email='davidvlu@gmail.com',
    packages=find_packages(),
    install_requires=[
        'tabulate',
    ],
    entry_points={
        'console_scripts': [
            'metro_db=metro_db.peek:main',
        ],
    },
    extras_require={
        'dev': extra_test,
    },
)
