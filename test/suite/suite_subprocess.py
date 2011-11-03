#!/usr/bin/env python
#
# See the file LICENSE for redistribution information.
#
# Copyright (c) 2008-2011 WiredTiger, Inc.
#	All rights reserved.
#
# suite_subprocess.py
# 	Run a subprocess within the test suite
#

import unittest
from wiredtiger import WiredTigerError
import wttest
import subprocess
import os

# Used as a 'mixin' class along with a WiredTigerTestCase class
class suite_subprocess:
    subproc = None

    def has_error_in_file(self, filename):
        """
        Return whether the file contains 'ERROR'.
        WT utilities issue a 'WT_ERROR' output string upon error.
        """
        with open(filename, 'r') as f:
            for line in f:
                if 'ERROR' in line:
                    return True
        return False

    def check_no_error_in_file(self, filename):
        """
        Raise an error and show output context if the file contains 'ERROR'.
        WT utilities issue a 'WT_ERROR' output string upon error.
        """
        lines = []
        hasError = False
        hasPrevious = False  # do we need to prefix an ellipsis?
        hasNext = False  # do we need to suffix an ellipsis?
        with open(filename, 'r') as f:
            for line in f:
                lines.append(line)
                hasError = hasError or 'ERROR' in line
                if hasError:
                    if len(lines) > 10:
                        hasNext = True
                        break
                else:
                    if len(lines) > 5:
                        lines.pop(0)
                        hasPrevious = True
        if hasError:
            print '**************** ERROR in output file: ' + filename + ' ****************'
            if hasPrevious:
                print '...'
            for line in lines:
                print line,
            if hasNext:
                print '...'
            print '********************************'
            self.fail('ERROR found in output file: ' + filename)

    def check_empty_file(self, filename):
        """
        Raise an error if the file is not empty
        """
        filesize = os.path.getsize(filename)
        if filesize > 0:
            with open(filename, 'r') as f:
                contents = f.read(1000)
                print 'ERROR: ' + filename + ' should be empty, but contains:\n'
                print contents + '...\n'
        self.assertEqual(filesize, 0)

    def check_non_empty_file(self, filename):
        """
        Raise an error if the file is empty
        """
        filesize = os.path.getsize(filename)
        if filesize == 0:
            print 'ERROR: ' + filename + ' should not be empty (this command expected error output)'
        self.assertNotEqual(filesize, 0)

    def runWt(self, args, outfilename=None, errfilename=None, reopensession=True):
        """
        Run the 'wt' process
        """

        # we close the connection to guarantee everything is
        # flushed, and that we can open it from another process
        if self.conn != None:
            self.conn.close(None)
            self.conn = None

        wtoutname = outfilename
        if wtoutname == None:
            wtoutname = "wt.out"
        wterrname = errfilename
        if wterrname == None:
            wterrname = "wt.err"
        with open(wterrname, "w") as wterr:
            with open(wtoutname, "w") as wtout:
                if self._gdbSubprocess:
                    procargs = ["gdb", "--args", "../../.libs/wt"]
                else:
                    procargs = ["../../wt"]
                procargs.extend(args)
                if self._gdbSubprocess:
                    print str(procargs)
                    print "*********************************************"
                    print "**** Run 'wt' via: run " + " ".join(procargs[3:]) + ">" + wtoutname + " 2>" + wterrname
                    print "*********************************************"
                    proc = subprocess.Popen(procargs)
                else:
                    proc = subprocess.Popen(procargs, stdout=wtout, stderr=wterr)
                proc.wait()
        if errfilename == None:
            self.check_empty_file(wterrname)
        if outfilename == None:
            self.check_empty_file(wtoutname)

        # Reestablish the connection if needed
        if reopensession:
            self.conn = self.setUpConnectionOpen(".")
            self.session = self.setUpSessionOpen(self.conn)
