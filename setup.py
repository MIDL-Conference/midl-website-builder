from setuptools import setup


setup(
    name='MIDL website builder',
    version='0.1',
    description='Tool for building static websites for the MIDL conference series',
    url='https://midl.io',
    license='CC-BY-SA-4.0',
    author='Nikolas Lessmann',
    packages=['mwb'],
    install_requires=[
        'jinja2',
        'markdown',
        'pyscss',
        'pyyaml'
    ]
)
