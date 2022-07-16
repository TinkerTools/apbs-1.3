#!/usr/bin/python
""" Python APBS No Input Driver File
    
    This module allows a user to run APBS through Python. Use this module if
    you wish to include APBS in a Python-based application.  This specific
    version allows a user to read in data from the Python level without
    using the command line - thus enabling the ability to link seamlessly
    with other Python programs.  Here the 'INPUT and 'PQR' variables are
    predetermined global strings, but can (and *should*) be dynamically created
    as desired - that's one of the main advantages of using Python!

    It is strongly recommended that you edit out any part of this script that
    you do not need - many different options are included, but this makes the
    code much harder to read.  I

    The module mimics the main.c driver that is used in the C version of APBS.
    The functions which are called are located in apbslib.py, which is 
    automatically generated by SWIG to wrap each APBS function.  See the APBS
    documentation for more information about each function.

    To access energy, potential, or force vectors for further use, see the
    appropriate printResults() function at the top of this script.  This is
    merely an example - instead of printing the forces and energies you'll
    simply want to pass the arrays to other Python functions.

    NOTE:  You ***MUST*** use

        calcforce comps

    in the input file for each calculation that you wish to obtain a force
    vector - otherwise the vector will NOT be calculated.

"""    

from apbslib import *
import sys, time
import string
import re
from sys import stdout, stderr

__author__ = "Todd Dolinsky, Nathan Baker"
__date__ = "July 2007"

INPUT = """read
    mol pqr ion.pqr
end
elec name solvated
    mg-manual
    dime 65 65 65
    nlev 4
    grid 0.33 0.33 0.33
    gcent mol 1
    chgm spl2
    mol 1
    lpbe
    bcfl mdh
    ion 1 0.000 2.0
    ion -1 0.000 2.0
    pdie 1.0
    sdie 78.54
    chgm spl2
    srfm spl2
    sdens 10.0
    srad 1.4
    swin 0.3
    temp 298.15
    gamma 0.105
    calcenergy total
    calcforce comps
end
elec name reference
    mg-manual
    dime 65 65 65
    nlev 4
    grid 0.33 0.33 0.33
    gcent mol 1
    mol 1
    lpbe
    bcfl mdh
    ion 1 0.000 2.0
    ion -1 0.000 2.0
    pdie 1.0
    sdie 1.0
    chgm spl2
    srfm spl2
    sdens 10.0
    srad 1.4
    swin 0.3
    temp 298.15
    gamma 0.105
    calcenergy total
    calcforce comps
end
 
print energy 1 - 2 end
 
quit
"""
 
PQR = "ATOM      1  I   ION     1       0.000   0.000  0.000  1.00  3.00"

Python_kb = 1.3806581e-23
Python_Na = 6.0221367e+23
NOSH_MAXMOL = 20
NOSH_MAXCALC = 20

class APBSError(Exception):
    """ APBSError class

        The APBSError class inherits off the Exception module and returns
        a string defining the nature of the error. 
    """
    
    def __init__(self, value):
        """
            Initialize with error message

            Parameters
                value:  Error Message (string)
        """
        self.value = value
        
    def __str__(self):
        """
            Return the error message
        """
        return `self.value`

def getUnitConversion():
    """
        Get the unit conversion from kT to kJ/mol

        Returns
            factor: The conversion factor (float)
    """
    temp = 298.15
    factor = Python_kb/1000.0 * temp * Python_Na
    return factor

def getHeader():
    """ Get header information about APBS
        Returns (header)
            header: Information about APBS
    """

    """ Get header information about APBS
        Returns (header)
            header: Information about APBS
    """

    header = "\n\n\
    ----------------------------------------------------------------------\n\
    Adaptive Poisson-Boltzmann Solver (APBS)\n\
    Version 1.3\n\
    \n\
    APBS -- Adaptive Poisson-Boltzmann Solver\n\
    \n\
    Nathan A. Baker (nathan.baker@pnl.gov)\n\
    Pacific Northwest National Laboratory\n\
    \n\
    Additional contributing authors listed in the code documentation.\n\
    \n\
    Copyright (c) 2010, Pacific Northwest National Laboratory.  Portions Copyright (c) 2002-2010, Washington University in St. Louis.  Portions Copyright (c) 2002-2010, Nathan A. Baker.  Portions Copyright (c) 1999-2002,  The Regents of the University of California. Portions Copyright (c) 1995,  Michael Holst\n\
    \n\
    All rights reserved.\n\
    \n\
    Redistribution and use in source and binary forms, with or without\n\
    modification, are permitted provided that the following conditions are met:\n\
    \n\
    * Redistributions of source code must retain the above copyright notice, this\n\
      list of conditions and the following disclaimer.\n\
    \n\
    * Redistributions in binary form must reproduce the above copyright notice,\n\
      this list of conditions and the following disclaimer in the documentation\n\
      and/or other materials provided with the distribution.\n\
    \n\
    * Neither the name of Washington University in St. Louis nor the names of its\n\
      contributors may be used to endorse or promote products derived from this\n\
      software without specific prior written permission.\n\
    \n\
    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS\n\
    \"AS IS\" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT\n\
    LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR\n\
    A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR\n\
    CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,\n\
    EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,\n\
    PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR\n\
    PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF\n\
    LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING\n\
    NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS\n\
    SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.\n\
    ----------------------------------------------------------------------\n\
    \n\n"
    return header

def getUsage():
    """ Get usage information about running APBS via Python
        Returns (usage)
            usage: Text about running APBS via Python
    """
    
    usage = "\n\n\
    ----------------------------------------------------------------------\n\
    This driver program calculates electrostatic potentials, energies,\n\
    and forces using both multigrid methods.\n\
    It is invoked as:\n\n\
      python noinput.py\n\
    ----------------------------------------------------------------------\n\n"

    return usage


def printResults(energyList, potList, forceList):
    """
        Print the results stored in the energy, potential and force lists to
        stdout. The arrays are accessed as follows:

        energyList[calc #][atom #]: Per-atom energy for a specific calc #

        potList[calc #][atom #]  :  Per-atom potential for a specific calc #

        forceList is a little more difficult, as it is a list of dictionaries
        of lists:

        forceList[calc #]['force type'][atom #][x=0/y=1/z=2 direction ]

        So to access the qf x-component force from the first APBS elec
        calculation for the 2nd (atom id 1) atom, you can access

        forceList[0]['qf'][1][0]

        If you plan on using these lists extensively it would be wise to
        convert them into Python objects - this format is the cleanest for
        getting information back out from C, but not for dealing between
        Python functions.  
    """
    # Print the per-atom energies
    #    Each list corresponds to a calculation, having len(atoms) entries

    factor = getUnitConversion()

    for i in range(len(potList)):
        list = potList[i]
        print "\nPer-atom potentials from calculation %i" % i
        for j in range(len(list)):
            atom = list[j]
            print "\t%i\t%.4f kT/e" % (j, (float(atom)))     
    
    for i in range(len(energyList)):
        list = energyList[i]
        print "\nPer-atom energies from calculation %i" % i
        for j in range(len(list)):
            atom = list[j]
            print "\t%i\t%.4f kJ/mol" % (j, (float(atom) * factor * 0.5))     

    # Print the per-atom forces

    for i in range(len(forceList)):
        qflist = forceList[i]["qf"]
        iblist = forceList[i]["ib"]
        dblist = forceList[i]["db"]
        
        print "\nPer-atom forces from calculation %i" % i
        for j in range(len(qflist)):
            qf = "%.3E %.3E %.3E" % (qflist[j][0]*factor, qflist[j][1]*factor, qflist[j][2]*factor)
            ib = "%.3E %.3E %.3E" % (iblist[j][0]*factor, iblist[j][1]*factor, iblist[j][2]*factor)
            db = "%.3E %.3E %.3E" % (dblist[j][0]*factor, dblist[j][1]*factor, dblist[j][2]*factor)
            print "\t%i\t%s (qf)" % (j, qf)
            print "\t%i\t%s (ib)" % (j, ib)
            print "\t%i\t%s (db)" % (j, db)


def runAPBS(PQR, INPUT):
    """ Main driver for testing.  Runs APBS on given input file """
    
    # Initialize variables, arrays
    com = Vcom_ctor(1)
    rank = Vcom_rank(com)
    size = Vcom_size(com)
    mgparm = MGparm()
    pbeparm = PBEparm()
    mem = Vmem_ctor("Main")
    pbe = new_pbelist(NOSH_MAXMOL)
    pmg = new_pmglist(NOSH_MAXMOL)
    pmgp = new_pmgplist(NOSH_MAXMOL)
    realCenter = double_array(3)
    totEnergy = []
    x = []
    y = []
    z = []
    chg = []
    rad = []
    nforce = int_array(NOSH_MAXCALC)
    atomforce = new_atomforcelist(NOSH_MAXCALC)

    # Start the main timer
    main_timer_start = time.clock()

    # Parse the input file
    nosh = NOsh_ctor(rank, size)

    # Instead of having an input file, we have a string!

    if not parseInputFromString(nosh, INPUT):
        stderr.write("main:  Error while parsing input file.\n")
        raise APBSError, "Error occurred!"
   
    # Load the molecules using Valist_load routine, thereby
    # loading atoms directly into the valist object, removing
    # the need for an actual PQR file from stdin

    alist = new_valist(NOSH_MAXMOL)
    atoms = string.split(PQR,"\n")
    for i in range(len(atoms)):
        atom = atoms[i]
        if not (atom.startswith("ATOM") or atom.startswith("HETATM")): continue
        if atom == "": continue

        # Try matching to see if a chain ID is present
        haschain = 0
        if re.compile("( [A-Z]{3} [A-Z]{1} *\d+)").findall(atom) != []:
            haschain = 1

        params = string.split(atom)
        x.append(float(params[5+haschain]))
        y.append(float(params[6+haschain]))
        z.append(float(params[7+haschain]))
        chg.append(float(params[8+haschain]))
        rad.append(float(params[9+haschain]))
    
    # If there are more than one PQR file, make multiple Valist
    # objects.  Make sure to get the actual length of the
    # coordinate since atoms may contain non ATOM lines.

    myAlist = make_Valist(alist,0)
    Valist_load(myAlist, len(x), x,y,z,chg,rad)  

    if not NOsh_setupElecCalc(nosh, alist):
        stderr.write("main: Error setting up calculation.\n")
        raise APBSError, "Error setting up calculations!"


    for i in range(nosh.ncalc): totEnergy.append(0.0)

    # Initialize the Python holders
    energyList = []
    potList = []
    forceList = []

    # Load the various maps - since this example shows how to eliminate
    # inputs from the command line, this will probably not be used
  
    dielXMap = new_gridlist(NOSH_MAXMOL)
    dielYMap = new_gridlist(NOSH_MAXMOL)
    dielZMap = new_gridlist(NOSH_MAXMOL)
    if loadDielMaps(nosh, dielXMap, dielYMap, dielZMap) != 1:
        stderr.write("Error reading dielectric maps!\n")
        raise APBSError, "Error reading dielectric maps!"

    kappaMap = new_gridlist(NOSH_MAXMOL)
    if loadKappaMaps(nosh, kappaMap) != 1:
        stderr.write("Error reading kappa maps!\n")
        raise APBSError, "Error reading kappa maps!"

    chargeMap = new_gridlist(NOSH_MAXMOL)
    if loadChargeMaps(nosh, chargeMap) != 1:
        stderr.write("Error reading charge maps!\n")
        raise APBSError, "Error reading charge maps!"

    # Do the calculations

    stdout.write("Preparing to run %d PBE calculations. \n" % nosh.ncalc)

    for icalc in xrange(nosh.ncalc):
        stdout.write("---------------------------------------------\n")
        calc = NOsh_getCalc(nosh, icalc)
        mgparm = calc.mgparm
        pbeparm = calc.pbeparm
        if calc.calctype != 0:
            stderr.write("main:  Only multigrid calculations supported!\n")
            raise APBSError, "Only multigrid calculations supported!"

        for k in range(0, nosh.nelec):
            if NOsh_elec2calc(nosh,k) >= icalc:
                break

        name = NOsh_elecname(nosh, k)
        if name == "":
            stdout.write("CALCULATION #%d:  MULTIGRID\n" % (icalc+1))
        else:
            stdout.write("CALCULATION #%d (%s): MULTIGRID\n" % ((icalc+1),name))
        stdout.write("Setting up problem...\n")
	
        # Routine initMG
        
        if initMG(icalc, nosh, mgparm, pbeparm, realCenter, pbe, 
              alist, dielXMap, dielYMap, dielZMap, kappaMap, chargeMap, 
              pmgp, pmg) != 1:
            stderr.write("Error setting up MG calculation!\n")
            raise APBSError, "Error setting up MG calculation!"
	
        # Print problem parameters if desired (comment out if you want
        # to minimize output to stdout)
	
        printMGPARM(mgparm, realCenter)
        printPBEPARM(pbeparm)
      
        # Solve the problem : Routine solveMG
	
        thispmg = get_Vpmg(pmg,icalc)

        if solveMG(nosh, thispmg, mgparm.type) != 1:
            stderr.write("Error solving PDE! \n")
            raise APBSError, "Error Solving PDE!"

        # Set partition information : Routine setPartMG

        if setPartMG(nosh, mgparm, thispmg) != 1:
            stderr.write("Error setting partition info!\n")
            raise APBSError, "Error setting partition info!"
	
        # Get the energies - the energy for this calculation
        # (calculation number icalc) will be stored in the totEnergy array
        ret, totEnergy[icalc] = energyMG(nosh, icalc, thispmg, 0, 0.0, 0.0, 0.0, 0.0)

        # Calculate forces - doforce will be > 0 if anything other than
        # "calcforce no" is specified
        
        aforce = get_AtomForce(atomforce, icalc)
        doforce = wrap_forceMG(mem, nosh, pbeparm, mgparm, thispmg, aforce, alist, nforce, icalc)
      
        # Write out data from MG calculations : Routine writedataMG	
        writedataMG(rank, nosh, pbeparm, thispmg)
	
        # Write out matrix from MG calculations	
        writematMG(rank, nosh, pbeparm, thispmg)

        # Get the per-atom potentials and energies from this calculation.

        potentials = getPotentials(nosh, pbeparm, thispmg, myAlist)
        potList.append(potentials)
               
        energies = getEnergies(thispmg, myAlist)
        energyList.append(energies)

        # Get the forces from this calculation and store the result in
        # forceList.  For information on how to use this array see
        # printResults()

        if doforce:
            forceList.append(getForces(aforce, myAlist))
    
    # Handle print statements - comment out if limiting output to stdout

    if nosh.nprint > 0:
        stdout.write("---------------------------------------------\n")
        stdout.write("PRINT STATEMENTS\n")
    for iprint in xrange(nosh.nprint):
        if NOsh_printWhat(nosh, iprint) == NPT_ENERGY:
            printEnergy(com, nosh, totEnergy, iprint)
        elif NOsh_printWhat(nosh, iprint) == NPT_FORCE:
            printForce(com, nosh, nforce, atomforce, iprint)
        else:
            stdout.write("Undefined PRINT keyword!\n")
            break
                
    stdout.write("----------------------------------------\n")
    stdout.write("CLEANING UP AND SHUTTING DOWN...\n")

    # Clean up APBS structures
    killForce(mem, nosh, nforce, atomforce)
    killEnergy()
    killMG(nosh, pbe, pmgp, pmg)
    killChargeMaps(nosh, chargeMap)
    killKappaMaps(nosh, kappaMap)
    killDielMaps(nosh, dielXMap, dielYMap, dielZMap)
    killMolecules(nosh, alist)
    #delete_Nosh(nosh)
    
    # Clean up Python structures

    delete_double_array(realCenter)
    delete_int_array(nforce)
    delete_atomforcelist(atomforce)
    delete_valist(alist)
    delete_gridlist(dielXMap)
    delete_gridlist(dielYMap)
    delete_gridlist(dielZMap)
    delete_gridlist(kappaMap)
    delete_gridlist(chargeMap)
    delete_pmglist(pmg)
    delete_pmgplist(pmgp)
    delete_pbelist(pbe)
        
    # Clean up MALOC structures
    #delete_Com(com)
    #delete_Mem(mem)
    stdout.write("\n")
    stdout.write("Thanks for using APBS!\n\n")

    # Stop the main timer
    main_timer_stop = time.clock()
    stdout.write("Total execution time:  %1.6e sec\n" % (main_timer_stop - main_timer_start))

    return energyList, potList, forceList

if __name__ == "__main__":
    
    # Check invocation
    stdout.write(getHeader())
    if len(sys.argv) != 1:
        stderr.write("main:  Called with %d arguments!\n" % len(sys.argv))
        stderr.write(getUsage())
        raise APBSError, "Incorrect Usage!"

    energyList, potList, forceList = runAPBS(PQR, INPUT)

    # As an example, print the resulting information

    printResults(energyList, potList, forceList)
