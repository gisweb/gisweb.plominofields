# -*- coding: utf-8 -*-
#
# File: text.py
#
# Copyright (c) 2008 by ['Eric BREHAULT']
#
# Zope Public License (ZPL)
#

__author__ = """Eric BREHAULT <eric.brehault@makina-corpus.com>"""
__docformat__ = 'plaintext'

from zope.formlib import form
from zope.interface import implements
from zope.schema import getFields
from zope.schema import TextLine, Text
from zope.pagetemplate.pagetemplatefile import PageTemplateFile
from Products.CMFPlomino.fields.dictionaryproperty import DictionaryProperty
from zope import component
from Products.CMFPlomino.fields.base import IBaseField, BaseField, BaseForm
from Products.CMFPlomino.interfaces import IPlominoField

class IAutoSuggestField(IBaseField):
    """
    Text field schema
    """
    service = TextLine(title=u'Servizio',
                description=u'URL del Servizio. Il servizio deve rispondere una jsonString rappresentante un array di dictionaries con campi id,label,value ',
                required=True)
    size = TextLine(title=u'Size',
                description=u'Length or rows (depending on the widget)',
                required=False)
    minlength = TextLine(title=u'Lunghezza Minima',
                description=u'Lunghezza minima della stringa per attivare l\'autosuggest',
                default=u'1',
                required=False)
    fields = TextLine(title=u'parametri della richiesta',
                description=u'Elenco dei campi del form, separati da , che devono essere passati nella richiesta',
                default=u'',
                required=False)
    selectEvent = Text(title=u'Javascript settings',
                description=u'jQuery autocomplete function body for select event',
                default=u"""
        return true;
""",
                required=True)

class AutoSuggestField(BaseField):
    """
    """
    implements(IAutoSuggestField)
    plomino_field_parameters = {'interface': IAutoSuggestField,
                            'label':"AutoSuggest",
                            'index_type':"FieldIndex"}

    read_template = PageTemplateFile('autosuggest_read.pt')
    edit_template = PageTemplateFile('autosuggest_edit.pt')
    
    def getParameters(self):
        """
        """
        return self.jssettings

component.provideUtility(AutoSuggestField, IPlominoField, 'AutoSuggest')

for f in getFields(IAutoSuggestField).values():
    setattr(AutoSuggestField, f.getName(), DictionaryProperty(f, 'parameters'))

class SettingForm(BaseForm):
    """
    """
    form_fields = form.Fields(IAutoSuggestField)
