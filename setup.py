from setuptools import setup

setup(
    name='runci',
    version='0.0.1',
    description="vendor-agnostic tool for supporting container based CI/CD pipelines.",
    long_description="./README.md",
    long_description_content_type="text/markdown",
    url="https://github.com/lsibilla/runci",
    author="Laurent Sibilla",
    author_email="laurent@sibilla.be",
    license="GPLv3",
    py_modules=["runci"],
    include_package_data=True,
    install_requires=[
        'click',
        'pyyaml'
    ],
    entry_points={
        'console_scripts': ['runci=runci.cli.main:main'],
    },
)
