# -*- coding: utf-8 -*-
#
# File: date.py
#
# Copyright (c) 2009 by ['Eric BREHAULT']
#
# Zope Public License (ZPL)
#

__author__ = """Eric BREHAULT <eric.brehault@makina-corpus.com>"""
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

class IDateField(IBaseField):
    """
    Date field schema
    """
    format = TextLine(title=u'Format',
                      description=u'Date format (if different than database default format)',
                      required=False)
    startingyear = TextLine(title=u'Starting year',
                      description=u'Oldest year selectable in the calendar widget',
                      required=False)


class DateField(BaseField):
    """
    """
    implements(IDateField)
    
    plomino_field_parameters = {'interface': IDateField,
                                'label':"Date",
                                'index_type':"FieldIndex"}

    read_template = PageTemplateFile('date_read.pt')
    edit_template = PageTemplateFile('date_edit.pt')

    def validate(self, submittedValue):
        """
        """
        errors=[]
        fieldname = self.context.id
        submittedValue = submittedValue.strip()
        try:
            # calendar widget default format is '%Y-%m-%d %H:%M' and might use the AM/PM format
            if submittedValue[-2:] in ['AM', 'PM']:
                StringToDate(submittedValue, '%d/%m/%Y')
            else:
                StringToDate(submittedValue, '%d/%m/%Y')
        except:
            errors.append(fieldname+" must be a date/time (submitted value was: "+submittedValue+")")
        return errors

    def processInput(self, submittedValue):
        """
        """
        submittedValue = submittedValue.strip().replace('-','/')
        # calendar widget default format is '%Y-%m-%d' and might use the AM/PM format
        if not submittedValue:
            return None
        if submittedValue[-2:] in ['AM', 'PM']:
            d = StringToDate(submittedValue, '%d/%m/%Y')
        else:
            try:
                d = StringToDate(submittedValue, '%d/%m/%Y')
            except:
                d = StringToDate(DateToString(StringToDate(submittedValue, '%Y/%m/%d'),'%d/%m/%Y'), '%d/%m/%Y')
        return d

    def getFieldValue(self, form, doc, editmode, creation, request):
        """
        """
        fieldValue = BaseField.getFieldValue(self, form, doc, editmode, creation, request)

        mode = self.context.getFieldMode()

        if mode=="EDITABLE":
            if doc is None and not(creation) and request is not None:
                fieldName = self.context.id 
                fieldValue = request.get(fieldName, '')
                if not(fieldValue=='' or fieldValue is None):
                    fieldValue = StringToDate(fieldValue, form.getParentDatabase().getDateTimeFormat())
        return fieldValue

component.provideUtility(DateField, IPlominoField, 'DATE')

for f in getFields(IDateField).values():
    setattr(DateField, f.getName(), DictionaryProperty(f, 'parameters'))

class SettingForm(BaseForm):
    """
    """
    form_fields = form.Fields(IDateField)

