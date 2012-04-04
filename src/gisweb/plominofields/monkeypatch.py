"Monkey patch PlominoForm"
from Products.CMFPlomino import PlominoForm

def readInputs(self, doc, REQUEST, process_attachments=False, applyhidewhen=True):
    """ read submitted values in REQUEST and store them in document according
    fields definition
    """
    all_fields = self.getFormFields(includesubforms=True, doc=doc, applyhidewhen=False)
    # if applyhidewhen:
    #     displayed_fields = self.getFormFields(includesubforms=True, doc=doc, applyhidewhen=True)

    for f in all_fields:
        mode = f.getFieldMode()
        fieldName = f.id
        if mode=="EDITABLE":
            submittedValue = REQUEST.get(fieldName)
            if submittedValue is not None:
                if submittedValue=='':
                    doc.removeItem(fieldName)
                else:
                    v = f.processInput(submittedValue, doc, process_attachments)
                    doc.setItem(fieldName, v)
               # else:
               #     #the field was not submitted, probably because it is not part of the form (hide-when, ...)
               #     #so we just let it unchanged, but with SELECTION or DOCLINK, we need to presume it was empty
               #     #(as SELECT/checkbox/radio tags do not submit an empty value, they are just missing
               #     #in the querystring)
               #     if applyhidewhen and f in displayed_fields:
               #         fieldtype = f.getFieldType()
               #         if fieldtype == "SELECTION" or fieldtype == "DOCLINK":
               #             doc.removeItem(fieldName)

PlominoForm.readInputs = readInputs