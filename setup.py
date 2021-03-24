from distutils.core import setup

#  Generate requirement list from requirements.txt file
req = []
with open('requirements.txt', 'r') as fid:
    req = [line for line in fid if not line.strip().startswith('#')]

# Call setup command to make installable by pip install .
setup(name='cth_mts_biax',
      version='0.1',
      description='',
      author='',
      author_email='',
      url='',
      packages=['cth_mts_biax'],
      install_requires=req
     )
