// -*- C++ -*-

/* This software was produced by NIST, an agency of the U.S. government,
 * and by statute is not subject to copyright in the United States.
 * Recipients of this software assume all responsibilities associated
 * with its operation, modification and maintenance. However, to
 * facilitate maintenance we ask that before distributing modified
 * versions of this software, you first contact the authors at
 * oof_manager@nist.gov. 
 */

#ifndef EDGE2SHAPEFUNCTION_H
#define EDGE2SHAPEFUNCTION_H

#include "engine/shapefunction.h"

class Edge2ShapeFunction : public ShapeFunction {
public:
  Edge2ShapeFunction(const MasterElement&);
  virtual double value(ShapeFunctionIndex, const MasterCoord&) const;
  virtual double masterderiv(ShapeFunctionIndex, SpaceIndex, const MasterCoord&)
    const;
  virtual int degree() const { return 1; }
  virtual int deriv_degree() const { return 0; }
};


#endif
