//
//  Cijkl.hpp
//  CPOOF
//
//  Created by Keshavarzhadad, Shahriyar on 8/10/17.
//  Copyright © 2017 Keshavarzhadad, Shahriyar. All rights reserved.
//

#ifndef Cijkl_hpp
#define Cijkl_hpp

#include <stdio.h>
class Cijkl {
public:
    Cijkl(double c11,double c12, double c44);
    Cijkl();
    
    Cijkl rotate(double **qrot);
private:
    double cijkl[3][3][3][3];
};

#endif /* Cijkl_hpp */