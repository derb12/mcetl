#!/usr/bin/env python

"""The setup script."""


from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    long_description = readme_file.read()

requirements = [
    'lmfit',
    'matplotlib>=3.1',
    'numpy',
    'openpyxl',
    'pandas',
    'pysimplegui>=4.19',
    'scipy',
    'sympy',
]

setup_requirements = [
    #'pytest-runner',
]

test_requirements = [
    #'pytest>=3',
]

setup(
    author="Donald Erb",
    author_email='donnie.erb@gmail.com',
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Scientific/Engineering :: Chemistry',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Scientific/Engineering :: Physics',
        'Topic :: Scientific/Engineering :: Visualization'
    ],
    description="A simple Extract-Transform-Load framework focused on materials characterization.",
    install_requires=requirements,
    extras_require={
        'docs': [
            'sphinx',
            'sphinx-rtd-theme',
            'sphinx-autoapi'
        ]
    },
    license="BSD 3-clause",
    long_description=long_description,
    long_description_content_type='text/x-rst',
    include_package_data=True,
    keywords=['materials characterization', 'materials science', 'materials engineering'],
    name='mcetl',
    packages=find_packages(include=['mcetl', 'mcetl.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/derb12/mcetl',
    version='0.2.0',
    zip_safe=False,
)
