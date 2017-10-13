// -*- C++ -*-

/* This software was produced by NIST, an agency of the U.S. government,
 * and by statute is not subject to copyright in the United States.
 * Recipients of this software assume all responsibilities associated
 * with its operation, modification and maintenance. However, to
 * facilitate maintenance we ask that before distributing modified
 * versions of this software, you first contact the authors at
 * oof_manager@nist.gov. 
 */

#include <oofconfig.h>

#ifndef IMAGEBASE_H
#define IMAGEBASE_H

#include "common/coord.h"
#include <vtkImageData.h>
#include <vtkSmartPointer.h>

class ImageBase {
protected:
  vtkSmartPointer<vtkImageData> image;
protected:
  Coord size_; 
  ICoord sizeInPixels_;
public:
  ImageBase()
    : image(vtkSmartPointer<vtkImageData>())
  {}
  virtual ~ImageBase() {}
  const Coord &size() const { return size_; }
  const ICoord &sizeInPixels() const { return sizeInPixels_; }
  void setSize(const Coord*);
  virtual vtkSmartPointer<vtkImageData> getVTKImageData() const { 
    return image; 
  }
  void modified() const { image->Modified(); }
  void update() const {
    // image->Update();
  }
};


#endif // IMAGEBASE_H
