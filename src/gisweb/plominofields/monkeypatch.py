"Monkey patch PlominoForm"
from Products.CMFPlomino.PlominoForm import PlominoForm
from Products.CMFPlomino.PlominoForm import PlominoView

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.CMFPlomino.config import READ_PERMISSION

PlominoIndex.security = ClassSecurityInfo()
#PlominoIndex.security.declareProtected(READ_PERMISSION, 'search_json')
PlominoIndex.security.declareProtected(READ_PERMISSION, 'search_documents')
InitializeClass(PlominoIndex)

# NEW VERSION 1.13.3
def readInputs(self, doc, REQUEST, process_attachments=False, applyhidewhen=True):
    """ read submitted values in REQUEST and store them in document according
    fields definition
    """
    all_fields = self.getFormFields(includesubforms=True, doc=doc, applyhidewhen=False)
#    if applyhidewhen:
#        displayed_fields = self.getFormFields(includesubforms=True, doc=doc, applyhidewhen=True)

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
#            else:
#                #the field was not submitted, probably because it is not part of the form (hide-when, ...)
#                #so we just let it unchanged, but with SELECTION or DOCLINK, we need to presume it was empty
#                #(as SELECT/checkbox/radio tags do not submit an empty value, they are just missing
#                #in the querystring)
#                if applyhidewhen and f in displayed_fields:
#                    fieldtype = f.getFieldType()
#                    if fieldtype == "SELECTION" or fieldtype == "DOCLINK":
#                        doc.removeItem(fieldName)

PlominoForm.readInputs = readInputs

def search_documents(self, start=1, limit=None, only_allowed=True,
    getObject=True, fulltext_query=None, sortindex=None, reverse=None,
    query_request={}):
    """
    Return all the documents matching the view and the custom filter criteria.
    """
    index = self.getParentDatabase().getIndex()
    if not sortindex:
        sortindex = self.getSortColumn()
        if sortindex=='':
            sortindex=None
        else:
            sortindex=self.getIndexKey(sortindex)
    if not reverse:
        reverse = self.getReverseSorting()
    query = {'PlominoViewFormula_'+self.getViewName() : True}
    query.update(query_request)
    
    if fulltext_query:
        query['SearchableText'] = fulltext_query
    results=index.dbsearch(
        query,
        sortindex=sortindex,
        reverse=reverse,
        only_allowed=only_allowed) # di fatto questo parametro NON viene usato dal metodo dbsearch
    if limit:
        results = Batch(items=results, pagesize=limit, pagenumber=int(start/limit)+1)
    if getObject:
        return [r.getObject() for r in results]
    else:
        return results

def search_json(self, REQUEST=None, query_request={}):
    """ Returns a JSON representation of view filtered data
    REQUEST:
        iDisplayStart, opz
        iDisplayLength, opz
        sSearch, opz
        
    """
    data = []
    categorized = self.getCategorized()
    start = 1
    limit = -1
    search = None
    sort_index = None
    if REQUEST:
        start = int(REQUEST.get('iDisplayStart', 1))
        iDisplayLength = REQUEST.get('iDisplayLength', None)
        if iDisplayLength:
            limit = int(iDisplayLength)
        search = REQUEST.get('sSearch', '').lower()
        if search:
            search = " ".join([term+'*' for term in search.split(' ')])
        sort_column = REQUEST.get('iSortCol_0')
        if sort_column:
            sort_index = self.getIndexKey(self.getColumns()[int(sort_column)-1].id)
        reverse = REQUEST.get('sSortDir_0', None) or 'asc'
        if reverse=='desc':
            reverse = 0
        if reverse=='asc':
            reverse = 1 
    if limit < 1:
        limit = None
    results = self.search_documents(start=start,
                                   limit=limit,
                                   getObject=False,
                                   fulltext_query=search,
                                   sortindex=sort_index,
                                   reverse=reverse,
                                   query_request=query_request)
    total = display_total = len(results)
    columnids = [col.id for col in self.getColumns() if not getattr(col, 'HiddenColumn', False)]
    for b in results:
        row = [b.getPath().split('/')[-1]]
        for colid in columnids:
            v = getattr(b, self.getIndexKey(colid), '')
            if isinstance(v, list):
                v = [asUnicode(e).encode('utf-8').replace('\r', '') for e in v]
            else:
                v = asUnicode(v).encode('utf-8').replace('\r', '')
            row.append(v or '&nbsp;')
        if categorized:
            for cat in asList(row[1]):
                entry = [c for c in row]
                entry[1] = cat
                data.append(entry)
        else:
            data.append(row)
    return json.dumps({ 'iTotalRecords': total, 'iTotalDisplayRecords': display_total, 'aaData': data })

PlominoView.search_documents = search_documents
PlominoView.search_json = search_json
