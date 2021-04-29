from flask import abort, Flask, flash, render_template, request, redirect, send_from_directory, make_response, session
import os, time, json, random
import fileIO, recordCRUD, suggestions, detail, trash
from recordCRUD import Header, Record

# create the application object
app = Flask(__name__, static_folder='static')
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# GENERAL ROUTING
@app.route('/')
def baseView():
    if fileIO.checkEmpty():
        return render_template('new-collection.html', alert='false', selected='new-collection', filename='None Selected', colnames='')
    else:
        table = buildTable()
        bins = fileIO.readBins()
        return render_template('viewer.html', selected='viewer', table=table, bins=bins, hgvs_array=[*bins])

@app.route('/new-collection')
def new():
    if fileIO.checkEmpty():
        return render_template('new-collection.html', alert='false', selected='new-collection', filename='None Selected', colnames='', warning='False')
    else:
        return render_template('new-collection.html', alert='false', selected='new-collection', filename='', colnames='', warning='True')

@app.route('/upload', methods=['POST'])
def upload():
    r = make_response(redirect(request.referrer))
    #check if the post request has the file part
    if 'file' not in request.files:
        return r
    file = request.files['file']
    read = file.read()
    file_content = read.decode()
    file.seek(0)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
    cols = file_content.split('\n')[0].strip()
    fileIO.createFiles(file.filename.split('.')[0])
    return render_template('new-collection.html', selected='new-collection', filename=file.filename, colnames=cols, warning='False')

@app.route('/load', methods=['POST'])
def load():
    r = make_response(redirect(request.referrer))
    hgvs_col = request.form.get('hgvsSelect')
    int_col = request.form.get('intSelect')
    history = {}
    history["file uploaded"] = timestamp()
    history["entries"] = {}
    recordCRUD.init(hgvs_col, int_col, fileIO.readUpload(), history)
    return redirect('/')

@app.route('/new', methods=['POST'])
def addEntry():
    alert = 'false'
    #Get the new entry/entries from the HTML form
    new_content = request.form.get('new-entry')
    recordCRUD.addRecord(new_content)
    return redirect('/')

@app.route('/save', methods=['POST'])
def saveEdit():
    row = request.form.get('row')
    row = row.replace('&lt;','<')
    row = row.replace('&gt;','>')
    fields = row.split(',')
    id = fields[0]
    recordCRUD.editRecord(fields)
    return redirect("/detail?id=" + id)

@app.route('/detail')
def detailView():
    id = request.args.get('id')
    collection_map = fileIO.readCollectionMap()
    record = collection_map[id]
    header = collection_map['HEADER']
    th,tr = detail.buildTable(header,record)
    edits = detail.compileEdits(id)
    cv_int,synonyms,evidence = detail.compileClinVarInfo(record)
    return render_template('detail.html', selected='viewer', evidence=evidence, cv_int=cv_int, synonyms=synonyms, hgvs=record.hgvs, int=record.int, id=record.id, header=th, row=tr, edits=edits)

@app.route('/trash')
def trashView():
    if fileIO.checkEmpty():
        return render_template('new-collection.html', alert='false', selected='new-collection', filename='None Selected', colnames='')
    else:
        id = request.args.get('id')
        if id:
            trash.moveToTrash(id)
        table,total = trash.buildTrash()
        return render_template('trash.html', selected='trash', table=table, total=total)

@app.route('/about')
def about():
    type = request.args.get('type')
    if type == 'vrs':
        return render_template('about-vrs.html', selected='about-vrs')
    else:
        return render_template('about-localvar.html', selected='about-localvar')

@app.route('/file')
def file():
    if fileIO.checkEmpty():
        return render_template('new-collection.html', alert='true', selected='new-collection', filename='None Selected', colnames='')
    else:
        type = request.args.get('type')
        name = ''
        path = ''
        if type == 'history':
            history = fileIO.readHistory()
            name = fileIO.getFileName('history')
            path = '../static/history/' + name
            return render_template('file.html', selected='history', content=json.dumps(history, indent=4), filename=name, filepath=path)
        if type == 'collection':
            content = fileIO.writeSnapshot()
            name = fileIO.getFileName('snapshot')
            path = '../static/snapshot/' + name
            return render_template('file.html', selected='csv', content=content, filename=name, filepath=path)
        if type == 'bins':
            bins = fileIO.readBins()
            name = fileIO.getFileName('bins')
            path = '../static/bins/' + name
            return render_template('file.html', selected='bins', content=json.dumps(bins, indent=4), filename=name, filepath=path)

@app.route('/suggestions')
def createSuggestions():
    exp = {
        "update":"ClinVar has a different interpretation for the HGVS expressions of these entries",
        "merge-dup":"Merge entries that have identical HGVS expressions",
        "merge-syn":"Merge entries that have synonymous HGVS expressions"
    }
    if fileIO.checkEmpty():
        return render_template('new-collection.html', alert='true', selected='new-collection', filename='None Selected', colnames='')
    else:
        type = request.args.get('type')
        list,total = suggestions.init(type)
        return render_template('suggestions.html', total=total, explanation=exp[type], selected='suggestions|' + type, list=list)

@app.route('/delete')
def delete():
    fileIO.removeFiles()
    return redirect('/')

@app.route('/tailor', methods=['POST'])
def tailor():
    ints = request.form.get('ints')
    l = ints.split('|')
    type = request.args.get('type')
    suggestions.tailor(l,type)
    return redirect('/suggestions?type=update')

@app.route('/accept-suggestion', methods=['POST'])
def acceptSuggestion():
    hgvs = request.form.get('hgvs')
    suggestions.accept(hgvs)
    return redirect('/suggestions?type=update')

@app.route('/remove-suggestion', methods=['POST'])
def removeSuggestion():
    suggestion_map = fileIO.readSuggestionMap()
    id = request.form.get('entry-id')
    suggestion_map['IGNORE'].append(id)
    fileIO.writeSuggestionMap(suggestion_map)
    return redirect('/suggestions?type=update')

@app.route('/remove-dup-merge', methods=['POST'])
def removeDupMerge():
    hgvs = request.form.get('hgvs')
    suggestion_map = fileIO.readSuggestionMap()
    suggestion_map['DUP'].append(hgvs)
    fileIO.writeSuggestionMap(suggestion_map)
    return redirect("/suggestions?type=merge-dup")

@app.route('/dup-merge', methods=['POST'])
def dupMerge():
    row = request.form.get('update')
    trash_ids = request.form.get('trash')
    id = suggestions.dupMergeEvent(row,trash_ids)
    return redirect("/detail?id=" + id)

@app.route('/syn-merge', methods=['POST'])
def synMerge():
    row = request.form.get('update')
    trash = request.form.get('trash')
    ids = trash.split(',')
    for id in ids:
        moveToTrash(id)
    collection_map = fileIO.readCollectionMap()
    history = fileIO.readHistory()
    bins = fileIO.readBins()
    row = row.replace('&lt;','<')
    row = row.replace('&gt;','>')
    ll = row.split(',')
    id = ll[0]
    for i in range(0,len(ll)):
        if i == 0 or i == len(ll)-1:
            continue
        else:
            if collection_map[id][i] != ll[i]:
                col = collection_map['HEADER'][i]
                history["entries"][id]["edits"].append({
                    "update from synonym merge": "(" + col + ") \"" + collection_map[id][i] + "\" to \"" + ll[i] + "\"",
                    "timestamp": timestamp()
                })
                hgvs = ll[collection_map['HGVS-COL']]
                int = ll[collection_map['INT-COL']]
                if i == collection_map['INT-COL']: #interpretation change
                    bins[hgvs]["Interpretation"] = int
                    fileIO.writeBins(bins)
                if i == collection_map['HGVS-COL']: #HGVS change
                    new_bins = {}
                    vrs = "test2" #generateVRS()
                    ll[len(collection_map['HEADER'])-1] = vrs
                    if hgvs not in bins:
                        new_bins[hgvs] = {
                            "ID": id,
                            "Interpretation": int
                        }
                    else:
                        #Duplicate
                        alert = 'true'
                    #Update and save the bins
                    new_bins = updateBins(new_bins)
                    for hgvs in new_bins:
                        bins[hgvs] = new_bins[hgvs]
                    fileIO.writeBins(bins)
    collection_map[id] = ll
    fileIO.writeHistory(history)
    fileIO.writeCollectionMap(collection_map)
    fileIO.writeSnapshot()
    return redirect("/detail?id=" + id)

def buildTable():
    collection_map = fileIO.readCollectionMap()
    header = collection_map['HEADER']
    t = "<div>\n<table id=\"data-table\" class=\"viewer table table-striped table-bordered table-sm\">\n<thead>\n"
    ncol = len(header.fields)
    t += "<tr id=\"HEADER\" class=\"trow\">"
    for v in header.fields:
        t += "<th>" + v + "</th>"
    t += "</tr>\n</thead>\n<tbody>\n"
    for id in collection_map:
        if id != 'HEADER':
            record = collection_map[id]
            t += "<tr id=" + record.id + " class=\"trow\" onclick=select('"+ record.id + "')>"
            col = 0
            for v in record.fields:
                if col < len(header.fields):
                    t += "<td>" + v + "</td>"
                col += 1
            t += "</tr>\n"
    t += "</tbody>\n</table>\n</div>"
    return t

@app.route("/empty")
def emptyTrash():
    id = request.args.get('id')
    type = request.args.get('type')
    trash_map = fileIO.readTrash()
    history = fileIO.readHistory()
    if type == 'restore':
        trash.restoreRecord(id,trash_map,history)
        return redirect("/detail?id=" + id)
    else:
        history["entries"][id]["record deleted"] = timestamp()
        del trash_map[id]
        fileIO.writeHistory(history)
        fileIO.writeTrash(trash_map)
        return redirect("/trash")

def timestamp():
    utime = time.localtime()
    return time.strftime("%m/%d/%Y, %H:%M:%S", utime)


# start the server with the 'run()' method
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0",port=7000)
