from setuptools import setup

setup(name='jupyter_MyLua_kernel',
      version='0.0.1',
      description='Minimalistic Lua kernel for Jupyter',
      author='nufeng',
      author_email='18478162@qq.com',
      license='MIT',
      classifiers=[
          'License :: OSI Approved :: MIT License',
      ],
      url='https://github.com/nufeng1999/jupyter-MyLua-kernel/',
      download_url='https://github.com/nufeng1999/jupyter-MyLua-kernel/tarball/0.0.1',
      packages=['jupyter_MyLua_kernel'],
      scripts=['jupyter_MyLua_kernel/install_MyLua_kernel'],
      keywords=['jupyter', 'notebook', 'kernel', 'Lua','lua'],
      include_package_data=True
      )
