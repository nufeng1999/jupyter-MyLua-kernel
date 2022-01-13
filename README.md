![](https://img.shields.io/badge/Jupyter-Kernel-green?link=https://jupyter.org/&link=https://github.com/jupyter/jupyter/wiki/Jupyter-kernels) ![](https://img.shields.io/badge/MyLua-Kernel-orange) ![](https://img.shields.io/github/watchers/nufeng1999/jupyter-MyLua-kernel) <img alt="ViewCount" src="https://views.whatilearened.today/views/github/nufeng1999/jupyter-MyLua-kernel.svg">
    <a href="https://github.com/nufeng1999/jupyter-MyLua-kernel"><img alt="GitHub Clones" src="https://img.shields.io/badge/dynamic/json?color=success&label=Clone&query=count&url=https://raw.githubusercontent.com/nufeng1999/jupyter-MyLua-kernel/master/clone.json&logo=github"></a>
# MyLua kernel for Jupyter  
[Example](https://github.com/nufeng1999/jupyter-MyLua-kernel/blob/master/example/MyLua.ipynb "Example")
* Make sure you have the following requirements installed:
  * Lua
  * jupyter
  * zerorpc
  * python 3
  * pip
### Step-by-step
```bash
git clone https://github.com/nufeng1999/jupyter-MyLua-kernel.git
cd jupyter-MyLua-kernel
pip install -e . 
cd jupyter_MyLua_kernel && python3 install_MyLua_kernel --user
# now you can start the notebook
jupyter notebook
```
This is a very simplified exploration and development work, which is suitable for beginners and experts, especially for the development of computer system maintenance code.  
My minification kelnel of jupyter
|                   |                 |
| :--------------------------------------------------------------------- | :--------------------------------------------------------------------- |
|[MyBash](https://github.com/nufeng1999/jupyter-MyBash-kernel)           |[MyC](https://github.com/nufeng1999/jupyter-MyC-kernel)                 |
|[MyDart](https://github.com/nufeng1999/jupyter-MyDart-kernel)           |[MyGjs](https://github.com/nufeng1999/jupyter-MyGjs-kernel)             |
|[MyGo](https://github.com/nufeng1999/jupyter-MyGo-kernel)               |[MyGroovy](https://github.com/nufeng1999/jupyter-MyGroovy-kernel)       |
|[MyJava](https://github.com/nufeng1999/jupyter-MyJava-kernel)           |[MyKotlin](https://github.com/nufeng1999/jupyter-MyKotlin-kernel)       |
|[MyNodejs](https://github.com/nufeng1999/jupyter-MyNodejs-kernel)       |[MyPython](https://github.com/nufeng1999/jupyter-MyPython-kernel)       |
|[MyVala](https://github.com/nufeng1999/jupyter-MyVala-kernel)           |[MyVBScript](https://github.com/nufeng1999/jupyter-MyVBScript-kernel)   |
|[MyWolframScript](https://github.com/nufeng1999/jupyter-MyWLS-kernel)   |[MyHtml](https://github.com/nufeng1999/jupyter-MyHtml-kernel)           |  
|[MyTypeScript](https://github.com/nufeng1999/jupyter-MyTypeScript-kernel)|[MyPowerShell](https://github.com/nufeng1999/jupyter-MyPS-kernel)      |
|[MyBatch](https://github.com/nufeng1999/jupyter-MyBatch-kernel)         |[MyLua](https://github.com/nufeng1999/jupyter-MyLua-kernel)             |
|[MyPerl](https://github.com/nufeng1999/jupyter-MyPerl-kernel)           |[MyLua](https://github.com/nufeng1999/jupyter-MySwift-kernel)           |
|[MyPHP](https://github.com/nufeng1999/jupyter-MyPHP-kernel)             |[MyR](https://github.com/nufeng1999/jupyter-MyR-kernel)                 |
|[MyMake](https://github.com/nufeng1999/jupyter-MyMake-kernel)           |[MyRust](https://github.com/nufeng1999/jupyter-MyRust-kernel)           |
|[MyRuby](https://github.com/nufeng1999/jupyter-MyRuby-kernel)           |[MyTcl](https://github.com/nufeng1999/jupyter-MyTcl-kernel)             |
|[MyVimscript](https://github.com/nufeng1999/jupyter-MyVimscript-kernel) |[MyM4](https://github.com/nufeng1999/jupyter-MyM4-kernel)               |
|[MyDot](https://github.com/nufeng1999/jupyter-MyDot-kernel)             |                                                                    |
----  
### Support label  
#### Label  
Label prefix is `##%` or `//%`  
Example1:   
`##%overwritefile`  
`##%file:../src/do_execute.c`  
`##%noruncode`  
Example2:   
`##%runprg:ls`  
`##%runprgargs:-al`  
Example3:   
`##//%outputtype:text/html`  
`##%runprg:bash`   
`##%runprgargs:test.sh`  
`##%overwritefile`  
`##%file:test.sh`  
`echo "shell cmd test"`   
`ls`   
----  
#### Compile and run code
| label       |   value    | annotation                                                                                                       |
| :---------- | :--------: | :--------------------------------------------------------------------------------------------------------------- |
| cflags:     |            | Specifies the compilation parameters for C language compilation                                                  |
| ldflags:    |            | Specify the link parameters for C language connection                                                            |
| args:       |            | Specifies the parameters for the code file runtime                                                               |
| switches    |            | Specifies the parameters for Swiftc                                                                              |
| options     |            | Specifies the parameters for Perl,Lua                                                                            |
| coptions:   |            | Code compilation time parameters of JVM platform                                                                 |
| joptions:   |            | Code runtime parameters for the JVM platform                                                                     |
| runprg:     |            | The code content will be run by the execution file specified by runprg                                           |
| runprgargs: |            | runprg Parameters of the specified executable ,You can put the name specified by file into the parameter string. |
| outputtype: | text/plain | mime-type                                                                                                        |
| outencode:  | UTF-8      | set stdout encode                                                                                                |
| runinterm   |            | Run the code in the terminal                                                                                     |
| term:       |gnome-terminal| linux:gnome-terminal windows:c:\Windows\\System32\cmd.exe /c start                                             |
| cwd :       |            | The working directory in which the program runs                                                                  |
| cleartest   |            | clear test code                                                                                                  |
---
#### Interactive running code
| label         | value  | annotation                                                                                  |
| :------------ | :----: | :------------------------------------------------------------------------------------------ |
| runmode:      |  repl  | The code will run in interactive mode.                                                      |
| replcmdmode   |        | (repl interactive mode) to send stdin information to the specified process (repl child PID) |
| replsetip:    | "\r\n" | Set (repl interactive mode) the prompt string when waiting for input                        |
| replchildpid: |        | (repl interactive mode) specifies the running process number                                |
| repllistpid   |        | Lists the interactive process PIDs that are running                                         |
---
#### Interactive running GDB
| label  | value | annotation                                               |
| :----- | :---: | :------------------------------------------------------- |
| rungdb |       | Run GDB and send commands to GDB (repl interactive mode) |
---
#### Save code and include file
| label         | value | annotation                                               |
| :------------ | :---: | :---------------------------------------------------     |
| noruncode     |       | Do not run code content                                  |
| overwritefile |       | Overwrite existing files                                 |
| fileencode:   | UTF-8 | code file encode                                         |
| file:         |       | The code can be saved to multiple files                  |
| fndict:       |       | Dictionary for file names                                |
| filefordict:  |       | Replace $key of fndict with a string from the fndict when save file |
| fnlist:       |       | List for file names                                      |
| fileforlist:  |       | Replace $fnlist with a string from the list  when save file |
| include:      |       | Places the specified file contents in the label location |
---
#### Templates and testing
| label                                                                                                                                          |
| :--------------------------------------------------------------------------------------------------------------------------------------------- |
| Define a macro                                                                                                                                 |
| define:Define a macro，The content is jinja2 template. example:`##%define:M1 this is {{name}}`                                                 |
| &emsp; `##$Macroname` or `//$Macroname` Replace with macro                                                                                     |
| &emsp; `##$M1 name='jinja2 content'` This line will be replaced by this is jinja2 content                                                      |
| templatefile:                                                                                                                                  |
| Define template code area                                                                                                                      |
| `##jj2_begin` or  `//jj2_begin`                                                                                                                  |
| `##jj2_end`   or  `//jj2_end`                                                                                                                    |
| Put template code between `##jj2_begin` and `##jj2_end` ，jj2_begin Followed by parameters example: `name='jinja2 content'`.example: `##jj2_begin:name=www` |
| Define test code area                                                                                                                          |  
| `## test_begin`  or  `// test_begin`                                                                                                                  |
| `## test_end`    or  `// test_end`                                                                                                                    |
| test_Begin and test_End is the test code，Will not be saved to the file                                                                        |
| `##%cleartest` clear test code                                                                       |
| `##mdf:`    or  `//mdf:`                                                                                                                          |
| `##mdfend`  or  `//mdfend`                                                                                                                        |
| `##mdf` and `##mdfend`  content，Will be saved to the file                                                                                     |
---
#### Commands and environment variables
| label       |           value           | annotation                                                                         |
| :---------- | :-----------------------: | :--------------------------------------------------------------------------------- |
| command:    |                           | shell command or executable                                                        |
| pycmd:      |                           | python parameter command                                                           |
| dartcmd:    |                           | dart parameter command                                                             |
| fluttercmd: | flutter parameter command |                                                                                    |
| kcmd:       |                           | jupyter kernel command                                                             |
| env:        |                           | Setting environment variables for code file runtime.example: name=xxx name2='dddd' |
---
#### Behavior control
| label       |  value  | annotation                 |
| :---------- | :-----: | :------------------------- |
| noruncode   |         | Do not run code content    |
| onlycsfile  |         | Generate code files only   |
| onlyruncmd  |         | Run the label command only |
| onlycompile |         | Compile code content only  |
### License
[MIT](LICENSE.txt)
