
# coding: utf-8

import os, sys, glob, warnings

import pandas as pd
import numpy as np

# import colorlover as cl
import json
import csv
import lxml
import lxml.html
from lxml import etree
import xml.etree
import pdia
from pdia import *
import string
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

f = open('check_records.txt', 'wb')

# json can't load unicode strings.
# had to use ast: https://stackoverflow.com/questions/956867/how-to-get-string-objects-instead-of-unicode-from-json

# MCSS & MCMS
MCSS = """
{'Response': [{'Eliminations': [],
   'Index': 0,
   'OtherInfo': [],
   'Response': [{'Index': 0,
     'OtherInfoTextExist': False,
     'Selected': False,
     'val': ''},
    {'Index': 1,
     'OtherInfoTextExist': False,
     'Selected': False,
     'val': ''},
    {'Index': 2,
     'OtherInfoTextExist': False,
     'Selected': False,
     'val': ''},
    {'Index': 3, 'Selected': True, 'val': 4}]}]}
"""

MCMS = """
{'Response': [{'Eliminations': [],
   'Index': 0,
   'OtherInfo': [],
   'Response': [{'Index': 0, 'Selected': False, 'val': ''},
    {'Index': 1, 'Selected': True, 'val': 2},
    {'Index': 2,
     'OtherInfoTextExist': False,
     'Selected': False,
     'val': ''},
    {'Index': 3, 'Selected': True, 'val': 4}]}]}
"""

alpha2num = dict(zip(string.letters, [ord(c) % 32 for c in string.letters]))
num2alpha = dict(zip(range(1, 26), string.ascii_uppercase))

def parseXMLContent(node):
    """
    Takes in a XML <Content> node, and returns a JSON-like string
    with Key:value pairs.

    :param node: XML node containing the <key>xxx</key><value>yyy</value> pairs
    :return: a JSON-like string {key:value}
    """

    if etree.iselement(node):
        r = {}
        num=0
        for pair in node.iter('pair'):
 #           key = pair.find('key').text
            value = pair.find('value').text
            r[num] = value
            num += 1
    else:
        warnings.warn("ParseContent: expecting a XML node")
        return None
    return r

def MathMLExtraction(s):
    if not isinstance(s, basestring):
        return None
    return s
 #   if(s.find('</mn></math>')!=-1):
 #       length = len(s.split('</mn></math>')[0].rsplit('<mn>',1))
 #       return s.split('</mn></math>')[0].rsplit('<mn>', 1)[length - 1].encode("utf-8")
 #   elif(s.find('</mo></math>')!=-1):
 #       length = len(s.split('</mo></math>')[0].rsplit('<mo>',1))
 #       return s.split('</mo></math>')[0].rsplit('<mo>', 1)[length - 1].encode("utf-8")

def parseMC(s):
    """
    takes a string with response JSON, and returns the MC resposnes as an array of arrays.
    Each MC has 1 "records" which may have one or more "Selected==True" depending on SS or MS variant.
    The result will be an array of arrays, with each element being a response record.
    If no response, return [].
    If not a response string, return None
    
    """
#    print ('In MC')
    answerlist=[]
    try:
        RespDict=json.loads(s)
    except:
        return None
    for records in RespDict["Response"]:
            for record in records["Response"]:
                if(record["Selected"]==True):
                    # set the PartId to missing
                    #record["PartId"] = None
                    #answerlist.append(record)

                    # simplified output
                    ans=record["Index"]
                    if(record["val"]==""):
                        answerlist.append({str(ans):'X'})
                    else:
                        s = num2alpha[int(record["val"])]
                        answerlist.append({str(ans):s})
                        answerlist.append({'Eliminations':records["Eliminations"]})

    return answerlist

# BQChoice
# Note that this code does not recover "OtherInfo" text from each part.
sBQChoice="""
{'Response': [{'Index': 0,
   'OtherInfo': [],
   'OtherInfoTextExist': False,
   'PartId': 'VH271370',
   'Response': [{'Index': 0, 'Selected': False, 'val': ''},
    {'Index': 1, 'Selected': False, 'val': ''},
    {'Index': 2, 'Selected': False, 'val': ''},
    {'Index': 3, 'Selected': False, 'val': ''},
    {'Index': 4, 'Selected': True, 'val': 5}]},
  {'Index': 1,
   'OtherInfo': [],
   'OtherInfoTextExist': False,
   'PartId': 'VH271372',
   'Response': [{'Index': 0, 'Selected': False, 'val': ''},
    {'Index': 1, 'Selected': False, 'val': ''},
    {'Index': 2, 'Selected': True, 'val': 3},
    {'Index': 3, 'Selected': False, 'val': ''},
    {'Index': 4, 'Selected': False, 'val': ''}]},
  {'Index': 2,
   'OtherInfo': [],
   'OtherInfoTextExist': False,
   'PartId': 'VH271374',
   'Response': [{'Index': 0, 'Selected': False, 'val': ''},
    {'Index': 1, 'Selected': False, 'val': ''},
    {'Index': 2, 'Selected': False, 'val': ''},
    {'Index': 3, 'Selected': True, 'val': 4},
    {'Index': 4, 'Selected': False, 'val': ''}]},
  {'Index': 3,
   'OtherInfo': [],
   'OtherInfoTextExist': False,
   'PartId': 'VH271375',
   'Response': [{'Index': 0, 'Selected': False, 'val': ''},
    {'Index': 1, 'Selected': False, 'val': ''},
    {'Index': 2, 'Selected': False, 'val': ''},
    {'Index': 3, 'Selected': True, 'val': 4},
    {'Index': 4, 'Selected': False, 'val': ''}]}]}
"""
def parseBQChoice(s):
    """
    takes a string with response JSON, and returns the BQChoice resposnes as an array of arrays.
    Each BQChoice will have multiple objects with PartId. 
    return will be 
    """
#   print ('In BQChoices')
    answerlist=[]
    try:
        RespDict=json.loads(s)
    except:
        return None
    for records in RespDict["Response"]:
        if("PartId" in records):
            partID = records["PartId"]
        elif("GroupId" in records):
            partID = records["GroupId"]
 #       if (records.get("Selected") == None):
 #0           answerlist.append({partID: records["Response"]})
        for record in records["Response"]:
            if("Selected" in record):
                if(record["Selected"]==True):
                    # copying over the PartId from the parent object
                    #record["PartId"] = records["PartId"]
                    #answerlist.append(record)
                    
                    #Simplified output: PartId-val
 #                   answerlist.append("{}-{}".format(records["PartId"], record["val"]))
#                    answerlist.append([{'PartID':records["PartId"]},{'value':record["val"]}])
                    answerlist.append({partID: record["val"]})
            else:
                answerlist.append({partID: record})

    return answerlist

def parseGridMS(s):
#    print ('In GridMS')
    answerlist = []
    responsedict=dict()
    try:
        RespDict = json.loads(s)
    except:
        return None
    for items in RespDict["Response"]:
            for key, value in items.iteritems():
                if(key=='GroupId' or key=='PartId'):
                    id=value.encode("utf-8")
 #                   print (type(value))
    #            if (key == 'Response' and type(value)=="list"):
                if (key == 'Response'):
                    for element in value:
                        for k, v in element.iteritems():
                            if (k == 'Selected' and v == True):
#                                print(id, element['val'])
                                if (element['val'] != ''):
                                    value = element['val']
                                else:
                                    value = None
#                                answerlist.append("{}-{}".format(id, value))
#                                answerlist.append([{'ID':id},{'value':value}])
                                answerlist.append({id: value})
    #            elif(key == 'Response' and type(value)=="str"):
    #                answerlist.append("{}-{}".format(id, value))

    return answerlist
# BQNumeric
BQNumeric = """{'Response': [{'PartId': '1', 'Response': '4'}]}"""
def parseBQNumeric(s):
    """
    takes a string with response JSON, and returns the BQNumeric resposnes as an array of arrays.
    Each BQNumeric will have a single response. 
    return will be 
    """
#    print ('In BQNumeric')
    answerlist=[]
    try:
        RespDict=json.loads(s)
    except:
        return None
    for records in RespDict["Response"]:
        if(records["Response"]!=''):
            answerlist.append([{'PartId':records["PartId"].encode('ascii')},{"Response":records["Response"].encode('ascii')}])
    return answerlist 

def parseComposite(s):
    answerlist=[]
    try:
        RespDict = json.loads(s)
    except:
        return None
    for records in RespDict["Response"]:
        if(type(records)!= dict):
            warnings.warn("There is node whose type is not dict")
            continue
        if('Type' in records):
            for record in records["Response"]:
                if(record is None):
                    continue
                if(records['Type']=='T'):
                    if (record["Selected"] == True):
                        if (record['val'].find("<math")!=-1):
                            value = MathMLExtraction(record["val"])
                        else:
                            if(record['val']!=''):
                                value = record['val'].encode('ascii')
                            else:
                                value = record['val']
#                        #                       answerlist.append("{}-{}".format(records["PartId"], value))

                        answerlist.append({records["PartId"].encode('ascii'): value})
                elif(records['Type']=='MATCHMS'):#MatchMS
                    value="{}-{}".format(record['source'], record['target'])
                    #                       answerlist.append("{}-{}".format(records["PartId"], value))
                    answerlist.append({records["PartId"].encode('ascii'): value})
                elif(records['Type']=='MCSS' or records['Type']=='MCMS' or records['Type']=='MAPMS' or \
                                 records['Type']=='MAPSS' or records['Type']=='InlineChoices'):
                    #MAPMS and MAPSS look the same as MCMS and MCSS
                    if (record["Selected"] == True):
                        if (record["val"] == ""):
                            value='X'
                        else:
                            value=record["val"]
                        answerlist.append({records["PartId"].encode('ascii'):value})
        else:
            warnings.warn("Type is missing for Part ID", records['PartId'])
            continue
    return answerlist

def parseInteractive(s):
#    print ('In Interactive')
    answerlist = []
    try:
        RespDict = json.loads(s)
    except:
        return None
    if(RespDict['responseData']==None):
        return None
    if(type(RespDict['responseData'])==list):
        response=','.join(RespDict['responseData']).encode("utf-8")
    else:
        if (RespDict['responseData'].find("data:image") != -1):
            response=''
        else:
            response=RespDict['responseData'].encode("utf-8")
    answerlist.append({'Response':response})
    return answerlist

def parseMatchMS(s):
    answerlist = []
  #  print ('In MatchMS')
    try:
        RespDict = json.loads(s)
    except:
        return None
    for element in RespDict:
 #           print (type(element))
            for k,v in element.iteritems():
                if(k=='source'):
                    source=v
                elif(k=='target'):
                    target=v
#            answerlist.append("{}-{}".format(source, target))
            answerlist.append({source:target})
    return answerlist

def parseExtendedText(s):
    answerlist = []
#    print ('In ExtendedText')
    if(s==''):
        return None
    text=s.split('"Response":')[1].rstrip('}').lstrip('[').rstrip(']')
 #   try:
 #       RespDict = json.loads(s)
 #   except:
 #       return None
 #   if (RespDict["Response"]):
    if (text):
        if (text.find("<math xmlns=") != -1):  # mathml
                val = MathMLExtraction(text)
                answerlist.append({'Response':val})
        else:
#                content=lxml.html.fromstring(RespDict["Response"][0].lstrip('[').rstrip(']')).text_content()
                content=lxml.html.fromstring(text).text_content().encode("utf-8")
                answerlist.append({'Response':content.replace('\xc2\xa0', ' ')})
    return answerlist

def parseInlineChoiceListMS(s):
    answerlist = []
 #   print ('In InlineChoiceListMS')
    try:
        RespDict = json.loads(s)
    except:
        return None
    if(RespDict["Response"]):
        for records in RespDict["Response"]:
            if(records["Response"]):
                partID=records["PartId"].encode("utf-8")
                response=records["Response"][0].encode("utf-8")
            else:
                partID=str(records["PartId"])
                response=''
#          answerlist.append("{}-{}".format(records["PartId"], records["Response"][0].encode("utf-8")))
            answerlist.append({partID:response})
    return answerlist

def parseZones(s):
#    print ('In Zones')
    try:
        RespDict = json.loads(s)
        return RespDict['Response']
    except:
        return None

def parseSBT(s):

    if(s.find('<responseData>')!=-1):
       if(s.find('</responseData>')== -1):
 #       print 'poor formed xml'
            if((len(s)-len(s.rsplit('data:image',1)[0]))==10):
                txt=s.rsplit('data:image',1)[0]+'</value></pair></content></responseDatum></responseData>'
       else:
           txt=s.split('</responseData>')[0]+'</responseData>'
    else:
       return None
 #   try:
    txt= unicode(txt, errors='ignore')
    root = etree.fromstring(txt)
 #   except:
  #      w.write(s+'\n')
   #     warnings.warn("String cannot be parsed as XML")
    #    return None
    answerlist=[]
    for responseDatum in root.iter('responseDatum'):
        sceneId=responseDatum.findtext('sceneId')
        responseComponentId=responseDatum.findtext('responseComponentId')
        responseType=responseDatum.findtext('responseType')
        for content in responseDatum.iter('content'):
            ctdict=parseXMLContent(content)
            if(responseType=="Selection"):
                for key, value in ctdict.iteritems():
                    if(value=='true'):
                        sel=string.ascii_uppercase[key]
 #                       answerlist.append("{}-{}".format(responseComponentId, sel))
                        answerlist.append([{"ResponseComponentId":responseComponentId},{"Selection": sel}])
                        break
            elif(responseType=="Math"):
                #mathml, output last action
                for key, value in ctdict.iteritems():
                    val=MathMLExtraction(value)
                    #                    answerlist.append("{}-{}".format(key, value))
                    answerlist.append([{"key":str(key)},{"value":val}])
            elif (responseType == "Text"):
                for key, value in ctdict.iteritems():
                    if(value.startswith('![CDATA[')):
                        value=value.split('![CDATA[')[1].rstrip(']]')
#                    answerlist.append("{}-{}".format(key, value))
                    answerlist.append([{"key":str(key)},{"value":value}])
            elif(responseType == "Record"):
                for key, value in ctdict.iteritems():
 #                   answerlist.append("{}-{}".format(key, value))
                    answerlist.append([{"key":str(key)},{"value":value}])
            else:
                continue
    return answerlist

def parseFillInBlank(s):
#mathml, output last action
    answerlist=[]
#    print ('In FillinBlank')
    try:
        RespDict = json.loads(s)
    except:
        return None
    for records in RespDict["Response"]:
        if (records['Response'].find('<math xmlns=')!=-1):
            val=MathMLExtraction(records['Response'])
#                answerlist.append("{}-{}".format(records["PartId"],val))
            answerlist.append({records["PartId"]: val})
        else:
            val=records['Response']
            answerlist.append({'Response':val})
    return answerlist

def parseSQNotAnswered(s):
 #   f.write('In SQNotAnswered\n')
    try:
        RespDict = json.loads(s)
    except:
        return None
    answerlist = []
    if(s.find('PartId')!=-1 or s.find('GroupId')!=-1):
        print ('PartID?')
        if(s.find("Selected")!=-1):
            answerlist=parseBQChoice(s)
        else:
            answerlist.append(RespDict["Response"])
    elif(s.find('Selected')!=-1):
        print ('MC')
        answerlist=parseMC(s)
    else:
        print ('Text')
        answerlist.append({'Response': RespDict['Response']})
    return answerlist

def parseDialog(s):
    # combination of SBT, MCMS and ExtendedText
 #   print ('In Dialog')
    answerlist = []
    if (s.find('<responseData>') !=-1):
        #same as SBT
        answerlist=parseSBT(s)
    elif(s.find('PartId') !=-1):
        if(s.find("Selected")!=-1):
            answerlist=parseBQChoice(s)
        else:
            answerlist.append(RespDict["Response"])
    elif(s.find('Selected')!=-1):
        answerlist=parseMC(s)
    else:
        try:
            RespDict = json.loads(s)
            answerlist.append({'Response':RespDict['Response']})
        except:
            return None
    return answerlist

def parseBlockReview(s):
#combination of BQChoice, MC and Interactive
    print('In BlcokReview')
    answerlist = []
    if (s.find('PartId') != -1 or s.find('GroupId') != -1):
        if(s.find('Type')!=-1):
            answerlist=parseComposite(s)
        else:
            answerlist=parseBQChoice(s)
    elif(s.find('source')!=-1):
        answerlist=parseMatchMS(s)
    elif(s.find('"responseData"')!=-1):
        RespDict = json.loads(s)
        answerlist.append({'Response':RespDict['responseData']})
    elif(s.find("Selected")!=-1):
        answerlist=parseMC(s)
    else:
        answerlist.append(s)
    return answerlist

def parseResponses(df,
                     config=None, 
                     label="ItemTypeCode",
                     outputCol = "Answer"):
    """Parse the SQ response data, extract the responses from the JSON data

    :param df: the input data frame
    :type df: Pandas data frame
    
    :param label: optional, name of the column indicating the item type, which determines how to parse.
    :type outInfo: string

    :param config: optional configuation object; default to None
    :type config: object or None

    :returns: df with Response.PartId, Response.Index, value
    :rtype: Pandas data frame

    """

    assert (isinstance(df, pd.DataFrame))
    assert (label in df.columns)
    if config is None:
        config = {
            "handlers": {
                "BQNumeric": parseBQNumeric,
                "BQChoices": parseBQChoice,
                "BQMCSS": parseMC,
                "BQMCMS": parseMC,
                "ZonesMS": parseZones,
                "ZonesSS": parseZones,
                "GridMS": parseGridMS,
                "ReadingNonSBT": parseSBT,
                "SBT":parseSBT,
                "ExtendedText": parseExtendedText,
                "InlineChoiceListMS": parseInlineChoiceListMS,
                "Interactive": parseInteractive,
                "Composite": parseComposite,
                "CompositeCR": parseComposite,
                "FillInBlank": parseFillInBlank,
                "MultipleFillInBlank": parseFillInBlank,
                "SQNotAnswered": parseSQNotAnswered,
                "MCMS": parseMC,
                "MCSS": parseMC,
                "MatchMS ": parseMatchMS,
                "Dialog": parseDialog,
                "Directions": parseDialog,
                "BlockReview": parseBlockReview,
                "TimeLeftMessage": parseDialog,
                "TimeOutMessage": parseDialog,
                "ThankYou": parseMC
            }
        }
    
 #MatchMS label has a trailing space 'MatchMS '
    # check to see if there are events not handled
    #print config["handlers"]
    #print "Events in the data frame: {}".format(df[label].unique().tolist())
    #print "Events to be handled: {}".format(config["handlers"].keys())
#    print (df[label])
#    print (config["handlers"].keys())
    if len(set(df[label].unique().tolist())-set(config["handlers"].keys()))>0:
        print ("Not all item types are handled!\n{}".\
            format(set(df[label].unique().tolist())-set(config["handlers"].keys())))


    # now let's revert the config, to get `parser:[list of labels]`
    funcMap = {}
    for k, v in config["handlers"].iteritems():
        funcMap[v] = funcMap.get(v, []) + [k]

    # add a output
    out=[]
    # we now loop through all funcMap elements and do the conversion
    for parser, eventList in funcMap.iteritems():
        idx = df.loc[:, label].isin(eventList)
        df.loc[idx, outputCol] = df.loc[idx, "Response"].apply(parser)
        #print "Events={}, Handler={}".format(eventList, parser)
        #tmp = df.loc[idx, :].groupby("ItemResponseId").apply(parser)
        #try:
        #    tmp = tmp.drop("ItemResponseId",1).reset_index().drop("level_1")
        #except:
        #    tmp = tmp.reset_index()
        #out.append(tmp)
    # deal with events not in here
    
    return df
if __name__ == '__main__':

    if len(sys.argv)<2:
        print ("Usage: python {} csvFileName.csv".format(sys.argv[0]))
        exit()
		
    dataFileName = sys.argv[1]
    print(dataFileName)
    df = pd.read_csv(dataFileName, sep="\t", header=None,
                 names=["ItemResponseId","SubjectName","Grade","BookletNumber",
                        "BlockCode","AccessionNumber","ItemTypeCode","IsAnswered",
                        "IsSkipped","Response"])
    res = parseResponses(df)

# looking for duplicated responses
    res.loc[res.duplicated([ u'BookletNumber', u'AccessionNumber'], keep=False)]\
		.sort_values([ u'BookletNumber', u'AccessionNumber'])\
		.to_csv(dataFileName.replace(".txt", "")+'_DuplicatedResponses.csv')

    dfByAccNum = res.drop_duplicates([ u'BookletNumber', u'AccessionNumber'])\
		.pivot(columns='AccessionNumber', index="BookletNumber", values="Answer")

    # saving to a bunch of csv files
    res.to_csv(dataFileName.replace(".txt", "")+'_Responses.csv')

    dfByAccNum.to_csv(dataFileName.replace(".txt", "")+'_Responses_byAccNum.csv')