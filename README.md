
                  ############################################
                  Building APBS with or without Tinker Support
                  ############################################

      This directory contains a complete distribution of the APBS code
      for Poisson-Boltzmann calculations. To build APBS, run in order:
      "make distclean", "configure", "make" and "make install".

      The "configure" script provided in this distribution is for use
      with the GNU compilers on either Linux of macOS. For use with the
      Intel compilers, copy "configure-intel" to "configure". If using
      a Windows machine, copy "configure-windows" to "configure".

      #################################################
      Building APBS Libraries Needed for Tinker Support
      #################################################

      Use the following "configure" command to setup building of APBS
      with the libraries needed to link with Tinker. Please be sure to
      change the --prefix directory to the APBS 1.3 installation and
      --with-python option to the system Python 2 executable.

            ./configure --enable-tinker --disable-zlib \
            --prefix=/Users/ponder/apbs-1.3 \
            --with-python=/usr/bin/python2 \
            CFLAGS=-DVAPBSQUIET CXXFLAGS=-DVAPBSQUIET \
            FFLAGS=-DVAPBSQUIET

      After running "configure", use "make" and "make install" to build
      and install APBS. The libraries with APBS support for Tinker will
      be in the /lib and /contrib/lib subdirectories, and consist of
      libapbsmainroutines.a, libapbs.a, libmaloc.a and libapbsblas.a.

      You can then build a Tinker version with APBS capability by using
      Makefile-apbs from the /make area of the Tinker distribution. The
      /apbs/test directory contains benchmark tests and results for
      several small proteins when run from within Tinker.

      #############################################################
      Building APBS without Tinker Support (to use standalone APBS)
      #############################################################

      To create an APBS executable for Poisson-Boltzmann calculations,
      remove the --enable-tinker option to configure, and run the same
      commands listed above. The executable will be found in /bin. A
      static macOS executable is available as ./apbs-macos-1.3.tar.gz.

      On Windows, the APBS executable requires the Windows Sockets 2
      library, WS2_32.LIB, which comes as part of Visual Studio. As an
      alternative, the libwsock32.a library from a Cygwin installation
      can be used. The Cygwin library is included by using the Windows
      version of the configure script, configure-windows.

      In order to link a static Windows executable, use the -static flag
      in the link command, in addition to or instead of -static-libgcc.
      A static Windows executable is found here as ./apbs-win64-1.3.zip.

      A Linux executable that is static except for a few system libraries
      is available as ./apbs-linux64-1.3.tar.gz.

