// -*- C++ -*-

/* This software was produced by NIST, an agency of the U.S. government,
 * and by statute is not subject to copyright in the United States.
 * Recipients of this software assume all responsibilities associated
 * with its operation, modification and maintenance. However, to
 * facilitate maintenance we ask that before distributing modified
 * versions of this software, you first contact the authors at
 * oof_manager@nist.gov. 
 */

// This file contains forward declarations and typedefs from
// cskeleton2.h.  It can be included instead of that file in
// most situations, to reduce header file dependencies.

#ifndef CSKELETON2_I_H
#define CSKELETON2_I_H

#include <oofconfig.h>

#include <map>
#include <vector>

class CDeputySkeleton;
class CSkeleton;
class CSkeletonBase;

class DeputyProvisionalChanges;
class ProvisionalChanges;
class ProvisionalChangesBase;
class ProvisionalInsertion;
class ProvisionalMerge;
typedef std::vector<ProvisionalChangesBase*> ProvisionalChangesVector;

// SkelElNodeMap maps a part of a skeleton element (edge or face) to a
// list of Nodes that have been created on that part when constructing
// the real mesh elements.
class CSkeletonMultiNodeKey;
class Node;
typedef std::map<CSkeletonMultiNodeKey, std::vector<Node*>> SkelElNodeMap;


#endif // CSKELETON2_I_H
