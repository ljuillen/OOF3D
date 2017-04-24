# -*- python -*-

# This software was produced by NIST, an agency of the U.S. government,
# and by statute is not subject to copyright in the United States.
# Recipients of this software assume all responsibilities associated
# with its operation, modification and maintenance. However, to
# facilitate maintenance we ask that before distributing modified
# versions of this software, you first contact the authors at
# oof_manager@nist.gov. 

_enable = False


def set(state):
    global _enable
    _enable = state

def query():
    global _enable
    return _enable
    
def enabled():
    global _enable
    return _enable
