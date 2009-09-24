from setuptools import setup, find_packages
 
setup(
    name='django-member-academic',
    version='0.1.0',
    description='Member academic',
    author='Hisham Zarka',
    author_email='hzarka@gmail.com',
    url='http://github.com/hzarka/django-member-academic/',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    zip_safe=False,
)
