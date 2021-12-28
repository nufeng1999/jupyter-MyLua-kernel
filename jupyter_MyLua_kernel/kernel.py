##//%file:kernel.py
#
#   MyPython Jupyter Kernel
#
from math import exp
from queue import Queue
from threading import Thread
from ipykernel.kernelbase import Kernel
from pexpect import replwrap, EOF
from jinja2 import Environment, PackageLoader, select_autoescape,Template
from abc import ABCMeta, abstractmethod
from typing import List, Dict, Tuple, Sequence
from shutil import copyfile,move
from urllib.request import urlopen
import base64
import urllib.request
import urllib.parse
import platform
import pexpect
import signal
import typing 
import typing as t
import re
import signal
import subprocess
import tempfile
import os
import stat
import sys
import traceback
import os.path as path
import codecs
import time
import importlib
import importlib.util
import inspect
from plugins.ISpecialID import IStag,IDtag,IBtag,ITag,ICodePreproc
from plugins._filter2_magics import Magics
#
#   MyPython Jupyter Kernel
#
class IREPLWrapper(replwrap.REPLWrapper):
    def __init__(self, write_to_stdout, write_to_stderr, read_from_stdin,
                cmd_or_spawn,replsetip, orig_prompt, prompt_change,
                extra_init_cmd=None, line_output_callback=None):
        self._write_to_stdout = write_to_stdout
        self._write_to_stderr = write_to_stderr
        self._read_from_stdin = read_from_stdin
        self.line_output_callback = line_output_callback
        self.replsetip=replsetip
        self.startflag=True
        self.startexpecttimeout=60
        # x = time.localtime(time.time())
        self.start_time = time.time()
        replwrap.REPLWrapper.__init__(self, cmd_or_spawn, orig_prompt,
                                      prompt_change,extra_init_cmd=extra_init_cmd)
    def _expect_prompt(self, timeout=-1):
        if timeout ==None :
            # "None" means we are executing code from a Jupyter cell by way of the run_command
            # in the do_execute() code below, so do incremental output.
            retry=0
            received=False
            cmdstart_time = time.time()
            cmdexectimeout=10
            while True:
                if self.startflag :
                    cmdexectimeout=None
                    run_time = time.time() - cmdstart_time
                    if run_time > self.startexpecttimeout:
                        self.startflag=False
                        self.line_output_callback(self.child.before + '\r\n')
                        # self.line_output_callback("\nEnd of startup process\n")
                        break
                try:
                    pos = self.child.expect_exact([self.prompt, self.continuation_prompt, self.replsetip, pexpect.EOF, pexpect.TIMEOUT],timeout=cmdexectimeout)
                    if pos == 2:
                        # End of line received
                        if self.child.terminated:
                            self.line_output_callback("\nprocess.terminated\n")
                        self.line_output_callback(self.child.before +self.replsetip+ '\r\n')
                        self.line_output_callback("\nEnd of startup process\n")
                        self.replsetip=u'\r\n'
                        cmdexectimeout=None
                        self.startflag=False
                        break
                    elif pos ==3:
                        if len(self.child.before) != 0:
                            self.line_output_callback(self.child.before + '\r\n')
                        self.line_output_callback('The process has exited.\r\n')
                        break
                    elif pos == 0:
                        self.line_output_callback(self.child.before + '\n')
                        cmdstart_time = time.time()
                        if self.prompt!="\r\n":break
                    else:
                        if len(self.child.before) != 0:
                            # prompt received, but partial line precedes it
                            self.line_output_callback(self.child.before)
                            cmdstart_time = time.time()
                        else:
                            if self.startflag :
                                continue
                            run_time = time.time() - cmdstart_time
                            if run_time > 10:
                                break
                except Exception as e:
                    # self.line_output_callback(self.child.before)
                    self._write_to_stderr("[MyCkernel] Error:Executable _expect_prompt error! "+str(e)+"\n")
        else:
            # Otherwise, use existing non-incremental code
            pos = replwrap.REPLWrapper._expect_prompt(self, timeout=timeout)
        # Prompt received, so return normally
        return pos
class RealTimeSubprocess(subprocess.Popen):
    inputRequest = "<inputRequest>"
    kobj=None
    def setkobj(self,k=None):
        self.kobj=k
    def __init__(self, cmd, write_to_stdout, write_to_stderr, read_from_stdin,
        cwd=None,shell=False,env=None,kobj=None,outencode='UTF-8'):
        self.outencode=outencode
        self.kobj=kobj
        self._write_to_stdout = write_to_stdout
        self._write_to_stderr = write_to_stderr
        self._read_from_stdin = read_from_stdin
        if env!=None and len(env)<1:env=None
        
        super().__init__(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE,
                            bufsize=0,cwd=cwd,shell=shell,env=env)
        self._stdout_queue = Queue()
        self._stdout_thread = Thread(target=RealTimeSubprocess._enqueue_output, args=(self.stdout, self._stdout_queue))
        self._stdout_thread.daemon = True
        self._stdout_thread.start()
        self._stderr_queue = Queue()
        self._stderr_thread = Thread(target=RealTimeSubprocess._enqueue_output, args=(self.stderr, self._stderr_queue))
        self._stderr_thread.daemon = True
        self._stderr_thread.start()
    @staticmethod
    def _enqueue_output(stream, queue):
        for line in iter(lambda: stream.read(4096), b''):
            queue.put(line)
        stream.close()
    def write_contents(self,magics=None):
        def read_all_from_queue(queue):
            res = b''
            size = queue.qsize()
            while size != 0:
                res += queue.get_nowait()
                size -= 1
            return res
        stderr_contents = read_all_from_queue(self._stderr_queue)
        if stderr_contents:
            if self.kobj!=None:
                self.kobj._logln(stderr_contents.decode('UTF-8', errors='ignore'),3)
            else:
                self._write_to_stderr(stderr_contents.decode('UTF-8', errors='ignore'))
        stdout_contents = read_all_from_queue(self._stdout_queue)
        if stdout_contents:
            if self.kobj.get_magicsSvalue(magics,"outputtype").startswith("image"):
                self._write_to_stdout(stdout_contents,magics)
                ##reset outputtype
                magics['_st']["outputtype"]="text/plain"
                return
            contents=''
            if self.outencode=='UTF-8':
                contents = stdout_contents.decode('UTF-8', errors='ignore')
            else:
                contents = stdout_contents.decode(self.outencode, errors='ignore')
            # if there is input request, make output and then
            # ask frontend for input
            start = contents.find(self.__class__.inputRequest)
            if(start >= 0):
                contents = contents.replace(self.__class__.inputRequest, '')
                if(len(contents) > 0):
                    self._write_to_stdout(contents,magics)
                readLine = ""
                while(len(readLine) == 0):
                    readLine = self._read_from_stdin()
                # need to add newline since it is not captured by frontend
                readLine += "\n"
                self.stdin.write(readLine.encode())
            else:
                self._write_to_stdout(contents,magics)
    def wait_end(self,magics):
        while self.poll() is None:
            if self.kobj.get_magicsSvalue(magics,"outputtype").startswith("text"):
                self.write_contents(magics)
            pass
            continue
        self.write_contents(magics)
        if self.kobj==None:
            self._write_to_stdout("The process end:"+str(self.pid)+"\n",magics)
        else:
            self.kobj._logln("The process end:"+str(self.pid))
        ############################################
        # self.write_contents(magics)
        # wait for threads to finish, so output is always shown
        self._stdout_thread.join()
        self._stderr_thread.join()
        # self.write_contents(magics)
        return self.returncode
class MyKernel(Kernel):
    implementation = 'jupyter-MyPython-kernel'
    implementation_version = '1.0'
    language = 'Python'
    language_version = sys.version.split()[0]
    language_info = {'name': 'python',
                     'version': sys.version.split()[0],
                     'mimetype': 'text/x-python',
                     'codemirror_mode': {
                        'name': 'ipython',
                        'version': sys.version_info[0]
                     },
                     'pygments_lexer': 'ipython%d' % 3,
                     'nbconvert_exporter': 'python',
                     'file_extension': '.py'}
    banner = "MyPython kernel.\n" \
             "Uses , compiles in , and creates source code files and executables in temporary folder.\n"
    kernelinfo="[MyPython]"
    main_head = "\n" \
            "\n" \
            "int main(List<String> arguments){\n"
    main_foot = "\nreturn 0;\n}"
    def __init__(self, *args, **kwargs):
        super(MyKernel, self).__init__(*args, **kwargs)
        self._allow_stdin = True
        self.readOnlyFileSystem = False
        self.bufferedOutput = True
        self.linkMaths = True # always link math library
        self.wAll = True # show all warnings by default
        self.wError = False # but keep comipiling for warnings
        self.sys = platform.system()
        self.subsys=self.getossubsys()
        self.files = []
        self.isdstr=False
        self.issstr=False
        self._loglevel='1'
        # mastertemp = tempfile.mkstemp(suffix='.out')
        # os.close(mastertemp[0])
        # self.master_path = mastertemp[1]
        # self.resDir = path.join(path.dirname(path.realpath(__file__)), 'resources')
        self.chk_replexit_thread = Thread(target=self.chk_replexit, args=(self.g_rtsps))
        self.chk_replexit_thread.daemon = True
        self.chk_replexit_thread.start()
        self.init_plugin()
        self.mag=Magics(self,self.plugins,self.ICodePreprocs)
    pausestr='''
get_char()
{
SAVEDSTTY=`stty -g`
stty -echo
stty cbreak
dd if=/dev/tty bs=1 count=1 2> /dev/null
stty -raw
stty echo
stty $SAVEDSTTY
}
echo ""
echo "Press any key to start...or Press Ctrl+c to cancel"
char=`get_char`
echo "OK"
'''
    silent=None
    jinja2_env = Environment()
    g_rtsps={}
    g_chkreplexit=True
    def get_retinfo(self, rettype:int=0):
        retinfo={'status': 'ok', 'execution_count': self.execution_count, 'payload': [], 'user_expressions': {}}
        return retinfo
    def chkjoptions(self,magics,jarfile,targetdir):
        if len(self.addmagicsSkey(magics,'joptions'))>-1:
            index=-1
            try:
                index=self.addmagicsSkey(magics,'joptions').index('-cp')
            except Exception as e:
                pass
            if(index<0):
                magics['_st']['joptions']+=['-cp']
                magics['_st']['joptions']+=[':']
                index=index+1
            cpstr=magics['_st']['joptions'][index+1]
            cpstr=cpstr+":"+jarfile+":"+targetdir
            if cpstr.strip().startswith(':'):
                cpstr=cpstr[1:] 
            # self._log(cpstr)
            magics['_st']['joptions'][index+1]=cpstr
    def resolving_enveqval(self, envstr):
        if envstr is None or len(envstr.strip())<1:
            return os.environ
        # env_dict={}
        argsstr=self.replacemany(self.replacemany(self.replacemany(envstr.strip(),('  '),' '),('= '),'='),' =','=')
        pattern = re.compile(r'([^\s*]*)="(.*?)"|([^\s*]*)=(\'.*?\')|([^\s*]*)=(.[^\s]*)')
        for argument in pattern.findall(argsstr):
            li=list(argument)
            li= [i for i in li if i != '']
            # env_dict[str(li[0])]=li[1]
            os.environ.setdefault(str(li[0]),li[1])
        # envstr=str(str(envstr.split("|")).split("=")).replace(" ","").replace("\'","").replace("\"","").replace("[","").replace("]","").replace("\\","")
        # env_list=envstr.split(",")
        # for i in range(0,len(env_list),2):
        #     os.environ.setdefault(env_list[i],env_list[i+1])
        return os.environ
    def resolving_eqval2dict(self,argsstr):
        if not argsstr or len(argsstr.strip())<1:
            return None
        env_dict={}
        argsstr=self.replacemany(self.replacemany(self.replacemany(argsstr.strip(),('  '),' '),('= '),'='),' =','=')
        pattern = re.compile(r'([^\s*]*)="(.*?)"|([^\s*]*)=(\'.*?\')|([^\s*]*)=(.[^\s]*)')
        for argument in pattern.findall(argsstr):
            li=list(argument)
            li= [i for i in li if i != '']
            env_dict[str(li[0])]=li[1]
        return env_dict
##//%include:../src/_templateHander.py
##//%include:../src/_readtemplatefile.py
    def get_outencode(self,magics):
        encodestr=self.get_magicsSvalue(magics,"outencode")
        if len(encodestr)<1:
            encodestr='UTF-8'
        return encodestr
    def get_magicsSvalue(self,magics:Dict,key:str):
        return self.addmagicsSkey(magics,key)
    def get_magicsBvalue(self,magics:Dict,key:str):
        return self.addmagicsBkey(magics,key)
    def get_magicsbykey(self,magics:Dict,key:str):
        return self.addkey2dict(magics,key)
    
    def addmagicsSLkey(self,magics:Dict,key:str,value=None,func=None):
        return self.addmagicskey2(magics=magics,key=key,type='_sline',func=func,value=value)
    def addmagicsSkey(self,magics:Dict,key:str,func=None):
        return self.addmagicskey2(magics=magics,key=key,type='_st',func=func)
    def addmagicsBkey(self,magics:Dict,key:str,value=None,func=None):
        return self.addmagicskey2(magics=magics,key=key,type='_bt',func=func,value=value)
    
    def addmagicskey2(self,magics:Dict,key:str,type:str,func=None,value=None):
        if not magics[type].__contains__(key):
            ##添加 key
            d={key:[]}
            if value!=None:
                d={key:value}
            magics[type].update(d)
        if not magics[type+'f'].__contains__(key):
            ##添加 key相关回调函数
            d={key:[]}
            magics[type+'f'].update(d)
        if func!=None:
            magics[type+'f'][key]+=[func]
        return magics[type][key]
    def addkey2dict(self,magics:Dict,key:str,type:str=None):
        if not magics.__contains__(key):
            d={key:[]}
            if type!=None and type=="dict":
                d={key:{}}
            magics.update(d)
        return magics[key]
    usleep = lambda x: time.sleep(x/1000000.0)
    def replacemany(self,our_str, to_be_replaced:str, replace_with:str):
        while (to_be_replaced in our_str):
            our_str = our_str.replace(to_be_replaced, replace_with)
        return our_str
    def _filter_dict(self,argsstr):
        if not argsstr or len(argsstr.strip())<1:
            return None
        env_dict={}
        argsstr=self.replacemany(self.replacemany(self.replacemany(argsstr.strip(),('  '),' '),('= '),'='),' =','=')
        pattern = re.compile(r'([^\s*]*)="(.*?)"|([^\s*]*)=(\'.*?\')|([^\s*]*)=(.[^\s]*)')
        for argument in pattern.findall(argsstr):
            li=list(argument)
            li= [i for i in li if i != '']
            env_dict[str(li[0])]=li[1]
        return env_dict
    def _fileshander(self,files:List,srcfilename,magics)->str:
        index=-1
        fristfile=srcfilename
        try:
            for newsrcfilename in files:
                index=index+1
                newsrcfilename = os.path.join(os.path.abspath(''),newsrcfilename)
                if os.path.exists(newsrcfilename):
                    if magics!=None and len(self.addkey2dict(magics,'overwritefile'))<1:
                        newsrcfilename +=".new.py"
                if not os.path.exists(os.path.dirname(newsrcfilename)) :
                    os.makedirs(os.path.dirname(newsrcfilename))
                if index==0:
                    os.rename(srcfilename,newsrcfilename)
                    fristfile=newsrcfilename
                    files[0]=newsrcfilename
                else:
                    self._write_to_stdout("copy to :"+newsrcfilename+"\n")
                    copyfile(fristfile,newsrcfilename)
        except Exception as e:
                self._log(str(e),2)
        return files[0]
    def _is_specialID(self,line):
        if line.strip().startswith('##%') or line.strip().startswith('//%'):
            return True
        return False
    def _is_test_begin(self,line):
        if line==None or line=='':return ''
        return line.strip().startswith('##test_begin') or line.strip().startswith('//test_begin')
    def _is_test_end(self,line):
        if line==None or line=='':return ''
        return line.strip().startswith('##test_end') or line.strip().startswith('//test_end')
    def _is_dqm_begin(self,line):
        if line==None or line=='':return ''
        line=self.replacemany(line.strip(),(' '),'')
        if '=\"\"\"' in line: 
            self.isdstr=True
            return False
        if '\"\"\"' in line: 
            if self.isdstr:return False
            self.isdstr=False
            return True
        return line.lstrip().startswith('\"\"\"')
    def _is_dqm_end(self,line):
        if line==None or line=='':return ''
        if self.isdqm:
            return line.rstrip().endswith('\"\"\"')
        return False
    def _is_sqm_begin(self,line):
        if line==None or line=='':return ''
        line=self.replacemany(line.strip(),(' '),'')
        if '=\'\'\'' in line: 
            self.issstr=True
            return False
        if '\'\'\'' in line: 
            if self.issstr:return False
            self.issstr=False
            return True
        return line.lstrip().startswith('\'\'\'')
    def _is_sqm_end(self,line):
        if line==None or line=='':return ''
        if self.issqm:
            return line.rstrip().endswith('\'\'\'')
        return False
    
    def cleanCdqm(self,code):
        return re.sub(r"/\*.*?\*/", "", code, flags=re.M|re.S)
    def cleanCnotes(self,code):
        return re.sub(r"//.*", "", code)
    def cleannotes(self,line):
        ##tmpCode = re.sub(r"//.*", "", line)
        ##tmpCode = re.sub(r"/\*.*?\*/", "", tmpCode, flags=re.M|re.S)
        return '' if (not self._is_specialID(line)) and (line.lstrip().startswith('## ') or line.lstrip().startswith('// ')) else line
    isdqm=False##清除双引号多行注释
    def cleandqmA(self,code):
        return re.sub(r"\"\"\".*?\"\"\"", "", code, flags=re.M|re.S)
    def cleandqm(self,line):
        ##tmpCode = re.sub(r"\"\"\".*?\"\"\"", "", line, flags=re.M|re.S)
        if not self.isdqm:
            istb=self._is_dqm_begin(line)
            if istb: 
                self.isdqm=True
                if len(line.strip())>5:
                    iste=self._is_dqm_end(line)
                    if iste:self.isdqm=False
                return ''
        iste=self._is_dqm_end(line)
        if iste:
            self.isdqm=False
            return ''
        line= "" if self.isdqm else line
        return line
    issqm=False
    def cleansqmA(self,code):
        return re.sub(r"\'\'\'.*?\'\'\'", "", code, flags=re.M|re.S)
    def cleansqm(self,line):
        if not self.issqm:
            istb=self._is_sqm_begin(line)
            if istb: 
                self.issqm=True
                if len(line.strip())>5:
                    iste=self._is_sqm_end(line)
                    if iste:self.issqm=False
                return ''
        iste=self._is_sqm_end(line)
        if iste:
            self.issqm=False
            return ''
        line= "" if self.issqm else line
        return line
    istestcode=False
    def cleantestcodeA(self,code):
        code=re.sub(r"\/\/test_begin.*?\/\/test_end", "", code, flags=re.M|re.S)
        return re.sub(r"\#\#test_begin.*?\#\#test_end", "", code, flags=re.M|re.S)
    def cleantestcode(self,line):
        if not self.istestcode:
            istb=self._is_test_begin(line)
            if istb: 
                self.istestcode=True
                if len(line.strip())>5:
                    iste=self._is_test_end(line)
                    if iste:self.istestcode=False
                return ''
        iste=self._is_test_end(line)
        if iste:
            self.istestcode=False
            return ''
        line= "" if self.istestcode else line
        return line
    
    def repl_listpid(self,cmd=None):
        if len(self.g_rtsps)>0: 
            self._write_to_stdout("--------All replpid--------\n")
            for key in self.g_rtsps:
                self._write_to_stdout(key+"\n")
        else:
            self._write_to_stdout("--------All replpid--------\nNone\n")
    def chk_replexit(self,grtsps): 
        while self.g_chkreplexit:
            try:
                if len(grtsps)>0: 
                    for key in grtsps:
                        if grtsps[key].child.terminated:
                            pass
                            del grtsps[key]
            finally:
                pass
        if len(grtsps)>0: 
            for key in grtsps:
                if grtsps[key].child.terminated:
                    pass
                    del grtsps[key]
                else:
                    grtsps[key].child.terminate(force=True)
                    del grtsps[key]
    def cleanup_files(self):
        # keep the list of files create in case there is an exception
        # before they can be deleted as usual
        if self.files != None and len(self.files) > 0:
            for file in self.files:
                if(os.path.exists(file)):
                    os.remove(file)
    def new_temp_file(self, **kwargs):
        # We don't want the file to be deleted when closed, but only when the kernel stops
        kwargs['delete'] = False
        kwargs['mode'] = 'w'
        file = tempfile.NamedTemporaryFile(**kwargs)
        self.files.append(file.name)
        return file
    def create_codetemp_file(self,magics,code,suffix):
        encodestr='UTF-8'
        if magics!=None:
            encodestr=self.get_magicsSvalue(magics,"fileencode")
        if len(encodestr)<1:
            encodestr='UTF-8'
        if (suffix.strip().lower().endswith(".bat") or
            (suffix.strip().lower().endswith(".ps1") and self.sys=="Windows")):
            encodestr="GBK"
        source_file=self.new_temp_file(suffix=suffix,dir=os.path.abspath(''),encoding=encodestr)
        magics['codefilename']=source_file.name
        with  source_file:
            source_file.write(code)
            source_file.flush()
        return source_file
    def _log(self, output,level=1,outputtype='text/plain'):
        if self._loglevel=='0': return
        streamname='stdout'
        if not self.silent:
            prestr=self.kernelinfo+' Info:'
            if level==2:
                prestr=self.kernelinfo+' Warning:'
                streamname='stderr'
            elif level==3:
                prestr=self.kernelinfo+' Error:'
                streamname='stderr'
            else:
                prestr=self.kernelinfo+' Info:'
                streamname='stdout'
            # if len(outputtype)>0 and (level!=2 or level!=3):
                # self._write_display_data(mimetype=outputtype,contents=prestr+output)
                # return
            # Send standard output
            stream_content = {'name': streamname, 'text': prestr+output}
            self.send_response(self.iopub_socket, 'stream', stream_content)
    def _logln(self, output,level=1,outputtype='text/plain'):
        self._log(output+"\n",level=1,outputtype='text/plain')
    def _write_display_data(self,mimetype='text/html',contents=""):
        try:
            if mimetype.startswith('image'):
                metadata ={mimetype:{}}
                # contents=contents
                # self._logln(base64.encodebytes(contents))
                # contents=base64.encodebytes(contents)
                # contents=urllib.parse.quote(base64.b64encode(contents))
                header="<div><img alt=\"Output\" src=\"data:"+mimetype+";base64,"
                end="\"></div>"
                contents=header+base64.encodebytes(contents).decode( errors='ignore')+end
                mimetype='text/html'
                metadata = {mimetype:{}}
        except Exception as e:
            self._logln("_write_display_data err "+str(e),3)
            return
        self.send_response(self.iopub_socket, 'display_data', {'data': {mimetype:contents}, 'metadata': {mimetype:{}}})
    def _write_to_stdout(self,contents,magics=None):
        if magics !=None and len(magics['_st']['outputtype'])>0:
            self._write_display_data(mimetype=magics['_st']['outputtype'],contents=contents)
        else:
            self.send_response(self.iopub_socket, 'stream', {'name': 'stdout', 'text': contents})
    def _write_to_stderr(self, contents):
        self.send_response(self.iopub_socket, 'stream', {'name': 'stderr', 'text': contents})
    def _read_from_stdin(self):
        return self.raw_input()
    def readcodefile(self,filename,spacecount=0):
        filecode=''
        codelist1=None
        if not os.path.exists(filename):
            return ''
        with open(os.path.join(os.path.abspath(''),filename), 'r',encoding="UTF-8") as codef1:
            codelist1 = codef1.readlines()
        if len(codelist1)>0:
            for t in codelist1:
                filecode+=' '*spacecount + t
        return filecode
    def loadurl(self,url):
        content=''
        try:
            request=urllib.request.Request(url)
            myURL = urlopen(request)
            # content= myURL.read()
            lines = myURL.readlines()
            for line in lines:
                print(line)
                content+=line.decode()+"\n"
        except Exception as e:
            self._logln("loadurl error! "+str(e),3)
        return content
    #####################################################################
    def _start_replprg(self,command,args,magics):
        # Signal handlers are inherited by forked processes, and we can't easily
        # reset it from the subprocess. Since kernelapp ignores SIGINT except in
        # message handlers, we need to temporarily reset the SIGINT handler here
        # so that bash and its children are interruptible.
        sig = signal.signal(signal.SIGINT, signal.SIG_DFL)
        self.silent = None
        try:
            child = pexpect.spawn(command, args,timeout=60, echo=False,
                                  encoding='utf-8')
            self._write_to_stdout("replchild pid:"+str(child.pid)+"\n")
            self._write_to_stdout("--------process info---------\n")
            self.replwrapper = IREPLWrapper(
                                    self._write_to_stdout,
                                    self._write_to_stderr,
                                    self._read_from_stdin,
                                    child,
                                    replsetip=magics['_st']['replsetip'],
                                    orig_prompt='\r\n', 
                                    prompt_change=None,
                                    extra_init_cmd=None,
                                    line_output_callback=self.process_output)
            # self._write_to_stdout("replchild pid:"+str(self.replwrapper.child.pid)+"\n")
            self.g_rtsps[str(self.replwrapper.child.pid)]=self.replwrapper
        except Exception as e:
            self._write_to_stderr("[MyPythonkernel] Error:Executable _start_replprg error! "+str(e)+"\n")
        finally:
            signal.signal(signal.SIGINT, sig)
    def process_output(self, output,magics=None):
        if not self.silent:
            if magics !=None and len(magics['_st']['outputtype'])>0:
                self._write_display_data(mimetype=magics['_st']['outputtype'],contents=output)
                return
            # Send standard output
            stream_content = {'name': 'stdout', 'text': output}
            self.send_response(self.iopub_socket, 'stream', stream_content)
    def send_replcmd(self, code, silent, store_history=True,
                   user_expressions=None, allow_stdin=False,magics=None):
        self.silent = silent
        if not code.strip():
            return {'status': 'ok', 'execution_count': self.execution_count,
                    'payload': [], 'user_expressions': {}}
        interrupted = False
        try:
            # Note: timeout=None tells IREPLWrapper to do incremental
            # output.  Also note that the return value from
            # run_command is not needed, because the output was
            # already sent by IREPLWrapper.
            self._write_to_stdout("send replcmd:"+code.rstrip()+"\n")
            self._write_to_stdout("---Received information after send repl cmd---\n")
            if magics and len(magics['_st']['replchildpid'])>0 :
                if self.g_rtsps[magics['_st']['replchildpid']] and \
                    self.g_rtsps[magics['_st']['replchildpid']].child and \
                    not self.g_rtsps[magics['_st']['replchildpid']].child.terminated :
                    self.g_rtsps[magics['_st']['replchildpid']].run_command(code.rstrip(), timeout=None)
            else:
                if self.replwrapper and \
                    self.replwrapper.child and \
                    not self.replwrapper.child.terminated :
                    self.replwrapper.run_command(code.rstrip(), timeout=None)
            pass
        except KeyboardInterrupt:
            self.gdbwrapper.child.sendintr()
            interrupted = True
            self.gdbwrapper._expect_prompt()
            output = self.gdbwrapper.child.before
            self.process_output(output)
        except EOF:
            # output = self.gdbwrapper.child.before + 'Restarting GDB'
            # self._start_gdb()
            # self.process_output(output)
            pass
        if interrupted:
            return {'status': 'abort', 'execution_count': self.execution_count}
        # try:
        #     exitcode = int(self.replwrapper.run_command('echo $?').rstrip())
        # except Exception as e:
        #     self.process_output("[MyPythonkernel] Error:Executable send_replcmd error! "+str(e)+"\n")
        exitcode = 0
        if exitcode:
            error_content = {'execution_count': self.execution_count,
                             'ename': '', 'evalue': str(exitcode), 'traceback': []}
            self.send_response(self.iopub_socket, 'error', error_content)
            error_content['status'] = 'error'
            return error_content
        else:
            return {'status': 'ok', 'execution_count': self.execution_count,
                    'payload': [], 'user_expressions': {}}
    #####################################################################
    def do_shell_command(self,commands,cwd=None,shell=True,env=True,magics=None):
        try:
            if len(magics['_bt']['replcmdmode'])>0:
                findObj= commands[0].split(" ",1)
                if findObj and len(findObj)>1:
                    cmd=findObj[0]
                    arguments=findObj[1]
                    cmdargs=[]
                    for argument in re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")+', arguments):
                        cmdargs += [argument.strip('"')]
                    self._write_to_stdout(cmd)
                    self._write_to_stdout(''.join((' '+ str(s) for s in cmdargs))+"\n")
                    self._start_replprg(cmd,cmdargs,magics)
                    return
            cmds=[]
            for argument in re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")+', commands.strip()):
                cmds += [argument.strip('"')]
            p = self.create_jupyter_subprocess(cmds,cwd,shell,env=env,magics=magics)
            if magics!=None and len(self.get_magicsbykey(magics,'showpid'))>0:
                self._write_to_stdout("The process PID:"+str(p.pid)+"\n")
            self.g_rtsps[str(p.pid)]=p
            returncode=p.wait_end(magics)
            del self.g_rtsps[str(p.pid)]
            if returncode != 0:
                self._logln("Executable command exited with code {}\n".format(returncode),3)
            else:
                self._logln("command success.\n")
            return
        except Exception as e:
            self._logln("Executable command error! "+str(e)+"\n",3)
    
    def do_Py_command(self,commands,cwd=None,shell=False,env=True,magics=None):
        try:
            cmds=[]
            for argument in re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")+', commands.strip()):
                cmds += [argument.strip('"')]
            p = self.create_jupyter_subprocess(['python']+cmds,cwd,shell,env=env,magics=magics)
            if magics!=None and len(self.get_magicsbykey(magics,'showpid'))>0:
                self._write_to_stdout("The process PID:"+str(p.pid)+"\n")
            self.g_rtsps[str(p.pid)]=p
            returncode=p.wait_end(magics)
            del self.g_rtsps[str(p.pid)]
            if returncode != 0:
                self._logln("Executable python exited with code {}".format(returncode))
            else:
                self._logln("command python success.")
        except Exception as e:
            self._logln("Executable python command error! "+str(e)+"\n",3)
        return
    
    def send_cmd(self,pid,cmd):
        try:
            # self._write_to_stdout("send cmd PID:"+pid+"\n cmd:"+cmd)
            # if self.g_rtsps.has_key(pid):
                # self._write_to_stderr("[MyPythonkernel] Info:exist! "+pid+"\n")
            # self.g_rtsps[pid].stdin.write(cmd.encode())
            self.g_rtsps[pid]._write_to_stdout(cmd)
        except Exception as e:
            self._log("Executable send_cmd error! "+str(e)+"\n")
    
        return
    def create_jupyter_subprocess(self, cmd,cwd=None,shell=False,env=None,magics=None,outencode=None):
        try:
            if env==None or len(env)<1:env=os.environ
            
            newcwd=self.get_magicsSvalue(magics,'cwd')
            if len(newcwd.strip())>1:cwd=newcwd
            if cwd==None:cwd=os.path.abspath('')
            if magics!=None and magics['status']=='' and len(self.addmagicsBkey(magics,'runinterm'))>0:
                self.inittermcmd(magics)
                if len(magics['_st']['term'])<1:
                    self._logln("no term！",2)
                execfile=''
                for x in cmd:
                    execfile+=x+" "
                cmdshstr=self.create_termrunsh(execfile,magics)
                if self.sys=='Windows':
                    cmd=magics['_st']['term']+[cmdshstr]
                elif self.sys=='Linux':
                    cmd=magics['_st']['term']+['--',cmdshstr]
                else:
                    cmd=magics['_st']['term']+['--',cmdshstr]
            cstr=''
            for x in cmd: cstr+=x+" "
            self._logln(cstr)
            if(magics!=None and (outencode==None or len(outencode)<0)):
                outencode=self.get_outencode(magics)
            if(outencode==None or len(outencode)<0):
                outencode='UTF-8'
            return RealTimeSubprocess(cmd,
                                  self._write_to_stdout,
                                  self._write_to_stderr,
                                  self._read_from_stdin,cwd,shell,env,self,outencode=outencode)
        except Exception as e:
            self._logln("RealTimeSubprocess err:"+str(e),3)
            raise
    def getossubsys(self):
        uname=''
        try:
            u=os.popen('bash -c "uname"')
            uname=u.read()
        except Exception as e:
            self._logln(""+str(e),3)
        return uname
    def inittermcmd(self,magics):
        if len(magics['_st']['term'])>0:return ''
        termcmd=''
        try:
            if self.subsys.startswith('MINGW64') or self.subsys.startswith('CYGWIN'):
                termcmd='mintty "/usr/bin/bash" --login'
            if self.sys=='Linux':
                termcmd='gnome-terminal'
            elif self.sys=='Windows':
                termcmd='c:\\Windows\\System32\\cmd.exe /c start'
        except Exception as e:
            self._logln(""+str(e),3)
        if len(termcmd)>1:
            magics['_st']['term']=[]
            for argument in re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")+', termcmd):
                magics['_st']['term'] += [argument.strip('"')]
        return termcmd
    def create_termrunsh(self,execfile,magics):
        fil_ename=execfile
        uname=''
        try:
            u=os.popen('bash -c "uname"')
            uname=u.read()
        except Exception as e:
            self._logln(""+str(e),3)
        if self.subsys.startswith('MINGW64') or self.subsys.startswith('CYGWIN'):
            pausestr=self.pausestr
            termrunsh="\n"+execfile+"\n"+pausestr+"\n"
            termrunsh_file=self.create_codetemp_file(magics,termrunsh,suffix='.sh')
            newsrcfilename=termrunsh_file.name
            fil_ename=newsrcfilename
        elif self.sys=='Windows' :
            termrunsh="echo off\r\ncls\r\n"+execfile+"\r\npause\r\nexit\r\n"
            if execfile.strip().lower().endswith(".bat"):
                termrunsh="echo off\r\ncls\r\ncall "+execfile+"\r\npause\r\nexit\r\n"
            termrunsh_file=self.create_codetemp_file(magics,termrunsh,suffix='.bat')
            newsrcfilename=termrunsh_file.name
            fil_ename=newsrcfilename
        elif self.sys=='Linux':
            pausestr=self.pausestr
            termrunsh="\n"+execfile+"\n"+pausestr+"\n"
            termrunsh_file=self.create_codetemp_file(magics,termrunsh,suffix='.sh')
            newsrcfilename=termrunsh_file.name
            fil_ename=newsrcfilename
        else:
            self._logln("Cannot create terminal!",3)
        self._logln(fil_ename)
        os.chmod(newsrcfilename,stat.S_IRWXU+stat.S_IRGRP+stat.S_IXGRP+stat.S_IXOTH)
        return fil_ename
    def generate_Pythonfile(self, source_filename, binary_filename, cflags=None, ldflags=None):
        return
#####################################################################
#####################################################################
    def _add_main(self, magics, code):
        # remove comments
        tmpCode = re.sub(r"//.*", "", code)
        tmpCode = re.sub(r"/\*.*?\*/", "", tmpCode, flags=re.M|re.S)
        x = re.search(r".*\s+main\s*\(", tmpCode)
        if not x:
            code = self.main_head + code + self.main_foot
            # magics['_st']['cflags'] += ['-lm']
        return magics, code
    def raise_plugin(self,code,magics,returncode=None,filename='',ifunc=1,ieven=1)->Tuple[bool,str]:
        bcancel_exec=False
        bretcancel_exec=False
        retstr=''
        for pluginlist in self.plugins:
            for pkey,pvalue in pluginlist.items():
                # print( pkey +":"+str(len(pvalue))+"\n")
                for pobj in pvalue:
                    newline=''
                    try:
                        # if key in pobj.getIDSptag(pobj):
                        if ifunc==1 and ieven==1:
                                bretcancel_exec,retstr=pobj.on_before_buildfile(pobj,code,magics)
                        elif ifunc==2 and ieven==1:
                                bretcancel_exec,retstr=pobj.on_before_compile(pobj,code,magics)
                        elif ifunc==3 and ieven==1:
                                bretcancel_exec,retstr=pobj.on_before_exec(pobj,code,magics)
                        elif ifunc==1 and ieven==2:
                                bretcancel_exec=pobj.on_after_buildfile(pobj,returncode,filename,magics)
                        elif ifunc==2 and ieven==2:
                                bretcancel_exec=pobj.on_after_compile(pobj,returncode,filename,magics)
                        elif ifunc==3 and ieven==2:
                                bretcancel_exec=pobj.on_after_exec(pobj,returncode,filename,magics)
                        elif ifunc==3 and ieven==3:
                                bretcancel_exec=pobj.on_after_completion(pobj,returncode,filename,magics)        
                        bcancel_exec=bretcancel_exec & bcancel_exec
                        if bcancel_exec:
                            return bcancel_exec,""
                    except Exception as e:
                        self._log(pobj.getName(pobj)+"---"+str(e)+"\n")
                    finally:pass
        return bcancel_exec,retstr
    def do_execute_script(self, code, magics,silent, store_history=True,
                   user_expressions=None, allow_stdin=True):
        try:
            bcancel_exec,retinfo,magics, code=self.do_preexecute(
                code,magics, 
                silent, store_history,user_expressions, allow_stdin)
            if bcancel_exec:return retinfo
            return_code=0
            fil_ename=''
            retstr=''
            bcancel_exec,retstr=self.raise_plugin(code,magics,return_code,fil_ename,1,1)
            if bcancel_exec:return  self.get_retinfo()
            bcancel_exec,retinfo,magics, code,fil_ename,retstr=self.do_create_codefile(
                magics,code, 
                silent, store_history,user_expressions, allow_stdin)
            if bcancel_exec:return retinfo
            code,magics,return_code,fil_ename
            bcancel_exec,retstr=self.raise_plugin(code,magics,return_code,fil_ename,1,2)
            if bcancel_exec:return  self.get_retinfo()
            fil_ename=magics['codefilename']
            if len(self.get_magicsbykey(magics,'noruncode'))>0:
                bcancel_exec=True
                return self.get_retinfo()
            bcancel_exec,retstr=self.raise_plugin(code,magics,return_code,fil_ename,2,1)
            if bcancel_exec:return  self.get_retinfo()
            bcancel_exec,retinfo,magics, code,fil_ename,retstr=self.do_compile_code(
                return_code,fil_ename,magics,code, 
                silent, store_history,user_expressions, allow_stdin)
            if bcancel_exec:return  retinfo
            bcancel_exec,retstr=self.raise_plugin(code,magics,return_code,fil_ename,2,2)
            if bcancel_exec:return  self.get_retinfo()
            if len(self.get_magicsbykey(magics,'onlycompile'))>0:
                self._log("only run compile \n")
                bcancel_exec=True
                return retinfo
            bcancel_exec,retstr=self.raise_plugin(code,magics,return_code,fil_ename,3,1)
            if bcancel_exec:return self.get_retinfo()
            self._logln("The process :"+fil_ename)
            bcancel_exec,retinfo,magics, code,fil_ename,retstr=self.do_runcode(
                return_code,fil_ename,magics,code, 
                silent, store_history,user_expressions, allow_stdin)
            if bcancel_exec:return retinfo
            bcancel_exec,retstr=self.raise_plugin(code,magics,return_code,fil_ename,3,3)
            if bcancel_exec:return self.get_retinfo()
        except Exception as e:
            self._log(""+str(e),3)
        return self.get_retinfo()
    def do_execute_class(self, code, magics,silent, store_history=True,
                   user_expressions=None, allow_stdin=True):
        try:
            return_code=0
            fil_ename=''
            outpath=''
            bcancel_exec,retinfo,magics, code=self.do_preexecute(
                code, magics,
                silent, store_history,user_expressions, allow_stdin)
            if bcancel_exec:return retinfo
            return_code=0
            fil_ename=''
            bcancel_exec,retstr=self.raise_plugin(code,magics,return_code,fil_ename,1,1)
            if bcancel_exec:return  self.get_retinfo()
            bcancel_exec,retinfo,magics, code,fil_ename,class_filename,outpath,retstr=self.do_create_codefile(
                magics,code, 
                silent, store_history,user_expressions, allow_stdin)
            if bcancel_exec:return retinfo
            bcancel_exec,retstr=self.raise_plugin(code,magics,return_code,fil_ename,1,2)
            if bcancel_exec:return  self.get_retinfo()
            fil_ename=magics['codefilename']
            if len(self.get_magicsbykey(magics,'noruncode'))>0:
                bcancel_exec=True
                return self.get_retinfo()
            bcancel_exec,retstr=self.raise_plugin(code,magics,return_code,fil_ename,2,1)
            if bcancel_exec:return  self.get_retinfo()
            bcancel_exec,retinfo,magics, code,fil_ename,class_filename,outpath,retstr=self.do_compile_code(
                return_code,fil_ename,magics,code, 
                silent, store_history,user_expressions, allow_stdin)
            if bcancel_exec:return  self.get_retinfo()
            bcancel_exec,retstr=self.raise_plugin(code,magics,return_code,fil_ename,2,2)
            if bcancel_exec:return  self.get_retinfo()
            if len(self.get_magicsbykey(magics,'onlycompile'))>0:
                self._log("only run compile \n")
                bcancel_exec=True
                return retinfo
            bcancel_exec,retstr=self.raise_plugin(code,magics,return_code,fil_ename,3,1)
            if bcancel_exec:return self.get_retinfo()
            self._logln("The process :"+class_filename)
            bcancel_exec,retinfo,magics, code,fil_ename,retstr=self.do_runcode(
                return_code,fil_ename,class_filename,outpath,magics,code, 
                silent, store_history,user_expressions, allow_stdin)
            if bcancel_exec:return retinfo
            bcancel_exec,retstr=self.raise_plugin(code,magics,return_code,fil_ename,3,3)
            if bcancel_exec:return self.get_retinfo()
        except Exception as e:
            self._log("???"+str(e),3)
        return self.get_retinfo()
    def do_execute_runprg(self, code, magics,silent, store_history=True,
                   user_expressions=None, allow_stdin=True):
        try:
            bcancel_exec,retinfo,magics, code=self.dor_preexecute(
                code,magics, 
                silent, store_history,user_expressions, allow_stdin)
            if bcancel_exec:return retinfo
            return_code=0
            fil_ename=''
            bcancel_exec,retstr=self.raise_plugin(code,magics,return_code,fil_ename,1,1)
            if bcancel_exec:return  self.get_retinfo()
            bcancel_exec,retinfo,magics, code,fil_ename,retstr=self.dor_create_codefile(
                magics,code, 
                silent, store_history,user_expressions, allow_stdin)
            if bcancel_exec:return retinfo
            bcancel_exec,retstr=self.raise_plugin(code,magics,return_code,fil_ename,1,2)
            if bcancel_exec:return  self.get_retinfo()
            fil_ename=magics['codefilename']
            if len(self.get_magicsbykey(magics,'noruncode'))>0:
                bcancel_exec=True
                return self.get_retinfo()
            bcancel_exec,retstr=self.raise_plugin(code,magics,return_code,fil_ename,3,1)
            if bcancel_exec:return self.get_retinfo()
            self._logln("The process :"+fil_ename)
            bcancel_exec,retinfo,magics, code,fil_ename,retstr=self.dor_runcode(
                return_code,fil_ename,magics,code, 
                silent, store_history,user_expressions, allow_stdin)
            if bcancel_exec:return retinfo
            bcancel_exec,retstr=self.raise_plugin(code,magics,return_code,fil_ename,3,3)
            if bcancel_exec:return self.get_retinfo()
        except Exception as e:
            self._log(""+str(e),3)
        return self.get_retinfo()
##do_runcode
    def dor_runcode(self,return_code,fil_ename,magics,code, silent, store_history=True,
                    user_expressions=None, allow_stdin=True):    
        ##runprg
        ##runprgargs
        return_code=return_code
        fil_ename=fil_ename
        bcancel_exec=False
        retinfo=self.get_retinfo()
        retstr=''
        runprg=self.get_magicsSvalue(magics,'runprg')
        runprgargs=self.get_magicsSvalue(magics,'runprgargs')
        if (len(runprgargs)<1):
            self._logln("No label runprgargs!",2)
        # self._logln(runprgargs[0])
        ##代码运行前
        p = self.create_jupyter_subprocess([runprg]+ runprgargs,cwd=None,shell=False,env=self.addkey2dict(magics,'env'),magics=magics)
        self.g_rtsps[str(p.pid)]=p
        return_code=p.returncode
        ##代码启动后
        bcancel_exec,retstr=self.raise_plugin(code,magics,return_code,fil_ename,3,2)
        
        if len(self.addkey2dict(magics,'showpid'))>0:
            self._logln("The process PID:"+str(p.pid))
        return_code=p.wait_end(magics)
        # self._logln("The process end:"+str(p.pid))
        ##
        ##调用接口
        # return_code=p.returncode
        ##代码运行结束
        if p.returncode != 0:
            self._logln("Executable exited with code {}".format(p.returncode),2)
        return bcancel_exec,retinfo,magics, code,fil_ename,retstr
##do_create_codefile
    def dor_create_codefile(self,magics,code, silent, store_history=True,
                    user_expressions=None, allow_stdin=True):    
        ##runprg
        ##runprgargs
        return_code=0
        fil_ename=''
        bcancel_exec=False
        retinfo=self.get_retinfo()
        retstr=''
        ##调生成文件前接口
        source_file=self.create_codetemp_file(magics,code,suffix='.sh')
        newsrcfilename=source_file.name
        fil_ename=newsrcfilename
        return_code=True
        
        return bcancel_exec,retinfo,magics, code,fil_ename,retstr
##do_preexecute
    def dor_preexecute(self,code,magics,silent, store_history=True,
                user_expressions=None, allow_stdin=False):        
        ##runprg
        ##runprgargs
        bcancel_exec=False
        retinfo=self.get_retinfo()
        return bcancel_exec,retinfo,magics, code
    def do_execute(self, code, silent, store_history=True,
                   user_expressions=None, allow_stdin=True):
        self.silent = silent
        retinfo=self.get_retinfo()
        if len(code.strip())<1:return retinfo
        magics, code = self.mag.filter(code)
        if (len(self.get_magicsbykey(magics,'onlyrunmagics'))>0 or len(self.get_magicsbykey(magics,'onlyruncmd'))>0):
            bcancel_exec=True
            return retinfo
        if len(self.get_magicsBvalue(magics,'replcmdmode'))>0:
            bcancel_exec=True
            retinfo= self.send_replcmd(code, silent, store_history,user_expressions, allow_stdin)
            return retinfo
        if(len(self.get_magicsSvalue(magics,'runprg'))>0):
            retinfo=self.do_execute_runprg(code, magics,silent, store_history,
                   user_expressions, allow_stdin)
            self.cleanup_files()
            return retinfo
        if(self.runfiletype=='script'):
            retinfo=self.do_execute_script(code, magics,silent, store_history,
                   user_expressions, allow_stdin)
        elif(self.runfiletype=='class'):
            retinfo=self.do_execute_class(code, magics,silent, store_history,
                   user_expressions, allow_stdin=True)
        elif(self.runfiletype=='exe'):
            retinfo=self.do_execute_script(code, magics,silent, store_history,
                   user_expressions, allow_stdin)
        self.cleanup_files()
        return retinfo
    def do_shutdown(self, restart):
        self.g_chkreplexit=False
        self.chk_replexit_thread.join()
        # self.onkernelshutdown()
        self.cleanup_files()
#####################################################################
##接口发现并注册
##//%test
##
    ISplugins={"0":[],
         "1":[],
         "2":[],
         "3":[],
         "4":[],
         "5":[],
         "6":[],
         "7":[],
         "8":[],
         "9":[]}
    IDplugins={"0":[],
         "1":[],
         "2":[],
         "3":[],
         "4":[],
         "5":[],
         "6":[],
         "7":[],
         "8":[],
         "9":[]}
    IBplugins={"0":[],
         "1":[],
         "2":[],
         "3":[],
         "4":[],
         "5":[],
         "6":[],
         "7":[],
         "8":[],
         "9":[]}
    ICodePreprocs={"0":[],
         "1":[],
         "2":[],
         "3":[],
         "4":[],
         "5":[],
         "6":[],
         "7":[],
         "8":[],
         "9":[]}
    plugins=[ISplugins,IDplugins,IBplugins]
    def pluginRegister(self,obj):
        if obj==None:return
        try:
            obj.setKernelobj(obj,self)
            priority=obj.getPriority(obj)
            if not inspect.isabstract(obj) and issubclass(obj,IStag):
                self.ISplugins[str(priority)]+=[obj]
            elif not inspect.isabstract(obj) and issubclass(obj,IDtag):
                self.IDplugins[str(priority)]+=[obj]
            elif not inspect.isabstract(obj) and issubclass(obj,IBtag):
                self.IBplugins[str(priority)]+=[obj]
            elif not inspect.isabstract(obj) and issubclass(obj,ICodePreproc):
                self.ICodePreprocs[str(priority)]+=[obj]
        except Exception as e:
            pass
        pass
    def pluginISList(self):
        self._log("---------pluginISList--------\n")
        for key,value in self.ISplugins.items():
            # print( key +":"+str(len(value))+"\n")
            for obj in value:
                self._log(obj.getName(obj)+"\n")
    def pluginIDList(self):
        self._log("---------pluginIDList--------\n")
        for key,value in self.IDplugins.items():
            # print( key +":"+str(len(value))+"\n")
            for obj in value:
                self._log(obj.getName(obj)+"\n")
    def pluginIBList(self):
        self._log("---------pluginIBList--------\n")
        for key,value in self.IBplugins.items():
            # print( key +":"+str(len(value))+"\n")
            for obj in value:
                self._log(obj.getName(obj)+"\n")
    def onkernelshutdown(self,restart):
        for key,value in self.IDplugins.items():
            # print( key +":"+str(len(value))+"\n")
            for obj in value:
                try:
                    newline=obj.on_shutdown(obj,restart)
                    if newline=='':break
                except Exception as e:
                    pass
                finally:pass
    def callIDplugin(self,magics,line):
        newline=line
        for key,value in self.IDplugins.items():
            # print( key +":"+str(len(value))+"\n")
            for obj in value:
                try:
                    newline=obj.on_IDpReorgCode(obj,magics,newline)
                    if newline=='':break
                except Exception as e:
                    pass
                finally:pass
        return newline
    def init_plugin(self):
        mypath = os.path.dirname(os.path.abspath(__file__))
        idir=os.path.join(mypath,'../plugins')
        sys.path.append(mypath)
        sys.path.append(idir)
        for f in os.listdir(idir):
            if os.path.isfile(os.path.join(idir,f)):
                try:
                    name=os.path.splitext(f)[0]
                    if name!='pluginmng' and name!='kernel' and(spec := importlib.util.find_spec(name)) is not None:
                        module = importlib.import_module(name)
                        for name1, obj in inspect.getmembers(module,
                            lambda obj: 
                                callable(obj) 
                                and inspect.isclass(obj) 
                                and not inspect.isabstract(obj) 
                                and issubclass(obj,ITag)
                                ):
                            # self._write_to_stdout("\n"+obj.__name__+"\n")
                            self.pluginRegister(obj)
                    else:
                        pass
                except Exception as e:
                    pass
                finally:
                    pass
class MyLuaKernel(MyKernel):
    implementation = 'jupyter-MyLua-kernel'
    implementation_version = '1.0'
    language = 'lua'
    language_version = ''
    language_info = {'name': 'lua',
                     'version': sys.version.split()[0],
                     'mimetype': 'text/lua',
                     'codemirror_mode': {
                        'name': 'ipython',
                        'version': sys.version_info[0]
                     },
                     'pygments_lexer': 'ipython%d' % 3,
                     'nbconvert_exporter': 'Lua',
                     'file_extension': '.ts'}
    runfiletype='script'
    banner = "MyLua kernel.\n" \
             "Uses lua, creates source code files and executables in temporary folder.\n"
    kernelinfo="[MyLua]"
    main_head = "\n" \
            "\n" \
            "int main(List<String> arguments){\n"
    main_foot = "\nreturn 0;\n}"
##//%include:src/comm_attribute.py
    def __init__(self, *args, **kwargs):
        super(MyLuaKernel, self).__init__(*args, **kwargs)
        self._allow_stdin = True
        self.readOnlyFileSystem = False
        self.bufferedOutput = True
        self.linkMaths = True # always link math library
        self.wAll = True # show all warnings by default
        self.wError = False # but keep comipiling for warnings
        
#################
    def compile_with_luac(self, source_filename, binary_filename, cflags=None, ldflags=None,env=None,magics=None):
        outfile=binary_filename
        orig_cflags=cflags
        orig_ldflags=ldflags
        index=0
        for s in cflags:
            if s.startswith('-o'):
                if(len(s)>2):
                    outfile=s[2:]
                    del cflags[index]
                else:
                    outfile=cflags[cflags.index('-o')+1]
                    if outfile.startswith('-'):
                        outfile=binary_filename
                    del cflags[cflags.index('-o')+1]
                    del cflags[cflags.index('-o')]
            binary_filename=outfile
            index+=1
        args=[]
        if magics!=None and len(self.addkey2dict(magics,'ccompiler'))>0:
            args = magics['ccompiler'] + orig_cflags +[source_filename] + orig_ldflags
        else:
            args = ['luac'] + cflags+ ['-o', binary_filename]+[source_filename]+ ldflags
        # self._log(''.join((' '+ str(s) for s in args))+"\n")
        return self.create_jupyter_subprocess(args,env=env,magics=magics),binary_filename,args
    def _exec_luac_(self,source_filename,magics):
        self._logln('Generating executable file')
        with self.new_temp_file(suffix='.out') as binary_file:
            
            magics['status']='compiling'
            p,outfile,luaccmd = self.compile_with_luac(
                source_filename, 
                binary_file.name,
                self.get_magicsSvalue(magics,'cflags'),
                self.get_magicsSvalue(magics,'ldflags'),
                self.get_magicsbykey(magics,'env'),
                magics=magics)
            returncode=p.wait_end(magics)
            p.write_contents()
            magics['status']=''
            binary_file.name=os.path.join(os.path.abspath(''),outfile)
            if returncode != 0:  # Compilation failed
                self._logln(''.join((str(s) for s in luaccmd))+"\n",3)
                self._logln("C compiler exited with code {}, the executable will not be executed".format(returncode),3)
                # delete source files before exit
                os.remove(source_filename)
                os.remove(binary_file.name)
        return p.returncode,binary_file.name
##do_runcode
    def do_runcode(self,return_code,fil_ename,magics,code, silent, store_history=True,
                    user_expressions=None, allow_stdin=True):
        return_code=return_code
        fil_ename=fil_ename
        bcancel_exec=False
        retinfo=self.get_retinfo()
        retstr=''
        ##代码运行前 options
        options=self.get_magicsSvalue(magics,'options')
        luacmd=['lua']
        if len(options)>0:
            luacmd+=options
        p = self.create_jupyter_subprocess(luacmd+[fil_ename]+ magics['_st']['args'],cwd=None,shell=False,env=self.addkey2dict(magics,'env'),magics=magics)
        #p = self.create_jupyter_subprocess([binary_file.name]+ magics['args'],cwd=None,shell=False)
        #p = self.create_jupyter_subprocess([self.master_path, binary_file.name] + magics['args'],cwd='/tmp',shell=True)
        self.g_rtsps[str(p.pid)]=p
        return_code=p.returncode
        ##代码启动后
        bcancel_exec,retstr=self.raise_plugin(code,magics,return_code,fil_ename,3,2)
        # if bcancel_exec:return bcancel_exec,retinfo,magics, code,fil_ename,retstr
        
        if len(self.addkey2dict(magics,'showpid'))>0:
            self._write_to_stdout("The process PID:"+str(p.pid)+"\n")
        return_code=p.wait_end(magics)
        # del self.g_rtsps[str(p.pid)]
        # p.write_contents(magics)
        ##
        ##调用接口
        return_code=p.returncode
        ##代码运行结束
        if p.returncode != 0:
            self._log("Executable exited with code {}".format(p.returncode),2)
        return bcancel_exec,retinfo,magics, code,fil_ename,retstr
##do_compile_code
    def do_compile_code(self,return_code,fil_ename,magics,code, silent, store_history=True,
                    user_expressions=None, allow_stdin=True):
        return_code=0
        fil_ename=fil_ename
        sourcefilename=fil_ename
        bcancel_exec=False
        retinfo=self.get_retinfo()
        retstr=''
        returncode,binary_filename=self._exec_luac_(fil_ename,magics)
        fil_ename=binary_filename
        return_code=returncode
        
        if returncode!=0:return  True,retinfo, code,fil_ename,retstr
        return bcancel_exec,retinfo,magics, code,fil_ename,retstr
##do_create_codefile
    def do_create_codefile(self,magics,code, silent, store_history=True,
                    user_expressions=None, allow_stdin=True):
        return_code=0
        fil_ename=''
        bcancel_exec=False
        retinfo=self.get_retinfo()
        retstr=''
        source_file=self.create_codetemp_file(magics,code,suffix='.lua')
        newsrcfilename=source_file.name
        fil_ename=newsrcfilename
        return_code=True
        return bcancel_exec,self.get_retinfo(),magics, code,fil_ename,retstr
##do_preexecute
    def do_preexecute(self,code,magics,silent, store_history=True,
                user_expressions=None, allow_stdin=False):
        bcancel_exec=False
        retinfo=self.get_retinfo()
        
        return bcancel_exec,retinfo,magics, code
