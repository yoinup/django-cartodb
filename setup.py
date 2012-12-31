# coding=utf-8

from setuptools import setup, find_packages

setup(
    name='django-cartodb',
    version='0.1',
    install_requires=[
        'django>=1.4',
        'cartodb-python>=0.6'],
    url='https://github.com/yoinup/django-cartodb',
    packages=find_packages(),
    include_package_data=True,
    license='BSD License',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ],
    author='Javier Cordero',
    author_email='jcorderomartinez@gmail.com'
)
