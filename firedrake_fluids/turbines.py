#    Copyright (C) 2014 Imperial College London.

#    This file is part of Firedrake-Fluids.
#
#    Firedrake-Fluids is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Firedrake-Fluids is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Firedrake-Fluids.  If not, see <http://www.gnu.org/licenses/>.

import sys

from firedrake import *
import libspud

from firedrake_fluids import LOG
from firedrake_fluids.expression import ExpressionFromOptions

class BaseArray:
   
   def __init__(self):
      pass
   
   def write_turbine_drag(self, options):
      """ Write the turbine drag field to a file for visualisation.
      
      :param dict options: The options dictionary created when the simulation was being set up.
      :returns: None
      """
      
      LOG.debug("Integral of the turbine drag field: %.2f" % (assemble(self.turbine_drag*dx)))
      LOG.debug("Writing turbine drag field to file...")
      f = File("%s_%s.pvd" % (options["simulation_name"], "TurbineDrag"))
      f << self.turbine_drag
      return
      
   def power(self, velocity, density=1000):
      r""" Return the power :math:`P` generated by the turbine array at a given flow velocity, defined by
      
      .. math:: P = \int_\Omega{\rho C_t \|\mathbf{u}\|^3}
      
      where :math:`\rho` is the density, :math:`C_t` is the turbine drag coefficient, :math:`\mathbf{u}` is the velocity.
      
      :param ufl.Function velocity: The velocity field.
      :param density: The density field, which can be a constant value or a ufl.Function. Its default value is 1000 kg/m**3.
      :returns: The power generated by the turbine array over the whole domain.
      :rtype: float
      """
      power = assemble(density*self.turbine_drag()*(dot(velocity, velocity))**1.5*dx)
      return power

class IndividualArray(BaseArray):
   """ An array comprising individual turbines represented discretely. """

   def __init__(self, base_option_path, mesh):
      """ Create an array of turbines.
      
      :param str base_option_path: The top-most level of the turbine options in the simulation's configuration/options file.
      :param mesh: The Mesh object.
      :returns: None
      """
      
      fs = FunctionSpace(mesh, "CG", 1)

      turbine_type = libspud.get_option(base_option_path + "/array/turbine_type/name")
      turbine_coords = eval(libspud.get_option(base_option_path + "/array/turbine_coordinates"))
      turbine_radius = eval(libspud.get_option(base_option_path + "/array/turbine_radius"))
      K = libspud.get_option(base_option_path + "/array/scalar_field::TurbineDragCoefficient/value/constant")

      self.drag = Function(fs).interpolate(Expression("0"))
      for coords in turbine_coords:
         # For each coordinate tuple in the list, create a new turbine.
         # FIXME: This assumes that all turbines are of the same type.
         try:
            if(turbine_type == "bump"):
               turbine = BumpTurbine(K=K, coords=coords, r=turbine_radius)
            elif(turbine_type == "tophat"):
               turbine = TopHatTurbine(K=K, coords=coords, r=turbine_radius)
            else:
               raise ValueError("Unknown turbine type '%s'." % turbine_type)
         except ValueError as e:
            LOG.exception(e)
            sys.exit()

         self.drag += Function(fs).interpolate(turbine)
         LOG.info("Added %s turbine at %s..." % (turbine_type, coords))

      self.optimise = libspud.have_option(base_option_path + "/optimise")
      return

   def turbine_drag(self):
      return self.drag
      
class TopHatTurbine(Expression):
   r""" A class representing a turbine whose drag coefficient :math:`C_t` is defined by a top-hat function. """

   def eval(self, value, X, K=None, coords=None, r=None):
      px = sqrt((X[0]-coords[0])**2)
      py = sqrt((X[1]-coords[1])**2)
      
      if(px <= r[0] and py <= r[1]):
         value[0] = K
      else:
         value[0] = 0
      
class BumpTurbine(Expression):
   r""" A class representing a turbine whose drag coefficient :math:`C_t` is defined by a bump function. """

   def eval(self, value, X, K=None, coords=None, r=None):
      value[0] = K
      for i in range(2):
         p = sqrt(((X[i]-coords[i])/r[i])**2)
         if(p < 1.0):
            value[0] *= exp( 1.0 - 1.0/(1.0 - p**2) )
         else:
            value[0] *= 0

class ContinuumArray(BaseArray):
   """ An array comprising turbines represented as a continuum. """

   def __init__(self, base_option_path, mesh):
      """ Create an array of turbines.
      
      :param str base_option_path: The top-most level of the turbine options in the simulation's configuration/options file.
      :param mesh: The Mesh object.
      :returns: None
      """
      
      fs = FunctionSpace(mesh, "CG", 1)

      self.thrust_coefficient = libspud.get_option(base_option_path + "/array/thrust_coefficient")
      self.turbine_area = libspud.get_option(base_option_path + "/array/turbine_area")
      self.minimum_distance = libspud.get_option(base_option_path + "/array/minimum_distance")
      self.location = libspud.get_option(base_option_path + "/array/location")
      self.turbine_density = Function(fs, name="TurbineDensity").interpolate(Expression(self.location + "? %f : 0" % self.bounds()[1]))
      
      self.optimise = libspud.have_option(base_option_path + "/optimise")
      return
      
   def turbine_drag(self):
      return 0.5*self.thrust_coefficient*self.turbine_area*self.turbine_density

   def bounds(self):
      return [0.0, 1.0/(self.minimum_distance**2)]
      
