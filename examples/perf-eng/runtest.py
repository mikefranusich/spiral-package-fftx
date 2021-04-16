#! python

##  Copyright (c) 2018-2021, Carnegie Mellon University
##  See LICENSE for details

##  This script reads a file, cube-sizes.txt, that contains several cube size
##  specifications for the 3D DFT.  This script will:
##      Generate a SPIRAL script using the DFT size spec
##      Run SPIRAL to generate the CUDA code
##      Save the generated code (to sub-directory srcs)
##      Compile the CUDA code for the DFT (install in sub-directory exes)
##      Build a script to run all the generated code (timescript.sh)
##  

import sys
import subprocess
import os, stat
import re
import shutil

_inclfile = 'mddft3d.cu'
_funcname = 'mddft3d'
_timescript = 'timescript.sh'

##  Setup 'empty' tiing script
timefd = open ( _timescript, 'w' )
timefd.write ( '#! /bin/bash \n\n' )
timefd.write ( '##  Timing script to run Cuda code for various transform sizes \n\n' )
timefd.close()
_mode = stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
os.chmod ( _timescript, _mode )

with open ( 'cube-sizes.txt', 'r' ) as fil:
    for line in fil.readlines():
        print ( 'Line read = ' + line )
        testscript = open ( 'testscript.g', 'w' )
        testscript.write ( line )
        testscript.close()
        line = re.sub ( '.*\[', '', line )               ## drop "szcube := ["
        line = re.sub ( '\].*', '', line )               ## drop "];"
        line = re.sub ( ' *', '', line )                 ## compress out white space
        line = line.rstrip()                             ## remove training newline
        dims = re.split ( ',', line )
        _dimx = dims[0]
        _dimy = dims[1]
        _dimz = dims[2]

        ##  Generate the SPIRAL script: cat testscript.g, mddft-cuda-frame.g,
        ##  and mddft-meas.g (if want to call CMeasure())
        _spiralhome = os.environ.get('SPIRAL_HOME')
        _catfils = _spiralhome + '/gap/bin/catfiles.py'
        cmdstr = 'python ' + _catfils + ' myscript.g testscript.g mddft-cuda-frame.g' ## mddft-meas.g'
        result = subprocess.run ( cmdstr, shell=True, check=True )
        res = result.returncode

        ##  Generate the code by running SPIRAL
        if sys.platform == 'win32':
            cmdstr = _spiralhome + '/spiral.bat < myscript.g'
        else:
            cmdstr = _spiralhome + '/spiral < myscript.g'
            
        result = subprocess.run ( cmdstr, shell=True, check=True )
        res = result.returncode

        ##  Create the srcs directory (if it doesn't exist)
        srcs_dir = 'srcs'
        isdir = os.path.isdir ( srcs_dir )
        if not isdir:
            os.mkdir ( srcs_dir )

        ##  Copy the generated CUDA source file to srcs
        _filenamestem = '-' + _dimx + 'x' + _dimy + 'x' + _dimz
        _destfile = 'srcs/' + _funcname + _filenamestem + '.cu'
        shutil.copy ( _inclfile, _destfile )

        ##  Check if auxilliary files were generated and copy to srcs if so
        _artifact = _funcname + '.rt.g'
        isfile = os.path.isfile ( _artifact )         ## was ruletree generated
        if isfile:
            _destfile = 'srcs/' + _funcname + _filenamestem + '.rt.g'
            shutil.copy ( _artifact, _destfile )

        _artifact = _funcname + '.ss.g'
        isfile = os.path.isfile ( _artifact )         ## was sumsruletree generated
        if isfile:
            _destfile = 'srcs/' + _funcname + _filenamestem + '.ss.g'
            shutil.copy ( _artifact, _destfile )

        _artifact = _funcname + '.spl.g'
        isfile = os.path.isfile ( _artifact )         ## was SPL generated
        if isfile:
            _destfile = 'srcs/' + _funcname + _filenamestem + '.spl.g'
            shutil.copy ( _artifact, _destfile )

        ##  Create the build directory (if it doesn't exist)
        build_dir = 'build'
        isdir = os.path.isdir ( build_dir )
        if not isdir:
            os.mkdir ( build_dir )

        ##  Run cmake and build to build the code

        cmdstr = 'rm -rf * && cmake -DINCLUDE_DFT=' + _inclfile + ' -DFUNCNAME=' + _funcname
        cmdstr = cmdstr + ' -DDIM_M=' + _dimx + ' -DDIM_N=' + _dimy + ' -DDIM_K=' + _dimz

        os.chdir ( build_dir )

        if sys.platform == 'win32':
            cmdstr = cmdstr + ' .. && cmake --build . --config Release --target install'
        else:
            cmdstr = cmdstr + ' .. && make install'

        print ( cmdstr )
        ##  sys.exit (0)                    ## testing script, stop here

        result = subprocess.run ( cmdstr, shell=True, check=True )
        res = result.returncode

        if (res != 0):
            print ( result )
            sys.exit ( res )

        os.chdir ( '..' )

        timefd = open ( _timescript, 'a' )
        timefd.write ( '##  Cube = [' + _dimx + ', ' + _dimy + ', ' + _dimz + ' ]\n' )
        if sys.platform == 'win32':
            _exename = './exes/dftdriver' + _filenamestem + '.exe'
        else:
            _exename = './exes/dftdriver' + _filenamestem

        timefd.write ( _exename +  '\n\n' )
        timefd.close()

        ##  Uncomment this section if you want to run (time) each DFT as it is generated
        # result = subprocess.run ( _exename )
        # res = result.returncode
        # if (res != 0):
        #     print ( result )
        #     sys.exit ( res )

sys.exit (0)

