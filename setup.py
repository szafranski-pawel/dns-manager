from setuptools import find_packages, setup

setup(
    name='dns_manager',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Flask==2.2.2',
        'Flask-Login==0.6.2',
        'SQLAlchemy==1.4.46',
        'Flask-SQLAlchemy==3.0.2',
        'WTForms==3.0.1',
        'Flask-WTF==1.0.1',
        'dnspython',
        'email-validator==1.3.0',
        'blinker==1.5',
        'pydantic==1.10.4',
        'Flask-Pydantic==0.11.0'
    ],
)