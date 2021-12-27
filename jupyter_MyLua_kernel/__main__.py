from ipykernel.kernelapp import IPKernelApp
from .kernel import MyLuaKernel
IPKernelApp.launch_instance(kernel_class=MyLuaKernel)
