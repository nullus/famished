from setuptools import find_packages, setup

setup(
    name='fab',
    version='1.0.3',
    packages=find_packages(),
    author='Dylan Perry',
    author_email='dylan.perry@gmail.com',
    entry_points = {
        "console_scripts": [
            "masterless-enc=masterless.enc:cli"
        ],
    },
)
