import mwb
import setuptools


setuptools.setup(
    name='MIDL website builder',
    version=mwb.__version__,
    description='Tool for building static websites for the MIDL conference series',
    url='https://www.midl.io',
    license='Apache 2.0',
    author='Nikolas Lessmann',
    packages=['mwb'],
    install_requires=[
        'jinja2',
        'markdown',
        'pyscss',
        'pyyaml',
        'htmlmin'
    ]
)
