#!/usr/bin/python
"""
Opal client for remote APBS execution.

Written by Samir Unni, Dave Gohara, Nathan Baker, Yong Huang based on example code from Sriram Krishnan

----------------------------------------------------------------------
    APBS -- Adaptive Poisson-Boltzmann Solver
    Version 1.3
    
    Nathan A. Baker (baker@biochem.wustl.edu)
    Dept. Biochemistry and Molecular Biophysics
    Center for Computational Biology
    Washington University in St. Louis
    
    Additional contributing authors listed in the code documentation.
    
    Copyright (c) 2002-2010, Washington University in St. Louis.
    Portions Copyright (c) 2002-2010.  Nathan A. Baker
    Portions Copyright (c) 1999-2002.  The Regents of the University of California.
    Portions Copyright (c) 1995.  Michael Holst
    
    All rights reserved.
    
    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:
    
    * Redistributions of source code must retain the above copyright notice, this
    list of conditions and the following disclaimer.
    
    * Redistributions in binary form must reproduce the above copyright notice,
    this list of conditions and the following disclaimer in the documentation
    and/or other materials provided with the distribution.
    
    * Neither the name of Washington University in St. Louis nor the names of its
    contributors may be used to endorse or promote products derived from this
    software without specific prior written permission.
    
    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
    "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
    LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
    A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
    CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
    EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
    PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
    PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
    LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
    NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
    SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
----------------------------------------------------------------------
    APBS uses FETK (the Finite Element ToolKit) to solve the
    Poisson-Boltzmann equation numerically.  FETK is a portable collection
    of finite element modeling class libraries developed by the Michael Holst
    research group and written in an object-oriented form of C.  FEtk is
    designed to solve general coupled systems of nonlinear partial differential
    equations using adaptive finite element methods, inexact Newton methods,
    and algebraic multilevel methods.  More information about FEtk may be found
    at <http://www.FEtk.ORG>.
----------------------------------------------------------------------
    APBS also uses Aqua to solve the Poisson-Boltzmann equation numerically.
    Aqua is a modified form of the Holst group PMG library <http://www.FEtk.ORG>
    which has been modified by Patrice Koehl
    <http://koehllab.genomecenter.ucdavis.edu/> for improved efficiency and
    memory usage when solving the Poisson-Boltzmann equation.
----------------------------------------------------------------------
    Please cite your use of APBS as:
    
    Baker NA, Sept D, Joseph S, Holst MJ, McCammon JA. Electrostatics of
    nanosystems: application to microtubules and the ribosome. Proc.
    Natl. Acad. Sci. USA 98, 10037-10041 2001.
----------------------------------------------------------------------
"""
__date__  = "3 September 2009"
__author__ = "Samir Unni, Dave Gohara, Nathan Baker, Yong Huang"
__version__ = "1.3"

import sys
from sys import stdout, stderr
import time
import httplib, urllib
import string
import os, os.path
import subprocess
import getopt

########################################################################
#### USERS SHOULD ADD THEIR OWN PATH TO THE APBS INSTALLATION HERE! ####
# This path variable is only needed if you are installing a binary distribution of APBS.  It should point to
# the location where APBS was installed; e.g., the directory that contains the APBS bin, include, lib, and
# share sub-directories.  The following value is just an example and may not be appropriate for your system
# depending on where you installed APBS:
userPath = "/usr/local/apbs-1.3"
########################################################################

#### Here are our help and credit messages
creditString = __doc__
helpString = "\n\n\
    This driver program calculates electrostatic potentials, energies, and forces\n\
    using both multigrid and finite element methods.  It is invoked as:\n\
    \n\
	ApbsClient.py [options] apbs.in\n\
    \n\
    where apbs.in is a formatted input file and [options] are:\n\
    \n\
    --output-file=<name>     Enables output logging to the path listed in <name>.\n\
    --output-format=<type>   Specifies format for logging.  Options for type are\n\
      either \"xml\" or \"flat\".   Uses flat-file format if --output-format is not used.\n\
    --help                   Display this help information.\n\
    \n\
    Options specific to the Opal web client are:\n\
    \n\
    --fetch=<output file location>\n\
                             Used to specify the location to which the files should be\n\
                             downloaded. Files are downloaded to current directory if\n\
                             <output file location> or the entire flag is omitted when\n\
                             expected.\n\
    --library-location=<directory>\n\
                             This path variable is only needed if you are using a binary\n\
                             distribution of APBS.  It should point to the location where\n\
                             APBS was installed; e.g., the directory that contains the APBS\n\
                             bin, include, lib, and share sub-directories.  The following\n\
                             value is just an example and may not be appropriate for your\n\
                             system, depending on where you installed APBS:\n\
                               --library-location=/usr/local/apbs-1.3\n\
                             Note that you can also edit this Python file to eliminate the\n\
                             need to specify this option.\n\
    --job-id=<job ID>        Specifies the job ID of the run for which results are to be\n\
                             downloaded. Expects the '--fetch' flag to be present as well.\n\
    --no-fetch               Disables fetching of files following (only) a blocked run.\n\
    --non-blocking           Disables blocking and outputs a URL at which the data can be\n\
                             retreived later.\n\
    --service-location=<URL> Specifies the location of the Opal server.  Defaults to\n\
                             http://kryptonite.nbcr.net/opal2/services/apbs_1.3\n\
    --local                  Perform a local APBS run using whatever APBS executable is\n\
                             available in the path \
\n----------------------------------------------------------------------\n\
\n"

def processOptions():
	""" A function that transforms command line options into a dictionary for further processing.  However,
	presence of the -h or --help option causes the script to print help information and exit. """
	global helpString
	global service_url
	shortOptions = "h"
	longOptions = ["help", "local", "library-location=", "output-format=", "output-file=", "fetch=", "job-id=", "no-fetch", "non-blocking", "service-location="]
	opts, args = getopt.getopt(sys.argv[1:], shortOptions, longOptions)
	optionDict = {}
	for o, a in opts:
		if o in ("-h", "--help"):
			stdout.write("%s\n" % helpString)
			sys.exit()
		elif o == "--local":
			optionDict["local"] = True
		elif o == "--output-format":
			if a in ("xml", "flat"):
				optionDict["output-format"] = a
			else:
				stderr.write("Invalid argument (%s) for --output-format!\n" % a)
				sys.exit(13)
		elif o == "--output-file":
			optionDict["output-file"] = a
		elif o == "--fetch":
			optionDict["fetch"] = a
		elif o == "--job-id":
			optionDict["job-id"] = a
		elif o == "--no-fetch":
			optionDict["no-fetch"] = True
		elif o == "--non-blocking":
			optionDict["non-blocking"] = True
		elif o == "--service-location":
			optionDict["service-location"] = a
			service_url = optionDict["service-location"]
		elif o == "--library-location":
			optionDict["library-location"] = a
		else:
			stderr.write("Ignoring unrecognized option %s.\n" % o)
	optionDict["args"] = args
	if not (optionDict.has_key("fetch") and optionDict.has_key("job-id")):
		if (optionDict.has_key("fetch") or optionDict.has_key("job-id")):
			stderr.write("Error.  Please use both \"--fetch\" and \"--job-id\" flags together.\n")
			stderr.write("Ignoring these flags...\n")
	return optionDict

#### Setup a list of paths to search for Opal-related modules ####
sys.path.append(userPath)

# This is the path determined by autoconf/automake
configPath = "/Users/ponder/lib/python2.7/site-packages"
modPaths = [configPath, os.path.join(configPath, "ZSI")]
sys.path = sys.path + modPaths

# This is the current working directory
sys.path.append(os.getcwd())

# This is an attempt to decipher the path of this script if not in the current directory (and not in the path)
myExecPath = sys.argv[0]
pathSplit = os.path.split(myExecPath)
libPath = os.path.join(pathSplit[0], "../lib/python2.5/site-packages")
sys.path.append(os.path.abspath(libPath))

# Now check to see if the user specified the APBS installation path on the command line
if __name__ == "__main__":
	optDict = processOptions()
	if optDict.has_key("library-location"):
		sys.path.append(optDict["library-location"])
try:
	import ZSI
	from AppService_client import AppServiceLocator, AppServicePortTypeSoapBindingSOAP, getAppMetadataRequest, launchJobRequest, queryStatusRequest, getOutputsRequest, launchJobBlockingRequest, getOutputAsBase64ByNameRequest
	from AppService_types import ns0
	from ZSI.TC import String
except ImportError, errstr:
	stderr.write("ImportError:  %s\n" % errstr)
	stderr.write("ApbsClient.py could not find the necessary Python libraries in any of the following locations:\n")
	for path in sys.path:
		stderr.write("\t%s\n" % path)
	stderr.write("Please edit the ApbsClient.py file using your favorite text editor and add the location\n")
	stderr.write("of your APBS installation to the section of the ApbsClient.py file labeled\n")
	stderr.write("\"#### USERS SHOULD ADD THEIR OWN PATH TO THE APBS INSTALLATION HERE! ####\"\n")
	raise ImportError, errstr

#### Autoconf the various URLs and version numbers needed for the remote server
service_url = "http://kryptonite.nbcr.net/opal2/services/apbs_1.3"
parallel_service_url = "http://oolite.calit2.optiputer.net/opal2/services/apbs-parallel-1.3"
local_version = "1.3"
maxmem = -1

def enoughMemory(inputFileName):
    if(maxmem == -1):
        return True

    inputFile = file(inputFileName, 'r')
    for line in inputFile:
        line = line.strip()
        if(line[:4].lower()=='dime'):
            grid_dimensions = line.split()
    return ((int(grid_dimensions[1])*int(grid_dimensions[2])*int(grid_dimensions[3])*160/(1024*1024) < maxmem))

def fetchResults(jobID,outputDirectory,outputFiles,fetchAll):
	""" Downloads files from Opal server (only if automatic downloading is enabled). """
	stdout.write("Downloading select results:\n")
	if outputDirectory != None:
		stdout.write("\tOutput directory:  %s\n" % outputDirectory)
		try:
			os.makedirs(outputDirectory)
		except OSError:
			pass
		os.chdir(outputDirectory)
    
	for file in outputFiles:
		fileName = file._name
		urllib.urlretrieve(file._url, fileName)
		stdout.write("\tDownloading %s...\n" % fileName)

def pollStatus(jobID,outputDirectory):
	""" Determines current status of run and executes fetching of results if the run is completed. """
	global service_url
	appServicePort = AppServiceLocator().getAppServicePort(service_url)
	status = appServicePort.queryStatus(queryStatusRequest(jobID))
	
	if status._code == 4:
		stderr.write("Error!  The calculation failed!\n")
		stderr.write("Message:  %s\n" % status._message)
		sys.exit(13)
	elif status._code != 8:
		stderr.write("Sorry, the calculation hasn't been completed yet. Please wait a short while and attempt to fetch the files again.\n")
		sys.exit(13)
	else:
		resp = appServicePort.getOutputs(getOutputsRequest(jobID))
		fetchResults(jobID, outputDirectory, resp._outputFile, status._code==4)

def initLocalVars():
	""" Initializes variables for local usage.  This should eventually be merged with processOptions """
	vars = {'typeOfRun' : 'local'}
	optionDict = processOptions()
	
	# Non-blocking parser
	if optionDict.has_key("no-fetch"):
		vars['fetchFiles'] = False
	else:
		vars["fetchFiles"] = True
	if optionDict.has_key("non-blocking"):
		vars['blocking'] = False
	else:
		vars["blocking"] = True
	# Samir:  I have no idea what fetchFileDescriptionLocation was supposed to do so I set it to None
	vars['fetchFileDescriptionLocation'] = None
	
	# Parses location to save to after a blocking run
	if optionDict.has_key("fetch") and vars["blocking"]:
		vars["outputDirectory"] = optionDict["fetch"]
	else:
		vars['outputDirectory'] = None
	
	# Parses custom service location
	if optionDict.has_key("service-location"):
		vars["service_url"] = optionDict["service-location"]

	# parses filename to write to
	vars['outFile'] = False
	if optionDict.has_key("output-file"):
		vars["argList"] = "--output-file=%s" % optionDict["output-file"]
		vars["outFile"] = True
	if optionDict.has_key("output-format") and vars["outFile"]:
		if not vars.has_key("argList"):
			vars["argList"] = ""
		argString = "--output-format=%s" % optionDict["output-format"]
		vars["argList"] = "%s %s" % (vars["argList"], argString)
		    
	return vars

def initRemoteVars(argv):
	""" Initializes variables for remote usage """
	vars = {'typeOfRun':'remote'}
    
	# data will always be written to a file, and have the same main file name as the .in file, since that can't be specified through the web interface
	vars['outFileName'] = os.path.basename(argv[-1])
	for i in (1, len(vars['outFileName'])):
		if(vars['outFileName'][-i]=="."):
			vars['outFileName']=vars['outFileName'][:-i]+".out"
			break
	return vars

def displayResults(jobID):
	""" Displays URLs of resulting files, if they are not to be fetched automatically. """
	global service_url
	appServicePort = AppServiceLocator().getAppServicePort(service_url)
	resp = appServicePort.getOutputs(getOutputsRequest(jobID))
	
	# Retrieve a listing of all output files
	stdout.write("\tStandard Output:  %s\n" % resp._stdOut, "\n")
	stdout.write("\tStandard Error:  %s\n", resp._stdErr)
	if (resp._outputFile != None):
		for i in range(0, resp._outputFile.__len__()):
			stdout.write("\t%s:  %s\n" % (resp._outputFile[i]._name, resp._outputFile[i]._url))
		stdout.write("\tStandard Error:  %s\n" % resp._stdErr)

def execApbs(vars=None, argv=None):
	""" Executes APBS and regulates checking of job status and retrieval of data if job is successfully completed. """
	if argv is None:
		# i.e. if it is a local run
		argv = sys.argv
		webRun = False
	else:
		webRun = True
		custom_service_url = None
		if vars != None:
			if vars.has_key('service_url'):
				custom_service_url = vars['service_url']
		vars = initRemoteVars(argv)
		if custom_service_url != None:
			vars['service_url'] = custom_service_url
	global service_url	
	#*argument parser
	# command-line arguments
	vars['inFile'] = argv[-1]
	
	# parses input file
	if(vars['inFile'].find("/")==-1):
		directory=""
	else:
		directory = os.path.dirname(vars['inFile'])+'/'
		vars['inFile'] = os.path.basename(vars['inFile'])
		
	nprocs = 1
	if not vars.has_key('service_url'):
		# find out if it's sequential or parallel
		tempFile = open(directory+vars['inFile'], 'r')
		version_check_flag = True
		for line in tempFile:
			# remove whitespace
			line=line.strip()
			if(line[:5]=='pdime'):
				dimension_array = line.split()
				nprocs = int(dimension_array[1])*int(dimension_array[2])*int(dimension_array[3])
				global parallel_service_url
				vars['service_url'] = parallel_service_url
				version_check_flag = False
			if(line[:5]=='async'):
				vars['service_url'] = service_url
				version_check_flag = True
				break
		if version_check_flag:
			vars['service_url'] = service_url
			
		tempFile.close()
	else:
		version_check_flag = True     # Enable version checking for custom defined Opal service as well 
		service_url = vars['service_url']
	# Retrieve a reference to the AppServicePort
	#*this is also from the path to the service
	appServicePort = AppServiceLocator().getAppServicePort(vars['service_url'])
	
	# Set up remote job launch
	req = launchJobRequest()
	# Checks version compatibility (but currently only works for sequential calculations)
	if version_check_flag:
		opal_version = AppServicePortTypeSoapBindingSOAP(vars['service_url']).getAppMetadata(getAppMetadataRequest())._usage.split()[-1]
		if opal_version != local_version:
			stderr.write("WARNING! WARNING! WARNING! WARNING! WARNING! WARNING! WARNING!\n")
			stderr.write("It appears that the remote server version of APBS (%s) does not match\nthe local version (%s)!\n" % (opal_version,local_version))
			stderr.write("Proceed at your own risk!!\n")
			stderr.write("WARNING! WARNING! WARNING! WARNING! WARNING! WARNING! WARNING!\n")
			if webRun:
				return False
	
	if(vars.has_key('argList')):
		vars['argList'] = vars['argList'] + " " + vars['inFile']
	else:
		vars['argList']=vars['inFile']
		
	req._argList = vars['argList']
	req._numProcs = nprocs
	# append all input files in this manner - in this case we have two of them
	
	inputFiles = []
	#*this is where apbs.in is read in
	inputFiles.append(ns0.InputFileType_Def('inputFile'))
	#*this must be the same as req._argList is defined to be
	inputFiles[-1]._name = vars['inFile']
	tempFile = open(directory+vars['inFile'], 'r')
	inputFiles[-1]._contents = tempFile.read()
	tempFile.close()
    
	# this is where the rest of the files to read in are determined
	start = False
	tempFile = open(directory+vars['inFile'], 'r')
	for line in tempFile:
		# remove whitespace
		line=line.strip()
		if(line=="end"):
			break
		if(start and line.find("#")!=0):
			# eliminates lines with just comments
			# remove comment
			if(line.find("#")!=-1):
				line = line[:line.find("#")]
			# re-remove whitespace (left after comment removal)
			line=line.strip()
			# remove everything except file name
			count = -1
			while line[count]!=' ':
				count = count-1
			fileName=line[count+1:]
			inputFiles.append(ns0.InputFileType_Def('inputFile'))
			inputFiles[-1]._name=fileName
			tempFile2 = open(directory+fileName, "r")
			inputFiles[-1]._contents = tempFile2.read()
			tempFile2.close()
		if(line=="read"):
			start = True
	
	tempFile.close()
	
	# req's inputFile variable is the array of input files created in the lines directly above
	req._inputFile = inputFiles
	
	if vars['typeOfRun']=='remote':
		appServicePort.launchJob(req)
		return [appServicePort, appServicePort.launchJob(req)]
	
	# Launch job, and retrieve job ID
	print "Launching remote APBS job"
	try:
		resp = appServicePort.launchJob(req)
	except ZSI.FaultException, errstr:
		stderr.write("Error! Failed to execute Opal job. Please send the entire output to the APBS development team.\n")
		stderr.write("%s\n" % errstr.fault.AsSoap())
		sys.exit(13)
	
	jobID = resp._jobID
	print "Received Job ID:", jobID
    
	status = resp._status
    
	if(vars['blocking']):
		# Poll for job status
		print "Polling job status"
		while 1:
			# print current status
			stdout.write("Status:\n")
			stdout.write("\tCode:  %s\n" % status._code)
			stdout.write("\tMessage:  %s\n" % status._message)
			stdout.write("\tURL for all results:  %s\n" % status._baseURL)
			
			if (status._code == 8) or (status._code == 4) or (not vars['blocking']):
				# STATUS_DONE || STATUS_FAILED
				break
			
			# Sleep for 30 seconds
			stdout.write("Waiting 30 seconds...\n")
			time.sleep(30)
            
			# Query job status
			status = appServicePort.queryStatus(queryStatusRequest(jobID))
        
		# Output
		if vars['fetchFiles']:
			pollStatus(jobID, vars['outputDirectory'])
		else:
			displayResults(jobID)
			
			
	else:
		stdout.write("When the job is complete, the results can be retrieved at: \n")
		stdout.write("\t%s\n" % status._baseURL)
		stdout.write("If you want to use the APBS Opal client to download the results for you, the job ID is:\n")
		stdout.write("\t%s\n" % jobID)
		
def main():
	""" Parses input, runs local jobs, and fetches files from previously completed calculations. """
	# __main__ output
	global helpString
	print creditString
	# Check for invocation with no arguments
	if len(sys.argv) == 1:
		stderr.write("Error!  This program must be called with at least one option!\n")
		stderr.write("%s\n" % helpString)
		sys.exit()

	# Process the options
	optionDict = processOptions()
	if optionDict.has_key("help"):
		stdout.write("%s\n" % helpString)
		sys.exit()

	# Local run
	if optionDict.has_key("local"):
		# Assemble an argument string to run as a sub-process
		args = [] # must be returned
		args.append('apbs')
		if optionDict.has_key("output-file"):
			argString = "--output-file=%s" % optionDict["output-file"]
			args.append(argString)
		if optionDict.has_key("output-format"):
			argString = "--output-format=%s" % optionDict["output-format"]
			args.append(argString)
		if optionDict.has_key("args"):
			args = args + optionDict["args"]
		if(not enoughMemory(optionDict["args"][-1])):
			# Add Opal error sending support
			print "Job will use too much memory to complete calculation"
			sys.exit()
		stdout.write("Running:  %s...\n" % " ".join(args))
		subprocess.call(args)
		sys.exit()

	# Determines if this is a run to just fetch the files after a non-blocking calculation
	if optionDict.has_key("job-id"):
		jobID = optionDict["job-id"]
		outputDirectory = None
		if optionDict.has_key("fetch"):
			outputDirectory = optionDict["fetch"]
		pollStatus(jobID,outputDirectory)
		sys.exit()



# Run the main driver if we are invoked 
if __name__ == "__main__":
	main()
	execApbs(vars=initLocalVars())
