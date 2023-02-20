import setuptools
import pkg_resources
import pathlib
import os
import re


def get_version(filename, pattern=None):
    """Extract the __version__ from a file without importing it.

    While you could get the __version__ by importing the module, the very act
    of importing can cause unintended consequences.  For example, Distribute's
    automatic 2to3 support will break.  Instead, this searches the file for a
    line that starts with __version__, and extract the version number by
    regular expression matching.

    By default, two or three dot-separated digits are recognized, but by
    passing a pattern parameter, you can recognize just about anything.  Use
    the `version` group name to specify the match group.

    :param filename: The name of the file to search.
    :type filename: string
    :param pattern: Optional alternative regular expression pattern to use.
    :type pattern: string
    :return: The version that was extracted.
    :rtype: string
    """
    if pattern is None:
        cre = re.compile(r'(?P<version>\d+\.\d+(?:\.\d+)?(?:(?:a|b|rc)\d+)?)')
    else:
        cre = re.compile(pattern)
    with open(filename) as fp:
        for line in fp:
            if line.startswith('__version__'):
                mo = cre.search(line)
                assert mo, 'No valid __version__ string found'
                return mo.group('version')
    raise AssertionError('No __version__ assignment found')


def get_main_module_name() -> str:
    """
    Extract the main module name by scraping in the project files. The main module is the directory which
    contains a Python file containing a line with the work '__main__' in it.
    :return: The name of the main module.
    """
    # noinspection PyTypeChecker
    def _scrape(dir_path: str):
        current = pathlib.Path(__file__)
        dir_path = pathlib.Path(dir_path)
        dirs = list()
        for name in os.listdir(dir_path):
            if name == 'venv' or name.startswith('.'):
                continue
            sub_path = dir_path.joinpath(name)
            if sub_path.is_dir():
                sub_items = os.listdir(sub_path)
                if any(['.ini' in n for n in sub_items]):
                    continue
                if '__init__.py' not in sub_items:
                    continue
                dirs += _scrape(sub_path)
            elif sub_path.is_file():
                if sub_path.name == 'setup.py':
                    continue
                if not sub_path.name.endswith('.py') or sub_path == current:
                    continue
                with sub_path.open() as f:
                    if '__main__' in f.read():
                        dirs.append(sub_path.parent)
        return dirs
    module_paths = _scrape(os.getcwd())
    if not module_paths:
        raise ModuleNotFoundError('Module name not found.')
    if len(module_paths) > 1:
        raise ModuleNotFoundError(f'Multiple main modules found: {[p.name for p in module_paths]}.')
    return module_paths[0].name


def setup(**kwargs):
    """
    Utility to setup a distribution. If no name is given, the setup process will try automatically extract the
    module name to setup from the project. Version is also extracted from a __version__ variable in the main module.
    If a README.md file exists in the project root, it's loaded and used as module long description.
    :param kwargs: (optional) Key value arguments of setuptools.
    """
    # Get module name
    name = kwargs.get('name') or get_main_module_name()
    # Get module path
    kwargs['name'] = name
    module_path_name = kwargs.get('module_path_name', name)
    module_path = pathlib.Path(os.path.basename(module_path_name))
    # Parse version
    for file_name in os.listdir(module_path):
        if file_name == '__init__.py':
            # noinspection PyTypeChecker
            kwargs['version'] = get_version(module_path.joinpath(file_name))
    # Parse requirements
    with pathlib.Path('requirements.txt').open() as requirements_txt:
        install_requires = [
            str(requirement) for requirement
            in pkg_resources.parse_requirements(requirements_txt)
        ]
    # Try to get README if no long description
    long_description = kwargs.get('long_description')
    if long_description is None:
        try:
            with open(pathlib.Path(__file__).parent / "README.md", encoding="utf8") as f:
                kwargs['long_description'] = f.read()
                kwargs['long_description_content_type'] = "text/markdown"
        except:
            pass
    # Get packages
    packages = setuptools.find_packages(exclude=["test", "doc", "docs", "venv"])
    # Setup
    setuptools.setup(
        packages=packages, include_package_data=True,
        install_requires=install_requires, **kwargs)
