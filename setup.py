from distutils.core import setup

setup(
    name="updatechangelog",
    include_package_data=True,
    package_data={"updatechangelog": ["templates/*"]},
    install_requires=["jinja2", "py", "gitpython", "pytz"],
    version="0.1",
    packages=["updatechangelog"],
    license="MIT",
    scripts=["update_changelog"],
    description="OBS service to update changelog",
)
