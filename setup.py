from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='resch',
    version='0.1.1',
    description='Static Scheduling for FPGA-based Accelerators',
    long_description=readme,
    author='Pascal Jungblut',
    author_email='pascal.jungblut@nm.ifi.lmu.de',
    url='https://github.com/pascalj/resch',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)
