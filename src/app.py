from flask import abort, Flask, flash, render_template, request, redirect, send_from_directory, make_response, session
import os, time, json, psutil, random
import fileIO, recordCRUD, suggestions
from recordCRUD import Header, Record

# create the application object
app = Flask(__name__, static_folder='static')
app.config['UPLOAD_FOLDER'] = 'static/uploads'

table = ""

# GENERAL ROUTING
@app.route('/')
def base():
    if fileIO.checkEmpty():
        return render_template('new-collection.html', alert='false', selected='new-collection', filename='None Selected', colnames='')
    else:
        table = buildTable()
        bins = fileIO.readBins()
        return render_template('viewer.html', selected='viewer', table=table, bins=bins, hgvs_array=[*bins])

@app.route('/trash')
def trash():
    if fileIO.checkEmpty():
        return render_template('new-collection.html', alert='false', selected='new-collection', filename='None Selected', colnames='')
    else:
        id = request.args.get('id')
        if id:
            moveToTrash(id)
        table,total = buildTrash()
        return render_template('trash.html', selected='trash', table=table, total=total)


#SOMETHING WEIRD ABOUT SAVING HGVS FROM MANUAL POST -> SYN TOOL DIDN'T DETECT. TEST MORE.
@app.route('/save', methods=['POST'])
def saveEdit():
    #Load the content map, bins, and snapshot file
    collection_map = fileIO.readCollectionMap()
    bins = fileIO.readBins()
    history = fileIO.readHistory()
    row = request.form.get('row')
    row = row.replace('&lt;','<')
    row = row.replace('&gt;','>')
    print(row)
    ll = row.split(',')
    id = ll[0]
    hgvs_change = False
    for i in range(0,len(ll)):
        if i == 0 or i == len(ll)-1:
            continue
        else:
            if collection_map[id][i] != ll[i]:
                col = collection_map['HEADER'][i]
                history["entries"][id]["edits"].append({
                    "manual edit": "(" + col + ") \"" + collection_map[id][i] + "\" to \"" + ll[i] + "\"",
                    "timestamp": timestamp()
                })
                hgvs = ll[collection_map['HGVS-COL']]
                int = ll[collection_map['INT-COL']]
                if i == collection_map['INT-COL']: #interpretation change
                    bins[hgvs]["Interpretation"] = int
                    fileIO.writeBins(bins)
                if i == collection_map['HGVS-COL']: #HGVS change
                    new_bins = {}
                    #Add entry to bins
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

@app.route('/new', methods=['POST'])
def addEntry():
    alert = 'false'
    history = {}
    bins = {}
    #Load the content map, bins, and snapshot file
    collection_map = fileIO.readCollectionMap()
    bins = fileIO.readBins()
    history = fileIO.readHistory()
    #Get the new entry from the HTML form
    new_content = request.form.get('new-entry')
    #Get the number of fields the new entry should have
    ncol = len(collection_map['HEADER']) - 2
    entries = new_content.split('\n')
    new_bins = {}
    for entry in entries:
        entry = entry.strip()
        #Create a new ID
        new_id = str(random.randint(0,1000000))
        #Ensure that the new ID is unique
        while new_id in collection_map:
            new_id = str(random.randint(0,1000000))
        #Make sure each enw entry has the right number of fields
        if len(entry.split(',')) == ncol:
            #Add the new record to the content map
            ll = entry.split(',')
            ll.insert(0,new_id)
            collection_map[new_id] = ll
            #Add event to history
            history["entries"][new_id] = {
                "record added": timestamp(),
                "edits":[]
            }
            #Add entry to bins
            hgvs = ll[collection_map['HGVS-COL']]
            int = ll[collection_map['INT-COL']]
            vrs = "test" #generateVRS()
            ll.insert(ncol + 2,vrs)
            if hgvs not in bins:
                new_bins[hgvs] = {
                    "ID": new_id,
                    "Interpretation": int
                }
            else:
                #Duplicate
                alert = 'true'
        else:
            #Bad entry
            alert = 'true'
    #Save the updated history
    fileIO.writeHistory(history)
    #Save the updated content map
    fileIO.writeCollectionMap(collection_map)
    #Update and save the snapshot
    fileIO.writeSnapshot()
    #Update and save the bins
    new_bins = updateBins(new_bins)
    for hgvs in new_bins:
        bins[hgvs] = new_bins[hgvs]
    fileIO.writeBins(bins)
    return redirect('/')

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

@app.route('/detail')
def detail():
    id = request.args.get('id')
    collection_map = fileIO.readCollectionMap()
    hgvs = collection_map[id][collection_map['HGVS-COL']]
    int = collection_map[id][collection_map['INT-COL']]
    row = collection_map[id]
    tr = '<tr id=\"' + row[0] + '\">'
    idx = 0
    for cell in row:
        if idx == 0 or idx == len(row) - 1:
            tr += '<td>' + cell.strip() + '</td>\n'
        else:
            tr += '<td><div class=\"edit-cells\" contenteditable>' + cell.strip() + '</div></td>\n'
        idx += 1
    tr += '</tr>'
    header = collection_map['HEADER']
    th = ''
    for cell in header:
        th += '<th>' + cell.strip() + '</th>\n'
    history = fileIO.readHistory()
    edits = '<b>' + history["entries"][id]["record added"] + '</b>\n<i>record added</i>\n\n'
    for e in history["entries"][id]["edits"]:
        if "timestamp" in e:
            edits += '<b>' + e["timestamp"] + '</b>\n' + '<i>' + [*e][0] + '</i>\n' + e[[*e][0]] + '\n\n'
        else:
            edits += '<b>' + e[[*e][0]] + '</b>\n' + '<i>' + [*e][0] + '</i>\n\n'
    cv_int = ''
    li = ''
    synonyms = ''
    try:
        bins = fileIO.readBins()
        cv_int = bins[hgvs]["ClinVar Interpretation"]
        for s in bins[hgvs]["ClinVar Synonyms"]:
            li += '<li class="mb-2">' + s["HGVS"] + '</li>'
        synonyms = '<ul style="list-style:none" class="pl-0">' + li + '</ul>'
        evidence = 'https://www.ncbi.nlm.nih.gov/clinvar/' + bins[hgvs]["ClinVar VariationID"]
    except:
        cv_int = 'None'
        synonyms = 'None'
        evidence = '#'

    return render_template('detail.html', selected='viewer', evidence=evidence, cv_int=cv_int, synonyms=synonyms, hgvs=hgvs, int=int, id=id, header=th, row=tr, edits=edits)

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

@app.route('/new-collection')
def new():
    if fileIO.checkEmpty():
        return render_template('new-collection.html', alert='false', selected='new-collection', filename='None Selected', colnames='', warning='False')
    else:
        return render_template('new-collection.html', alert='false', selected='new-collection', filename='', colnames='', warning='True')

@app.route('/load', methods=['POST'])
def load():
    r = make_response(redirect(request.referrer))
    hgvs_col = request.form.get('hgvsSelect')
    int_col = request.form.get('intSelect')
    history = {}
    history["file uploaded"] = timestamp()
    history["entries"] = {}
    fileIO.writeHistory(history)
    print('enhancing file...')
    enhanceFile(hgvs_col, int_col, fileIO.readUpload())
    print('redirecting')
    return redirect('/')

@app.route('/delete')
def delete():
    fileIO.removeFiles()
    return redirect('/')

@app.route('/tailor', methods=['POST'])
def tailor():
    ints = request.form.get('ints')
    l = ints.split('|')
    type = request.args.get('type')
    if type == 'update':
        bins = fileIO.readBins()
        collection_map = fileIO.readCollectionMap()
        history = fileIO.readHistory()
        for hgvs in bins:
            if "ClinVar Interpretation" in bins[hgvs]:
                if bins[hgvs]["Interpretation"] == l[0] and bins[hgvs]["ClinVar Interpretation"] == l[1]:
                    id = bins[hgvs]["ID"]
                    history["entries"][id]["edits"].append({
                        "accepted interpretation update": "\"" + bins[hgvs]["Interpretation"] + "\" to \"" + bins[hgvs]["ClinVar Interpretation"] + "\"",
                        "timestamp": timestamp()
                    })
                    bins[hgvs]["Interpretation"] = bins[hgvs]["ClinVar Interpretation"]
                    collection_map[id][collection_map["INT-COL"]] = bins[hgvs]["ClinVar Interpretation"]
        fileIO.writeSnapshot()
        fileIO.writeBins(bins)
        fileIO.writeCollectionMap(collection_map)
        fileIO.writeHistory(history)
    elif type == 'remove':
        suggestion_map = fileIO.readSuggestionMap()
        if l[0] in suggestion_map:
            suggestion_map[l[0]].append(l[1])
        else:
            suggestion_map[l[0]] = [l[1]]
        fileIO.writeSuggestionMap(suggestion_map)
    else:
        return
    return redirect('/suggestions?type=update')

@app.route('/accept-suggestion', methods=['POST'])
def acceptSuggestion():
    bins = fileIO.readBins()
    collection_map = fileIO.readCollectionMap()
    history = fileIO.readHistory()
    hgvs = request.form.get('hgvs')
    id = bins[hgvs]["ID"]
    history["entries"][id]["edits"].append({
        "accepted interpretation update": "\"" + bins[hgvs]["Interpretation"] + "\" to \"" + bins[hgvs]["ClinVar Interpretation"] + "\"",
        "timestamp": timestamp()
    })
    bins[hgvs]["Interpretation"] = bins[hgvs]["ClinVar Interpretation"]
    collection_map[id][collection_map["INT-COL"]] = bins[hgvs]["ClinVar Interpretation"]
    fileIO.writeSnapshot()
    fileIO.writeBins(bins)
    fileIO.writeCollectionMap(collection_map)
    fileIO.writeHistory(history)
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
    fileIO.write(suggestion_map)
    return redirect("/suggestions?type=merge-dup")

@app.route('/dup-merge', methods=['POST'])
def dupMergeEvent():
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
    hgvs_change = False
    for i in range(0,len(ll)):
        if i == 0 or i == len(ll)-1:
            continue
        else:
            if collection_map[id][i] != ll[i]:
                col = collection_map['HEADER'][i]
                history["entries"][id]["edits"].append({
                    "update from duplicate merge": "(" + col + ") \"" + collection_map[id][i] + "\" to \"" + ll[i] + "\"",
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
    if table == "":
        collection_map = fileIO.readCollectionMap()
        t = "<div>\n<table id=\"data-table\" class=\"viewer table table-striped table-bordered table-sm\">\n<thead>\n"
        ncol = len(collection_map['HEADER'])
        t += "<tr id=\"HEADER\" class=\"trow\">"
        for v in collection_map['HEADER']:
            t += "<th>" + v + "</th>"
        t += "</tr>\n</thead>\n<tbody>\n"
        for key in collection_map:
            if key != 'HEADER' and key != 'HGVS-COL' and key != 'INT-COL':
                ll = collection_map[key]
                id = ll[0]
                t += "<tr id=" + id + " class=\"trow\" onclick=select('"+ id + "')>"
                col = 0
                for v in ll:
                    if col < ncol:
                        t += "<td>" + v + "</td>"
                    col += 1
                t += "</tr>\n"
        t += "</tbody>\n</table>\n</div>"
        return t
    else:
        return table

@app.route("/empty")
def emptyTrash():
    id = request.args.get('id')
    type = request.args.get('type')
    trash = fileIO.readTrash()
    history = fileIO.readHistory()
    if type == 'restore':
        bins = fileIO.readBins()
        collection_map = fileIO.readCollectionMap()
        history["entries"][id]["edits"].append({
            "record restored from trash": timestamp()
        })
        collection_map[id] = trash[id]["map"]
        hgvs = collection_map[id][collection_map['HGVS-COL']]
        if hgvs not in bins:
            bins[hgvs] = trash[id]["bin"]
        else:
            int = collection_map[id][collection_map['INT-COL']]
            if bins[hgvs]["Duplicates"] == []:
                bins[hgvs]["Duplicates"].append({
                    "ID": id,
                    "Interpretation": int
                })
        del trash[id]
        fileIO.writeSnapshot()
        fileIO.writeBins(bins)
        fileIO.writeCollectionMap(collection_map)
        fileIO.writeHistory(history)
        fileIO.writeTrash(trash)
        return redirect("/detail?id=" + id)
    else:
        history["entries"][id]["record deleted"] = timestamp()
        del trash[id]
        fileIO.writeHistory(history)
        fileIO.writeTrash(trash)
        return redirect("/trash")

def buildTrash():
    total = 0
    trash = fileIO.readTrash()
    trash['HEADER'].insert(0,'ACTION')
    t = "<div>\n<table class=\"table table-striped table-bordered table-sm\">\n<thead>\n"
    t += "<tr id=\"HEADER\">"
    for v in trash['HEADER']:
        t += "<th>" + v + "</th>"
    t += "</tr>\n</thead>\n<tbody>\n"
    rows = ''
    for key in trash:
        if key != 'HEADER':
            ll = trash[key]["map"]
            id = ll[0]
            row = "<tr id=" + id + ">"
            for i in range(0,len(ll)):
                if i == 0:
                    row += "<td><button onclick=\"restore('" + id + "')\" class=\"btn btn-sm btn-primary\"><img src=\"../static/icons/rotate-ccw.svg\"></button> <button onclick=\"trashModal('true','" + id + "')\" class=\"btn btn-sm btn-danger\"><img src=\"../static/icons/trash-white.svg\"></button></td>"
                row += "<td>" + ll[i] + "</td>"
            row += "</tr>\n"
            rows = row + rows
            total += 1
    t += rows + "</tbody>\n</table>\n</div>"
    return t,total

def enhanceFile(hgvs_col,int_col,file):
    collection_map = {}
    bins = {}
    trash = {}
    enhanced = ''
    start = time.time()
    history = fileIO.readHistory()
    lines = file.split('\n')
    first = True



    for line in lines:
        fields = line.split(',')
        if first == True:
            collection_map['HEADER'] = ll
            trash['HEADER'] = ll
            int_col = 0
            hgvs_col = 0
            for i in range(len(ll)):
                #Get index of HGVS column
                if ll[i] == hgvs_col:
                    collection_map['HGVS-COL'] = i
                    hgvs_col = i
                if ll[i] == int_col:
                    collection_map['INT-COL'] = i
                    int_col = i
            header = Record(fields, len(fields), int_col, hgvs_col)


            first = False
            ll.append('VRS')
        else:
            try:
                hgvs = ll[collection_map['HGVS-COL']]
                if hgvs in bins:
                    bins[hgvs]["Duplicates"].append({
                        "ID": ll[0],
                        "Interpretation": ll[collection_map['INT-COL']]
                    })
                else:
                    bins[hgvs] = {
                        "ID": ll[0],
                        "Interpretation": ll[collection_map['INT-COL']],
                        "Duplicates":[]
                    }
            except:
                continue
            vrs = ''
            try:
                vrs = "test" #generateVRS(hgvs)
            except Exception as e:
                vrs = "Not currently supported by VRS"
            ll.append(vrs)
            collection_map[ll[0]] = ll
            history["entries"][ll[0]] = {
                "record added": timestamp(),
                "edits": []
            }
    fileIO.writeCollectionMap(collection_map)
    fileIO.writeTrash(trash)
    buildBins(bins)
    print("--- %s seconds ---" % (time.time() - start))
    process = psutil.Process(os.getpid())
    print(process.memory_info().rss)# in bytes
    fileIO.writeHistory(history)

def buildBins(bins):
    with open('clinvar-bins.json','r') as json_file:
        cv_bins = json.load(json_file)
        #Loop through all ClinVar bins once (larger file)
        for variationID in cv_bins:
            cv_int = cv_bins[variationID]['Interpretation']
            syn_list = []
            match = ''
            for syn in cv_bins[variationID]['Representations']:
                if syn['HGVS'] in bins:
                    bins[syn['HGVS']]["ClinVar VariationID"] = variationID
                    bins[syn['HGVS']]["ClinVar Interpretation"] = cv_int
                    bins[syn['HGVS']]["ClinVar Synonyms"] = cv_bins[variationID]['Representations']
                    idx = 0
                    match = 0
                    for s in bins[syn['HGVS']]["ClinVar Synonyms"]:
                        if s["HGVS"] == syn['HGVS']:
                            match = idx
                        idx += 1
                    del bins[syn['HGVS']]["ClinVar Synonyms"][match]
        fileIO.writeBins(bins)

def updateBins(bins):
    cv_bins = {}
    with open('clinvar-bins.json','r') as json_file:
        cv_bins = json.load(json_file)
    #Loop through all ClinVar bins once (larger file)
    for variationID in cv_bins:
        cv_int = cv_bins[variationID]['Interpretation']
        syn_list = []
        match = ''
        for syn in cv_bins[variationID]['Representations']:
            if syn['HGVS'] in bins:
                bins[syn['HGVS']]["ClinVar VariationID"] = variationID
                bins[syn['HGVS']]["ClinVar Interpretation"] = cv_int
                bins[syn['HGVS']]["ClinVar Synonyms"] = cv_bins[variationID]['Representations']
                idx = 0
                match = 0
                for s in bins[syn['HGVS']]["ClinVar Synonyms"]:
                    if s["HGVS"] == syn['HGVS']:
                        match = idx
                    idx += 1
                del bins[syn['HGVS']]["ClinVar Synonyms"][match]
    return bins

def moveToTrash(id):
    bins = fileIO.readBins()
    collection_map = fileIO.readCollectionMap()
    history = fileIO.readHistory()
    trash = fileIO.readTrash()
    history["entries"][id]["edits"].append({
        "record moved to trash": timestamp()
    })
    hgvs = collection_map[id][collection_map['HGVS-COL']]
    trash[id] = {
        "map":[],
        "bin":{}
    }
    trash[id]["map"] = collection_map[id]
    trash[id]["bin"] = bins[hgvs]
    if bins[hgvs]["Duplicates"] == []:
        del bins[hgvs]
    else:
        if bins[hgvs]["ID"] == id:
            bins[hgvs]["ID"] = bins[hgvs]["Duplicates"][0]["ID"]
            bins[hgvs]["Interpretation"] = bins[hgvs]["Duplicates"][0]["Interpretation"]
            del bins[hgvs]["Duplicates"][0]
    del collection_map[id]
    fileIO.writeSnapshot()
    fileIO.writeBins(bins)
    fileIO.writeHistory(history)
    fileIO.writeTrash(trash)

# start the server with the 'run()' method
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0",port=7000)
