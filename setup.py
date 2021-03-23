import setuptools
import os

with open("README-package.md", "r") as fh:
    long_description = fh.read()

def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()

def get_version(rel_path):
    for line in read(rel_path).split('\n'):
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1].strip()
    else:
        raise RuntimeError("Unable to find version string.")


setuptools.setup(
    name="fstk",
    version=get_version('fstk/__init__.py'),
    author="Meow",
    description="Fast Switch Time Keeper",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    package_data = {
        '': ['assets/*'],
    },

    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
    ],
    install_requires=[
        'PySide2>=5.10',
        'requests>=2'
    ],
    extras_require = {
        ':python_version < "3.8.5"': [
            'importlib_resources',
        ],
    },
    python_requires='>=3',
)

