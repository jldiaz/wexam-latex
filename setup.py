import setuptools

setuptools.setup(
    name="examtool",
    version="0.1.0",
    url="None",

    author="JL Diaz",
    author_email="jldiaz@uniovi.es",

    description="Herramienta para crear examenes a partir de markdown/yaml",
    long_description=open('README.rst').read(),

    packages=setuptools.find_packages(),

    package_data={'': ['extra_files/*', 'templates/*']},

    install_requires=[
        'ruamel.yaml',
        'click',
        'pypandoc',
        'jinja2',
        'simhash',
        ],

    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
    ],
)
