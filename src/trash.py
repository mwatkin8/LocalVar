import time, fileIO

def buildTrash():
    total = 0
    trash = fileIO.readTrash()
    trash["HEADER"].fields.insert(0,'ACTION')
    t = "<div>\n<table class=\"table table-striped table-bordered table-sm\">\n<thead>\n"
    t += "<tr id=\"HEADER\">"
    for v in trash['HEADER'].fields:
        t += "<th>" + v + "</th>"
    t += "</tr>\n</thead>\n<tbody>\n"
    rows = ''
    for id in trash:
        if id != 'HEADER':
            record = trash[id]["record"]
            row = "<tr id=" + record.id + ">"
            for i in range(0,len(record.fields)):
                if i == 0:
                    row += "<td><button onclick=\"restore('" + id + "')\" class=\"btn btn-sm btn-primary\"><img src=\"../static/icons/rotate-ccw.svg\"></button> <button onclick=\"trashModal('true','" + id + "')\" class=\"btn btn-sm btn-danger\"><img src=\"../static/icons/trash-white.svg\"></button></td>"
                row += "<td>" + record.fields[i] + "</td>"
            row += "</tr>\n"
            rows = row + rows
            total += 1
    t += rows + "</tbody>\n</table>\n</div>"
    return t,total

def moveToTrash(id):
    bins = fileIO.readBins()
    collection_map = fileIO.readCollectionMap()
    history = fileIO.readHistory()
    trash = fileIO.readTrash()
    trash["HEADER"] = collection_map["HEADER"]
    history["entries"][id]["edits"].append({
        "record moved to trash": timestamp()
    })
    record = collection_map[id]
    hgvs = record.hgvs
    trash[id] = {
        "record": record,
        "bin": bins[record.hgvs]
    }
    print(trash)
    if bins[record.hgvs]["Duplicates"] == []:
        del bins[record.hgvs]
    else:
        if bins[record.hgvs]["ID"] == id:
            bins[record.hgvs]["ID"] = bins[record.hgvs]["Duplicates"][0]["ID"]
            bins[record.hgvs]["Interpretation"] = bins[record.hgvs]["Duplicates"][0]["Interpretation"]
            del bins[record.hgvs]["Duplicates"][0]
    del collection_map[id]
    fileIO.writeCollectionMap(collection_map)
    fileIO.writeSnapshot()
    fileIO.writeBins(bins)
    fileIO.writeHistory(history)
    fileIO.writeTrash(trash)

def restoreRecord(id,trash,history):
    bins = fileIO.readBins()
    collection_map = fileIO.readCollectionMap()
    history["entries"][id]["edits"].append({
        "record restored from trash": timestamp()
    })
    collection_map[id] = trash[id]["record"]
    hgvs = collection_map[id].hgvs
    if hgvs not in bins:
        bins[hgvs] = trash[id]["bin"]
    else:
        int = collection_map[id].int
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

def timestamp():
    utime = time.localtime()
    return time.strftime("%m/%d/%Y, %H:%M:%S", utime)
