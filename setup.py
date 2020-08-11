"""
Django-RouteView
----------------
A RouteView class which register itself
"""

from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


from setuptools import setup

setup(
    name='django_routeview',
    version='1.0.0',
    url='https://github.com/TiphaineLAURENT/Django_RouteView',
    license='BSD',
    author='Tiphaine LAURENT',
    author_email='tip.lau@hotmail.fr',
    description='A RouteView class which register itself',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=['django_routeview'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'Django'
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    python_requires='>=3.6'
)
