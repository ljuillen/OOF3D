# -*- python -*-

# This software was produced by NIST, an agency of the U.S. government,
# and by statute is not subject to copyright in the United States.
# Recipients of this software assume all responsibilities associated
# with its operation, modification and maintenance. However, to
# facilitate maintenance we ask that before distributing modified
# versions of this software, you first contact the authors at
# oof_manager@nist.gov. 

# Pixel selection modification tools that *don't* depend on the image,
# and hence aren't in the image module.

from ooflib.SWIG.common import config
from ooflib.SWIG.common import pixelselectioncourier
from ooflib.SWIG.common import switchboard
from ooflib.common import color
from ooflib.common import debug
from ooflib.common import enum
from ooflib.common import microstructure as msmodule
from ooflib.common import primitives
from ooflib.common import registeredclass
from ooflib.common import selectionshape
from ooflib.common import selectionoperators
from ooflib.common.IO import colordiffparameter
from ooflib.common.IO import oofmenu
from ooflib.common.IO import parameter
from ooflib.common.IO import pixelgroupparam
from ooflib.common.IO import pixelselectionmenu
from ooflib.common.IO import reporter
from ooflib.common.IO import whoville
from ooflib.common.IO import xmlmenudump
import ooflib.common.microstructure
import ooflib.common.units


#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

# VoxelSelectionModifier is the registered class for the selection
# tools that appear in the RCF on the PixelPage.

# Simple selection modifiers that don't take any parameters other than
# a Microstructure or Image should be registered using
# SimpleVoxelSelectionModRegistration, which will automatically create
# a menu item for them.  The subclasses need to have a select() method
# which takes a PixelSelectionContext arg.

# Other selection modifiers are registered with
# VoxelSelectionModRegistration.  When used, an instance of the
# subclass is passed as the 'method' argument to
# OOF.VoxelSelection.Select.

class VoxelSelectionModifier(registeredclass.RegisteredClass):
    registry = []

    
def simpleSelectionCB(menuitem, microstructure):
    ms = msmodule.microStructures[microstructure]
    selection = ms.getSelectionContext()
    selection.reserve()
    selection.begin_writing()
    try:
        # SimpleVoxelSelectionModRegistration sets menuitem.data to a
        # VoxelSelectionModifier subclass, which has a static select()
        # method.
        menuitem.data.select(selection)
    finally:
        selection.end_writing()
        selection.cancel_reservation()
    switchboard.notify('pixel selection changed', selection)
    switchboard.notify('redraw')


class SimpleVoxelSelectionModRegistration(registeredclass.Registration):
    def __init__(self, name, subclass, ordering, secret=0, **kwargs):
        registeredclass.Registration.__init__(
            self,
            name=name,
            registeredclass=VoxelSelectionModifier,
            subclass=subclass,
            ordering=ordering,
            params=[],
            secret=secret,
            **kwargs)
        self.menuitem = pixelselectionmenu.selectmenu.addItem(
            oofmenu.OOFMenuItem(
                name,
                params=[whoville.WhoParameter('microstructure',
                                              msmodule.microStructures,
                                              tip=parameter.emptyTipString)],
                ordering=ordering,
                callback=simpleSelectionCB))
        self.menuitem.data = subclass
    def callMenuItem(self, microstructure, selectionModifier):
        self.menuitem.callWithDefaults(microstructure=microstructure)

class VoxelSelectionModRegistration(registeredclass.Registration):
    def __init__(self, name, subclass, ordering, secret=0, **kwargs):
        registeredclass.Registration.__init__(
            self,
            name=name,
            registeredclass=VoxelSelectionModifier,
            subclass=subclass,
            ordering=ordering,
            params=[],
            secret=secret,
            **kwargs)
        self.menuitem = pixelselectionmenu.selectmenu.Select
    def callMenuItem(self, microstructure, selectionModifier):
        self.menuitem.callWithDefaults(source=microstructure,
                                       method=selectionModifier)

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

# Simple selection methods

class ClearVoxelSelection(VoxelSelectionModifier):
    @staticmethod
    def select(selection):
        selection.start()
        selection.clear()

SimpleVoxelSelectionModRegistration(
    'Clear', ClearVoxelSelection, ordering=0,
    discussion="<para>Unselect all voxels.</para>")

class InvertVoxelSelection(VoxelSelectionModifier):
    @staticmethod
    def select(selection):
        selection.start()
        selection.invert()
        
SimpleVoxelSelectionModRegistration(
    'Invert', InvertVoxelSelection, ordering=0.1,
    discussion="""<para>
    Selected voxels will be unselected and unselelcted ones will be
    selected.</para>"""
)

# Undo and Redo are secret because they have buttons and don't need to
# be in the RCF.

class UndoVoxelSelection(VoxelSelectionModifier):
    @staticmethod
    def select(selection):
        selection.undo()

SimpleVoxelSelectionModRegistration('Undo', UndoVoxelSelection, ordering=-1,
                                    secret=True)

class RedoVoxelSelection(VoxelSelectionModifier):
    @staticmethod
    def select(selection):
        selection.redo()

SimpleVoxelSelectionModRegistration('Redo', RedoVoxelSelection, ordering=-1,
                                    secret=True)

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#


## TODO: Rewrite to use VoxelSelectionMethod instead of
## VoxelSelectionModifier? No-- all VoxelSelectionMethods appear in the
## toolbox, and not all VoxelSelectionModifiers are appropriate there.

class GroupSelector(VoxelSelectionModifier):
    def __init__(self, group, operator):
        self.group = group
        self.operator = operator
    def __call__(self, ms, selection):
        group = ms.findGroup(self.group)
        if group is not None:
            selection.start()
            self.operator.operate(
                selection, pixelselectioncourier.GroupSelection(ms, group))

registeredclass.Registration(
    'Group',
    VoxelSelectionModifier,
    GroupSelector,
    ordering=1,
    params=[
        pixelgroupparam.PixelGroupParameter('group',
                                            tip='Pixel group to work with.'),
        parameter.RegisteredParameter(
            'operator', selectionoperators.PixelSelectionOperator,
            tip="How to use the group to modify the current selection.")],
    tip="Modify the current selection via boolean operations"
    " with the pixels in a pixel group.")

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

# The selection methods operate upon sets of pixels defined by shapes
# from the SelectionShape class.  The SelectionShape subclasses don't
# actually have methods that extract the selected voxels because the
# scope would be wrong -- they're really just containers for the shape
# parameters, and they're used for things other than voxels.  However,
# we *do* want to use the SelectionShape classes themselves, and not
# derive VoxelSelectionShape classes from them, because it makes sense
# to use the same shape classes when selecting other sorts of objects.
# So here we create a dict that maps the SelectionShape classes to
# functions that return the appropriate courier objects.

# These couriers are used in activeareamod.py as well.

couriers = {}

def _box_courier(shape, ms):
    return pixelselectioncourier.BoxSelection(
        ms, shape.point0, shape.point1)
couriers[selectionshape.BoxSelectionShape] = _box_courier

def _circ_courier(shape, ms):
    return pixelselectioncourier.CircleSelection(ms, shape.center, shape.radius)
couriers[selectionshape.CircleSelectionShape] = _circ_courier

def _elps_courier(shape, ms):
    return pixelselectioncourier.EllipseSelection(
        ms, shape.point0, shape.point1)
couriers[selectionshape.EllipseSelectionShape] = _elps_courier

#=--=##=--=##=--=##=--=##=--=#

class RegionSelector(VoxelSelectionModifier):
    def __init__(self, shape, units, operator):
        self.shape = shape
        self.units = units
        self.operator = operator
    def __call__(self, ms, selection):
        selection.start()
        scaled = self.units.scale(ms, self.shape)
        courier = couriers[self.shape.__class__](scaled, ms)
        self.operator.operate(selection, courier)

registeredclass.Registration(
    "Region",
    VoxelSelectionModifier,
    RegionSelector,
    ordering=1.5,
    params=[
        parameter.RegisteredParameter(
            'shape', selectionshape.SelectionShape,
            tip='The shape of the region to select.'),
        parameter.RegisteredParameter(
            'units', ooflib.common.units.UnitsRC,
            value=ooflib.common.units.PhysicalUnits(),
            tip="The units for the shape's length parameters."),
        parameter.RegisteredParameter(
            'operator', selectionoperators.PixelSelectionOperator,
            tip="How to use the region to modify the current selection.")
        ],
    tip="Modify the current selection via boolean operations using the pixels"
    " within a given geometrically defined region."
    )

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

class Despeckle(VoxelSelectionModifier):
    def __init__(self, neighbors):
        self.neighbors = neighbors
    def __call__(self, ms, selection):
        selection.start()
        selection.select(pixelselectioncourier.DespeckleSelection(
            ms, selection.getSelectionAsGroup(), self.neighbors))
        
class Elkcepsed(VoxelSelectionModifier):
    def __init__(self, neighbors):
        self.neighbors = neighbors
    def __call__(self, ms, selection):
        selection.start()
        selection.unselect(pixelselectioncourier.ElkcepsedSelection(
            ms, selection.getSelectionAsGroup(), self.neighbors))

# The allowed ranges for the parameters are determined by geometry.
# Settings outside of the allowed ranges either select all pixels or
# no pixels and aren't useful.
if config.dimension() == 2:
    despeckleRange = (4, 8)
    despeckleDefault = 8
    elkcepsedRange = (1, 4)
    elkcepsedDefault = 3
else:
    despeckleRange = (10, 26)
    despeckleDefault = 15
    elkcepsedRange = (1, 13)
    elkcepsedDefault = 9

registeredclass.Registration(
    'Despeckle',
    VoxelSelectionModifier,
    Despeckle,
    ordering=2.0,
    params=[parameter.IntRangeParameter(
            'neighbors', despeckleRange, despeckleDefault,
            tip="Select pixels with at least this many selected neighbors")
    ],
    tip="Recursively select all pixels with a minimum number of selected neighbors. This fills in small holes in the selection.",
    discussion=xmlmenudump.loadFile('DISCUSSIONS/common/menu/despeckle.xml')
    )

registeredclass.Registration(
    'Elkcepsed',
    VoxelSelectionModifier,
    Elkcepsed,
    ordering=2.1,
    params=[parameter.IntRangeParameter(
            'neighbors', elkcepsedRange, elkcepsedDefault,
       tip="Deselect pixels with fewer than this many selected neighbors.")
    ],
    tip="Recursively deselect all pixels with fewer than a minimum number of selected neighbors.  This has the effect of removing small islands and peninsulas, and is the opposite of 'Despeckle'.",
    discussion=xmlmenudump.loadFile('DISCUSSIONS/common/menu/elkcepsed.xml')
    )

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

class Expand(VoxelSelectionModifier):
    def __init__(self, radius):
        self.radius = radius
    def __call__(self, ms, selection):
        selection.start()
        selection.select(pixelselectioncourier.ExpandSelection(
            ms, selection.getSelectionAsGroup(), self.radius))

class Shrink(VoxelSelectionModifier):
    def __init__(self, radius):
        self.radius = radius
    def __call__(self, ms, selection):
        selection.start()
        selection.unselect(pixelselectioncourier.ShrinkSelection(
            ms, selection.getSelectionAsGroup(), self.radius))

## TODO 3.1: Allow radius to be set in either physical or pixel units
## by adding a "units" parameter.

registeredclass.Registration(
    'Expand',
    VoxelSelectionModifier,
    Expand,
    ordering=3.0,
    params=[
        parameter.FloatParameter(
            'radius', 1.0,
            tip='Select pixels within this distance of other selected pixels.'),
    ],
    tip="Select all pixels within a given distance of the current selection.",
    discussion=xmlmenudump.loadFile("DISCUSSIONS/common/menu/expand_pixsel.xml")
    )

registeredclass.Registration(
    'Shrink',
    VoxelSelectionModifier,
    Shrink,
    ordering=3.1,
    params=[
        parameter.FloatParameter(
            'radius', 1.0,
            tip='Deselect pixels within this distance.')
    ],
    tip="Deselect all pixels within a given distance of the boundaries of the current selection.",
    discussion=xmlmenudump.loadFile('DISCUSSIONS/common/menu/shrink_pixsel.xml')
    )

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

class CopyPixelSelection(VoxelSelectionModifier):
    def __init__(self, source):
        self.source = source
    def __call__(self, ms, selection):
        selection.start()
        sourceMS = ooflib.common.microstructure.microStructures[self.source]
        selection.selectFromGroup(
            sourceMS.getObject().pixelselection.getSelectionAsGroup())

registeredclass.Registration(
    'Copy',
    VoxelSelectionModifier,
    CopyPixelSelection,
    ordering=4.0,
    params=[
    whoville.WhoParameter('source', ooflib.common.microstructure.microStructures,
                          tip="Copy the current selection from this Microstructure.")],
    tip="Copy the current selection from another Microstructure.",
    discussion=xmlmenudump.loadFile('DISCUSSIONS/common/menu/copy_pixsel.xml')
    )

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

