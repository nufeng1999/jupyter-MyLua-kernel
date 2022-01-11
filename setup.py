#!/usr/bin/env python
# coding: utf-8
with open("README.md", "r") as f:
	long_description = f.read()
import setuptools
setuptools.setup(name='jupyter_MyLua_kernel',
      version='0.0.1',
      description='Minimalistic Lua kernel for Jupyter',
    long_description=long_description,
    long_description_content_type="text/markdown",
      author='nufeng',
      author_email='18478162@qq.com',
      license='MIT',
      url='https://github.com/nufeng1999/jupyter-MyLua-kernel/',
      download_url='https://github.com/nufeng1999/jupyter-MyLua-kernel/releases/tag/0.0.1',
    packages=setuptools.find_packages(),
	classifiers=[
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
	],
      scripts=['jupyter_MyLua_kernel/install_MyLua_kernel'],
      keywords=['jupyter', 'notebook', 'kernel', 'Lua','lua'],
      include_package_data=True
      )
