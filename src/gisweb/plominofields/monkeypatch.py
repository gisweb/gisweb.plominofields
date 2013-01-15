"Monkey patch PlominoForm"
from Products.CMFPlomino.PlominoUtils import asUnicode, asList
from jsonutil import jsonutil as json

from plone.app.content.batching import Batch

from Products.CMFPlomino.PlominoForm import PlominoForm
from Products.CMFPlomino.PlominoView import PlominoView

from Products.CMFPlomino.index import PlominoIndex
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.CMFPlomino.config import READ_PERMISSION

PlominoIndex.security = ClassSecurityInfo()
PlominoIndex.security.declareProtected(READ_PERMISSION, 'search_json')
PlominoIndex.security.declareProtected(READ_PERMISSION, 'search_documents')
InitializeClass(PlominoView)

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

# elenco degli opratori supportati in formato chiave, etichetta
op_match = {
    'gt': 'Maggiore di',
    'lt': 'Minore di',
    'wi': 'Compreso tra'
}

def search_documents(self, start=1, limit=None, only_allowed=True,
    getObject=True, fulltext_query=None, sortindex=None, reverse=None,
    query_request={}):
    """
    Return all the documents matching the view and the custom filter criteria.
    """
    pdb = self.getParentDatabase()
    index = pdb.getIndex()
    if not sortindex:
        sortindex = self.getSortColumn()
        if sortindex=='':
            sortindex=None
        else:
            sortindex=self.getIndexKey(sortindex)
    if not reverse:
        reverse = self.getReverseSorting()
    query = {'PlominoViewFormula_'+self.getViewName() : True}

    total = len(index.dbsearch(query, only_allowed=only_allowed))

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
        return [r.getObject() for r in results], total
    else:
        return results, total

def search_json(self, REQUEST=None):
    """ Returns a JSON representation of view filtered data
    """
    data = []
    categorized = self.getCategorized()
    start = 1
    search = None
    sort_index = None
    reverse = 1

    if REQUEST:
        start = int(REQUEST.get('iDisplayStart', 1))

        limit = REQUEST.get('iDisplayLength')
        # In case limit == -1 we want it to be None
        limit = (limit and int(limit)) and None

        search = REQUEST.get('sSearch', '').lower()
        if search:
            search = " ".join([term+'*' for term in search.split(' ')])
        sort_column = REQUEST.get('iSortCol_0')
        if sort_column:
            sort_index = self.getIndexKey(self.getColumns()[int(sort_column)-1].id)
        reverse = REQUEST.get('sSortDir_0') or 'asc'
        if reverse=='desc':
            reverse = 0
        if reverse=='asc':
            reverse = 1

    query_request = json.loads(REQUEST['query'])

    results, total = self.search_documents(start=1,
                                   limit=None,
                                   getObject=False,
                                   fulltext_query=search,
                                   sortindex=sort_index,
                                   reverse=reverse,
                                   query_request=query_request)

    if limit:
        results = Batch(items=results, pagesize=limit, pagenumber=int(start/limit)+1)
    display_total = len(results)

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
PlominoView.supported_query_operators = op_match


from persistent.dict import PersistentDict
def TemporaryDocument__init__(self, parent, form, REQUEST, real_doc=None):
    self._parent=parent
    if real_doc is not None:
        self.items=PersistentDict(real_doc.items)
        self.real_id=real_doc.id
    else:
        self.items={}
        self.real_id="TEMPDOC"
    self.setItem('Form', form.getFormName())
    form.readInputs(self, REQUEST)
    self._REQUEST=REQUEST
from Products.CMFPlomino.PlominoDocument import TemporaryDocument
TemporaryDocument.__init__ = TemporaryDocument__init__
