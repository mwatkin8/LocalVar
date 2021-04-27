import fileIO, random

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

def dupMerge():
    list = ''
    count = 0
    dup_check = {}
    dups = {}
    collection_map = fileIO.readCollectionMap()
    suggestion_map = fileIO.readSuggestionMap()
    for id in collection_map:
        if id != 'HEADER' and id != 'HGVS-COL' and id != 'INT-COL':
            ll = collection_map[id]
            hgvs = ll[collection_map['HGVS-COL']]
            int = ll[collection_map['INT-COL']]
            if hgvs not in dup_check:
                dup_check[hgvs] = id
            else:
                if hgvs in dups:
                    dups[hgvs].append(id)
                else:
                    dups[hgvs] = [id]
    if dups != {}:
        for hgvs in dups:
            if hgvs not in suggestion_map["DUP"]:
                ids = []
                count += 1
                vrs = ''
                list += "<div class=\"mt-4 media rounded box-shadow\">\
                    <div class=\"media-body pb-3 mb-0 lh-125\">"
                list += "<div>\n<table id=\"data-table\" class=\"table table-bordered table-sm mb-1\">\n<thead>\n"
                list += "<tr id=\"HEADER\">"
                ncol = len(collection_map['HEADER'])
                for v in collection_map['HEADER']:
                    list += "<th><div style=\"text-align: center;\">" + v + "</div></th>"
                list += "</tr>\n</thead>\n<tbody>\n"
                list += "<tr>"
                ll = collection_map[dup_check[hgvs]]
                ids.append(ll[0])
                vrs = collection_map[dup_check[hgvs]][ncol -1]
                col = 0
                for v in ll:
                    if col == collection_map['HGVS-COL'] or col == ncol -1:
                        list += "<td><div class=\"pt-2 pb-2\" style=\"text-align: center;\"><div style=\"text-align: center;\">" + v + "</div></td>"
                    else:
                        if col < ncol:
                            r = str(random.randint(0,1000000))
                            list += "<td id=\"" + r + "\"><div class=\"pt-2 pb-2\" style=\"text-align: center;\"><button onclick=\"merge(\'" + hgvs + "\',\'" + r + "\',\'" + str(col) +"\')\" style=\"vertical-align: bottom;\"class=\"btn btn-primary btn-sm\"><img src=\"../static/icons/plus.svg\"></button></div><div class=\"cell-content\" style=\"text-align: center;\">" + v + "</div></td>"
                    col += 1
                list += "</tr>\n"
                for e in dups[hgvs]:
                    ll = collection_map[e]
                    id = ll[0]
                    ids.append(id)
                    list += "<tr>"
                    col = 0
                    for v in ll:
                        if col == collection_map['HGVS-COL'] or col == ncol -1:
                            list += "<td><div class=\"pt-2 pb-2\" style=\"text-align: center;\"><div style=\"text-align: center;\">" + v + "</div></td>"
                        else:
                            if col < ncol:
                                r = str(random.randint(0,1000000))
                                list += "<td id=\"" + r + "\"><div class=\"pt-2 pb-2\" style=\"text-align: center;\"><button onclick=\"merge(\'" + hgvs + "\',\'" + r + "\',\'" + str(col) + "\')\" style=\"vertical-align: bottom;\"class=\"btn btn-primary btn-sm\"><img src=\"../static/icons/plus.svg\"></button></div><div class=\"cell-content\" style=\"text-align: center;\">" + v + "</div></td>"
                        col += 1
                    list += "</tr>\n"
                list += "</tbody></table></div>"

                list += "<div style=\"text-align: center;\"><img src=\"../static/icons/arrow-down.svg\"></div>"

                list += "<div class=\"pt-1\">\n<table class=\"table table-bordered table-sm\">\
                        <tbody><tr id=\"" + hgvs + "\">"
                for i in range(0,ncol):
                    if i == collection_map['HGVS-COL']:
                        list += "<td><div style=\"text-align: center;\">" + hgvs + "</div></td>"
                    elif i == len(ll) -1:
                        list += "<td><div style=\"text-align: center;\">" + vrs + "</div></td>"
                    else:
                        list += "<td><div style=\"text-align: center;\"></div></td>"
                list += "</tr>\n"
                list += "</tbody></table></div>"
                list += "<div class=\"ml-3\" style=\"text-align:center\">\
                    <button class=\"btn btn-sm btn-outline-success\" onclick=\"mergeDupModal('show','" + hgvs + "','" + ','.join(ids) + "')\"> Merge </button>&nbsp;&nbsp;<button class=\"btn btn-sm btn-outline-danger\" onclick=\"removeDupMerge('" + hgvs + "')\">Ignore</button>\
                </div>"
                list += "</div></div>"
            else:
                print('here')
    return list,count

def synMerge():
    list = ''
    count = 0
    collection_map = fileIO.readCollectionMap()
    bins = fileIO.readBins()
    has_syn = {}
    for b in bins:
        if "ClinVar Synonyms" in bins[b]:
            if len(bins[b]["ClinVar Synonyms"]) > 0:
                has_syn[b] = bins[b]
    syn_map = {}
    for id in collection_map:
        if id != 'HEADER' and id != 'HGVS-COL' and id != 'INT-COL':
            hgvs = collection_map[id][collection_map['HGVS-COL']]
            for h in has_syn:
                for syn in bins[h]["ClinVar Synonyms"]:
                    if hgvs == syn["HGVS"]:
                        if id in syn_map:
                            syn_map[id].append(bins[h]["ID"])
                        else:
                            syn_map[id] = [bins[h]["ID"]]
                        break
    if syn_map != {}:
        for id in syn_map:
            ids = []
            count += 1
            vrs = ''
            list += "<div class=\"mt-4 media rounded box-shadow\">\
                <div class=\"media-body pb-3 mb-0 lh-125\">"
            list += "<div>\n<table id=\"data-table\" class=\"table table-bordered table-sm mb-1\">\n<thead>\n"
            list += "<tr id=\"HEADER\">"
            ncol = len(collection_map['HEADER'])
            for v in collection_map['HEADER']:
                list += "<th><div style=\"text-align: center;\">" + v + "</div></th>"
            list += "</tr>\n</thead>\n<tbody>\n"
            unique = str(random.randint(0,1000000))
            list += "<tr>"
            ll = collection_map[id]
            ids.append(ll[0])
            vrs = collection_map[id][len(ll) -1]
            col = 0
            for v in ll:
                if col < ncol:
                    r = str(random.randint(0,1000000))
                    if col == ncol -1:
                        list += "<td id=\"" + r + "\"><div class=\"cell-content\" style=\"text-align: center;\">" + v + "</div></td>"
                    else:
                        if col == collection_map['HGVS-COL']:
                            vrs = ll[ncol - 1]
                            list += "<td id=\"" + r + "\"><div class=\"pt-2 pb-2\" style=\"text-align: center;\"><button onclick=\"mergeSyn(\'" + unique + "\',\'" + r + "\',\'" + str(col) + "\',\'" + vrs + "\',\'" + str(ncol) + "\')\" style=\"vertical-align: bottom;\"class=\"btn btn-primary btn-sm\"><img src=\"../static/icons/plus.svg\"></button></div><div class=\"cell-content\" style=\"text-align: center;\">" + v + "</div></td>"
                        else:
                            list += "<td id=\"" + r + "\"><div class=\"pt-2 pb-2\" style=\"text-align: center;\"><button onclick=\"mergeSyn(\'" + unique + "\',\'" + r + "\',\'" + str(col) + "\',\'\',\'" + str(ncol) + "\')\" style=\"vertical-align: bottom;\"class=\"btn btn-primary btn-sm\"><img src=\"../static/icons/plus.svg\"></button></div><div class=\"cell-content\" style=\"text-align: center;\">" + v + "</div></td>"
                col += 1
            list += "</tr>\n"
            for e in syn_map[id]:
                ll = collection_map[e]
                ids.append(ll[0])
                list += "<tr>"
                col = 0
                for v in ll:
                    if col < ncol:
                        r = str(random.randint(0,1000000))
                        if col == ncol - 1:
                            list += "<td id=\"" + r + "\"><div class=\"cell-content\" style=\"text-align: center;\">" + v + "</div></td>"
                        else:
                            if col == collection_map['HGVS-COL']:
                                vrs = ll[ncol - 1]
                                list += "<td id=\"" + r + "\"><div class=\"pt-2 pb-2\" style=\"text-align: center;\"><button onclick=\"mergeSyn(\'" + unique + "\',\'" + r + "\',\'" + str(col) + "\',\'" + vrs + "\',\'" + str(ncol) + "\')\" style=\"vertical-align: bottom;\"class=\"btn btn-primary btn-sm\"><img src=\"../static/icons/plus.svg\"></button></div><div class=\"cell-content\" style=\"text-align: center;\">" + v + "</div></td>"
                            else:
                                list += "<td id=\"" + r + "\"><div class=\"pt-2 pb-2\" style=\"text-align: center;\"><button onclick=\"mergeSyn(\'" + unique + "\',\'" + r + "\',\'" + str(col) + "\',\'\',\'" + str(ncol) + "\')\" style=\"vertical-align: bottom;\"class=\"btn btn-primary btn-sm\"><img src=\"../static/icons/plus.svg\"></button></div><div class=\"cell-content\" style=\"text-align: center;\">" + v + "</div></td>"
                    col += 1
                list += "</tr>\n"
            list += "</tbody></table></div>"

            list += "<div style=\"text-align: center;\"><img src=\"../static/icons/arrow-down.svg\"></div>"

            list += "<div class=\"pt-1\">\n<table class=\"table table-bordered table-sm\">\
                    <tbody><tr id=\"" + unique + "\">"
            for i in range(0,ncol):
                list += "<td><div style=\"text-align: center;\"></div></td>"
            list += "</tr>\n"
            list += "</tbody></table></div>"
            list += "<div class=\"ml-3\" style=\"text-align:center\">\
                <button class=\"btn btn-sm btn-outline-success\" onclick=\"mergeSynModal('show','" + unique + "','" + ','.join(ids) + "')\"> Merge </button>&nbsp;&nbsp;<button class=\"btn btn-sm btn-outline-danger\" onclick=\"suggestModal('true')\">Ignore</button>\
            </div>"
            list += "</div></div>"
    return list,count
