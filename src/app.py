from flask import abort, Flask, flash, render_template, request, redirect, send_from_directory, make_response, session
import os, time, json, psutil, random
from os import listdir
from os.path import isfile, join
from ga4gh.core import ga4gh_identify
from ga4gh.vrs import models
from ga4gh.vrs.dataproxy import SeqRepoRESTDataProxy
from ga4gh.vrs.extras.translator import Translator

# create the application object
app = Flask(__name__, static_folder='static')
app.config['UPLOAD_FOLDER'] = 'static/uploads'

table = ""
hgvs_col = ""
int_col = ""

# GENERAL ROUTING
@app.route('/')
def base():
    onlyfiles = [f for f in listdir('static/uploads') if isfile(join('static/uploads', f))]
    if onlyfiles == []:
        return render_template('new-collection.html', alert='false', selected='new-collection', filename='None Selected', colnames='')
    else:
        table = buildTable()
        onlyfiles = [f for f in listdir('static/bins') if isfile(join('static/bins', f))]
        with open('static/bins/' + onlyfiles[0], 'r') as json_file:
            bins = json.load(json_file)
            return render_template('viewer.html', selected='viewer', table=table, bins=bins, hgvs_array=[*bins])

@app.route('/save', methods=['POST'])
def saveEdit():
    content_map = {}
    history = {}
    bins = {}
    #Load the content map, bins, and snapshot file
    onlyfiles = [f for f in listdir('static/map') if isfile(join('static/map', f))]
    map_file = onlyfiles[0]
    with open('static/map/' + map_file, 'r') as json_file:
        content_map = json.load(json_file)
    onlyfiles = [f for f in listdir('static/bins') if isfile(join('static/bins', f))]
    bin_file = onlyfiles[0]
    with open('static/bins/' + bin_file, 'r') as json_file:
        bins = json.load(json_file)
    onlyfiles = [f for f in listdir('static/history') if isfile(join('static/history', f))]
    history_file = onlyfiles[0]
    with open('static/history/' + history_file, 'r') as json_file:
        history = json.load(json_file)
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
            if content_map[id][i] != ll[i]:
                col = content_map['HEADER'][i]
                utime = time.localtime()
                history["entries"][id]["edits"].append({
                    "manual edit": "(" + col + ") " + content_map[id][i] + " to " + ll[i],
                    "timestamp": time.strftime("%m/%d/%Y, %H:%M:%S", utime)
                })
                if i == content_map['HGVS-COL']: #HGVS change
                    new_bins = {}
                    #Add entry to bins
                    hgvs = ll[content_map['HGVS-COL']]
                    int = ll[content_map['INT-COL']]
                    seqrepo_rest_service_url = "http://localhost:5000/seqrepo"
                    dp = SeqRepoRESTDataProxy(base_url=seqrepo_rest_service_url)
                    tlr = Translator(data_proxy=dp)
                    #vrs_allele = tlr.translate_from(hgvs,'hgvs')
                    #vrs = ga4gh_identify(vrs_allele)
                    vrs = "test2"
                    ll[len(content_map['HEADER'])-1] = vrs
                    if hgvs not in bins:
                        new_bins[hgvs] = {
                            "ID": id,
                            "Interpretation": int
                        }
                    else:
                        #Duplicate
                        alert = 'true'
                    #Update and save the bins
                    cv_bins = {}
                    with open('clinvar-bins.json','r') as json_file:
                        cv_bins = json.load(json_file)
                        #Loop through all ClinVar bins once (larger file)
                        for variationID in cv_bins:
                            cv_int = cv_bins[variationID]['Interpretation']
                            syn_list = []
                            match = ''
                            for syn in cv_bins[variationID]['Representations']:
                                if syn['HGVS'] in new_bins:
                                    new_bins[syn['HGVS']]["ClinVar VariationID"] = variationID
                                    new_bins[syn['HGVS']]["ClinVar Interpretation"] = cv_int
                                    new_bins[syn['HGVS']]["ClinVar Synonyms"] = cv_bins[variationID]['Representations']
                                    idx = 0
                                    match = 0
                                    for s in new_bins[syn['HGVS']]["ClinVar Synonyms"]:
                                        if s["HGVS"] == syn['HGVS']:
                                            match = idx
                                        idx += 1
                                    del new_bins[syn['HGVS']]["ClinVar Synonyms"][match]
                    for hgvs in new_bins:
                        bins[hgvs] = new_bins[hgvs]
                    with open('static/bins/' + bin_file, 'w') as update:
                        update.write(json.dumps(bins,indent=4))
                content_map[id] = ll
                #Save the updated history
                with open('static/history/' + history_file, 'w') as update:
                    update.write(json.dumps(history,indent=4))
                #Save the updated content map
                with open('static/map/' + map_file, 'w') as update:
                    update.write(json.dumps(content_map,indent=4))
                #Update and save the snapshot
                onlyfiles = [f for f in listdir('static/snapshot') if isfile(join('static/snapshot', f))]
                with open('static/snapshot/' + onlyfiles[0], 'w') as out_file:
                    content = ','.join(content_map['HEADER']) + '\n'
                    for key in content_map:
                        if key != 'HEADER' and key != 'HGVS-COL' and key != 'INT-COL':
                            content += ','.join(content_map[key]) + '\n'
                    out_file.write(content)

    return redirect("/detail?id=" + id)

@app.route('/new', methods=['POST'])
def addEntry():
    alert = 'false'
    content_map = {}
    history = {}
    bins = {}
    #Load the content map, bins, and snapshot file
    onlyfiles = [f for f in listdir('static/map') if isfile(join('static/map', f))]
    map_file = onlyfiles[0]
    with open('static/map/' + map_file, 'r') as json_file:
        content_map = json.load(json_file)
    onlyfiles = [f for f in listdir('static/bins') if isfile(join('static/bins', f))]
    bin_file = onlyfiles[0]
    with open('static/bins/' + bin_file, 'r') as json_file:
        bins = json.load(json_file)
    onlyfiles = [f for f in listdir('static/history') if isfile(join('static/history', f))]
    history_file = onlyfiles[0]
    with open('static/history/' + history_file, 'r') as json_file:
        history = json.load(json_file)
    #Get the new entry from the HTML form
    new_content = request.form.get('new-entry')
    #Get the number of fields the new entry should have
    ncol = len(content_map['HEADER']) - 2
    entries = new_content.split('\n')
    new_bins = {}
    for entry in entries:
        entry = entry.strip()
        #Create a new ID
        new_id = str(random.randint(0,1000000))
        #Ensure that the new ID is unique
        while new_id in content_map:
            new_id = str(random.randint(0,1000000))
        #Make sure each enw entry has the right number of fields
        if len(entry.split(',')) == ncol:
            #Add the new record to the content map
            ll = entry.split(',')
            ll.insert(0,new_id)
            content_map[new_id] = ll
            #Add event to history
            utime = time.localtime()
            history["entries"][new_id] = {
                "record added": time.strftime("%m/%d/%Y, %H:%M:%S", utime),
                "edits":[]
            }
            #Add entry to bins
            hgvs = ll[content_map['HGVS-COL']]
            int = ll[content_map['INT-COL']]
            seqrepo_rest_service_url = "http://localhost:5000/seqrepo"
            dp = SeqRepoRESTDataProxy(base_url=seqrepo_rest_service_url)
            tlr = Translator(data_proxy=dp)
            #vrs_allele = tlr.translate_from(hgvs,'hgvs')
            #vrs = ga4gh_identify(vrs_allele)
            vrs = "test"
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
    with open('static/history/' + history_file, 'w') as update:
        update.write(json.dumps(history,indent=4))
    #Save the updated content map
    with open('static/map/' + map_file, 'w') as update:
        update.write(json.dumps(content_map,indent=4))
    #Update and save the snapshot
    onlyfiles = [f for f in listdir('static/snapshot') if isfile(join('static/snapshot', f))]
    with open('static/snapshot/' + onlyfiles[0], 'w') as out_file:
        content = ','.join(content_map['HEADER']) + '\n'
        for key in content_map:
            if key != 'HEADER' and key != 'HGVS-COL' and key != 'INT-COL':
                content += ','.join(content_map[key]) + '\n'
        out_file.write(content)
    #Update and save the bins
    cv_bins = {}
    with open('clinvar-bins.json','r') as json_file:
        cv_bins = json.load(json_file)
        #Loop through all ClinVar bins once (larger file)
        for variationID in cv_bins:
            cv_int = cv_bins[variationID]['Interpretation']
            syn_list = []
            match = ''
            for syn in cv_bins[variationID]['Representations']:
                if syn['HGVS'] in new_bins:
                    new_bins[syn['HGVS']]["ClinVar VariationID"] = variationID
                    new_bins[syn['HGVS']]["ClinVar Interpretation"] = cv_int
                    new_bins[syn['HGVS']]["ClinVar Synonyms"] = cv_bins[variationID]['Representations']
                    idx = 0
                    match = 0
                    for s in new_bins[syn['HGVS']]["ClinVar Synonyms"]:
                        if s["HGVS"] == syn['HGVS']:
                            match = idx
                        idx += 1
                    del new_bins[syn['HGVS']]["ClinVar Synonyms"][match]
    for hgvs in new_bins:
        bins[hgvs] = new_bins[hgvs]
    with open('static/bins/' + bin_file, 'w') as update:
        update.write(json.dumps(bins,indent=4))
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
    onlyfiles = [f for f in listdir('static/uploads') if isfile(join('static/uploads', f))]
    if onlyfiles == []:
        return render_template('new-collection.html', alert='true', selected='new-collection', filename='None Selected', colnames='')
    else:
        type = request.args.get('type')
        name = ''
        path = ''
        if type == 'history':
            onlyfiles = [f for f in listdir('static/history') if isfile(join('static/history', f))]
            with open('static/history/' + onlyfiles[0], 'r') as json_file:
                content = json.load(json_file)
            name = onlyfiles[0]
            path = '../static/history/' + name
            return render_template('file.html', selected='history', content=json.dumps(content, indent=4), filename=name, filepath=path)
        if type == 'collection':
            onlyfiles = [f for f in listdir('static/map') if isfile(join('static/map', f))]
            with open('static/map/' + onlyfiles[0], 'r') as json_file:
                content_map = json.load(json_file)
            onlyfiles = [f for f in listdir('static/snapshot') if isfile(join('static/snapshot', f))]
            with open('static/snapshot/' + onlyfiles[0], 'w') as update:
                content = ','.join(content_map['HEADER']) + '\n'
                for key in content_map:
                    if key != 'HEADER' and key != 'HGVS-COL' and key != 'INT-COL':
                        content += ','.join(content_map[key]) + '\n'
            name = onlyfiles[0]
            path = '../static/snapshot/' + name
            return render_template('file.html', selected='csv', content=content, filename=name, filepath=path)
        if type == 'bins':
            onlyfiles = [f for f in listdir('static/bins') if isfile(join('static/bins', f))]
            with open('static/bins/' + onlyfiles[0], 'r') as json_file:
                content = json.load(json_file)
            name = onlyfiles[0]
            path = '../static/bins/' + name
            return render_template('file.html', selected='bins', content=json.dumps(content, indent=4), filename=name, filepath=path)

@app.route('/detail')
def detail():
    id = request.args.get('id')
    onlyfiles = [f for f in listdir('static/map') if isfile(join('static/map', f))]
    with open('static/map/' + onlyfiles[0], 'r') as json_file:
        content_map = json.load(json_file)
        hgvs_col_num = content_map['HGVS-COL']
        int_col_num = content_map['INT-COL']
        hgvs = content_map[id][hgvs_col_num]
        int = content_map[id][int_col_num]
        row = content_map[id]
        tr = '<tr id=\"' + row[0] + '\">'
        idx = 0
        for cell in row:
            if idx == 0 or idx == len(row) - 1:
                tr += '<td>' + cell.strip() + '</td>\n'
            else:
                tr += '<td><div class=\"edit-cells\" contenteditable>' + cell.strip() + '</div></td>\n'
            idx += 1
        tr += '</tr>'
        header = content_map['HEADER']
        th = ''
        for cell in header:
            th += '<th>' + cell.strip() + '</th>\n'
        edits = ''
        onlyfiles = [f for f in listdir('static/history') if isfile(join('static/history', f))]
        with open('static/history/' + onlyfiles[0], 'r') as json_file:
            content_history = json.load(json_file)
            edits = json.dumps(content_history["entries"][id],indent=2)
        cv_int = ''
        li = ''
        synonyms = ''
        try:
            onlyfiles = [f for f in listdir('static/bins') if isfile(join('static/bins', f))]
            with open('static/bins/' + onlyfiles[0], 'r') as json_file:
                bins = json.load(json_file)
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
    with open('static/history/' + file.filename.split('.')[0] + '-history.json', 'w') as fp:
        pass
    with open('static/snapshot/' + file.filename.split('.')[0] + '-snapshot.csv', 'w') as fp:
        pass
    with open('static/bins/' + file.filename.split('.')[0] + '-bins.json', 'w') as fp:
        pass
    with open('static/map/' + file.filename.split('.')[0] + '-map.json', 'w') as fp:
        pass
    with open('static/intmap/' + file.filename.split('.')[0] + '-intmap.json', 'w') as fp:
        fp.write('{}')
    return render_template('new-collection.html', selected='new-collection', filename=file.filename, colnames=cols, warning='False')

@app.route('/suggestions')
def suggestions():
    exp = {
        "update":"ClinVar has a different interpretation for the HGVS expressions of these entries",
        "merge-dup":"Merge entries that have identical HGVS expressions",
        "merge-syn":"Merge entries that have HGVS expressions that are synonyms"
    }
    onlyfiles = [f for f in listdir('static/uploads') if isfile(join('static/uploads', f))]
    if onlyfiles == []:
        return render_template('new-collection.html', alert='true', selected='new-collection', filename='None Selected', colnames='')
    else:
        type = request.args.get('type')
        list,total = buildSuggestions(type)
        return render_template('suggestions.html', total=total, explanation=exp[type], selected='suggestions|' + type, list=list)

@app.route('/new-collection')
def new():
    onlyfiles = [f for f in listdir('static/uploads') if isfile(join('static/uploads', f))]
    if onlyfiles == []:
        return render_template('new-collection.html', alert='false', selected='new-collection', filename='None Selected', colnames='', warning='False')
    else:
        return render_template('new-collection.html', alert='false', selected='new-collection', filename='', colnames='', warning='True')

@app.route('/load', methods=['POST'])
def load():
    r = make_response(redirect(request.referrer))
    global hgvs_col
    hgvs_col = request.form.get('hgvsSelect')
    global int_col
    int_col = request.form.get('intSelect')
    utime = time.localtime() # get struct_time
    content_history = {}
    content_history["file uploaded"] = time.strftime("%m/%d/%Y, %H:%M:%S", utime)
    content_history["entries"] = {}
    onlyfiles = [f for f in listdir('static/history') if isfile(join('static/history', f))]
    with open('static/history/' + onlyfiles[0], 'w') as update:
        update.write(json.dumps(content_history,indent=4))
    onlyfiles = [f for f in listdir('static/uploads') if isfile(join('static/uploads', f))]
    with open('static/uploads/' + onlyfiles[0], 'r') as file:
        #Add column selection for HGVS, add ClinVar cols
        enhanceFile(hgvs_col,int_col,file.read())
    return redirect('/')

@app.route('/delete')
def delete():
    onlyfiles = [f for f in listdir('static/uploads') if isfile(join('static/uploads', f))]
    if onlyfiles != []:
        os.remove('static/uploads/' + onlyfiles[0])
    onlyfiles = [f for f in listdir('static/history') if isfile(join('static/history', f))]
    if onlyfiles != []:
        os.remove('static/history/' + onlyfiles[0])
    onlyfiles = [f for f in listdir('static/bins') if isfile(join('static/bins', f))]
    if onlyfiles != []:
        os.remove('static/bins/' + onlyfiles[0])
    onlyfiles = [f for f in listdir('static/snapshot') if isfile(join('static/snapshot', f))]
    if onlyfiles != []:
        os.remove('static/snapshot/' + onlyfiles[0])
    onlyfiles = [f for f in listdir('static/map') if isfile(join('static/map', f))]
    if onlyfiles != []:
        os.remove('static/map/' + onlyfiles[0])
    onlyfiles = [f for f in listdir('static/intmap') if isfile(join('static/intmap', f))]
    if onlyfiles != []:
        os.remove('static/intmap/' + onlyfiles[0])
    return redirect('/')

def enhanceFile(hgvs_col,int_col,file):
    seqrepo_rest_service_url = "http://localhost:5000/seqrepo"
    dp = SeqRepoRESTDataProxy(base_url=seqrepo_rest_service_url)
    tlr = Translator(data_proxy=dp)
    enhanced = ''
    lines = file.split('\n')
    first = True
    start = time.time()
    content_map = {}
    bins = {}
    hgvs_col_num = 0
    int_col_num = 0
    onlyfiles = [f for f in listdir('static/history') if isfile(join('static/history', f))]
    with open('static/history/' + onlyfiles[0], 'r') as json_file:
        content_history = json.load(json_file)
        for line in lines:
            ll = line.split(',')
            if first == True:
                content_map['HEADER'] = ll
                for i in range(len(ll)):
                    #Get index of HGVS column
                    if ll[i] == hgvs_col:
                        hgvs_col_num = i
                        content_map['HGVS-COL'] = i
                    if ll[i] == int_col:
                        int_col_num = i
                        content_map['INT-COL'] = i
                first = False
                ll.append('VRS')
            else:
                try:
                    hgvs = ll[hgvs_col_num]
                    bins[hgvs] = {
                        "ID": ll[0],
                        "Interpretation": ll[int_col_num]
                    }
                except:
                    continue
                vrs = ''
                try:
                    #vrs_allele = tlr.translate_from(hgvs,'hgvs')
                    #vrs = ga4gh_identify(vrs_allele)
                    vrs = "test"
                except Exception as e:
                    vrs = "Not currently supported by VRS"
                ll.append(vrs)
                content_map[ll[0]] = ll
                utime = time.localtime() # get struct_time
                content_history["entries"][ll[0]] = {
                    "record added": time.strftime("%m/%d/%Y, %H:%M:%S", utime),
                    "edits": []
                }
            enhanced += ','.join(ll) + '\n'
        #Save content_map as a JSON file
        onlyfiles = [f for f in listdir('static/map') if isfile(join('static/map', f))]
        with open('static/map/' + onlyfiles[0], 'w') as update:
            update.write(json.dumps(content_map,indent=4))
        buildBins(bins)
        print("--- %s seconds ---" % (time.time() - start))
        process = psutil.Process(os.getpid())
        print(process.memory_info().rss)# in bytes
    onlyfiles = [f for f in listdir('static/history') if isfile(join('static/history', f))]
    with open('static/history/' + onlyfiles[0], 'w') as update:
        update.write(json.dumps(content_history,indent=4))

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

        onlyfiles = [f for f in listdir('static/bins') if isfile(join('static/bins', f))]
        with open('static/bins/' + onlyfiles[0], 'w') as update:
            update.write(json.dumps(bins,indent=4))

@app.route('/tailor', methods=['POST'])
def tailor():
    intmap = {}
    onlyfiles = [f for f in listdir('static/intmap') if isfile(join('static/intmap', f))]
    intmap_file = onlyfiles[0]
    with open('static/intmap/' + intmap_file, 'r') as json_file:
        intmap = json.load(json_file)
    ints = request.form.get('ints')
    l = ints.split('|')
    if l[0] in intmap:
        intmap[l[0]].append(l[1])
    else:
        intmap[l[0]] = [l[1]]
    with open('static/intmap/' + intmap_file, 'w') as update:
        update.write(json.dumps(intmap,indent=4))
    return redirect('/suggestions?type=update')

def buildSuggestions(type):
    list = ''
    count = 0
    if type == 'update':
        bins = {}
        onlyfiles = [f for f in listdir('static/bins') if isfile(join('static/bins', f))]
        with open('static/bins/' + onlyfiles[0], 'r') as json_file:
            bins = json.load(json_file)
        intmap = {}
        onlyfiles = [f for f in listdir('static/intmap') if isfile(join('static/intmap', f))]
        with open('static/intmap/' + onlyfiles[0], 'r') as json_file:
            intmap = json.load(json_file)
            print(intmap)
        for hgvs in bins:
            if "ClinVar Interpretation" in bins[hgvs]:
                if bins[hgvs]["Interpretation"] != bins[hgvs]["ClinVar Interpretation"] and bins[hgvs]["ClinVar Interpretation"] != 'Conflicting interpretations of pathogenicity':
                    if bins[hgvs]["Interpretation"] in intmap and bins[hgvs]["ClinVar Interpretation"] in intmap[bins[hgvs]["Interpretation"]]:
                        continue
                    else:
                        count += 1
                        list += "<div class=\"media pt-3 rounded box-shadow\">\
                            <div class=\"media-body pb-3 mb-0 lh-125\">\
                                <div class=\"ml-3\" style=\"display:inline-block\">\
                                    <button class=\"btn btn-sm btn-success\" onclick=\"suggestModal('true','yes-modal')\"><img src=\"../static/icons/check.svg\"></img></button>&nbsp;&nbsp;<button class=\"btn btn-sm btn-danger\" onclick=\"suggestModal('true','no-modal','" + bins[hgvs]["Interpretation"] + '|' + bins[hgvs]["ClinVar Interpretation"] + "')\"><img src=\"../static/icons/x.svg\"></button>\
                                </div>&nbsp;\
                                <h5 class=\"mt-2\" style=\"display:inline-block;font-weight:normal\">" + bins[hgvs]["Interpretation"] + " (Current)  <img class=\"pb-1\" src=\"../static/icons/arrow-right.svg\"> " + bins[hgvs]["ClinVar Interpretation"] + "</h5>\
                                <a style=\"display:inline-block;float:right;font-size:large;\" class=\"mt-2 pl-3 mr-3\" href=\"/detail?id=" + bins[hgvs]["ID"] + "\">" + bins[hgvs]["ID"] + "</a>\
                                <span style=\"display:inline-block;float:right;font-size:large;\" class=\"mt-2\">" + hgvs + "</span>\
                            </div>\
                        </div>"
    if type == 'merge-dup':
        dup_check = {}
        dups = {}
        onlyfiles = [f for f in listdir('static/map') if isfile(join('static/map', f))]
        with open('static/map/' + onlyfiles[0], 'r') as json_file:
            content_map = json.load(json_file)
            hgvs_col_num = content_map['HGVS-COL']
            int_col_num = content_map['INT-COL']
            for id in content_map:
                if id != 'HEADER' and id != 'HGVS-COL' and id != 'INT-COL':
                    ll = content_map[id]
                    hgvs = ll[hgvs_col_num]
                    int = ll[int_col_num]
                    if hgvs not in dup_check:
                        dup_check[hgvs] = id
                    else:
                        if hgvs in dups:
                            dups[hgvs].append(id)
                        else:
                            dups[hgvs] = [id]
            if dups != {}:
                for hgvs in dups:
                    count += 1
                    vrs = ''
                    list += "<div class=\"mt-4 media rounded box-shadow\">\
                        <div class=\"media-body pb-3 mb-0 lh-125\">"
                    list += "<div>\n<table id=\"data-table\" class=\"table table-bordered table-sm mb-1\">\n<thead>\n"
                    list += "<tr id=\"HEADER\">"
                    ncol = len(content_map['HEADER'])
                    for v in content_map['HEADER']:
                        list += "<th><div style=\"text-align: center;\">" + v + "</div></th>"
                    list += "</tr>\n</thead>\n<tbody>\n"
                    list += "<tr>"
                    ll = content_map[dup_check[hgvs]]
                    vrs = content_map[dup_check[hgvs]][len(ll) -1]
                    col = 0
                    for v in ll:
                        if col == hgvs_col_num or col == len(ll) -1:
                            list += "<td><div class=\"pt-2 pb-2\" style=\"text-align: center;\"><div style=\"text-align: center;\">" + v + "</div></td>"
                        else:
                            if col < ncol:
                                r = str(random.randint(0,1000000))
                                list += "<td id=\"" + r + "\"><div class=\"pt-2 pb-2\" style=\"text-align: center;\"><button onclick=\"merge(\'" + hgvs + "\',\'" + r + "\',\'" + str(col) +"\')\" style=\"vertical-align: bottom;\"class=\"btn btn-primary btn-sm\"><img src=\"../static/icons/plus.svg\"></button></div><div class=\"cell-content\" style=\"text-align: center;\">" + v + "</div></td>"
                        col += 1
                    list += "</tr>\n"
                    for e in dups[hgvs]:
                        ll = content_map[e]
                        id = ll[0]
                        list += "<tr>"
                        col = 0
                        for v in ll:
                            if col == hgvs_col_num or col == len(ll) -1:
                                list += "<td><div class=\"pt-2 pb-2\" style=\"text-align: center;\"><div style=\"text-align: center;\">" + v + "</div></td>"
                            else:
                                if col < ncol:
                                    r = str(random.randint(0,1000000))
                                    list += "<td id=\"" + r + "\"><div class=\"pt-2 pb-2\" style=\"text-align: center;\"><button onclick=\"merge(\'" + hgvs + "\',\'" + r + "\',\'" + str(col) + "\')\" style=\"vertical-align: bottom;\"class=\"btn btn-primary btn-sm\"><img src=\"../static/icons/plus.svg\"></button></div><div class=\"cell-content\" style=\"text-align: center;\">" + v + "</div></td>"
                            col += 1
                        list += "</tr>\n"
                    list += "</tbody></table></div>"

                    list += "<div style=\"text-align: center;\"><img src=\"../static/icons/arrow-down.svg\"></div>"

                    list += "<div class=\"pt-1\">\n<table id=\"" + hgvs + "\" class=\"table table-bordered table-sm\">\
                            <tbody><tr>"
                    for i in range(0,ncol):
                        if i == hgvs_col_num:
                            list += "<td><div style=\"text-align: center;\">" + hgvs + "</div></td>"
                        elif i == len(ll) -1:
                            list += "<td><div style=\"text-align: center;\">" + vrs + "</div></td>"
                        else:
                            list += "<td><div style=\"text-align: center;\"></div></td>"
                    list += "</tr>\n"
                    list += "</tbody></table></div>"
                    list += "<div class=\"ml-3\" style=\"text-align:center\">\
                        <button class=\"btn btn-sm btn-outline-success\"> Confirm <span data-feather=\"check\"></span></button>&nbsp;&nbsp;<button class=\"btn btn-sm btn-outline-danger\" onclick=\"suggestModal('true')\">Delete <span data-feather=\"x\"></span></button>\
                    </div>"
                    list += "</div></div>"

    if type == 'merge-syn':
        onlyfiles = [f for f in listdir('static/map') if isfile(join('static/map', f))]
        with open('static/map/' + onlyfiles[0], 'r') as json_file:
            content_map = json.load(json_file)
            onlyfiles = [f for f in listdir('static/bins') if isfile(join('static/bins', f))]
            with open('static/bins/' + onlyfiles[0], 'r') as json_file:
                bins = json.load(json_file)
                has_syn = {}
                for b in bins:
                    if "ClinVar Synonyms" in bins[b]:
                        if len(bins[b]["ClinVar Synonyms"]) > 0:
                            has_syn[b] = bins[b]
                hgvs_col_num = content_map['HGVS-COL']
                syn_map = {}
                for id in content_map:
                    if id != 'HEADER' and id != 'HGVS-COL' and id != 'INT-COL':
                        ll = content_map[id]
                        hgvs = ll[hgvs_col_num]
                        for h in has_syn:
                            for syn in bins[h]["ClinVar Synonyms"]:
                                if hgvs == syn["HGVS"]:
                                    print('match!')
                                    if id in syn_map:
                                        syn_map[id].append(bins[h]["ID"])
                                    else:
                                        syn_map[id] = [bins[h]["ID"]]
                        break
                if syn_map != {}:
                    for id in syn_map:
                        count += 1
                        vrs = ''
                        list += "<div class=\"mt-4 media rounded box-shadow\">\
                            <div class=\"media-body pb-3 mb-0 lh-125\">"
                        list += "<div>\n<table id=\"data-table\" class=\"table table-bordered table-sm mb-1\">\n<thead>\n"
                        list += "<tr id=\"HEADER\">"
                        ncol = len(content_map['HEADER'])
                        for v in content_map['HEADER']:
                            list += "<th><div style=\"text-align: center;\">" + v + "</div></th>"
                        list += "</tr>\n</thead>\n<tbody>\n"
                        list += "<tr>"
                        ll = content_map[id]
                        vrs = content_map[id][len(ll) -1]
                        col = 0
                        for v in ll:
                            if col == hgvs_col_num or col == len(ll) -1:
                                list += "<td><div class=\"pt-2 pb-2\" style=\"text-align: center;\"><div style=\"text-align: center;\">" + v + "</div></td>"
                            else:
                                if col < ncol:
                                    r = str(random.randint(0,1000000))
                                    list += "<td id=\"" + r + "\"><div class=\"pt-2 pb-2\" style=\"text-align: center;\"><button onclick=\"merge(\'" + 'hgvs' + "\',\'" + r + "\',\'" + str(col) +"\')\" style=\"vertical-align: bottom;\"class=\"btn btn-primary btn-sm\"><img src=\"../static/icons/plus.svg\"></button></div><div class=\"cell-content\" style=\"text-align: center;\">" + v + "</div></td>"
                            col += 1
                        list += "</tr>\n"
                        for e in syn_map[id]:
                            ll = content_map[e]
                            list += "<tr>"
                            col = 0
                            for v in ll:
                                if col == hgvs_col_num or col == len(ll) -1:
                                    list += "<td><div class=\"pt-2 pb-2\" style=\"text-align: center;\"><div style=\"text-align: center;\">" + v + "</div></td>"
                                else:
                                    if col < ncol:
                                        r = str(random.randint(0,1000000))
                                        list += "<td id=\"" + r + "\"><div class=\"pt-2 pb-2\" style=\"text-align: center;\"><button onclick=\"merge(\'" + 'hgvs' + "\',\'" + r + "\',\'" + str(col) + "\')\" style=\"vertical-align: bottom;\"class=\"btn btn-primary btn-sm\"><img src=\"../static/icons/plus.svg\"></button></div><div class=\"cell-content\" style=\"text-align: center;\">" + v + "</div></td>"
                                col += 1
                            list += "</tr>\n"
                        list += "</tbody></table></div>"

                        list += "<div style=\"text-align: center;\"><img src=\"../static/icons/arrow-down.svg\"></div>"

                        list += "<div class=\"pt-1\">\n<table id=\"" + 'hgvs' + "\" class=\"table table-bordered table-sm\">\
                                <tbody><tr>"
                        hgvs = ll[hgvs_col_num]
                        for i in range(0,ncol):
                            if i == hgvs_col_num:
                                list += "<td><div style=\"text-align: center;\">" + hgvs + "</div></td>"
                            elif i == len(ll) -1:
                                list += "<td><div style=\"text-align: center;\">" + vrs + "</div></td>"
                            else:
                                list += "<td><div style=\"text-align: center;\"></div></td>"
                        list += "</tr>\n"
                        list += "</tbody></table></div>"
                        list += "<div class=\"ml-3\" style=\"text-align:center\">\
                            <button class=\"btn btn-sm btn-outline-success\"> Confirm <span data-feather=\"check\"></span></button>&nbsp;&nbsp;<button class=\"btn btn-sm btn-outline-danger\" onclick=\"suggestModal('true')\">Delete <span data-feather=\"x\"></span></button>\
                        </div>"
                        list += "</div></div>"
    return list,count

def buildTable():
    if table == "":
        onlyfiles = [f for f in listdir('static/map') if isfile(join('static/map', f))]
        with open('static/map/' + onlyfiles[0], 'r') as json_file:
            content_map = json.load(json_file)
            t = "<div>\n<table id=\"data-table\" class=\"table table-striped table-bordered table-sm\">\n<thead>\n"
            ncol = len(content_map['HEADER'])
            t += "<tr id=\"HEADER\" class=\"trow\">"
            for v in content_map['HEADER']:
                t += "<th>" + v + "</th>"
            t += "</tr>\n</thead>\n<tbody>\n"
            for key in content_map:
                if key != 'HEADER' and key != 'HGVS-COL' and key != 'INT-COL':
                    ll = content_map[key]
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

# start the server with the 'run()' method
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0",port=7000)
