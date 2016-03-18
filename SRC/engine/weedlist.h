// -*- C++ -*-
// $RCSfile: weedlist.h,v $
// $Revision: 1.7.2.3 $
// $Author: langer $
// $Date: 2013-11-08 20:44:55 $

/* This software was produced by NIST, an agency of the U.S. government,
 * and by statute is not subject to copyright in the United States.
 * Recipients of this software assume all responsibilities associated
 * with its operation, modification and maintenance. However, to
 * facilitate maintenance we ask that before distributing modified
 * versions of this software, you first contact the authors at
 * oof_manager@nist.gov. 
 */

#include <oofconfig.h>

#include <vector>

// Eliminate zeros from a list

// Is this used?  Do we need it?

template <class TYPE>
void weedlist(std::vector<TYPE> vec) {
  int nz = 0;			// number of non-zeros so far
  for(int i=0; i<vec.size(); i++) {
    if(vec[i] != 0) {
      if(i > nz) {
	vec[nz] = vec[i];
	vec[i] = 0;
      }
      nz++;
    }
  }
  if(vec.size() != nz) {
    vec.resize(nz);
  }
}
