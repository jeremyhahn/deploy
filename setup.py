from setuptools import setup

setup(
    name='deploy',
    version='0.1',
    scripts=['deploy'],
    install_requires=[
        'click',
        'boto3',
        'json',
        'requests',
        'time'
    ]
)
