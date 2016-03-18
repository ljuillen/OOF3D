# -*- python -*-
# $RCSfile: tests.py,v $
# $Revision: 1.1.2.1 $
# $Author: fyc $
# $Date: 2013-07-10 16:12:21 $

# This software was produced by NIST, an agency of the U.S. government,
# and by statute is not subject to copyright in the United States.
# Recipients of this software assume all responsibilities associated
# with its operation, modification and maintenance. However, to
# facilitate maintenance we ask that before distributing modified
# versions of this software, you first contact the authors at
# oof_manager@ctcms.nist.gov. 

from generics import *

def bdyList(*bdys):
    return chooserCheck(
        "OOF2:Boundary Analysis Page:Pane:frame:BoundaryListScroll:BoundaryList",
        bdys)

def goSensitive(sensitive):
    return is_sensitive("OOF2:Boundary Analysis Page:Go") == sensitive

