from setuptools import find_packages, setup

setup(
    name='famished',
    version='1.0.3',
    packages=find_packages(where="src/fab"),
    package_dir={'':'src/fab'},
    author='Dylan Perry',
    author_email='dylan.perry@gmail.com',
    entry_points = {
        "console_scripts": [
            "masterless-enc=masterless.enc:cli"
        ],
    },
)
