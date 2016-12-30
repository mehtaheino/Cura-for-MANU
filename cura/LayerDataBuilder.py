# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from .Layer import Layer
from .LayerPolygon import LayerPolygon
from UM.Mesh.MeshBuilder import MeshBuilder
from .LayerData import LayerData

import numpy

## Builder class for constructing a LayerData object
class LayerDataBuilder(MeshBuilder):
    def __init__(self):
        super().__init__()
        self._layers = {}
        self._element_counts = {}

    def addLayer(self, layer):
        if layer not in self._layers:
            self._layers[layer] = Layer(layer)

    def addPolygon(self, layer, polygon_type, data, line_width):
        if layer not in self._layers:
            self.addLayer(layer)

        p = LayerPolygon(self, polygon_type, data, line_width)
        self._layers[layer].polygons.append(p)

    def getLayer(self, layer):
        if layer in self._layers:
            return self._layers[layer]

    def getLayers(self):
        return self._layers

    def getElementCounts(self):
        return self._element_counts

    def setLayerHeight(self, layer, height):
        if layer not in self._layers:
            self.addLayer(layer)

        self._layers[layer].setHeight(height)

    def setLayerThickness(self, layer, thickness):
        if layer not in self._layers:
            self.addLayer(layer)

        self._layers[layer].setThickness(thickness)

    #   material color map: [r, g, b, a] for each extruder row.
    def build(self, material_color_map):
        vertex_count = 0
        index_count = 0
        for layer, data in self._layers.items():
            vertex_count += data.lineMeshVertexCount()
            index_count += data.lineMeshElementCount()

        vertices = numpy.empty((vertex_count, 3), numpy.float32)
        line_dimensions = numpy.empty((vertex_count, 2), numpy.float32)
        colors = numpy.empty((vertex_count, 4), numpy.float32)
        indices = numpy.empty((index_count, 2), numpy.int32)
        extruders = numpy.empty((vertex_count), numpy.int32)
        line_types = numpy.empty((vertex_count), numpy.int32)

        vertex_offset = 0
        index_offset = 0
        for layer, data in self._layers.items():
            ( vertex_offset, index_offset ) = data.build( vertex_offset, index_offset, vertices, colors, line_dimensions, extruders, line_types, indices)
            self._element_counts[layer] = data.elementCount

        self.addVertices(vertices)
        self.addColors(colors)
        self.addIndices(indices.flatten())

        material_colors = numpy.zeros((line_dimensions.shape[0], 4), dtype=numpy.float32)
        for extruder_nr in range(material_color_map.shape[0]):
            material_colors[extruders == extruder_nr] = material_color_map[extruder_nr]
        material_colors[line_types == LayerPolygon.MoveCombingType] = [0.0, 0.0, 0.8, 1.0]
        material_colors[line_types == LayerPolygon.MoveRetractionType] = [0.0, 0.0, 0.8, 1.0]

        attributes = {
            "line_dimensions": {
                "value": line_dimensions,
                "opengl_name": "a_line_dim",
                "opengl_type": "vector2f"
                },
            "extruders": {
                "value": extruders,
                "opengl_name": "a_extruder",
                "opengl_type": "float"
                },
            "colors": {
                "value": material_colors,
                "opengl_name": "a_material_color",
                "opengl_type": "vector4f"
                },
            "line_types": {
                "value": line_types,
                "opengl_name": "a_line_type",
                "opengl_type": "float"
                }
            }

        return LayerData(vertices=self.getVertices(), normals=self.getNormals(), indices=self.getIndices(),
                        colors=self.getColors(), uvs=self.getUVCoordinates(), file_name=self.getFileName(),
                        center_position=self.getCenterPosition(), layers=self._layers,
                        element_counts=self._element_counts, attributes=attributes)
