import codecs
import setuptools

from version import __version__ as version


install_requires = [
    'datadog >=0.20,<0.21"',
    'apache-log-parser >=1.6,<2.0'
]

tests_require = [
    'pytest>=3.1.0',  # Pinned for the ``pytest.param`` method
]

extras_require = {
    'test': tests_require
}


def long_description():
    with codecs.open('README.md', encoding='utf8') as f:
        return f.read()


setuptools.setup(
    name='rtv',
    version=version,
    description='A local HTTP log monitoring tool',
    long_description=long_description(),
    url='https://github.com/michael-lazar/Akita',
    author='Michael Lazar',
    author_email='lazar.michael22@gmail.com',
    license='MIT',
    keywords='http log monitoring terminal console metrics',
    packages=['akita'],
    install_requires=install_requires,
    test_requires=tests_require,
    extras_require=extras_require,
    entry_points={'console_scripts': ['akita=akita.__main__:main']},
    classifiers=[
        'Intended Audience :: End Users/Desktop',
        'Environment :: Console :: Curses',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Terminals',
        'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
        ],
)
