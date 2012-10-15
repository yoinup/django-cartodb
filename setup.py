# coding=utf-8

from distutils.core import setup

setup(
    name='django-cartodb',
    version='0.1',
    package_dir={
        '': 'django_cartodb',
        'lib': 'django_cartodb/lib'},
    requires=[
        'django>=1.4',
        'cartodb-python>=0.6'],
    packages=['django_cartodb'],
    author='Javier Cordero',
    author_email='jcorderomartinez@gmail.com'
)
