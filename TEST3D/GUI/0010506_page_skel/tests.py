# -*- python -*-

# This software was produced by NIST, an agency of the U.S. government,
# and by statute is not subject to copyright in the United States.
# Recipients of this software assume all responsibilities associated
# with its operation, modification and maintenance. However, to
# facilitate maintenance we ask that before distributing modified
# versions of this software, you first contact the authors at
# oof_manager@nist.gov. 

from generics import *

def skeletonMethodListCheck(*names):
    return chooserCheck('OOF3D:Skeleton Page:Pane:Modification:Method:Chooser', names)

def currentSkeletonMethodCheck(name):
    return chooserStateCheck('OOF3D:Skeleton Page:Pane:Modification:Method:Chooser', name)
    
def skeletonMethodTargetsListCheck(method, *names):
    return chooserCheck('OOF3D:Skeleton Page:Pane:Modification:Method:'+method+':targets:Chooser', names)

def currentSkeletonMethodTargetsCheck(method, name):
    return chooserStateCheck('OOF3D:Skeleton Page:Pane:Modification:Method:'+method+':targets:Chooser', name)
    
def skeletonMethodCriterionListCheck(method, *names):
    return chooserCheck('OOF3D:Skeleton Page:Pane:Modification:Method:'+method+':criterion:Chooser', names)
    
def currentSkeletonMethodCriterionCheck(method, name):
    return chooserStateCheck('OOF3D:Skeleton Page:Pane:Modification:Method:'+method+':criterion:Chooser', name)

def skeletonMethodMethodListCheck(method, *names):
    return chooserCheck('OOF3D:Skeleton Page:Pane:Modification:Method:'+method+':method:Chooser', names)

def currentSkeletonMethodMethodCheck(method, name):
    return chooserStateCheck('OOF3D:Skeleton Page:Pane:Modification:Method:'+method+':method:Chooser', name)
    
def skeletonPageModificationSensitivityCheck0():
    return sensitizationCheck({ 'Pane:Modification:Method':1,
				'Pane:Modification:Prev':0,
				'Pane:Modification:OK':0,
				'Pane:Modification:Next':0,
				'Pane:Modification:Undo':0,
				'Pane:Modification:Redo':0
				},
			       base='OOF3D:Skeleton Page')
       
def skeletonPageModificationSensitivityCheck1():
    return sensitizationCheck({ 'Pane:Modification:Method':1,
				'Pane:Modification:Prev':0,
				'Pane:Modification:OK':1,
				'Pane:Modification:Next':0,
				'Pane:Modification:Undo':0,
				'Pane:Modification:Redo':0
				},
			       base='OOF3D:Skeleton Page')
