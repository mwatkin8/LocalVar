import fileIO

def buildTable(header,record):
    th = ''
    for f in header.fields:
        th += '<th>' + f.strip() + '</th>\n'
    tr = '<tr id=\"' + record.id + '\">'
    idx = 0
    for f in record.fields:
        if idx == 0 or idx == len(header.fields) - 1:
            tr += '<td>' + f.strip() + '</td>\n'
        else:
            tr += '<td><div class=\"edit-cells\" contenteditable>' + f.strip() + '</div></td>\n'
        idx += 1
    tr += '</tr>'
    return th,tr

def compileEdits(id):
    history = fileIO.readHistory()
    edits = '<b>' + history["entries"][id]["record added"] + '</b>\n<i>record added</i>\n\n'
    for e in history["entries"][id]["edits"]:
        if "timestamp" in e:
            edits += '<b>' + e["timestamp"] + '</b>\n' + '<i>' + [*e][0] + '</i>\n' + e[[*e][0]] + '\n\n'
        else:
            edits += '<b>' + e[[*e][0]] + '</b>\n' + '<i>' + [*e][0] + '</i>\n\n'
    return edits

def compileClinVarInfo(record):
    li = ''
    try:
        bins = fileIO.readBins()
        cv_int = bins[record.hgvs]["ClinVar Interpretation"]
        for s in bins[record.hgvs]["ClinVar Synonyms"]:
            li += '<li class="mb-2">' + s["HGVS"] + '</li>'
        synonyms = '<ul style="list-style:none" class="pl-0">' + li + '</ul>'
        evidence = 'https://www.ncbi.nlm.nih.gov/clinvar/' + bins[record.hgvs]["ClinVar VariationID"]
    except:
        cv_int = 'None'
        synonyms = 'None'
        evidence = '#'
    return cv_int,synonyms,evidence
