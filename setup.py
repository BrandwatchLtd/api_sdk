from setuptools import setup

setup(
    name='bwapi',

    version='1.1.0',

    description='A software development kit for the Brandwatch API',

    url='https://github.com/BrandwatchLtd/api_sdk',

    author='Amy Barker, Jamie Lebovics, and Paul Siegel',
    author_email='amyb@brandwatch.com, paul@brandwatch.com',

    license='License :: OSI Approved :: MIT License',

    classifiers=[

        'Development Status :: 5 - Production/Stable',

        'Intended Audience :: Developers',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5'
    ],

    py_modules=['bwproject', 'bwresources', 'bwdata', 'filters'],

    install_requires=['requests']

)
