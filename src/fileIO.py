import os,json
from os import listdir
from os.path import isfile,join
from recordCRUD import Header, Record

def getFileName(type):
    onlyfiles = [f for f in listdir('static/' + type) if isfile(join('static/' + type, f))]
    return onlyfiles[0]

def checkEmpty():
    onlyfiles = [f for f in listdir('static/uploads') if isfile(join('static/uploads', f))]
    if onlyfiles == []:
        return True
    else:
        return False

def readUpload():
    content = ''
    onlyfiles = [f for f in listdir('static/uploads') if isfile(join('static/uploads', f))]
    with open('static/uploads/' + onlyfiles[0], 'r') as file:
         content = file.read()
    return content

def createFiles(name):
    with open('static/history/' + name + '-history.json', 'w') as fp:
        pass
    with open('static/snapshot/' + name + '-snapshot.csv', 'w') as fp:
        pass
    with open('static/bins/' + name + '-bins.json', 'w') as fp:
        pass
    with open('static/collection-map/' + name + '-map.json', 'w') as fp:
        pass
    with open('static/suggestion-map/' + name + '-suggmap.json', 'w') as fp:
        fp.write('{\"IGNORE\":[],\"DUP\":[],\"SYN\":[]}')
    with open('static/trash/' + name + '-trash.json', 'w') as fp:
        pass

def removeFiles():
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
    onlyfiles = [f for f in listdir('static/collection-map') if isfile(join('static/collection-map', f))]
    if onlyfiles != []:
        os.remove('static/collection-map/' + onlyfiles[0])
    onlyfiles = [f for f in listdir('static/suggestion-map') if isfile(join('static/suggestion-map', f))]
    if onlyfiles != []:
        os.remove('static/suggestion-map/' + onlyfiles[0])
    onlyfiles = [f for f in listdir('static/trash') if isfile(join('static/trash', f))]
    if onlyfiles != []:
        os.remove('static/trash/' + onlyfiles[0])

"""
SNAPSHOT - .csv file of the collection
"""
def writeSnapshot():
    content = ''
    #First, open the content map
    collection_map = readCollectionMap()
    #Read the map and create the snapshot
    onlyfiles = [f for f in listdir('static/snapshot') if isfile(join('static/snapshot', f))]
    with open('static/snapshot/' + onlyfiles[0], 'w') as update:
        content = ','.join(collection_map['HEADER'].fields) + '\n'
        #Ignore custom fields added to the map
        for id in collection_map:
            if id != 'HEADER':
                content += ','.join(collection_map[id].fields) + '\n'
        update.write(content)
    return content

"""
COLLECTION MAP - json object of the collection
{
    "HEADER": [ list of column names ],
    "HGVS-COL": index of HGVS column,
    "INT-COL": index of interpretation column,
    record ID: [ list of fields for that record (each row of table) ],
    ...
}
"""
def readCollectionMap():
    content = []
    collection_map = {}
    onlyfiles = [f for f in listdir('static/collection-map') if isfile(join('static/collection-map', f))]
    with open('static/collection-map/' + onlyfiles[0], 'r') as json_file:
        content = json.load(json_file)
    for i in range(0,len(content)):
        if i == 0:
            header = Header(content[i]["fields"],content[i]["int_col"],content[i]["hgvs_col"])
            collection_map["HEADER"] = header
        else:
            record = Record(content[i]["fields"],content[i]["id"],content[i]["int"],content[i]["hgvs"],content[i]["vrs"])
            collection_map[record.id] = record
    return collection_map

def writeCollectionMap(collection_map):
    content = []
    for id in collection_map:
        content.append(collection_map[id].export())
    onlyfiles = [f for f in listdir('static/collection-map') if isfile(join('static/collection-map', f))]
    with open('static/collection-map/' + onlyfiles[0], 'w') as update:
        update.write(json.dumps(content))

"""
BINS - json object of the HGVS bins
{
    HGVS expression: {
        "ID": record ID,
        "Interpretation": record interpretation,
        "Duplicates": [ list of record IDs with same HGVS expression],
        (optional) "ClinVar VariationID": VariationID from ClinVar,
        (optional) "ClinVar Interpretation": clinical significance from ClinVar,
        (optional) "ClinVar Synonyms": [
            {
                "HGVS": HGVS expression of synonyms listed in ClinVar,
                "VRS": VRS identifier for that HGVS expression
            },
            ...
        ]
    }
}
"""
def readBins():
    bins = {}
    onlyfiles = [f for f in listdir('static/bins') if isfile(join('static/bins', f))]
    with open('static/bins/' + onlyfiles[0], 'r') as json_file:
        bins = json.load(json_file)
    return bins

def writeBins(bins):
    onlyfiles = [f for f in listdir('static/bins') if isfile(join('static/bins', f))]
    with open('static/bins/' + onlyfiles[0], 'w') as update:
        update.write(json.dumps(bins,indent=4))
"""
HISTORY - json object of the collection history
*all timestamps in (%m/%d/%Y, %H:%M:%S) format*
{
    "file uploaded": timestamp when .csv file loaded ,
    "entries": {
        record ID: {
            "record added": timestamp when record added to collection,
            "edits": [
                (all are optional)
                {
                    "manual edit": (column name) "original string" to "new string",
                    "timestamp": timestamp when edit was made
                },
                {
                    "accepted interpretation update": "original string" to "new string",
                    "timestamp": timestamp when edit was made
                },
                {
                    "update from duplicate merge": (column name) "original string" to "new string",
                    "timestamp": timestamp when edit was made
                },
                {
                    "update from synonym merge": (column name) "original string" to "new string",
                    "timestamp": timestamp when edit was made
                },
                {
                    "update from manual merge": (column name) "original string" to "new string",
                    "timestamp": timestamp when edit was made
                },
                {
                    "record moved to trash": timestamp when record was moved from collection to trash
                },
                {
                    "record restored from trash": timestamp when record was moved from trash to collection
                }
            ]
            (optional) "record deleted": timestamp when record is deleted from trash
        }
    }
}
"""
def readHistory():
    history = {}
    onlyfiles = [f for f in listdir('static/history') if isfile(join('static/history', f))]
    with open('static/history/' + onlyfiles[0], 'r') as json_file:
        history = json.load(json_file)
    return history

def writeHistory(history):
    onlyfiles = [f for f in listdir('static/history') if isfile(join('static/history', f))]
    with open('static/history/' + onlyfiles[0], 'w') as update:
        update.write(json.dumps(history,indent=4))

"""
SUGGESTION MAP - json object of suggestion preferences
{
    'IGNORE': [ list of record ids to ignore when compiling interpretation update suggestions ],
    'DUP': [ list of hgvs expressions to ignore when compiling duplicate suggestions ],
    'SYN': [ list of ... ],
    collection-specific interpretation: [ list of ClinVar interpretation types that have been marked as equivalent ]
}
"""
def readSuggestionMap():
    suggestion_map = {}
    onlyfiles = [f for f in listdir('static/suggestion-map') if isfile(join('static/suggestion-map', f))]
    with open('static/suggestion-map/' + onlyfiles[0], 'r') as json_file:
        suggestion_map = json.load(json_file)
    return suggestion_map

def writeSuggestionMap(suggestion_map):
    onlyfiles = [f for f in listdir('static/suggestion-map') if isfile(join('static/suggestion-map', f))]
    with open('static/suggestion-map/' + onlyfiles[0], 'w') as update:
        update.write(json.dumps(suggestion_map,indent=4))

"""
TRASH - json object of records removed from collection
{
    "HEADER": [ list of column names ],
    record ID: {
        "map" : [ list of fields for that record (each row of table) ],
        "bin" : {
            "ID": record ID,
            "Interpretation": record interpretation,
            "Duplicates": [ list of record IDs with same HGVS expression],
            (optional) "ClinVar VariationID": VariationID from ClinVar,
            (optional) "ClinVar Interpretation": clinical significance from ClinVar,
            (optional) "ClinVar Synonyms": [
                {
                    "HGVS": HGVS expression of synonyms listed in ClinVar,
                    "VRS": VRS identifier for that HGVS expression
                },
                ...
            ]
        }
    }
}
"""
def readTrash():
    content,trash = {},{}
    onlyfiles = [f for f in listdir('static/trash') if isfile(join('static/trash', f))]
    with open('static/trash/' + onlyfiles[0], 'r') as json_file:
        content = json.load(json_file)
    for id in content:
        if id == 'HEADER':
            header = Header(content["HEADER"]["fields"],content["HEADER"]["int_col"],content["HEADER"]["hgvs_col"])
            trash["HEADER"] = header
        else:
            r = content[id]["record"]
            record = Record(r["fields"],id,r["int"],r["hgvs"],r["vrs"])
            trash[record.id] = {
                "record":record,
                "bin": content[id]["bin"]
            }
    return trash

def writeTrash(trash):
    content = {}
    for id in trash:
        if id == 'HEADER':
            content[id] = trash["HEADER"].export()
        else:
            content[id] = {
                "record": trash[id]["record"].export(),
                "bin": trash[id]["bin"]
            }
    onlyfiles = [f for f in listdir('static/trash') if isfile(join('static/trash', f))]
    with open('static/trash/' + onlyfiles[0], 'w') as update:
        update.write(json.dumps(content,indent=4))
