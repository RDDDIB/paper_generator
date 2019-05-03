from setuptools import setup


def readme():
    with open('README.rst') as reader:
        return reader.read()


setup(name='paper_generator',
      version='0.2.1',
      description='A wrapper for pylatex.',
      long_description=readme(),
      url='',
      author='Roland Baumann',
      author_email='r.dddib.b@gmail.com',
      license='',
      keywords='latex pylatex pdf generator',
      packages=['paper_generator'],
      extras_require={
          'numpy': ["numpy"],
          'pandas': ["pandas"],
          'date': ["dateparser"],
      },
      install_requires=[
          'pylatex',
      ],
      include_package_data=True,
      zip_safe=False)
