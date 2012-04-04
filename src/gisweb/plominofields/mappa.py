# -*- coding: utf-8 -*-
#
# File: mappa.py
#
# Copyright (c) 2011 by ['Marco Carbone']
#
# Zope Public License (ZPL)
#

__author__ = """Marco Carbone <marco.carbone@gisweb.it>"""
__docformat__ = 'plaintext'


from zope.formlib import form
from zope.interface import implements
from zope.schema import getFields
from zope.schema import TextLine, Text, List, Bool
from zope.schema.vocabulary import SimpleVocabulary
from zope import component
from dictionaryproperty import DictionaryProperty
from zope.pagetemplate.pagetemplatefile import PageTemplateFile
from z3c.form.browser import checkbox
import simplejson as json

from Products.CMFPlomino.interfaces import IPlominoField
from Products.CMFPlomino.fields.dictionaryproperty import DictionaryProperty

from base import IBaseField, BaseField, BaseForm


class IMappaField(IBaseField):
    """
    Mappa field schema
    """
    

    service = TextLine(title=u'Servizio',
                description=u'URL Servizio che restituisce la mappa',
                required=True)
    mapset = TextLine(title=u'Mapset',
                description=u'Nome del mapset',
                required=True)
    width =  TextLine(title=u'Larghezza',
                description=u'Larghezza della mappa espressa in pixel',
                default=u'600',
                required=True)
    height =  TextLine(title=u'Altezza',
                description=u'Altezza della mappa espressa in pixel',
                default=u'450',
                required=True)
    point = Bool(title = u'Tipo di geometria : Punto',
                   description = u'Tipo di geometria : Punto',
                   required = False,
                   default = False)
    line = Bool(title = u'Tipo di geometria : Linea',
                   description = u'Tipo di geometria : Linea',
                   required = False,
                   default = False)
    polygon = Bool(title = u'Tipo di geometria : Poligono',
                   description = u'Tipo di geometria : Poligono',
                   required = False,
                   default = False)
    mappaprm = List(title=u'Parametri della mappa',
                      description=u'Parametri da passare al servizio di visualizzazione della mappa (es. legend=1)',
                      required=False,
                      default=[],
                      value_type=TextLine(title=u'Entry'))



class MappaField(BaseField):
    """
    """
    implements(IMappaField)
    
    plomino_field_parameters = {'interface': IMappaField,
                                'label':"Mappa",
                                'index_type':"FieldIndex"}

    read_template = PageTemplateFile('mappa_read.pt')
    edit_template = PageTemplateFile('mappa_edit.pt')


    def tojson(self, value):
        """
        """
        if value is None or value == "":
            value = {}
        if isinstance(value, basestring):
            return value
        return json.dumps(value)
    
    def validate(self, submittedValue):
        """
        """
        errors=[]
        fieldname = self.context.id
        submittedValue = submittedValue.strip()
        try:
            if submittedValue:
                prmList=submittedValue.split(';')
                if len(prmList)!=5:
                    errors.append(fieldname+' deve essere una stringa rappresentante una geometria valida "EPSG;GEOMETRY;X;Y;SCALE" valore immesso : '+submittedValue)
                else:
                    if prmList[0].find('EPSG:')!=0:
                        errors.append('Manca la parte di EPSG : '+prmList[0])

                
        except:
            errors.append(fieldname+' deve essere una stringa rappresentante una geometria valida "EPSG;GEOMETRY;X;Y;SCALE" valore immesso : '+submittedValue)

        return errors

    
    def processInput(self, submittedValue):
        """
        """
        #try:
        #    return json.loads(submittedValue)
        #except:
        #    return {}
        obj={'srid':None,'geometry':None,'x':None,'y':None,'scale':None}
        if submittedValue:
            prmList=submittedValue.split(';')
            obj['srid']=prmList[0].replace('EPSG:','')
            obj['geometry']=prmList[1]
            obj['x']=prmList[2]
            obj['y']=prmList[3]
            obj['scale']=prmList[4]
        return obj

    def getFieldValue(self, form, doc, editmode, creation, request):
        """
        """
        fieldValue = BaseField.getFieldValue(self, form, doc, editmode, creation, request)
        
        mode = self.context.getFieldMode()

        if mode=="EDITABLE":
            if doc is None and not(creation) and request is not None:
                fieldValue = request.get(fieldName, '')
                #if not(fieldValue=='' or fieldValue is None):
                    #fieldValue = self.tojson(fieldvalue)
                    
        if fieldValue:
            return 'EPSG:'+fieldValue['srid']+';'+fieldValue['geometry']+';'+fieldValue['x']+';'+fieldValue['y']+';'+fieldValue['scale']
        else:
            return ''          

component.provideUtility(MappaField, IPlominoField, 'MAPPA')

for f in getFields(IMappaField).values():
    setattr(MappaField, f.getName(), DictionaryProperty(f, 'parameters'))

class SettingForm(BaseForm):
    """
    """
    form_fields = form.Fields(IMappaField)

