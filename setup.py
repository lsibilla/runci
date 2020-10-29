from setuptools import setup

setup(
    name='runci',
    version='0.0.1',
    description="Vendor agnostic build automation tool for supporting pipelines as code, mainly focusing on docker and docker-compose tasks.",
    long_description="../README.md",
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
