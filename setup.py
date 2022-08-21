from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in core_banking/__init__.py
from core_banking import __version__ as version

setup(
	name="core_banking",
	version=version,
	description="For all core banking modules in ERPNext. Initially to be used for Pension Schemes and any instioffering core banking features",
	author="Lonius Limited",
	author_email="info@lonius.co.ke",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
