from flask import abort, Flask, flash, render_template, request, redirect, send_from_directory, make_response, session
import os, time, json
from os import listdir
from os.path import isfile, join
from ga4gh.core import ga4gh_identify
from ga4gh.vrs import models
from ga4gh.vrs.dataproxy import SeqRepoRESTDataProxy
from ga4gh.vrs.extras.translator import Translator

# create the application object
app = Flask(__name__, static_folder='static')
app.config['UPLOAD_FOLDER'] = 'static/uploads'

file_content = ""
table = ""
hgvs_col = ""
hgvs_col_num = ""
int_col = ""
int_col_num = ""
content_map = {}
bins = {}
content_history = {}

# GENERAL ROUTING
@app.route('/')
def base():
    onlyfiles = [f for f in listdir('static/uploads') if isfile(join('static/uploads', f))]
    if onlyfiles == []:
        return render_template('new-collection.html', alert='false', selected='new-collection', filename='None Selected', colnames='')
    else:
        table = buildTable()
        return render_template('viewer.html', selected='viewer', table=table, bins=bins, hgvs_array=[*bins])

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
            content = ''
            onlyfiles = [f for f in listdir('static/history') if isfile(join('static/history', f))]
            with open('static/history/' + onlyfiles[0], 'w') as update:
                content = json.dumps(content_history,indent=4)
            name = onlyfiles[0]
            path = '../static/history/' + name
            return render_template('file.html', selected='history', content=content, filename=name, filepath=path)
        if type == 'collection':
            onlyfiles = [f for f in listdir('static/snapshot') if isfile(join('static/snapshot', f))]
            with open('static/snapshot/' + onlyfiles[0], 'w') as update:
                content = ','.join(content_map['HEADER']) + '\n'
                for key in content_map:
                    if key != 'HEADER':
                        content += ','.join(content_map[key]) + '\n'
            name = onlyfiles[0]
            path = '../static/snapshot/' + name
            return render_template('file.html', selected='csv', content=content, filename=name, filepath=path)
        if type == 'bins':
            content = ''
            onlyfiles = [f for f in listdir('static/bins') if isfile(join('static/bins', f))]
            with open('static/bins/' + onlyfiles[0], 'w') as update:
                content = json.dumps(bins,indent=4)
            name = onlyfiles[0]
            path = '../static/bins/' + name
            return render_template('file.html', selected='bins', content=content, filename=name, filepath=path)

@app.route('/detail')
def detail():
    id = request.args.get('id')
    hgvs = content_map[id][hgvs_col_num]
    int = content_map[id][int_col_num]
    row = content_map[id]
    tr = ''
    for cell in row:
        tr += '<td><div contenteditable>' + cell.strip() + '</div></td>\n'
    header = content_map['HEADER']
    th = ''
    for cell in header:
        th += '<th>' + cell.strip() + '</th>\n'
    edits = ''
    for e in content_history['entries'][id]:
        edits += e + ' - ' + content_history['entries'][id][e]
    cv_int = ''
    li = ''
    synonyms = ''
    try:
        cv_int = bins[hgvs]["ClinVar Interpretation"]
        for s in bins[hgvs]["ClinVar Synonyms"]:
            li += '<li class="mb-2">' + s + '</li>'
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
    ll = file_content.split('\n')
    with open('static/history/' + file.filename.split('.')[0] + '-history.json', 'w') as fp:
        pass
    with open('static/snapshot/' + file.filename.split('.')[0] + '-snapshot.csv', 'w') as fp:
        pass
    with open('static/bins/' + file.filename.split('.')[0] + '-bins.json', 'w') as fp:
        pass
    return render_template('new-collection.html', selected='new-collection', filename=file.filename, colnames=ll[0].strip(), warning='False')

@app.route('/suggestions')
def suggestions():
    exp = {
        "update":"ClinVar has a different interpretation for the HGVS expressions of these entries",
        "merge-dup":"Merge two entries that have identical HGVS expressions",
        "merge-syn":"Merge two entries that have HGVS expressions that are synonyms"
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
    global content_history
    content_history["file uploaded"] = time.strftime("%m/%d/%Y, %H:%M:%S", utime)
    content_history["entries"] = {}
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
    return redirect('/')

def enhanceFile(hgvs_col,int_col,file):
    seqrepo_rest_service_url = "http://localhost:5000/seqrepo"
    dp = SeqRepoRESTDataProxy(base_url=seqrepo_rest_service_url)
    tlr = Translator(data_proxy=dp)
    enhanced = ''
    lines = file.split('\n')
    first = True
    start = time.time()
    for line in lines:
        ll = line.split(',')
        if first == True:
            content_map['HEADER'] = ll
            for i in range(len(ll)):
                #Get index of HGVS column
                if ll[i] == hgvs_col:
                    global hgvs_col_num
                    hgvs_col_num = i
                if ll[i] == int_col:
                    global int_col_num
                    int_col_num = i
            first = False
            ll.append('VRS')
        else:
            try:
                hgvs = ll[hgvs_col_num]
                global bins
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
            global content_history
            content_history["entries"][ll[0]] = {
                "record added": time.strftime("%m/%d/%Y, %H:%M:%S", utime)
            }
        enhanced += ','.join(ll) + '\n'
    buildBins()
    print("--- %s seconds ---" % (time.time() - start))
    onlyfiles = [f for f in listdir('static/history') if isfile(join('static/history', f))]
    with open('static/history/' + onlyfiles[0], 'w') as update:
        update.write(json.dumps(content_history,indent=4))
    global file_content
    file_content = enhanced

def buildBins():
    with open('clinvar-bins.json','r') as json_file:
        cv_bins = json.load(json_file)
        global bins
        #Loop through all ClinVar bins once (larger file)
        for variationID in cv_bins:
            cv_int = cv_bins[variationID]['Interpretation']
            syn_list = []
            match = ''
            for syn in cv_bins[variationID]['Representations']:
                if syn['HGVS'] in bins:
                    match = syn['HGVS']
                else:
                    syn_list.append(syn['HGVS'])
            if match != '':
                bins[match]["ClinVar VariationID"] = variationID
                bins[match]["ClinVar Interpretation"] = cv_int
                bins[match]["ClinVar Synonyms"] = syn_list

def buildSuggestions(type):
    list = ''
    count = 0
    if type == 'update':
        for hgvs in bins:
            if "ClinVar Interpretation" in bins[hgvs]:
                if bins[hgvs]["Interpretation"] != bins[hgvs]["ClinVar Interpretation"]:
                    count += 1
                    list += "<div class=\"media pt-3 rounded box-shadow\">\
                        <div class=\"media-body pb-3 mb-0 lh-125\">\
                            <div class=\"ml-3\" style=\"display:inline-block\">\
                                <button class=\"btn btn-sm btn-outline-success\"><span data-feather=\"check\"></span></button>&nbsp;&nbsp;<button class=\"btn btn-sm btn-outline-danger\" onclick=\"suggestModal('true')\"><span data-feather=\"x\"></span></button>\
                            </div>&nbsp;\
                            <h5 class=\"mt-2\" style=\"display:inline-block;font-weight:normal\">" + bins[hgvs]["Interpretation"] + " (Current)  <span class=\"mb-1\" data-feather=\"arrow-right\"></span> " + bins[hgvs]["ClinVar Interpretation"] + "</h5>\
                            <a style=\"display:inline-block;float:right;font-size:large;\" class=\"mt-2 pl-3 mr-3\" href=\"/detail?id=" + bins[hgvs]["ID"] + "\">" + bins[hgvs]["ID"] + "</a>\
                            <span style=\"display:inline-block;float:right;font-size:large;\" class=\"mt-2\">" + hgvs + "</span>\
                        </div>\
                    </div>"
    if type == 'merge-dup':
        #dup_check = []
        #for line in ll:
        #    hgvs = line[hgvs_col_num]
        #    if hgvs not in dup_check:
        #        dup_check.append((hgvs,))
        list = ''
    if type == 'merge-syn':
        list = ''
        count = 0
    return list,count

def buildTable():
    table = "<div>\n<table id=\"data-table\" class=\"table table-striped table-bordered table-sm\">\n<thead>\n"
    ll = file_content.split('\n')
    first = True
    ncol = len(ll[0].split(','))
    for line in ll:
        id = line.split(',')[0]
        if first == True:
            table += "<tr id=" + id + " class=\"trow\">"
        else:
            table += "<tr id=" + id + " class=\"trow\" onclick=select('"+ id + "')>"
        col = 0
        for v in line.split(','):
            if first == True:
                table += "<th>" + v + "</th>"
            else:
                if col < ncol:
                    table += "<td>" + v + "</td>"
            col += 1
        if first == True:
            first = False
            table += "</tr>\n</thead>\n<tbody>\n"
        else:
            table += "</tr>\n"
    table += "</tbody>\n</table>\n</div>"
    return table

# start the server with the 'run()' method
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0",port=7000)
