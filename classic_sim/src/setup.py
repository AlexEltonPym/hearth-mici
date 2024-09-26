from setuptools import setup
from Cython.Build import cythonize

setup(
  name='classic sim',
  ext_modules=cythonize("*.py", annotate=True),
  zip_safe = False
)