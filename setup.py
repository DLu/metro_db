from setuptools import setup, find_packages

extra_test = [
    'pytest>=4',
    'pytest-cov>=2',
]

setup(
    name='metro_db',
    description='A wrapper around the sqlite3 database for easy database development',
    version='v0.3.0',
    url='https://github.com/DLu/metro_db',
    author='David V. Lu!!',
    author_email='davidvlu@gmail.com',
    packages=find_packages(),
    install_requires=[
        'pyyaml',
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
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Topic :: Database',
    ],
)
