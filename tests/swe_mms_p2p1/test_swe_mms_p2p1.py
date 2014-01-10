import pytest
import numpy
from firedrake import *

import shallow_water

def swe_mms_p2p1():
   configs = ["MMS_A", "MMS_B", "MMS_C"]
   norms = []
   
   for c in configs:
      sw = shallow_water.ShallowWater(path = c + ".swml")
      sw.run()
      h_old = sw.h_old
      
      f = Function(sw.function_spaces["FreeSurfaceFunctionSpace"])
      f.interpolate(Expression("sin(x[0])*sin(x[1])"))
      
      norms.append(sqrt(assemble(dot(h_old - f, h_old - f) * dx)))
   
   return norms
      
def test_swe_mms_p2p1():
   norms = numpy.array(swe_mms_p2p1())
   convergence_order = numpy.log2(norms[:-1] / norms[1:])
   print "Convergence order:", convergence_order
   assert (numpy.array(convergence_order) > 1.3).all()
      
if __name__ == '__main__':
   import os
   os.system("make")
   pytest.main(os.path.abspath(__file__))
