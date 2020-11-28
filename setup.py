"""
Django-ModelAPIView
----------------
An APIView class which handles endpoints associated with its model
"""

from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


from setuptools import setup

setup(
    name='django_modelapiview',
    version='1.4.13',
    url='https://github.com/TiphaineLAURENT/Django_APIView',
    license='BSD',
    author='Tiphaine LAURENT',
    author_email='tip.lau@hotmail.fr',
    description='Two view classes to handle API endpoints',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=['django_modelapiview'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'Django>=3.1',
    	'django_routeview>=1.1.0'
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
    python_requires='>=3.9'
)
