# -*- python -*-

# This software was produced by NIST, an agency of the U.S. government,
# and by statute is not subject to copyright in the United States.
# Recipients of this software assume all responsibilities associated
# with its operation, modification and maintenance. However, to
# facilitate maintenance we ask that before distributing modified
# versions of this software, you first contact the authors at
# oof_manager@nist.gov. 

from ooflib.SWIG.common import config
from ooflib.SWIG.common import crandom
from ooflib.SWIG.common import pixelgroup
from ooflib.SWIG.common import switchboard
from ooflib.SWIG.common import ooferror
from ooflib.common import debug
from ooflib.common import enum
from ooflib.common import primitives
from ooflib.common import registeredclass
from ooflib.common import utils
from ooflib.common.IO import parameter
from ooflib.common.IO import pixelgroupparam
from ooflib.common.IO import whoville
from ooflib.common.IO import xmlmenudump
if config.dimension() == 2:
    from ooflib.engine import skeletonelement
from ooflib.engine.IO import materialparameter
from ooflib.engine.IO import pbcparams
from ooflib.engine.IO import skeletongroupparams
import types
#Interface branch
from ooflib.engine.IO import interfaceparameters

import ooflib.engine.coverage

from ooflib.engine.skeletonselection import \
    NodeSelectionModifier, SegmentSelectionModifier, \
    FaceSelectionModifier, ElementSelectionModifier, \
    NodeSelectionModRegistration, SegmentSelectionModRegistration, \
    FaceSelectionModRegistration, ElementSelectionModRegistration
    

## TODO 3.1 OPT: Should this be moved to C++?  Yes, and use couriers as in pixel
## selection.

## TODO 3.1: Add more face selection methods.  Select by aspect ratio?
## Area?

## TODO MER: Combine the group selection methods (Add Group, Intersect
## Group, etc) into one method with a SkeletonSelectionOperator arg,
## the way the GroupSelector in pixelselectionmod.py works.  

## TODO 3.1: Add Region selection methods, in the style of BoxSelection
## for voxels.

# TODO 3.1: Can the Segment/Element/Node/Face operations here all be
# derived from common SkeletonSelectable classes?

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

# Ordering: The order in which the skeleton selection modifiers appear
# in the menus should be as similar as possible for the different
# selection modes.  The order is determined by the "ordering" arg in
# the registrations.

## TODO: These aren't used consistently below.  Make sure that all
## orderings use them.

#   The group selection methods, Select Group, Unselect Group, Add
#   Group, and Intersect Group, come first, in that order, with
#   ordering=0.x, where x=1,2,3,4.
_selectGroupOrdering = 0.0
_unselectGroupOrdering = 0.1
_addGroupOrdering = 0.2
_intersectGroupOrdering=0.3

#   The "Select from Selected Object" methods have ordering=1.x, where
#   x is the dimension of the Object.
_selectFromNodesOrdering = 1.0
_selectFromSegmentsOrdering = 1.1
_selectFromFacesOrdering = 1.2
_selectFromElementsOrdering = 1.3

#   Other selection methods have ordering >= 2.0
_homogeneityOrdering = 3.3
_internalBoundaryOrdering = 3.5
_namedBoundaryOrdering = 3.6
_interfaceOrdering = 3.7

_periodicPartnerOrdering = 8

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

        
# # This is the function that actually runs a selection modification.
# # It is the menu callback for the automatically-generated menu
# # items in engine/IO/skeletonselectmenu.py.  This one routine
# # works for node, segment, and element selections.

# def modify(menuitem, skeleton, **params):
#     registration = menuitem.data
#     modifier = registration(**params)
#     skelcontext = whoville.getClass('Skeleton')[skeleton]
#     selection = modifier.getSelection(skelcontext)
#     selection.begin_writing()
#     try:
#         modifier(skelcontext, selection)
#     finally:
#         selection.end_writing()

#     selection.mode().modifierApplied(modifier) # sends switchboard signal
#     selection.signal()

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#
#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

# Node selection modifiers

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#
    
class NodeFromSelectedSegments(NodeSelectionModifier):
    def select(self, skeleton, selection):
        nodes = set()
        for segment in skeleton.segmentselection.retrieve():
            nodes.update(segment.getNodes())
        selection.start()
        selection.clear()
        selection.select(nodes)

NodeSelectionModRegistration(
    'Select from Selected Segments',
    NodeFromSelectedSegments,
    ordering=_selectFromSegmentsOrdering,
    tip="Select nodes from selected segments.",
    discussion=xmlmenudump.loadFile(
        'DISCUSSIONS/engine/menu/nodes_from_segments.xml'))

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

class NodeFromSelectedElements(NodeSelectionModifier):
    def __init__(self, coverage):
        self.coverage = coverage

    def getAllNodes(self, context):
        nodes = set()
        for element in context.elementselection.retrieve():
            nodes.update(element.getNodes())
        return nodes

    if config.dimension() == 2:
        def getExteriorNodes(self, context):
            # A segment is on the boundary of the selection if it
            # belongs to only one selected element.
            skel = context.getObject()
            segdict = {}   # counts how many times each segment has been seen
            for element in context.elementselection.retrieve():
                for i in range(len(element.getNodes())):
                    n0 = element.nodes[i]
                    n1 = element.nodes[(i+1)%element.nnodes()]
                    seg = skel.findSegment(n0, n1)
                    segdict[seg] = segdict.get(seg, 0) + 1
            bdysegs = [seg for seg,count in segdict.items() if count == 1]
            nodes = set()
            for seg in bdysegs:
                segnodes = seg.nodes()
                nodes.add(segnodes[0])
                nodes.add(segnodes[1])
            return nodes
    else:                       # dimension == 3
        def getExteriorNodes(self, context):
            # In 3D, a node is on a boundary of the element selection
            # if it's on a boundary face of the element selection.
            # TODO OPT: Might it be faster to skip the faces and just ask
            # if a node has both selected and unselected elements?
            bdyfaces = context.exteriorFacesOfSelectedElements()
            nodes = set()
            for face in bdyfaces:
                nodes.update(face.getNodes())
            return nodes
                
    def select(self, skeleton, selection):
        if self.coverage == "All":
            selected = self.getAllNodes(skeleton)
        elif self.coverage == "Exterior":
            selected = self.getExteriorNodes(skeleton)
        else:                   # self.coverage == "Interior"
            selected = (self.getAllNodes(skeleton) -
                        self.getExteriorNodes(skeleton))
        selection.start()
        selection.clear()
        selection.select(selected)


NodeSelectionModRegistration(
    'Select from Selected Elements',
    NodeFromSelectedElements,
    ordering=_selectFromElementsOrdering,
    params = [enum.EnumParameter('coverage', ooflib.engine.coverage.Coverage)],
    tip="Select nodes from selected elements.",
    discussion=xmlmenudump.loadFile(
        'DISCUSSIONS/engine/menu/nodes_from_elements.xml'))

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

class NodeFromSelectedFaces(NodeSelectionModifier):
    def __init__(self, coverage):
        self.coverage = coverage

    def select(self, skeleton, selection):
        if self.coverage == "All":
            nodes = self.getAllNodes(skeleton)
        elif self.coverage == "Exterior":
            nodes = self.getExteriorNodes(skeleton)
        else:
            nodes = (self.getAllNodes(skeleton)
                     - self.getExteriorNodes(skeleton))
        selection.start()
        selection.clear()
        selection.select(nodes)

    def getAllNodes(self, skeleton):
        nodes = set()
        for face in skeleton.faceselection.retrieve():
            nodes.update(face.getNodes())
        return nodes
    def getExteriorNodes(self, skeleton):
        # Exterior nodes are the nodes that are on the exterior
        # segments, which are the segments belonging to only one
        # selected face.
        segs = skeleton.exteriorSegmentsOfSelectedFaces()
        nodes = set()
        for seg in segs:
            nodes.update(seg.getNodes())
        return nodes
        

NodeSelectionModRegistration(
    'Select from Selected Faces',
    NodeFromSelectedFaces,
    ordering=_selectFromFacesOrdering,
    params = [enum.EnumParameter('coverage', ooflib.engine.coverage.Coverage)],
    tip="Select nodes from selected faces.")
    

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

class SelectInternalBoundaryNodes(NodeSelectionModifier):
    def __init__(self, ignorePBC=False):
        self.ignorePBC = ignorePBC
    def select(self, skeleton, selection):
        skel = skeleton.getObject()
        nodelist = []
        for node in skel.getNodes():
            if self.ignorePBC:
                elements = node.aperiodicNeighborElements()
            else:
                elements = node.getElements()
            # Select the Node if not all of its Elements have the same
            # category.
            cat = elements[0].dominantPixel(skel)
            for element in elements[1:]:
                if cat != element.dominantPixel(skel):
                    nodelist.append(node)
                    break
        selection.start()
        selection.clear()
        selection.select(nodelist)
                    
if config.dimension() == 2:
    params=[pbcparams.PBCBooleanParameter('ignorePBC', False,
                                          tip='Ignore periodicity?')]
else:
    params = []

NodeSelectionModRegistration(
    'Select Internal Boundaries',
    SelectInternalBoundaryNodes,
    ordering=_internalBoundaryOrdering,
    params=params,
    tip="Select all nodes on material or group boundaries.",
    discussion=xmlmenudump.loadFile(
        'DISCUSSIONS/engine/menu/boundary_nodes.xml'))

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

class SelectNamedBoundaryNodes(NodeSelectionModifier):
    def __init__(self, boundary):
        self.boundary = boundary
    def select(self, skeleton, selection):
        bdy = skeleton.getBoundary(self.boundary)
        nodes = bdy.boundary(skeleton.getObject()).getNodes()
        selection.start()
        selection.clear()
        selection.select(nodes)

NodeSelectionModRegistration(
    'Select Named Boundary',
    SelectNamedBoundaryNodes,
    ordering=_namedBoundaryOrdering,
    params=[
        skeletongroupparams.SkeletonPointBoundaryParameter(
            'boundary', tip="Select nodes in this boundary")
        ],
    tip="Select nodes belonging to the given skeleton point boundary.",
    discussion="""<para>

    Select all the &nodes; contained in the given &skel;
    <link linkend="Section-Concepts-Skeleton-Boundary">boundary</link>.
    The boundary must be a
    <link linkend="Section-Concepts-Skeleton-Boundary-Point">point</link>
    boundary.
    
    </para>"""
    )

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

class SelectPeriodicPartnerNodes(NodeSelectionModifier):
    def select(self, skeleton, selection):
        oldnodes = skeleton.nodeselection.retrieve()
        newnodes = set()
        for node in oldnodes:
            for p in node.getPartners():
                newnodes.add(p)
        selection.start()
        selection.select(newnodes)

registeredclass.TwoDOnlyRegistration(
    'Select Periodic Partners',
    SelectPeriodicPartnerNodes,
    ordering=_periodicPartnerOrdering,
    tip="Select nodes whose periodic partners are already selected.",
    discussion="""<para>

    If the &skel; is <link
    linkend="Section-Concepts-Skeleton-Periodicity">periodic</link>,
    every &node; on a periodic boundary has a partner on the
    opposite boundary.  This command selects the periodic partners
    of the currently selected &nodes;, without unselecting any
    &nodes;.

    </para>"""
    )

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

## Since we only have tetrahedral elements in 3D, there's no
## difference between expanding by shared elements, segments, or
## faces.  TODO 3.1: If we ever add non-tetrahedral elements, this
## should be rewritten to look like ExpandElementSelection.

class ExpandNodeSelection(NodeSelectionModifier):
    def select(self, skeleton, selection):
        skel = skeleton.getObject()
        newnodes = set()
        for node in selection.retrieve():
            for segment in skel.getNodeSegments(node):
                    newnodes.add(segment.get_other_node(node))
        selection.start()
        selection.select(newnodes)

NodeSelectionModRegistration(
    'Expand',
    ExpandNodeSelection,
    ordering=2.0,
    tip="Select the neighbors of selected Nodes.")

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

# Select the indicated group.

## TODO: Compine the various "Group" selectors into one, and use the
## SelectionOperators.

class NodeSelectGroup(NodeSelectionModifier):
    def __init__(self, group):
        self.group = group
    def select(self, skeleton, selection):
        # Retrieve the members first -- if an exception occurs, the
        # system state will be as before.
        members = skeleton.nodegroups.get_group(self.group)
        selection.start()
        selection.clear()
        selection.select(members)

NodeSelectionModRegistration(
    'Select Group',
    NodeSelectGroup,
    ordering=_selectGroupOrdering,
    params=[
        skeletongroupparams.NodeGroupParameter('group',
                                               tip="Node group to select.")
        ],
    tip='Select the members of a group, discarding the current selection.',
    discussion="""<para>
    Select all the &nodes; in the given <link
    linkend='Section-Concepts-Skeleton-Groups'>group</link>.  The
    currently selected &nodes; will first be deselected.  To select a
    group without first deselecting, use <xref
    linkend='MenuItem-OOF.NodeSelection.Add_Group'/>.
    </para>""")

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

# Unselect the indicated group.

class NodeDeselectGroup(NodeSelectionModifier):
    def __init__(self, group):
        self.group = group
    def select(self, skeleton, selection):
        members = skeleton.nodegroups.get_group(self.group)
        selection.start()
        selection.deselect(members)

NodeSelectionModRegistration(
    'Unselect Group',
    NodeDeselectGroup,
    ordering=_unselectGroupOrdering,
    params=[skeletongroupparams.NodeGroupParameter('group',
                                             tip="Node group to deselect.")],
    tip='Unselect the members of a group.',
    discussion="""<para>
    Deselect all of the &nodes; that are members of the specified
    <link linkend='Section-Concepts-Skeleton-Groups'>group</link>.
    Any &nodes; that are members of the group but that are not
    currently selected will be unaffected.
    </para>""")

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

# Add the group to the selection, retaining the current selection.

class NodeAddSelectGroup(NodeSelectionModifier):
    def __init__(self, group):
        self.group = group
    def select(self, skeleton, selection):
        members = skeleton.nodegroups.get_group(self.group)
        selection.start()
        # Minor inefficiency: this reselects already-selected group
        # members, but it would probably take just as much effort to
        # *not* select them.
        selection.select(members)


NodeSelectionModRegistration(
    'Add Group',
    NodeAddSelectGroup,
    ordering=_addGroupOrdering,
    params=[skeletongroupparams.NodeGroupParameter('group',
                                                   tip="Node group to select.")
            ],
    tip='Select the members of a group, retaining the current selection.',
    discussion="""<para>
    Select all of the &nodes; in the given <link
    linkend='Section-Concepts-Skeleton-Groups'>group</link> in
    addition to all of the currently selected &nodes;.  To select
    <emphasis>only</emphasis> the &nodes; in a group, discarding the
    previous selection, use <xref
    linkend='MenuItem-OOF.NodeSelection.Select_Group'/>.
    </para>""")

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

# Select the intersection of the group and the selection.

class NodeIntersectGroup(NodeSelectionModifier):
    def __init__(self, group):
        self.group = group
    def select(self, skeleton, selection):
        nlist = skeleton.nodegroups.get_group(self.group)
        ilist = filter(lambda x: x.isSelected(), nlist)
        selection.start()
        selection.clear()
        selection.select(ilist)

NodeSelectionModRegistration(
    'Intersect Group',
    NodeIntersectGroup,
    ordering=_intersectGroupOrdering,
    params=[skeletongroupparams.NodeGroupParameter('group',
                                                   tip="Node group to select.")
            ],
    tip='Select the intersection of a group and the current selection.',
    discussion="""<para>
    Select the &nodes; that are both in the given <link
    linkend='Section-Concepts-Skeleton-Groups'>group</link> and in the
    current selection.
    </para>""")


#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#
#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#
#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

# Segment selection modifiers

class SegFromSelectedElements(SegmentSelectionModifier):
    def __init__(self, coverage):
        self.coverage = coverage

    def getAllSegments(self, context):
        segments = set()
        skel = context.getObject()
        for element in context.elementselection.retrieve():
            if config.dimension() == 2:
                el_segments = element.getSegments(skel)
                for seg in el_segments:
                    segments.add(seg)
            else: # dimension==3
                segments.update(skel.getElementSegments(element))
        return segments

    def getExteriorSegments(self, context):
        segments = set()
        if config.dimension() == 2:
            skel = context.getObject()
            for element in context.elementselection.retrieve():
                el_segments = element.getSegments(skel)
                for seg in el_segments:
                    # A segment is on the exterior of the selection if it
                    # belongs to only one element.
                    n = 0
                    for el in seg.getElements():
                        if el.selected:
                            n += 1
                    if n == 1:
                        segments.add(seg)

        else:               # dimension==3 
            segments = context.exteriorSegmentsOfSelectedElements()
        return segments

    def getInternalSegments(self, skelcontext):
        bdysegs = set(self.getExteriorSegments(skelcontext))
        allsegs = set(self.getAllSegments(skelcontext))
        return allsegs - bdysegs

    def select(self, skeleton, selection):
        if self.coverage == "All":
            selected = self.getAllSegments(skeleton)
        elif self.coverage == "Exterior":
            selected = self.getExteriorSegments(skeleton)
        else:                   # self.coverge == "Interior"
            selected = self.getInternalSegments(skeleton)
        selection.start()
        selection.clear()
        selection.select(selected)

SegmentSelectionModRegistration(
    'Select from Selected Elements',
    SegFromSelectedElements,
    ordering=_selectFromElementsOrdering,
    params = [
        enum.EnumParameter("coverage", 
                           ooflib.engine.coverage.Coverage)],
    tip="Select segments from selected elements.",
    discussion=xmlmenudump.loadFile(
        'DISCUSSIONS/engine/menu/segments_from_elements.xml'))

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

## TODO 3.1: Add a modifier that deselects segments with fewer than n
## selected nodes, where n is 1 or 2.  Maybe just add a parameter to
## this method that tells it whether to select segments with at least
## n selected nodes, or to deselect segments with fewer.

class SegFromSelectedNodes(SegmentSelectionModifier):
    def __init__(self, min_nodes):
        self.min_nodes = min_nodes
    def select(self, skeleton, selection):
        selected = set()
        skel = skeleton.getObject()
        if self.min_nodes == 1:
            for node in skeleton.nodeselection.retrieve():
                selected.update(skel.getNodeSegments(node))
        elif self.min_nodes == 2:
            for node in skeleton.nodeselection.retrieve():
                segs = skel.getNodeSegments(node)
                for seg in segs:
                    if seg.get_other_node(node).isSelected():
                        selected.add(seg)
        selection.start()
        selection.clear()
        selection.select(selected)

SegmentSelectionModRegistration(
    "Select from Selected Nodes",
    SegFromSelectedNodes,
    params=[
        parameter.IntRangeParameter(
            'min_nodes', (1,2), value=1,
            tip="Select segments with at least this many selected endpoints.")],
    ordering=_selectFromNodesOrdering,
    tip="Select segments from the selected nodes.")
        
#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

class SegFromSelectedFaces(SegmentSelectionModifier):
    def __init__(self, coverage):
        self.coverage = coverage

    def getAllSegments(self, skelctxt):
        segments = set()
        skel = skelctxt.getObject()
        for face in skelctxt.faceselection.retrieve():
            segments.update(skel.getFaceSegments(face))
        return segments

    def getExteriorSegments(self, skelctxt):
        return skelctxt.exteriorSegmentsOfSelectedFaces()

    def getInternalSegments(self, skelctxt):
        allsegs = set(self.getAllSegments(skelctxt))
        bdysegs = set(self.getExteriorSegments(skelctxt))
        return allsegs - bdysegs

    def select(self, skeleton, selection):
        if self.coverage == 'All':
            selected = self.getAllSegments(skeleton)
        elif self.coverage == 'Exterior':
            selected = self.getExteriorSegments(skeleton)
        else:                   # self.coverage == 'Interior'
            selected = self.getInternalSegments(skeleton)
        selection.start()
        selection.clear()
        selection.select(selected)

SegmentSelectionModRegistration(
    'Select from Selected Faces',
    SegFromSelectedFaces,
    ordering=_selectFromFacesOrdering,
    params=[
        enum.EnumParameter('coverage', ooflib.engine.coverage.Coverage)],
    tip="Select the edges of the selected faces.")

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

class SelectInternalBoundarySegments(SegmentSelectionModifier):
    def select(self, skeleton, selection):
        skel = skeleton.getObject()
        ms = skeleton.getMicrostructure()
        segset = set()
        for face in skel.getFaces():
            elements = skel.getFaceElements(face)
            if (len(elements) == 2 and
                (elements[0].dominantPixel(skel)
                 != elements[1].dominantPixel(skel))):
                segset.update(skel.getFaceSegments(face))
        selection.start()
        selection.clear()
        selection.select(segset)

SegmentSelectionModRegistration(
    'Select Internal Boundaries',
    SelectInternalBoundarySegments,
    ordering=_internalBoundaryOrdering,
    tip="Select segments on material or group boundaries.")

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

#Interface branch
class SelectInterfaceSegments(SegmentSelectionModifier):
    def __init__(self, interface):
        self.interface = interface
    def select(self, skeleton, selection):
        skel = skeleton.getObject()
        interfacemsplugin=skel.getMicrostructure().getPlugIn("Interfaces")
        try:
            interfacedef=interfacemsplugin.namedinterfaces[self.interface]
        except KeyError:
            #Should not happen
            raise ooferror.ErrPyProgrammingError("Interface not found!")
        seglist = []
        for segment in skel.segments.values():
            yes,side1elem=interfacedef.isInterfaceSegment(segment,skel)
            if yes:
                seglist.append(segment)
        selection.start()
        selection.clear()
        selection.select(seglist)

if config.dimension() == 2:
    SegmentSelectionModRegistration(
        'Select Interface Segments',
        SegmentSelectionModifier,
        SelectInterfaceSegments,
        ordering=_interfaceOrdering,
        params=[
        interfaceparameters.InterfacesParameter(
                'interface',
                tip='Select segments in this interface.')],
        tip="Select segments from an interface definition.",
        discussion="""<para>
        Select all the &sgmts; that belong to the given interface definition.
        </para>"""
        )

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

class SelectNamedBoundarySegments(SegmentSelectionModifier):
    def __init__(self, boundary):
        self.boundary = boundary
    def select(self, skeleton, selection):
        bdy = skeleton.getBoundary(self.boundary) # A SkelContextEdgeBoundary
        bdyobj = bdy.boundary(skeleton.getObject()) # A CSkeletonEdgeBoundary
        if config.dimension() == 2:
            edges = [e.segment for e in bdyobj.edges]
        else:                   # dim = 3
            edges = bdyobj.getUnorientedSegments() # list of CSkeletonSegments
            # edges = [e.get_segment() for e in oredges] # 
        selection.start()
        selection.clear()
        selection.select(edges)
            

SegmentSelectionModRegistration(
    'Select Named Boundary',
    SelectNamedBoundarySegments,
    ordering=_namedBoundaryOrdering,
    params=[skeletongroupparams.SkeletonEdgeBoundaryParameter(
            'boundary',
            tip="Select segments in this boundary")],
    tip="Select segments belonging to the given skeleton edge boundary.",
    discussion="""<para>

    Select all the &sgmts; contained in the given &skel;
    <link linkend="Section-Concepts-Skeleton-Boundary">boundary</link>.
    The boundary must be a
    <link linkend="Section-Concepts-Skeleton-Boundary-Edge">edge</link>
    boundary.

    </para>"""
    )

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

class SelectPeriodicPartnerSegments(SegmentSelectionModifier):
    def select(self, skeleton, selection):
        oldsegs = skeleton.segmentselection.retrieve()
        newsegs = set()
        skel = skeleton.getObject()
        for seg in oldsegs:
            partner = seg.getPartner(skel)
            if partner:
                newsegs.add(partner)
        selection.start()
        selection.select(newsegs)

registeredclass.TwoDOnlyRegistration(
    'Select Periodic Partners',
    SegmentSelectionModifier,
    SelectPeriodicPartnerSegments,
    ordering=8,
    tip="Select the periodic partners of the currently selected Segments.",
    discussion="""<para>

    If the &skel; is <link
    linkend="Section-Concepts-Skeleton-Periodicity">periodic</link>,
    every &sgmt; on a periodic boundary has a partner on the opposite
    boundary.  This command selects the periodic partners of the
    currently selected &sgmts;, without unselecting any &sgmts;.

        </para>"""
    )

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

class SegmentHomogeneity(SegmentSelectionModifier):
    def __init__(self, threshold=0.9):
        self.threshold = threshold

    def select(self, skeleton, selection):
        selected = []
        skel = skeleton.getObject()
        for segment in skel.getSegments():
            if segment.homogeneity(skel) < self.threshold:
                selected.append(segment)
        selection.start()
        selection.clear()
        selection.select(selected)

SegmentSelectionModRegistration(
    'Select by Homogeneity',
    SegmentHomogeneity,
    ordering=_homogeneityOrdering,
    params = [parameter.FloatRangeParameter('threshold', (0.0, 1.0, 0.01),
                                            value=0.9,
                                            tip='The threshold homogeneity.')],
    tip="Select segments with homogeneity less than the given threshold.",
    discussion=xmlmenudump.loadFile(
        'DISCUSSIONS/engine/menu/hetero_segments.xml'))

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

class RandomSegments(SegmentSelectionModifier):
    def __init__(self, probability=0.5):
        self.probability = probability
    def select(self, skeleton, selection):
        selected = []
        skel = skeleton.getObject()
        for segment in skel.getSegments():
            if crandom.rndm() < self.probability:
                selected.append(segment)
        selection.start()
        selection.clear()
        selection.select(selected)

SegmentSelectionModRegistration(
    'Select Randomly',
    RandomSegments,
    ordering=100,
    params = [
        parameter.FloatRangeParameter(
            'probability', (0.0, 1.0, 0.01),
            value=0.5,
            tip='The probability of selecting a segment.')],
    tip="Select segments randomly.")

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

## TODO: Combine all group selection operations into one, using
## SelectionOperators.

# Select the indicated group.
class SegmentSelectGroup(SegmentSelectionModifier):
    def __init__(self, group):
        self.group = group
    def select(self, skeleton, selection):
        # Group retrieval may throw an exception -- do it first.
        members = skeleton.segmentgroups.get_group(self.group)
        selection.start()
        selection.clear()
        selection.select(members)

SegmentSelectionModRegistration(
    'Select Group',
    SegmentSelectGroup,
    ordering=_selectGroupOrdering,
    params=[skeletongroupparams.SegmentGroupParameter('group',
                                                      tip="Name of the group")],
    tip='Select the members of a group, discarding the current selection.',
    discussion="""<para>
    Select all of the &sgmts; in the given <link
    linkend='Section-Concepts-Skeleton-Groups'>group</link> after unselecting
    all of the currently selected &sgmts;.  To select
    <emphasis>only</emphasis> the &sgmts; in a group, retaining the
    previous selection, use <xref
    linkend='MenuItem-OOF.SegmentSelection.Select_Group'/>.
    </para>"""
)

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

# Unselect the indicated group.
class SegmentDeselectGroup(SegmentSelectionModifier):
    def __init__(self, group):
        self.group = group
    def select(self, skeleton, selection):
        members = skeleton.segmentgroups.get_group(self.group)
        selection.start()
        selection.deselect(members)

SegmentSelectionModRegistration(
    'Unselect Group',
    SegmentDeselectGroup,
    ordering=_unselectGroupOrdering,
    params=[
    skeletongroupparams.SegmentGroupParameter('group',
                                              tip="Segment group to select.")],
    tip='Unselect the members of a group.',
    discussion="""<para>
    Deselect all of the &sgmts; that are members of the specified
    <link linkend='Section-Concepts-Skeleton-Groups'>group</link>.
    Any &sgmts; that are members of the group but that are not
    currently selected will be unaffected.
    </para>""")

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

# Add the group to the selection, retaining the current selection.
class SegmentAddSelectGroup(SegmentSelectionModifier):
    def __init__(self, group):
        self.group = group
    def select(self, skeleton, selection):
        members = skeleton.segmentgroups.get_group(self.group)
        selection.start()
        selection.select(members)

SegmentSelectionModRegistration(
    'Add Group',
    SegmentAddSelectGroup,
    ordering=_addGroupOrdering,
    params=[
    skeletongroupparams.SegmentGroupParameter('group',
                                              tip="Segment group to select.")],
    tip='Select the members of a group, retaining the current selection.',
    discussion="""<para>
    Select all of the &sgmts; in the given <link
    linkend='Section-Concepts-Skeleton-Groups'>group</link> in
    addition to all of the currently selected &sgmts;.  To select
    <emphasis>only</emphasis> the &sgmts; in a group, discarding the
    previous selection, use <xref
    linkend='MenuItem-OOF.SegmentSelection.Select_Group'/>.
    </para>""")

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

# Select the intersection of the group and the selection.
class SegmentIntersectGroup(SegmentSelectionModifier):
    def __init__(self, group):
        self.group = group
    def select(self, skeleton, selection):
        slist = skeleton.segmentgroups.get_group(self.group)
        ilist = filter(lambda x: x.isSelected(), slist)
        selection.start()
        selection.clear()
        selection.select(ilist)

SegmentSelectionModRegistration(
    'Intersect Group',
    SegmentIntersectGroup,
    ordering=_intersectGroupOrdering,
    params=[
    skeletongroupparams.SegmentGroupParameter('group',
                                              tip="Segment group to select.")],
    tip='Select the intersection of a group and the current selection.',
    discussion="""<para>
    Select the &sgmts; that are both in the given <link
    linkend='Section-Concepts-Skeleton-Groups'>group</link> and in the
    current selection.
    </para>""")

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#
#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#
#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

# Face selection modifiers

# TODO 3.1: add more face selection modifiers.

class SelectInternalBoundaryFaces(FaceSelectionModifier):
    def select(self, skeleton, selection):
        skel = skeleton.getObject()
        ms = skeleton.getMicrostructure()
        faceset = set()
        for face in skel.getFaces():
            elements = skel.getFaceElements(face)
            if (len(elements) == 2 and
                (elements[0].dominantPixel(skel)
                 != elements[1].dominantPixel(skel))):
                faceset.add(face)
        selection.start()
        selection.clear()
        selection.select(faceset)

FaceSelectionModRegistration(
    'Select Internal Boundaries',
    SelectInternalBoundaryFaces,
    ordering=_internalBoundaryOrdering,
    tip="Select faces on material or group boundaries.")
                

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

class SelectNamedBoundaryFaces(FaceSelectionModifier):
    def __init__(self, boundary):
        self.boundary = boundary
    def select(self, skeleton, selection):
        bdy = skeleton.getBoundary(self.boundary)
        faces = bdy.boundary(skeleton.getObject()).getFaces()
        # faces is a set of OrientedCSkeletonFaces.
        selection.start()
        selection.clear()
        selection.select([f.get_face() for f in faces])

FaceSelectionModRegistration(
    'Select Named Boundary',
    SelectNamedBoundaryFaces,
    ordering=_namedBoundaryOrdering,
    params=[
        skeletongroupparams.SkeletonFaceBoundaryParameter(
            'boundary', tip='Select faces in this boundary')
        ],
    tip='Select faces belonging to the given skeleton face boundary.')

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

class FaceSelectGroup(FaceSelectionModifier):
    def __init__(self, group):
        self.group = group
    def select(self, skeleton, selection):
        members = skeleton.facegroups.get_group(self.group)
        selection.start()
        selection.clear()
        selection.select(members)

FaceSelectionModRegistration(
    'Select Group',
    FaceSelectGroup,
    ordering=_selectGroupOrdering,
    params=[
        skeletongroupparams.FaceGroupParameter('group',
                                               tip="Face group to select.")
        ],
    tip="Select the members of a group, discarding the current selection."
    )

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

## TODO: Combine all group selection operations into one, using
## SelectionOperators

class FaceDeselectGroup(FaceSelectionModifier):
    def __init__(self, group):
        self.group = group
    def select(self, skeleton, selection):
        members = skeleton.facegroups.get_group(self.group)
        selection.start()
        selection.deselect(members)

FaceSelectionModRegistration(
    'Unselect Group',
    FaceDeselectGroup,
    ordering=_unselectGroupOrdering,
    params=[
        skeletongroupparams.FaceGroupParameter(
            'group', tip='Face group to deselect.')],
    tip="Unselect the members of a group.")

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

class FaceAddSelectGroup(FaceSelectionModifier):
    def __init__(self, group):
        self.group = group
    def select(self, skeleton, selection):
        members = skeleton.facegroups.get_group(self.group)
        selection.start()
        selection.select(members)

FaceSelectionModRegistration(
    'Add Group',
    FaceAddSelectGroup,
    ordering=_addGroupOrdering,
    params=[
        skeletongroupparams.FaceGroupParameter('group',
                                               tip="Face group to select.")
        ],
    tip="Select the members of a group, retaining the current selection."
    )

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

class FaceIntersectGroup(FaceSelectionModifier):
    def __init__(self, group):
        self.group = group
    def select(self, skeleton, selection):
        flist = skeleton.facegroups.get_group(self.group)
        ilist = filter(lambda x: x.isSelected(), flist)
        selection.start()
        selection.clear()
        selection.select(ilist)

FaceSelectionModRegistration(
    'Intersect Group',
    FaceIntersectGroup,
    ordering=_intersectGroupOrdering,
    params=[
        skeletongroupparams.FaceGroupParameter('group',
                                               tip="Face group to select.")
        ],
    tip="Select the intersection of a group and the current selection."
    )

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

class FaceFromSelectedElements(FaceSelectionModifier):
    def __init__(self, coverage):
        self.coverage = coverage
    
    def select(self, skeleton, selection):
        if self.coverage == 'All':
            selected = self.getAllFaces(skeleton)
        elif self.coverage == 'Exterior':
            selected = self.getExteriorFaces(skeleton)
        else:                   # self.coverage == 'Interior'
            selected = self.getInternalFaces(skeleton)
        selection.start()
        selection.clear()
        selection.select(selected)

    def getAllFaces(self, skelctxt):
        faces = set()
        skel = skelctxt.getObject()
        for element in skelctxt.elementselection.retrieve():
            faces.update(skel.getElementFaces(element))
        return faces

    def getExteriorFaces(self, skelctxt):
        return skelctxt.exteriorFacesOfSelectedElements()

    def getInternalFaces(self, skelctxt):
        allfaces = self.getAllFaces(skelctxt)
        bdyfaces = self.getExteriorFaces(skelctxt)
        return allfaces - bdyfaces

FaceSelectionModRegistration(
    'Select from Selected Elements',
    FaceFromSelectedElements,
    ordering=_selectFromElementsOrdering,
    params = [
        enum.EnumParameter('coverage', ooflib.engine.coverage.Coverage)],
    tip="Select the faces of the selected elements.")

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

class FaceFromSelectedNodes(FaceSelectionModifier):
    def __init__(self, min_nodes):
        self.min_nodes = min_nodes
    def select(self, skeleton, selection):
        selected = set()
        skel = skeleton.getObject()
        if self.min_nodes == 1:
            for node in skeleton.nodeselection.retrieve():
                selected.update(skel.getNodeFaces(node))
        else:
            for node in skeleton.nodeselection.retrieve():
                for face in skel.getNodeFaces(node):
                    n = 0
                    for facenode in face.getNodes():
                        if facenode.isSelected():
                            n += 1
                    if n >= self.min_nodes:
                        selected.add(face)
        selection.start()
        selection.clear()
        selection.select(selected)

FaceSelectionModRegistration(
    'Select from Selected Nodes',
    FaceFromSelectedNodes,
    params=[
        parameter.IntRangeParameter(
            'min_nodes', (1, 3), value=1,
            tip="Select faces with at least this many selected nodes.")],
    ordering=_selectFromNodesOrdering,
    tip="Select every face containing selected nodes.")

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

class FaceFromSelectedSegments(FaceSelectionModifier):
    def select(self, skeleton, selection):
        selected = set()
        skel = skeleton.getObject()
        for seg in skeleton.segmentselection.retrieve():
            selected.update(skel.getSegmentFaces(seg))
        selection.start()
        selection.clear()
        selection.select(selected)

FaceSelectionModRegistration(
    'Select from Selected Segments',
    FaceFromSelectedSegments,
    ordering=_selectFromSegmentsOrdering,
    tip="Select every face adjacent to a selected segment.")

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#
#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#
#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

class ByElementMaterial(ElementSelectionModifier):
    def __init__(self, material):
        self.material = material
    def select(self, skeleton, selection):
        selected = []
        skel = skeleton.getObject()
        ms = skel.getMicrostructure()
        if self.material == '<Any>':
            for i in xrange(skel.nelements()):
                if skel.getElement(i).material(skel) is not None:
                    selected.append(skel.getElement(i))
        elif self.material == '<None>':
            for i in xrange(skel.nelements()):
                if skel.getElement(i).material(skel) is None:
                    selected.append(skel.getElement(i))
        else:
            for i in xrange(skel.nelements()):
                matl = skel.getElement(i).material(skel)
                if matl is not None and matl.name() == self.material:
                    selected.append(skel.getElement(i))
        selection.start()
        selection.clear()
        selection.select(selected)

ElementSelectionModRegistration(
    'Select by Material',
    ByElementMaterial,
    ordering=2.2,
    params=[materialparameter.AnyMaterialParameter('material',
                                tip="Select elements with this material.")],
    tip="Select all Elements with a given Material.",
    discussion=xmlmenudump.loadFile('DISCUSSIONS/engine/menu/bymaterial.xml'))

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

class ElementHomogeneity(ElementSelectionModifier):
    def __init__(self, threshold=0.9):
        self.threshold = threshold

    def select(self, skeleton, selection):
        selected = []
        skel = skeleton.getObject()
        ms = skel.getMicrostructure()
        for i in xrange(skel.nelements()):
            if skel.getElement(i).homogeneity(skel) < self.threshold:
                selected.append(skel.getElement(i))
        selection.start()
        selection.clear()
        selection.select(selected)

ElementSelectionModRegistration(
    'Select by Homogeneity',
    ElementHomogeneity,
    ordering=2.3,
    params = [
    parameter.FloatRangeParameter('threshold', (0.0, 1.0, 0.01), value=0.9,
                                  tip='Threshold homogeneity.')],
    tip="Select Elements with homogeneity less than the threshold homogeneity.",
    discussion=xmlmenudump.loadFile(
        'DISCUSSIONS/engine/menu/hetero_elements.xml')
    )

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

class ElementShapeEnergy(ElementSelectionModifier):
    def __init__(self, threshold = 0.8):
        self.threshold = threshold
    def select(self, skeleton, selection):
        selected = []
        skel = skeleton.getObject()
        for i in xrange(skel.nelements()):
            if skel.getElement(i).energyShape() > self.threshold:
                selected.append(skel.getElement(i))
        selection.start()
        selection.clear()
        selection.select(selected)

ElementSelectionModRegistration(
    'Select by Shape Energy',
    ElementShapeEnergy,
    ordering=2.4,
    params = [
    parameter.FloatRangeParameter(
            'threshold', (0.0, 1.0, 0.01), value=0.8,
            tip='Select Elements with shape-energy greater than this.')],
    tip="Select elements by shape-energy."
    " The greater the shape-energy the uglier the element.",
    discussion=xmlmenudump.loadFile(
        'DISCUSSIONS/engine/menu/element_by_shape.xml'))

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

class ElementIllegal(ElementSelectionModifier):
    def select(self, skeleton, selection):
        selected = []
        skel = skeleton.getObject()
        for i in xrange(skel.nelements()):
            if skel.getElement(i).illegal():
                selected.append(skel.getElement(i))
        selection.start()
        selection.clear()
        selection.select(selected)

ElementSelectionModRegistration(
    'Select Illegal Elements',
    ElementIllegal,
    ordering=2.5,
    tip="Select illegal elements.",
    discussion="""  <para>
    <command>Select_Illegal_Elements</command> selects all of the
    <link
    linkend="Section-Concepts-Skeleton-Illegality">illegal</link>
    &elems; in the given &skel;.  Illegal &elems; are hard to create,
    but if they have been created somehow, this command can be useful
    in eradicating them.
    </para>"""
    )

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

class ElementSuspect(ElementSelectionModifier):
    def select(self, skeleton, selection):
        selected = []
        skel = skeleton.getObject()
        for i in xrange(skel.nelements()):
            if skel.getElement(i).suspect():
                selected.append(skel.getElement(i))
        selection.start()
        selection.clear()
        selection.select(selected)

# TODO 3.1: need link for suspect elements concept
ElementSelectionModRegistration(
    'Select Suspect Elements',
    ElementSuspect,
    ordering=2.6,
    tip="Select suspect elements.",
    discussion="""  <para>
    <command>Select_Suspect_Elements</command> selects all of the
    <link
    linkend="Section-Concepts-Skeleton-Suspect">suspect</link>
    &elems; in the given &skel;.
    </para>"""
    )

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

class ElementFromSelectedNodes(ElementSelectionModifier):
    def __init__(self, min_nodes):
        self.min_nodes = min_nodes
    def select(self, skeleton, selection):
        selected = set()
        if self.min_nodes == 1:
            for node in skeleton.nodeselection.retrieve():
                selected.update(node.getElements())
        else:
            for node in skeleton.nodeselection.retrieve():
                for elem in node.getElements():
                    n = 0
                    for elemnode in elem.getNodes():
                        if elemnode.isSelected():
                            n += 1
                    if n >= self.min_nodes:
                        selected.add(elem)
        selection.start()
        selection.clear()
        selection.select(selected)

ElementSelectionModRegistration(
    'Select from Selected Nodes',
    ElementFromSelectedNodes,
    ordering=_selectFromNodesOrdering,
    params=[
        parameter.IntRangeParameter(
            'min_nodes', (1,4), value=1,
            tip='Select elements with at least this many selected nodes.')],
    tip="Select every element containing a selected node.",
    discussion=xmlmenudump.loadFile(
        'DISCUSSIONS/engine/menu/elements_from_nodes.xml'))

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

class ElementFromSelectedSegments(ElementSelectionModifier):
    def select(self, skeleton, selection):
        selected = set()
        skel = skeleton.getObject()
        for segment in skeleton.segmentselection.retrieve():
            selected.update(skel.getSegmentElements(segment))
        selection.start()
        selection.clear()
        selection.select(selected)

ElementSelectionModRegistration(
    'Select from Selected Segments',
    ElementFromSelectedSegments,
    ordering=_selectFromElementsOrdering,
    tip="Select every element adjacent to selected segments.",
    discussion=xmlmenudump.loadFile(
        'DISCUSSIONS/engine/menu/elements_from_segments.xml'))

class ElementFromSelectedFaces(ElementSelectionModifier):
    def select(self, skeleton, selection):
        selected = set()
        skel = skeleton.getObject()
        for face in skeleton.faceselection.retrieve():
            selected.update(skel.getFaceElements(face))
        selection.start()
        selection.clear()
        selection.select(selected)

ElementSelectionModRegistration(
    'Select from Selected Faces',
    ElementFromSelectedFaces,
    ordering=_selectFromFacesOrdering,
    tip='Select every element adjacent to selected faces.')

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

class ElementSelectionExpansionMode(enum.EnumClass(
        ("Faces",
         "Select Elements that share a Face with a selected Element."),
        ("Segments",
         "Select Elements that share a Segment with a selected Element."),
        ("Nodes", 
         "Select Elements that share a Node with a selected Element."))):
    tip="How to choose the neighboring Elements."

class ExpandElementSelection3D(ElementSelectionModifier):
    def __init__(self, mode):
        self.mode = mode
    def select(self, skeleton, selection):
        skel = skeleton.getObject()
        newelements = set()
        for element in selection.retrieve():
            if self.mode == "Faces":
                for face in skel.getElementFaces(element):
                    newelements.update(skel.getFaceElements(face))
            elif self.mode == "Nodes":
                for node in element.getNodes():
                    newelements.update(node.getElements())
            elif self.mode == "Segments":
                for segment in skel.getElementSegments(element):
                    newelements.update(skel.getSegmentElements(segment))
        selection.start()
        selection.clear()
        selection.select(newelements)
    
registeredclass.ThreeDOnlyRegistration(
    'Expand',
    ElementSelectionModifier,
    ExpandElementSelection3D,
    ordering=2.0,
    params=[
        enum.EnumParameter(
            'mode', ElementSelectionExpansionMode,
            ElementSelectionExpansionMode("Faces"),
            tip="How to choose neighboring Elements")],
    tip="Select the neighbors of the selected Elements.")


#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

# Select the indicated group.

class ElementSelectGroup(ElementSelectionModifier):
    def __init__(self, group):
        self.group = group
    def select(self, skeleton, selection):
        members = skeleton.elementgroups.get_group(self.group)
        selection.start()
        selection.clear()
        selection.select(members)

ElementSelectionModRegistration(
    'Select Group',
    ElementSelectGroup,
    ordering=_selectGroupOrdering,
    params=[
        skeletongroupparams.ElementGroupParameter('group',
                                                  tip="Name of the group.")
    ],
    tip='Select the members of a group, discarding the current selection.',
    discussion="""<para>
    Select all the &elems; in the given <link
    linkend='Section-Concepts-Skeleton-Groups'>group</link>.  The
    currently selected &elems; will first be deselected.  To select a
    group without first deselecting, use <xref
    linkend='MenuItem-OOF.ElementSelection.Add_Group'/>.
    </para>""")

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

# Unselect the indicated group.

class ElementDeselectGroup(ElementSelectionModifier):
    def __init__(self, group):
        self.group = group
    def select(self, skeleton, selection):
        members = skeleton.elementgroups.get_group(self.group)
        selection.start()
        selection.deselect(members)

ElementSelectionModRegistration(
    'Unselect Group',
    ElementDeselectGroup,
    ordering=_unselectGroupOrdering,
    params=[
    skeletongroupparams.ElementGroupParameter('group', tip="Name of the group.")
    ],
    tip='Unselect the members of a group.',
    discussion="""<para>
    Deselect all of the &elems; that are members of the specified
    <link linkend='Section-Concepts-Skeleton-Groups'>group</link>.
    Any &elems; that are members of the group but that are not
    currently selected will be unaffected.
    </para>""")

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

# Add the group to the selection, retaining the current selection.

class ElementAddSelectGroup(ElementSelectionModifier):
    def __init__(self, group):
        self.group = group
    def select(self, skeleton, selection):
        members = skeleton.elementgroups.get_group(self.group)
        selection.start()
        selection.select(members)

ElementSelectionModRegistration(
    'Add Group',
    ElementAddSelectGroup,
    ordering=_addGroupOrdering,
    params=[
    skeletongroupparams.ElementGroupParameter('group', tip="Name of the group.")
    ],
    tip='Select the members of a group, retaining the current selection.',
    discussion="""<para>
    Select all of the &elems; in the given <link
    linkend='Section-Concepts-Skeleton-Groups'>group</link> in
    addition to all of the currently selected &elems;.  To select
    <emphasis>only</emphasis> the &elems; in a group, discarding the
    previous selection, use <xref
    linkend='MenuItem-OOF.NodeSelection.Select_Group'/>.
    </para>"""
    )

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

# Select the intersection of the group and the selection.

class ElementIntersectGroup(ElementSelectionModifier):
    def __init__(self, group):
        self.group = group
    def select(self, skeleton, selection):
        elist = skeleton.elementgroups.get_group(self.group)
        ilist = filter(lambda x: x.isSelected(), elist)
        selection.start()
        selection.clear()
        selection.select(ilist)


ElementSelectionModRegistration(
    'Intersect Group',
    ElementIntersectGroup,
    ordering=_intersectGroupOrdering,
    params=[
    skeletongroupparams.ElementGroupParameter('group', tip="Name of the group.")
    ],
    tip='Select the intersection of a group and the current selection.',
    discussion="""<para>
    Select the &elems; that are both in the given <link
    linkend='Section-Concepts-Skeleton-Groups'>group</link> and in the
    current selection.
    </para>""")

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#

class ElementByPixelGroup(ElementSelectionModifier):
    def __init__(self, group):
        self.group = group
    def select(self, skeleton, selection):
        selected = []
        ms = skeleton.getMicrostructure()
        skel = skeleton.getObject()
        pxlgrp = ms.findGroup(self.group)
        for i in xrange(skel.nelements()):
            grpnames = pixelgroup.pixelGroupNames(
                ms, skel.getElement(i).dominantPixel(skel))
            if self.group in grpnames:
                selected.append(skel.getElement(i))
        selection.start()
        selection.clear()
        selection.select(selected)

ElementSelectionModRegistration(
    'Select by Pixel Group',
    ElementByPixelGroup,
    ordering=2.1,
    params=[pixelgroupparam.PixelGroupParameter(
            'group', tip='The name of a pixel group.')],
    tip="Select all Elements whose dominant pixel is in a given pixel group.",
    discussion="""<para>
    This command selects all &skel; &elems; whose
    <link linkend="Section-Concepts-Skeleton-Homogeneity">dominant pixel</link>
    is a member of the given &pixelgroup;.
   </para>""")

#=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=##=--=#
