import time, random
import fileIO, trash, recordCRUD

def init(type):
    list = ''
    count = 0
    if type == 'update':
        list,count = intUpdate()
    if type == 'merge-dup':
        list,count = dupMerge()
    if type == 'merge-syn':
        list,count = synMerge()
    return list,count

def intUpdate():
    list = ''
    count = 0
    bins = fileIO.readBins()
    suggestion_map = fileIO.readSuggestionMap()
    for hgvs in bins:
        if "ClinVar Interpretation" in bins[hgvs]:
            if bins[hgvs]["Interpretation"] != bins[hgvs]["ClinVar Interpretation"] and 'Conflicting interpretations of pathogenicity' not in bins[hgvs]["ClinVar Interpretation"]:
                if bins[hgvs]["Interpretation"] in suggestion_map and bins[hgvs]["ClinVar Interpretation"] in suggestion_map[bins[hgvs]["Interpretation"]]:
                    continue
                elif bins[hgvs]["ID"] in suggestion_map["IGNORE"]:
                    continue
                else:
                    count += 1
                    list += "<div class=\"media pt-3 rounded box-shadow\">\
                        <div class=\"media-body pb-3 mb-0 lh-125\">\
                            <div class=\"ml-3\" style=\"display:inline-block\">\
                                <button class=\"btn btn-sm btn-success\" onclick=\"suggestModal('true','yes-modal','" + bins[hgvs]["Interpretation"] + "|" + bins[hgvs]["ClinVar Interpretation"] + "','" + bins[hgvs]["ID"] + "','" + hgvs + "')\"><img src=\"../static/icons/check.svg\"></img></button>&nbsp;&nbsp;<button class=\"btn btn-sm btn-danger\" onclick=\"suggestModal('true','no-modal','" + bins[hgvs]["Interpretation"] + "|" + bins[hgvs]["ClinVar Interpretation"] + "','" + bins[hgvs]["ID"] + "','" + hgvs + "')\"><img src=\"../static/icons/x.svg\"></button>\
                            </div>&nbsp;\
                            <h5 class=\"mt-2\" style=\"display:inline-block;font-weight:normal\">" + bins[hgvs]["Interpretation"] + "  <img class=\"pb-1\" src=\"../static/icons/arrow-right.svg\"> " + bins[hgvs]["ClinVar Interpretation"] + " <span class=\"text-muted small\">(ClinVar)</span></h5>\
                            <a style=\"display:inline-block;float:right;font-size:large;\" class=\"mt-2 pl-3 mr-3\" href=\"/detail?id=" + bins[hgvs]["ID"] + "\">" + bins[hgvs]["ID"] + "</a>\
                            <span style=\"display:inline-block;float:right;font-size:large;\" class=\"mt-2\">" + hgvs + "</span>\
                        </div>\
                    </div>"
    return list,count

def tailor(l,type):
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
                    header = collection_map['HEADER']
                    record = collection_map[id]
                    record.int = bins[hgvs]["ClinVar Interpretation"]
                    record.fields[header.int_col] = bins[hgvs]["ClinVar Interpretation"]
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

def accept(hgvs):
    bins = fileIO.readBins()
    collection_map = fileIO.readCollectionMap()
    history = fileIO.readHistory()
    id = bins[hgvs]["ID"]
    history["entries"][id]["edits"].append({
        "accepted interpretation update": "\"" + bins[hgvs]["Interpretation"] + "\" to \"" + bins[hgvs]["ClinVar Interpretation"] + "\"",
        "timestamp": timestamp()
    })
    bins[hgvs]["Interpretation"] = bins[hgvs]["ClinVar Interpretation"]
    record = collection_map[id]
    header = collection_map['HEADER']
    record.int = bins[hgvs]["ClinVar Interpretation"]
    record.fields[header.int_col] = bins[hgvs]["ClinVar Interpretation"]
    fileIO.writeSnapshot()
    fileIO.writeBins(bins)
    fileIO.writeCollectionMap(collection_map)
    fileIO.writeHistory(history)

def dupMerge():
    list = ''
    count = 0
    collection_map = fileIO.readCollectionMap()
    suggestion_map = fileIO.readSuggestionMap()
    dups,dup_check = findDups(collection_map)
    if dups != {}:
        for hgvs in dups:
            if hgvs not in suggestion_map["DUP"]:
                count += 1
                header = collection_map['HEADER']
                record = collection_map[dup_check[hgvs]]
                list += buildDupTable(header,record,hgvs,dups,collection_map)
            else:
                print('here')
    return list,count

def findDups(collection_map):
    dups = {}
    dup_check = {}
    for id in collection_map:
        if id != 'HEADER':
            record = collection_map[id]
            if record.hgvs not in dup_check:
                dup_check[record.hgvs] = id
            else:
                if record.hgvs in dups:
                    dups[record.hgvs].append(id)
                else:
                    dups[record.hgvs] = [id]
    return dups,dup_check

def buildDupTable(header,record,hgvs,dups,collection_map):
    ids = []
    vrs = record.vrs
    ids.append(record.id)
    #Dynamically build the HTML to pass to the front end
    table = "<div class=\"mt-4 media rounded box-shadow\">\
                <div class=\"media-body pb-3 mb-0 lh-125\">\
                    <div>\
                        <table class=\"table table-bordered table-sm mb-1\">\
                            <thead>\
                                <tr id=\"HEADER\">"
    #First, add the column names as a header row of the table
    #Then add the first record with that HGVS expression found
    for f in header.fields:
        table += "                   <th><div style=\"text-align: center;\">" + f + "</div></th>"
    table += "                   </tr>\
                            </thead>\
                            <tbody>\
                                <tr>" + buildDupRow(header,record,hgvs) + "</tr>"
    #Add all additional records with that HGVS expression
    for id in dups[hgvs]:
        record = collection_map[id]
        ids.append(record.id)
        table += "               <tr>" + buildDupRow(header,record,hgvs) + "</tr>"
    table += "               </tbody>\
                        </table>\
                    </div>\
                    <div style=\"text-align: center;\"><img src=\"../static/icons/arrow-down.svg\"></div>\
                    <div class=\"pt-1\">\
                        <table class=\"table table-bordered table-sm\">\
                            <tbody>\
                                <tr id=\"" + hgvs + "\">"
    #Add another table below for the user-selected fields
    for i in range(0,len(header.fields)):
    #Auto-fill the HGVS and VRS fields
        if i == header.hgvs_col:
            table += "               <td><div style=\"text-align: center;\">" + hgvs + "</div></td>"
        elif i == len(header.fields)-1:
            table += "               <td><div style=\"text-align: center;\">" + vrs + "</div></td>"
        else:
            table += "               <td><div style=\"text-align: center;\"></div></td>"
    #Add buttons that will pass the info needed to merge the records
    table += "                   </tr>\
                            </tbody>\
                        </table>\
                    </div>\
                    <div class=\"ml-3\" style=\"text-align:center\">\
                        <button class=\"btn btn-sm btn-outline-success\" onclick=\"mergeDupModal('show','" + hgvs + "','" + ','.join(ids) + "')\"> Merge </button>&nbsp;&nbsp;<button class=\"btn btn-sm btn-outline-danger\" onclick=\"removeDupMerge('" + hgvs + "')\">Ignore</button>\
                    </div>\
                </div>\
            </div>"
    return table

def buildDupRow(header,record,hgvs):
    row = ''
    col = 0
    for f in record.fields:
        #If the field is an HGVS expression or VRS identifier, do not add a button (will be added automatically)
        if col == header.hgvs_col or col == len(header.fields)-1:
            row += "<td><div class=\"pt-2 pb-2\" style=\"text-align: center;\"><div style=\"text-align: center;\">" + f + "</div></td>"
        else:
            if col < len(header.fields)-1:
                #Use random identifiers to be able to pull values from the top table and put it into the lower table
                r = str(random.randint(0,1000000))
                row += "<td id=\"" + r + "\"><div class=\"pt-2 pb-2\" style=\"text-align: center;\"><button onclick=\"merge(\'" + hgvs + "\',\'" + r + "\',\'" + str(col) +"\')\" style=\"vertical-align: bottom;\"class=\"btn btn-primary btn-sm\"><img src=\"../static/icons/plus.svg\"></button></div><div class=\"cell-content\" style=\"text-align: center;\">" + f + "</div></td>"
        col += 1
    return row

def mergeEvent(type,row,trash_ids):
    ids = trash_ids.split(',')
    for id in ids:
        trash.moveToTrash(id)
    collection_map = fileIO.readCollectionMap()
    history = fileIO.readHistory()
    bins = fileIO.readBins()
    row = row.replace('&lt;','<')
    row = row.replace('&gt;','>')
    fields = row.split(',')
    recordCRUD.editRecord(type,fields)
    return fields[0]

def manualMerge(ids):
    id_list = ids.split(',')
    map = {
        id_list[0]:id_list[1:]
    }
    collection_map = fileIO.readCollectionMap()
    header = collection_map['HEADER']
    record = collection_map[id_list[0]]
    return buildSynTable('manual',header,record,map,collection_map)

def synMerge():
    list = ''
    count = 0
    collection_map = fileIO.readCollectionMap()
    suggestion_map = fileIO.readSuggestionMap()
    syn_map = findSyns(collection_map)
    if syn_map != {}:
        for id in syn_map:
            unique = id + '|'
            for sid in syn_map[id]:
                unique += sid + '|'
            unique = unique[:-1]
            print(unique)
            print(suggestion_map["SYN"])
            if unique not in suggestion_map["SYN"]:
                count += 1
                header = collection_map["HEADER"]
                record = collection_map[id]
                list += buildSynTable('syn',header,record,syn_map,collection_map)
    return list,count

def findSyns(collection_map):
    has_syn = {}
    bins = fileIO.readBins()
    for b in bins:
        if "ClinVar Synonyms" in bins[b]:
            if len(bins[b]["ClinVar Synonyms"]) > 0:
                has_syn[b] = bins[b]
    syn_map = {}
    for id in collection_map:
        if id != 'HEADER':
            for h in has_syn:
                for syn in bins[h]["ClinVar Synonyms"]:
                    if collection_map[id].hgvs == syn["HGVS"]:
                        if id in syn_map:
                                syn_map[id].append(bins[h]["ID"])
                        else:
                            if bins[h]["ID"] not in syn_map and id != bins[h]["ID"]:
                                syn_map[id] = [bins[h]["ID"]]
                        break
    print(syn_map)
    return syn_map

def buildSynTable(type,header,record,syn_map,collection_map):
    ids = [record.id]
    vrs = record.vrs
    unique = str(random.randint(0,1000000))
    #Dynamically build the HTML to pass to the front end
    table = "<div class=\"mt-4 media rounded box-shadow\">\
                <div class=\"media-body pb-3 mb-0 lh-125\">\
                    <div>\
                        <table class=\"table table-bordered table-sm mb-1\">\
                            <thead>\
                                <tr id=\"HEADER\">"
    #First, add the column names as a header row of the table
    #Then add the first record detected
    for f in header.fields:
        table +=                     "<th><div style=\"text-align: center;\">" + f + "</div></th>"
    table +=                     "</tr>\
                            </thead>\
                            <tbody>\
                                <tr>" + buildSynRow(header,record,unique)+ "</tr>"
    #Add all synonyms of that record
    for sid in syn_map[record.id]:
        syn = collection_map[sid]
        ids.append(syn.id)
        table +=                 "<tr>" + buildSynRow(header,syn,unique) + "</tr>"
    table +=                "</tbody>\
                        </table>\
                    </div>\
                    <div style=\"text-align: center;\"><img src=\"../static/icons/arrow-down.svg\"></div>\
                    <div class=\"pt-1\">\
                        <table class=\"table table-bordered table-sm\">\
                            <tbody>\
                                <tr id=\"" + unique + "\">"
    #Add another table below for the user-selected fields
    #Add as many cells as there are column names
    for i in range(0,len(header.fields)):
        table +=                    "<td><div style=\"text-align: center;\"></div></td>"
    #Add buttons that will pass the info needed to merge the records
    table +=                    "</tr>\
                            </tbody>\
                        </table>\
                    </div>\
                    <div class=\"ml-3\" style=\"text-align:center\">"
    if type == 'syn':
        table +=        "<button class=\"btn btn-sm btn-outline-success\" onclick=\"mergeSynModal('show','" + unique + "','" + ','.join(ids) + "')\"> Merge </button> <button class=\"btn btn-sm btn-outline-danger\" onclick=\"removeSynMerge('" + '|'.join(ids) + "')\">Ignore</button>"
    else:
        table +=        "<button class=\"btn btn-sm btn-outline-success\" onclick=\"mergeSynModal('show','" + unique + "','" + ','.join(ids) + "')\"> Merge </button> <button class=\"btn btn-sm btn-outline-danger\" onclick=\"hideManMerge()\">Cancel</button>"
    table +=        "</div>\
                </div>\
            </div>"
    return table

def buildSynRow(header,record,unique):
    row = ''
    col = 0
    for f in record.fields:
        if col < len(header.fields):
            r = str(random.randint(0,1000000))
            if col == len(header.fields)-1:
                row += "<td id=\"" + r + "\"><div class=\"cell-content\" style=\"text-align: center;\">" + f + "</div></td>"
            else:
                if col == header.hgvs_col:
                    row += "<td id=\"" + r + "\"><div class=\"pt-2 pb-2\" style=\"text-align: center;\"><button onclick=\"mergeSyn(\'" + unique + "\',\'" + r + "\',\'" + str(col) + "\',\'" + record.vrs + "\',\'" + str(len(header.fields)) + "\')\" style=\"vertical-align: bottom;\"class=\"btn btn-primary btn-sm\"><img src=\"../static/icons/plus.svg\"></button></div><div class=\"cell-content\" style=\"text-align: center;\">" + f + "</div></td>"
                else:
                    row += "<td id=\"" + r + "\"><div class=\"pt-2 pb-2\" style=\"text-align: center;\"><button onclick=\"mergeSyn(\'" + unique + "\',\'" + r + "\',\'" + str(col) + "\',\'\',\'" + str(len(header.fields)) + "\')\" style=\"vertical-align: bottom;\"class=\"btn btn-primary btn-sm\"><img src=\"../static/icons/plus.svg\"></button></div><div class=\"cell-content\" style=\"text-align: center;\">" + f + "</div></td>"
        col += 1
    return row

def timestamp():
    utime = time.localtime()
    return time.strftime("%m/%d/%Y, %H:%M:%S", utime)
