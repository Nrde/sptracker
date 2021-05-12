
# This file is part of sptracker.
#
#    sptracker is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    sptracker is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Foobar.  If not, see <http://www.gnu.org/licenses/>.

import zipfile
import glob
import os
import os.path
import pathlib
import shutil
import subprocess
import sys
import time

exec(open("release_settings.py").read())

test_release_process = False

# Only stracker comes in Linux and Windows flavors, so don't put
# OS on the others for now.
build_ptracker = False
build_stracker_windows = False
build_stracker_linux = False
build_stracker_packager = False

if "--test_release_process" in sys.argv:
    sys.argv.remove("--test_release_process")
    print("Test mode, no release will be done")
    test_release_process = True

ptracker_only = False
if "--ptracker_only" in sys.argv:
    sys.argv.remove('--ptracker_only')
    ptracker_only = True
    test_release_process = True

stracker_only = False
if "--stracker_only" in sys.argv:
    sys.argv.remove('--stracker_only')
    stracker_only = True
    test_release_process = True

stracker_packager_only = False
if "--stracker_packager_only" in sys.argv:
    sys.argv.remove('--stracker_packager_only')
    stracker_packager_only = True
    test_release_process = True

linux_only = False
if "--linux_only" in sys.argv:
    sys.argv.remove('--linux_only')
    linux_only = True
    test_release_process = True

windows_only = False
if "--windows_only" in sys.argv:
    sys.argv.remove('--windows_only')
    windows_only = True
    test_release_process = True

if ptracker_only or stracker_only or stracker_packager_only:
    if ptracker_only:
        build_ptracker = True
    if stracker_only:
        build_stracker_linux = True
        build_stracker_windows = True
    if stracker_packager_only:
        build_stracker_packager = True
else:
    build_ptracker = True
    build_stracker_windows = True
    build_stracker_linux = True
    build_stracker_packager = True

if windows_only and linux_only:
    print("Error: --windows_only and --linux_only are mutually exclusive")
    sys.exit(1)
if windows_only:
    build_stracker_linux = False
if linux_only:
    build_ptracker = False
    build_stracker_windows = False
    build_stracker_packager = False

if len(sys.argv) != 2:
    print ("Usage: create_release [--test_release_process] [--ptracker_only] [--stracker_only] [--linux_only] [--windows_only] [--stracker_packager_only] <version_number>")
    sys.exit(1)

if not test_release_process:
    git_status = subprocess.check_output([git, "status", "-s", "-uno"], universal_newlines=True)
    if not git_status.strip() == "":
        print ("git sandbox is dirty. Check in your changes first.")
        print (git_status)
        sys.exit(1)

version = sys.argv[1]

# Create virtualenv in case it doesn't exist yet
subprocess.run(["virtualenv", "env/windows"], check=True, universal_newlines=True)

# Use virtualenv
exec(open("env/windows/Scripts/activate_this.py").read())

if not linux_only:
    do_install = True
    lastcheck = pathlib.Path('env') / 'windows' / 'lastcheck'
    try:
        # only do the install/upgrade if the age is higher than a day
        do_install = (time.time() - lastcheck.stat().st_mtime) > 86400
    except:
        # or if it hasn't been done yet
        pass
    if do_install:
        # Install/upgrade packages
        subprocess.run(["env\windows\Scripts\pip.exe", "install", "--upgrade", "bottle"], check=True, universal_newlines=True)
        subprocess.run(["env\windows\Scripts\pip.exe", "install", "--upgrade", "cherrypy"], check=True, universal_newlines=True)
        subprocess.run(["env\windows\Scripts\pip.exe", "install", "--upgrade", "psycopg2"], check=True, universal_newlines=True)
        subprocess.run(["env\windows\Scripts\pip.exe", "install", "--upgrade", "python-dateutil"], check=True, universal_newlines=True)
        subprocess.run(["env\windows\Scripts\pip.exe", "install", "--upgrade", "wsgi-request-logger"], check=True, universal_newlines=True)
        subprocess.run(["env\windows\Scripts\pip.exe", "install", "--upgrade", "simplejson"], check=True, universal_newlines=True)
        subprocess.run(["env\windows\Scripts\pip.exe", "install", "--upgrade", "pyinstaller"], check=True, universal_newlines=True)
        subprocess.run(["env\windows\Scripts\pip.exe", "install", "--upgrade", "PySide2"], check=True, universal_newlines=True)
        # Since this downloads the entire file and is version locked, don't do it if already installed
        try:
            subprocess.run(["env\windows\Scripts\pip.exe", "show", "aspw"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            subprocess.run(["env\windows\Scripts\pip.exe", "install", "https://github.com/rogerbinns/apsw/releases/download/3.35.4-r1/apsw-3.35.4-r1.zip",
                            "--global-option=fetch", "--global-option=--version", "--global-option=3.35.4", "--global-option=--all",
                            "--global-option=build", "--global-option=--enable-all-extensions"], check=True,universal_newlines=True)
        lastcheck.touch()

if build_ptracker:

    shutil.rmtree("dist", True)
    assert not os.path.exists("dist")

    f = open("ptracker_lib/__init__.py", "w")
    f.write("version = '%s'" % version)
    f.close()
    f = open("stracker/stracker_lib/__init__.py", "w")
    f.write("version = '%s'" % version)
    f.close()

    if not test_release_process:
        git_status = subprocess.check_output([git, "status", "-s", "-uno"], universal_newlines=True)
        if not git_status.strip() == "":
            svn_commit = subprocess.check_output([git, "commit", "-a", "-s", "-m", "prepare release %s" % version])

    ptracker_py_files = """\
ptracker.py
ptracker_lib/__init__.py
ptracker_lib/helpers.py
ptracker_lib/acsim.py
ptracker_lib/profiler.py
ptracker_lib/sim_info.py
ptracker_lib/client_server/__init__.py
ptracker_lib/client_server/ac_client_server.py
ptracker_lib/client_server/client_server.py
ptracker_lib/client_server/client_server_impl.py""".split("\n")

    ptracker_pyd_files = """\
ptracker_lib/stdlib/_ctypes.pyd
ptracker_lib/stdlib/unicodedata.pyd
ptracker_lib/stdlib/CreateFileHook.dll
ptracker_lib/stdlib64/_ctypes.pyd
ptracker_lib/stdlib64/CreateFileHook.dll""".split("\n")

    def patch_ptracker_server(files):
        files = sorted(files)
        import hashlib
        hashfun = hashlib.sha1()
        for f in files:
            hashfun.update(open(f, 'rb').read())
        nf = open("ptracker-server-dist.py", "w")
        nf.write("# automatically generated by create_release.py\n")
        nf.write("files = " + repr(files) + "\n")
        nf.write("prot = " + repr(hashfun.digest()) + "\n")
        nf.write(open("ptracker-server.py", "r").read())

    patch_ptracker_server(ptracker_py_files)

    print("------------------- Building ptracker.exe -------------------------------")
    assert(os.path.isdir(f"{ac_install_dir}\\apps\python\system"))
    # this is to help ptracker.exe load modules from the user's AC install dir
    os.environ['PYTHONPATH'] = r"..\system;..\..\system"
    subprocess.run(["env\windows\Scripts\pyinstaller.exe",
                    # "--debug=bootloader",
                    "--windowed",
                    "--name", "ptracker", "--clean", "-y", "--onefile", 
                    "--paths", f"{ac_install_dir}\\apps\python\system",
                    "--path", "stracker", "--path", "stracker/externals",
                    "ptracker-server-dist.py"],
                   check=True, universal_newlines=True)

    def checksum(buffer):
        sign = buffer[:0x12] + buffer[(0x12+4):]
        import hashlib, struct
        hashfun = hashlib.sha1()
        hashfun.update(sign)
        digest = hashfun.digest()
        e1, = struct.unpack_from('B', digest)
        p = e1*(len(digest)-4)//255
        cs = digest[p:(p+4)]
        return cs

    # patch generated .exe file with a checksum
    fexe = open("dist/ptracker.exe", "rb")
    buffer = fexe.read()
    assert buffer[0x12:(0x12+4)] == b"\x00"*4
    fexe.close()
    cs = checksum(buffer)
    buffer = buffer[:0x12] + cs + buffer[(0x12+4):]
    fexe = open("dist/ptracker.exe", "wb")
    fexe.write(buffer)
    fexe.close()

    class nsis_builder:
        def __init__(self, target, script):
            self.temp_idx = 0
            self.target = target
            self.script = script
            self.files = {}

        def unslashify(self, s):
            return s.replace('/', '\\')

        def writestr(self, target, str):
            tfile = "nsis_temp_files%d" % self.temp_idx
            self.temp_idx += 1
            open(tfile, "wb").write(str)
            self.files[self.unslashify(target)] = self.unslashify(tfile)

        def write(self, file, target):
            self.files[self.unslashify(target)] = self.unslashify(file)

        def close(self):
            s = open(self.script + ".in", "r").read()
            dirs = set([os.path.split(outfn)[0] for outfn in self.files.keys()])
            subst = {
                'target':self.target,
                'DirStatements':"\n".join([r'CreateDirectory $INSTDIR\%s'%d for d in dirs]),
                'FileStatements':"\n".join([r'File "/oname=$INSTDIR\%s" %s'%(outfn, infn) for outfn,infn in self.files.items()]),
            }
            open(self.script, "w").write(s % subst)
            subprocess.run([r"C:\Program Files (x86)\NSIS\makensis.exe", self.script], check=True, universal_newlines=True)

    r = nsis_builder("versions/ptracker-V%s.exe" % version, "ptracker.nsh") 

    r.writestr(os.path.join("apps","python","ptracker","ptracker_lib","executable.py"),
               'ptracker_executable = ["apps/python/ptracker/dist/ptracker.exe"]\n'.encode(encoding="ascii"))

    files =( ptracker_py_files + ptracker_pyd_files
           + glob.glob("images/*.png")
           + glob.glob("images/*/*.png")
           + glob.glob("images/*/*.ini")
           + glob.glob("sounds/*.wav")
           + ["dist/ptracker.exe"]
           )

    icons = glob.glob("icons/*.png")

    http_static = (
              glob.glob("stracker/http_static/bootstrap/css/bootstrap.min.css")
            + glob.glob("stracker/http_static/bootstrap/css/bootstrap-datepicker.css")
            + glob.glob("stracker/http_static/bootstrap/css/bootstrap-multiselect.css")
            + glob.glob("stracker/http_static/bootstrap/css/bootstrap-theme.min.css")
            + glob.glob("stracker/http_static/bootstrap/css/custom.css")
            + glob.glob("stracker/http_static/bootstrap/css/fileinput.min.css")
            + glob.glob("stracker/http_static/bootstrap/css/sticky-footer.css")
            + glob.glob("stracker/http_static/bootstrap/fonts/glyphicons-halflings-regular.ttf")
            + glob.glob("stracker/http_static/bootstrap/js/bootstrap.min.js")
            + glob.glob("stracker/http_static/bootstrap/js/bootstrap-datepicker.js")
            + glob.glob("stracker/http_static/bootstrap/js/bootstrap-multiselect.js")
            + glob.glob("stracker/http_static/bootstrap/js/fileinput.min.js")
            + glob.glob("stracker/http_static/img/*.png")
            + glob.glob("stracker/http_static/jquery/jquery.min.js")
            )

    for f in files:
        t = os.path.join("apps", "python", "ptracker", f)
        print("adding",f,"as",t)
        r.write(f, t)

    for f in icons:
        t = os.path.join("content", "gui", f)
        print("adding",f,"as",t)
        r.write(f, t)

    for f in http_static:
        t = os.path.join("apps", "python", "ptracker", f[f.find("/")+1:])
        print("adding",f,"as",t)
        r.write(f, t)

    r.close()

# remove build / dist path
#if os.path.exists("dist"):
#    shutil.rmtree("dist")
#if os.path.exists("build"):
#    shutil.rmtree("build")

if build_stracker_windows or build_stracker_linux or build_stracker_packager:

    os.chdir("stracker")
    if os.path.exists('dist'):
        shutil.rmtree('dist')

    r = zipfile.ZipFile("../versions/stracker-V%s.zip" % version, "w")

    if build_stracker_windows:
        print("------------------- Building stracker.exe -------------------------------")
        subprocess.run(["../env/windows/Scripts/pyinstaller.exe", "--name", "stracker",
                        "--clean", "-y", "--onefile", "--exclude-module", "http_templates",
                        "--hidden-import", "cherrypy.wsgiserver.wsgiserver3",
                        "--hidden-import", "psycopg2", "--path", "..", "--path", "externals",
                        "stracker.py"],
                       check=True, universal_newlines=True)
        if os.path.exists('stracker-default.ini'):
            os.remove('stracker-default.ini')
        subprocess.run([r"dist\stracker.exe", "--stracker_ini", "stracker-default.ini"], universal_newlines=True)
        assert(os.path.isfile('stracker-default.ini'))
        r.write("dist/stracker.exe", "stracker.exe")
        r.write("stracker-default.ini", "stracker-default.ini")

    if build_stracker_packager:
        print("------------------- Building stracker-packager.exe ----------------------")
        subprocess.run(["../env/windows/Scripts/pyinstaller.exe", "--clean", "-y", "--onefile", "--path", "..", "--path", "externals", "stracker-packager.py"], check=True, universal_newlines=True)
        r.write("dist/stracker-packager.exe", "stracker-packager.exe")

    os.chdir("..")

    r.write("stracker/README.txt", "README.txt")
    r.write("www/stracker_doc.htm", "stracker/documentation.htm")
    r.write("stracker/start-stracker.cmd", "start-stracker.cmd")

    http_data = (glob.glob("stracker/http_static/bootstrap/*/*") +
                 glob.glob("stracker/http_static/img/*.png") +
                 glob.glob("stracker/http_static/jquery/*.js") +
                 glob.glob("stracker/http_static/stracker/js/graphs/*.js") +
                 glob.glob("stracker/http_templates/*.py"))
    for src in http_data:
        tgt = src[len("stracker/"):]
        print("adding",src,"as",tgt)
        r.write(src, tgt)

    if build_stracker_linux:
        print(REMOTE_BUILD_CMD)
        rbuild_out = subprocess.run(REMOTE_BUILD_CMD, check=True, universal_newlines=True)
        if not REMOTE_COPY_RESULT is None:
            rcopy_out = subprocess.run(REMOTE_COPY_RESULT, check=True, universal_newlines=True)

        r.write("stracker/stracker_linux_x86.tgz", "stracker_linux_x86.tgz")
