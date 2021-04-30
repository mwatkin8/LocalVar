import fileIO, json, time, random
from ga4gh.core import ga4gh_identify
from ga4gh.vrs import models
from ga4gh.vrs.dataproxy import SeqRepoRESTDataProxy
from ga4gh.vrs.extras.translator import Translator

class Header:
    def __init__(self, fields, int_col, hgvs_col):
        self.fields = fields
        self.int_col = int_col
        self.hgvs_col = hgvs_col

    def export(self):
        return {
            "fields": self.fields,
            "int_col": self.int_col,
            "hgvs_col": self.hgvs_col
        }

class Record:
    def __init__(self, fields, id, int, hgvs, vrs):
        self.fields = fields
        self.id = id
        self.int = int
        self.hgvs = hgvs
        self.vrs = vrs

    def export(self):
        return {
            "fields": self.fields,
            "id": self.id,
            "int": self.int,
            "hgvs": self.hgvs,
            "vrs": self.vrs
        }

def init(hgvs_name,int_name,file,history):
    collection_map,bins,trash = {},{},{}
    lines = file.split('\n')
    first = True
    header = None
    init_bins = {}
    for line in lines:
        fields = line.split(',')
        if len(fields) == 1:
            continue
        if first == True:
            header = makeHeader(hgvs_name,int_name,fields)
            collection_map["HEADER"] = header
            trash["HEADER"] = header
            first = False
        else:
            record = makeRecord(header,fields)
            collection_map[record.id] = record
            #Adds the HGVS, ID, and any HGVS duplicates into the initial bins map
            init_bins = addInitBin(init_bins,record)
            history = addHistory(history,record)
    fileIO.writeCollectionMap(collection_map)
    fileIO.writeTrash(trash)
    #Enhances the initial bins map with data from ClinVar
    enhanced_bins = enhanceBins(init_bins)
    fileIO.writeBins(enhanced_bins)
    fileIO.writeHistory(history)

def makeHeader(hgvs_name,int_name,fields):
    int_col = 0
    hgvs_col = 0
    for i in range(len(fields)):
        #Get index of HGVS column
        if fields[i] == hgvs_name:
            hgvs_col = i
        #Get index of interpretation column
        if fields[i] == int_name:
            int_col = i
    #Create a new Header object to save those column indices and all column names
    fields.append('VRS')
    header = Header(fields.copy(), int_col, hgvs_col)
    return header

def makeRecord(header,fields):
    try:
        vrs = generateVRS(fields[header.hgvs_col])
    except:
        vrs = "Not currently supported by VRS"
    fields.append(vrs)
    return Record(fields.copy(), fields[0], fields[header.int_col], fields[header.hgvs_col],vrs)

def addInitBin(init_bins,record):
    if record.hgvs in init_bins:
        init_bins[record.hgvs]["Duplicates"].append({
            "ID": record.id,
            "Interpretation": record.int
        })
    else:
        init_bins[record.hgvs] = {
            "ID": record.id,
            "Interpretation": record.int,
            "Duplicates":[]
        }
    return init_bins

def enhanceBins(init_bins):
    cv_bins = {}
    enhanced_bins = init_bins.copy()
    with open('clinvar-bins.json','r') as json_file:
        cv_bins = json.load(json_file)
    #Loop through all ClinVar bins once (larger file)
    for variationID in cv_bins:
        b = cv_bins[variationID]
        cv_int = b["Interpretation"]
        for rep in b["Representations"]:
            if rep["HGVS"] in enhanced_bins:
                syn = rep["HGVS"]
                enhanced_bins[syn]["ClinVar VariationID"] = variationID
                enhanced_bins[syn]["ClinVar Interpretation"] = cv_int
                enhanced_bins[syn]["ClinVar Synonyms"] = b["Representations"]
                idx = 0
                match = 0
                #Remove the actual HGVS expression from its own synonym list
                for cv_syn in enhanced_bins[syn]["ClinVar Synonyms"]:
                    if cv_syn["HGVS"] == syn:
                        match = idx
                    idx += 1
                del enhanced_bins[syn]["ClinVar Synonyms"][match]
    return enhanced_bins

def addHistory(history,record):
    history["entries"][record.id] = {
        "record added": timestamp(),
        "edits": []
    }
    return history

def generateVRS(hgvs):
    seqrepo_rest_service_url = "http://localhost:5000/seqrepo"
    dp = SeqRepoRESTDataProxy(base_url=seqrepo_rest_service_url)
    tlr = Translator(data_proxy=dp)
    vrs_allele = tlr.translate_from(hgvs,'hgvs')
    return ga4gh_identify(vrs_allele)

def timestamp():
    utime = time.localtime()
    return time.strftime("%m/%d/%Y, %H:%M:%S", utime)

def addRecord(new_content):
    #Load the collection map, bins, and history
    collection_map = fileIO.readCollectionMap()
    bins = fileIO.readBins()
    history = fileIO.readHistory()
    #Get the number of fields the new entry should have
    header = collection_map['HEADER']
    ncol = len(header.fields) - 2
    #User can upload multiple on new lines
    entries = new_content.split('\n')
    new_bin_entries = {}
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
            fields = entry.split(',')
            fields.insert(0,new_id)
            record = makeRecord(header,fields)
            collection_map[record.id] = record
            if record.hgvs not in bins:
                new_bin_entries = addInitBin(new_bin_entries,record)
            history = addHistory(history,record)
        else:
            #Bad entry
            alert = 'true'
    new_enhanced_bins = enhanceBins(new_bin_entries)
    for b in new_enhanced_bins:
        bins[b] = new_enhanced_bins[b]
    fileIO.writeHistory(history)
    fileIO.writeCollectionMap(collection_map)
    fileIO.writeSnapshot()
    fileIO.writeBins(bins)

def editRecord(type,fields):
    #Load the content map, bins, and snapshot file
    collection_map = fileIO.readCollectionMap()
    bins = fileIO.readBins()
    history = fileIO.readHistory()
    id = fields[0]
    record = collection_map[id]
    header = collection_map['HEADER']
    #Loop through the fields of the new entry and compare each to the existing record
    for i in range(0,len(fields)):
        #Ignore the ID and VRS fields since they cannot be edited
        if i == 0 or i == len(fields)-1:
            continue
        else:
            #If there is a field difference in the new entry, save in the history and update the record
            if record.fields[i] != fields[i]:
                col_name = header.fields[i]
                if type == 'manual':
                    history["entries"][id]["edits"].append({
                        "manual edit": "(" + col_name + ") \"" + record.fields[i] + "\" to \"" + fields[i] + "\"",
                        "timestamp": timestamp()
                    })
                if type == 'dup':
                    history["entries"][id]["edits"].append({
                        "update from merge": "(" + col_name + ") \"" + record.fields[i] + "\" to \"" +  fields[i] + "\"",
                        "timestamp": timestamp()
                    })
                if type == 'syn':
                    history["entries"][id]["edits"].append({
                        "update from merge": "(" + col_name + ") \"" + record.fields[i] + "\" to \"" +  fields[i] + "\"",
                        "timestamp": timestamp()
                    })
                hgvs = fields[header.hgvs_col]
                int = fields[header.int_col]
                #Interpretation change
                if i == header.int_col:
                    record.int = int
                    if hgvs in bins:
                        bins[hgvs]["Duplicates"].append({
                            "ID": record.id,
                            "Interpretation": record.int
                        })
                    else:
                        enhanced = enhanceBins({
                            "ID": record.id,
                            "Interpretation": record.int,
                            "Duplicates":[]
                        })
                        bins[hgvs] = enhanced
                    fileIO.writeBins(bins)
                    bins[hgvs]["Interpretation"] = int
                #HGVS change
                if i == header.hgvs_col:
                    record.hgvs = hgvs
                    try:
                        record.vrs = generateVRS(hgvs)
                    except:
                        record.vrs = "Not currently supported by VRS"
                    #If the HGVS exists in the bins already, add this record as a duplicate
                    if hgvs in bins:
                        bins[hgvs]["Duplicates"].append({
                            "ID": record.id,
                            "Interpretation": record.int
                        })
                    else:
                        enhanced = enhanceBins({
                            "ID": record.id,
                            "Interpretation": record.int,
                            "Duplicates":[]
                        })
                        bins[hgvs] = enhanced
                    fileIO.writeBins(bins)
    record.fields = fields
    collection_map[id] = record
    fileIO.writeHistory(history)
    fileIO.writeCollectionMap(collection_map)
    fileIO.writeSnapshot()
    fileIO.writeBins(bins)
