# -*- python -*-

# This software was produced by NIST, an agency of the U.S. government,
# and by statute is not subject to copyright in the United States.
# Recipients of this software assume all responsibilities associated
# with its operation, modification and maintenance. However, to
# facilitate maintenance we ask that before distributing modified
# versions of this software, you first contact the authors at
# oof_manager@nist.gov. 

from generics import *

def solverSubproblemsCheck(names):
    return names == [x.name() for x in treeViewColValues('OOF3D:Solver Page:VPane:Subproblems:SubproblemScroll:SubproblemList', 0)]

def solverFieldsCheck(names):
    return names == [x.name() for x in treeViewColValues('OOF3D:Solver Page:VPane:FieldInit:Scroll:Initializers', 0)]

def solverSubproblemsPageSensitivityCheck0():
    return sensitizationCheck({ 'VPane:Subproblems:Set':0,
				'VPane:Subproblems:Copy':0,
				'VPane:Subproblems:CopyAll':0,
				'VPane:Subproblems:Remove':0,
				'VPane:Subproblems:RemoveAll':0
				},
			       base='OOF3D:Solver Page')
			       
def solverSubproblemsPageSensitivityCheck1():
    return sensitizationCheck({ 'VPane:Subproblems:Set':1,
				'VPane:Subproblems:Copy':0,
				'VPane:Subproblems:CopyAll':0,
				'VPane:Subproblems:Remove':0,
				'VPane:Subproblems:RemoveAll':0
				},
			       base='OOF3D:Solver Page')
			       
def solverSubproblemsPageSensitivityCheck2():
    return sensitizationCheck({ 'VPane:Subproblems:Set':1,
				'VPane:Subproblems:Copy':1,
				'VPane:Subproblems:CopyAll':1,
				'VPane:Subproblems:Remove':1,
				'VPane:Subproblems:RemoveAll':1
				},
			       base='OOF3D:Solver Page')
			       
def solverFieldsPageSensitivityCheck0():
    return sensitizationCheck({ 'VPane:FieldInit:Set':0,
				'VPane:FieldInit:CopyInit':0,
				'VPane:FieldInit:Clear':0,
				'VPane:FieldInit:ClearAll':0,
				'VPane:FieldInit:ApplyAt':0,
				'VPane:FieldInit:Apply':0
				},
			       base='OOF3D:Solver Page')
			       
def solverFieldsPageSensitivityCheck1():
    return sensitizationCheck({ 'VPane:FieldInit:Set':1,
				'VPane:FieldInit:CopyInit':0,
				'VPane:FieldInit:Clear':0,
				'VPane:FieldInit:ClearAll':0,
				'VPane:FieldInit:ApplyAt':0,
				'VPane:FieldInit:Apply':0
				},
			       base='OOF3D:Solver Page')
			       
def solverFieldsPageSensitivityCheck2():
    return sensitizationCheck({ 'VPane:FieldInit:Set':1,
				'VPane:FieldInit:CopyInit':1,
				'VPane:FieldInit:Clear':1,
				'VPane:FieldInit:ClearAll':1,
				'VPane:FieldInit:ApplyAt':1,
				'VPane:FieldInit:Apply':1
				},
			       base='OOF3D:Solver Page')
