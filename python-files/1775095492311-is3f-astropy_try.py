import matplotlib.pyplot as plt
import numpy as np

from astropy.visualization import astropy_mpl_style, quantity_support

plt.style.use(astropy_mpl_style)
quantity_support()

import astropy.units as u
from astropy.coordinates.baseframe import BaseCoordinateFrame
from astropy.coordinates.representation import CartesianRepresentation
from astropy.coordinates.representation.geodetic import (
    BaseBodycentricRepresentation,
    BaseGeodeticRepresentation,
)

class MarsBestFitAeroid(BaseGeodeticRepresentation):
    """
    A Spheroidal representation of Mars that minimized deviations with respect to the
    areoid following
        Ardalan A. A, R. Karimi, and E. W. Grafarend (2010)
        https://doi.org/10.1007/s11038-009-9342-7
    """

    _equatorial_radius = 3395.4280 * u.km
    _flattening = 0.5227617843759314 * u.percent

class MarsBestFitOcentricAeroid(BaseBodycentricRepresentation):
    """
    A Spheroidal planetocentric representation of Mars that minimized deviations with
    respect to the areoid following
        Ardalan A. A, R. Karimi, and E. W. Grafarend (2010)
        https://doi.org/10.1007/s11038-009-9342-7
    """

    _equatorial_radius = 3395.4280 * u.km
    _flattening = 0.5227617843759314 * u.percent

class MarsSphere(BaseGeodeticRepresentation):
    """
    A Spherical representation of Mars
    """

    _equatorial_radius = 3395.4280 * u.km
    _flattening = 0.0 * u.percent

class MarsCoordinateFrame(BaseCoordinateFrame):
    """
    A reference system for Mars.
    """

    name = "Mars"

mars_sphere = MarsCoordinateFrame(
    lon=np.linspace(0, 360, 128) * u.deg,
    lat=np.linspace(-90, 90, 128) * u.deg,
    representation_type=MarsSphere,
)
mars = MarsCoordinateFrame(
    lon=np.linspace(0, 360, 128) * u.deg,
    lat=np.linspace(-90, 90, 128) * u.deg,
    representation_type=MarsBestFitAeroid,
)
mars_ocentric = MarsCoordinateFrame(
    lon=np.linspace(0, 360, 128) * u.deg,
    lat=np.linspace(-90, 90, 128) * u.deg,
    representation_type=MarsBestFitOcentricAeroid,
)

xyz_sphere = mars_sphere.represent_as(CartesianRepresentation)
xyz = mars.represent_as(CartesianRepresentation)
xyz_ocentric = mars_ocentric.represent_as(CartesianRepresentation)

fig, ax = plt.subplots(2, subplot_kw={"projection": "3d"})

ax[0].scatter(*((xyz - xyz_sphere).xyz << u.km))
ax[0].tick_params(labelsize=8)
ax[0].set(xlabel="x [km]", ylabel="y [km]", zlabel="z [km]")
ax[0].set_title("Mars-odetic spheroid difference from sphere")

ax[1].scatter(*((xyz_ocentric - xyz_sphere).xyz << u.km))
ax[1].tick_params(labelsize=8)
ax[1].set(xlabel="x [km]", ylabel="y [km]", zlabel="z [km]")

ax[1].set_title("Mars-ocentric spheroid difference from sphere")

plt.show()