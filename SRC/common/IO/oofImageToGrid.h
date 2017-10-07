// -*- C++ -*-

/* This software was produced by NIST, an agency of the U.S. government,
 * and by statute is not subject to copyright in the United States.
 * Recipients of this software assume all responsibilities associated
 * with its operation, modification and maintenance. However, to
 * facilitate maintenance we ask that before distributing modified
 * versions of this software, you first contact the authors at
 * oof_manager@nist.gov. 
 */

#ifndef __oofImageToGrid_h
#define __oofImageToGrid_h

#include <oofconfig.h>

#include <vtkRectilinearGridAlgorithm.h>

// vtkAlgorithm that converts vtkImageData to a vtkRectilinearGrid.

class oofImageToGrid : public vtkRectilinearGridAlgorithm
{
 public:
  vtkTypeMacro(oofImageToGrid, vtkRectilinearGridAlgorithm);
  void PrintSelf(std::ostream &, vtkIndent);

  static oofImageToGrid *New();

 protected:
  oofImageToGrid();
  virtual int FillInputPortInformation(int port, vtkInformation *info);
  virtual int RequestData(vtkInformation*, vtkInformationVector**,
			  vtkInformationVector*);
  virtual int RequestInformation(vtkInformation*, vtkInformationVector**,
   				 vtkInformationVector*);
  virtual int RequestUpdateExtent(vtkInformation*, vtkInformationVector**,
   				  vtkInformationVector*);

 private:
  oofImageToGrid(const oofImageToGrid&); // not implemented
  void operator=(const oofImageToGrid&); // not implemented
};

#endif // __oofImageToGrid_h
