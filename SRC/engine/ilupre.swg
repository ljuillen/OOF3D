// -*- C++ -*-

/* This software was produced by NIST, an agency of the U.S. government,
 * and by statute is not subject to copyright in the United States.
 * Recipients of this software assume all responsibilities associated
 * with its operation, modification and maintenance. However, to
 * facilitate maintenance we ask that before distributing modified
 * versions of this software, you first contact the authors at
 * oof_manager@nist.gov. 
 */

#ifndef ILUPRE_SWG
#define ILUPRE_SWG

%module ilupre

%include "engine/typemaps.swg"
%extern "common/doublevec.swg"
%extern "engine/preconditioner.swg"
%extern "engine/sparsemat.swg"
%pragma(python) code="from ooflib.SWIG.engine.preconditioner import PreconditionerBasePtr"
%pragma(python) code="from ooflib.SWIG.common.doublevec import DoubleVecPtr"
%pragma(python) code="from ooflib.SWIG.engine.sparsemat import SparseMatPtr"

%{
#include "common/doublevec.h"
#include "engine/ilupre.h"
%}

class ILUPreconditionerCore : public PreconditionerBase {
public:
  ILUPreconditionerCore(SparseMat&);
  ~ILUPreconditionerCore();
  SparseMat unfactored(); 
  SparseMat lower();
  SparseMat upper();
};

#endif // ILUPRE_SWG
