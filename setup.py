"""Setup file for build and dev install."""
from setuptools import setup, find_packages

setup(name='gear_range_calc',
      description='Create a streamlit frontend on localhost to try some gearing ranges.',
      zip_save=True,
      author='Mike Winkelmann',
      license='MIT',
      install_requires=['pandas',
                        'plotly',
                        'streamlit',],
      version='0.1.0',
      packages=find_packages(),
      entry_points={
          "console_scripts": [
              "run_gearrange_frontend = gear_range_calc.run_frontend:run_app",
          ]
      }
)