from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True, slots=True)
class OperatorSpec:
    """Mapping from a stable IR operator to a Blender node identifier."""

    blender_idname: str
    min_blender: tuple[int, int] = (4, 2)


_SPECS = {
    # Geometry sources.
    "primitive.box": OperatorSpec("GeometryNodeMeshCube"),
    "primitive.cylinder": OperatorSpec("GeometryNodeMeshCylinder"),
    "primitive.frustum": OperatorSpec("GeometryNodeMeshCone"),
    "primitive.icosphere": OperatorSpec("GeometryNodeMeshIcoSphere"),
    "primitive.grid": OperatorSpec("GeometryNodeMeshGrid"),
    "primitive.mesh_line": OperatorSpec("GeometryNodeMeshLine"),
    "primitive.mesh_circle": OperatorSpec("GeometryNodeMeshCircle"),
    "profile.line": OperatorSpec("GeometryNodeCurvePrimitiveLine"),
    "profile.circle": OperatorSpec("GeometryNodeCurvePrimitiveCircle"),
    "profile.quadrilateral": OperatorSpec("GeometryNodeCurvePrimitiveQuadrilateral"),
    "profile.arc": OperatorSpec("GeometryNodeCurveArc"),
    "profile.spiral": OperatorSpec("GeometryNodeCurveSpiral"),
    "profile.text": OperatorSpec("GeometryNodeStringToCurves"),
    # Fabrication and modification.
    "fabricate.sweep": OperatorSpec("GeometryNodeCurveToMesh"),
    "fabricate.fill_profile": OperatorSpec("GeometryNodeFillCurve"),
    "fabricate.extrude_elements": OperatorSpec("GeometryNodeExtrudeMesh"),
    "modify.transform": OperatorSpec("GeometryNodeTransform"),
    "modify.set_position": OperatorSpec("GeometryNodeSetPosition"),
    "modify.scale_elements": OperatorSpec("GeometryNodeScaleElements"),
    "modify.subdivide": OperatorSpec("GeometryNodeSubdivideMesh"),
    "modify.subdivision_surface": OperatorSpec("GeometryNodeSubdivisionSurface"),
    "modify.merge_by_distance": OperatorSpec("GeometryNodeMergeByDistance"),
    "modify.flip_faces": OperatorSpec("GeometryNodeFlipFaces"),
    "modify.delete_elements": OperatorSpec("GeometryNodeDeleteGeometry"),
    "modify.set_curve_radius": OperatorSpec("GeometryNodeSetCurveRadius"),
    "modify.set_curve_tilt": OperatorSpec("GeometryNodeSetCurveTilt"),
    "modify.fillet_curve": OperatorSpec("GeometryNodeFilletCurve"),
    "modify.resample_curve": OperatorSpec("GeometryNodeResampleCurve"),
    "modify.mesh_to_curve": OperatorSpec("GeometryNodeMeshToCurve"),
    "modify.triangulate": OperatorSpec("GeometryNodeTriangulate"),
    "modify.boolean": OperatorSpec("GeometryNodeMeshBoolean"),
    # Composition and instances.
    "compose.join": OperatorSpec("GeometryNodeJoinGeometry"),
    "compose.boolean": OperatorSpec("GeometryNodeMeshBoolean"),
    "compose.separate": OperatorSpec("GeometryNodeSeparateGeometry"),
    "instance.wrap": OperatorSpec("GeometryNodeGeometryToInstance"),
    "instance.duplicate": OperatorSpec("GeometryNodeDuplicateElements"),
    "instance.on_points": OperatorSpec("GeometryNodeInstanceOnPoints"),
    "instance.rotate": OperatorSpec("GeometryNodeRotateInstances"),
    "instance.realize": OperatorSpec("GeometryNodeRealizeInstances"),
    # Fields and queries.
    "field.position": OperatorSpec("GeometryNodeInputPosition"),
    "field.index": OperatorSpec("GeometryNodeInputIndex"),
    "field.spline_parameter": OperatorSpec("GeometryNodeSplineParameter"),
    "field.curve_endpoints": OperatorSpec("GeometryNodeCurveEndpointSelection"),
    "field.bounds": OperatorSpec("GeometryNodeBoundBox"),
    "field.statistic": OperatorSpec("GeometryNodeAttributeStatistic"),
    "field.domain_size": OperatorSpec("GeometryNodeAttributeDomainSize"),
    "field.sample_curve": OperatorSpec("GeometryNodeSampleCurve"),
    "field.scalar_math": OperatorSpec("ShaderNodeMath"),
    "field.vector_math": OperatorSpec("ShaderNodeVectorMath"),
    "field.combine_xyz": OperatorSpec("ShaderNodeCombineXYZ"),
    "field.separate_xyz": OperatorSpec("ShaderNodeSeparateXYZ"),
    "field.map_range": OperatorSpec("ShaderNodeMapRange"),
    "field.rotate_vector": OperatorSpec("ShaderNodeVectorRotate"),
    "field.boolean_math": OperatorSpec("FunctionNodeBooleanMath"),
    "field.compare": OperatorSpec("FunctionNodeCompare"),
    "field.align_rotation": OperatorSpec("FunctionNodeAlignRotationToVector"),
    "field.switch": OperatorSpec("GeometryNodeSwitch"),
    "field.named_attribute": OperatorSpec("GeometryNodeInputNamedAttribute"),
}

OPERATORS = MappingProxyType(_SPECS)


def operator_spec(name: str) -> OperatorSpec | None:
    return OPERATORS.get(name)
