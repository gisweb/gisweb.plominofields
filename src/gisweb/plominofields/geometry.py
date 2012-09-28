# -*- coding: utf-8 -*-
#
# File: geometry.py
#
#
#
# Zope Public License (ZPL)
#

__author__ = """Manuele PESENTI <manuele.pesenti@gisweb.it>"""
__docformat__ = 'plaintext'

from zope.formlib import form
from zope.interface import implements
from zope.schema import getFields
from zope.schema import TextLine
from zope import component
from zope.pagetemplate.pagetemplatefile import PageTemplateFile

from Products.CMFPlomino.PlominoUtils import StringToDate, DateToString

from Products.CMFPlomino.interfaces import IPlominoField
from Products.CMFPlomino.fields.dictionaryproperty import DictionaryProperty

from Products.CMFPlomino.fields.base import IBaseField, BaseField,BaseForm

import ogr, osr

try:
    import json
except ImportError:
    import simplejson as json
    
def CreateGeometryFromGoogleText(string, srid=4326):
    """
    string: 'lat1 lon1, lat2 lon2, ...'
    POINT(10 20)
    # MULTIPOINT (10 20,30 20)
    LINESTRING(0 0, 10 10)
    POLYGON((0 0, 10 10, 10 0, 0 0))
    # MULTIPOLYGON (((5 5,0 0,0 10,5 5)),((5 5,10 10,10 0,5 5)))
    """

    points = string.split(',')

    if not points:
        the_geom = ogr.CreateGeometryFromWkt('POINT EMPTY')

    # un solo punto
    if len(points)==1:
        # geometryName, geometryType = 'POINT', ogr.wkbPoint
        the_geom = ogr.Geometry(ogr.wkbPoint)
        x, y = map(float, points.split(' '))
        the_geom.AddPoint_2D(x, y)
    
    # più di due punti con estremi coincidenti
    if len(points)>2 and points[0] == points[-1]:
    
        inner_geom = ogr.Geometry(ogr.wkbLinearRing)
        for x, y in [map(float, coords.split(' ')) for coords in points]:
            the_geom.AddPoint_2D(x, y)
        the_geom = ogr.Geometry(ogr.wkbPolygon)
        the_geom.AddGeometry(inner_geom)
    
    # più di un punto
    else:
        the_geom = ogr.Geometry(ogr.wkbLineString)
        for x, y in [map(float, coords.split(' ')) for coords in points]:
            the_geom.AddPoint_2D(x, y)
        
    SR = osr.SpatialReference()
    SR.ImportFromEPSG(srid)
    the_geom.AssignSpatialReference(SR)
    
    return the_geom


class IGeometryField(IBaseField):
    """
    Geometries field schema
    """

class GeometryField(BaseField):
    """
    """
    implements(IGeometryField)
    
    plomino_field_parameters = {'interface': IGeometryField,
                                'label': "Geometry",
                                'index_type': "FieldIndex"}

    read_template = PageTemplateFile('text_read.pt')
    edit_template = PageTemplateFile('text_edit.pt')

    def getParameters(self):
        """
        Get field parameters
        """
        return self.jssettings
    
    def processInput(self, submittedValue, import_from='GoogleText'):
        """
        """
        errors=[]
        fieldname = self.context.id
        
        # il valore passato potrebbe contenere anche il codice EPSG
        # es: 'EPSG:4326, 8 44, 9 43 ...'
        geom_text = submittedValue.strip()
        
        if import_from == 'GoogleText':
            if geom_text.startswith('EPSG'):
                n = geom_text.index(',')
                return CreateGeometryFromGoogleText(geom_text[n+1:].strip(), srid=geom_text[5:n])
            return CreateGeometryFromGoogleText(geom_text)
        
        if import_from == 'WKT':
            return ogr.CreateGeometryFromWkt(geom_text)
            
        if import_from == 'WKT':
            return ogr.CreateGeometryFromWkt(geom_text)
    
    def validate(self, submittedValue, import_from='GoogleText'):
        """
        """
        errors=[]
        fieldname = self.context.id
        submittedValue = submittedValue.strip()
        
        try:
            self.processInput(submittedValue, import_from=import_from)
        except Exception as Error:
            errors.append('%s' % Error)
        
        return errors
        
    def getFieldValue(self, form, doc, editmode, creation, request, import_from='GoogleText'):
        """
        """
        fieldValue = BaseField.getFieldValue(self, form, doc, editmode, creation, request)

        mode = self.context.getFieldMode()

        if mode=="EDITABLE":
            if doc is None and not(creation) and request is not None:
                fieldName = self.context.id 
                fieldValue = request.get(fieldName, '')
                if not(fieldValue=='' or fieldValue is None):
                    fieldValue = self.processInput(submittedValue, import_from=import_from)
        return fieldValue
    
    def ExportToGoogleText(self, itemValue):
        """
        """
        obj = itemValue.ExportToJson()
        if obj['Type'] == 'Polygon':
            obj.CloseRings()
            bound = obj.GetBoundary()
            points = bound.GetPoints()
        else:
            points = itemValue.GetPoints()
        
        point_list = [list(x[:2]) for x in points]
        string_list = [' '.join(map(str, x)) for x in ll]
        
        return ','.join(string_list)
    
component.provideUtility(GeometryField, IPlominoField, 'GEOMETRY')

for f in getFields(IGeometryField).values():
    setattr(GeometryField, f.getName(), DictionaryProperty(f, 'parameters'))

class SettingForm(BaseForm):
    """
    """
    form_fields = form.Fields(IGeometryField)
