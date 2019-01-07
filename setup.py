from setuptools import setup

setup(
    name='bwapi',
    version='3.3.0',
    description='A software development kit for the Brandwatch API',
    url='https://github.com/BrandwatchLtd/api_sdk',
    author='Amy Barker, Jamie Lebovics, Paul Siegel and Jessica Bowden',
    author_email=
    'amyb@brandwatch.com, paul@brandwatch.com, jess@brandwatch.com',
    license='License :: OSI Approved :: MIT License',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
    ],
    py_modules=['bwproject', 'bwresources', 'bwdata', 'filters'],
    scripts=['authenticate.py'],
    install_requires=['requests'],
    tests_require=['responses'])
