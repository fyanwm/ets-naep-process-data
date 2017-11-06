
# coding: utf-8

# # Reconstructing Process Data

# - reconstruct the history of the response as `responseHistory`
#     - `"-B"` for eliminating "B"
#     - `"+B"` for un-eliminating "B"
#     - `"@B"` for selecting "B"
#     - `"@"` for deselecting the last selection; auto-generated when you, e.g., select B, then eliminate B.
#     - `"X"` for Clear Answer button click; this only clears the options, not the elimination status (??)
# - reconstruct the selection and elimination status of each option
# - apply the 4 different scoring rules to extract responses based on each rule

# In[40]:

import os, glob, os.path
import pandas as pd
import numpy as np
import json
import csv
import time
import io
from xlrd import open_workbook
import ast
import string

import logging
from logging.config import dictConfig

# # Defining utility functions
# 
# The function `concatActions()` creates the response history representation for each item. In the case no data is available (either because students did not interact with any of the items, or if the process data are not found), the function `noData()` generates the corresponding error message. 

# In[188]:


def noData(df, msg):
    return pd.Series({"responseHistory": msg})


# The function `trackResponseStates()` is the workhorse. It takes the records of an item:
# 
# - drops any trailing `Clear Answer` button presses
# - reconstructs the selection and elimination status for the 4 options
# - get the response history string
# - apply the 4 different scoring rules
# - returns the data as a Pandas Series

# In[191]:

def concatActions(itemLog):

   assert(isinstance(itemLog, pd.DataFrame))
   assert("extInfo" in itemLog.columns)
   num2alpha = dict(zip(range(1, 6), string.ascii_uppercase))
   hist=[]
   nrow=0
   for index, row in itemLog.iterrows():
       if (row['Label'] == 'Clear Answer'):
           hist.append('X')
       else:
           if (isinstance(row['extInfo'], str)):
               extInfostring = row['extInfo'].replace("'", '\"').replace('u"', '"')
               d = json.loads(extInfostring)
               for key, value in d.iteritems():
                   #                print >> logfile1, "Dictionary key: ",key," value: ",value
                   option = key.split("_")[1].replace('"', '')
                   action = value.replace('"', "")
                   if (row['Label'] == 'Eliminate Choice'):
                       if (action == 'eliminated'):
                           s = "-" + num2alpha[int(option)]
                           hist.append(s)
                       elif (action == 'uneliminated'):
                           s = "+" + num2alpha[int(option)]
                           hist.append(s)
                   elif (row['Label'] == 'Click Choice'):
                       if (action == 'checked'):
                           s = "@" + num2alpha[int(option)]
                           hist.append(s)
                       elif (action == 'unchecked'):
                           # this should not happen for MCSS
                           # but we keep this here as a reminder that this could for MCMS
                           s = "^" + num2alpha[int(option)]
                           hist.append(s)
       nrow=nrow+1
   res="`"+" ".join(hist)
   return res

def parseResponses(itemLog):
    """Given the response log for an item, track the state of the options.
    Two sets of states for each option: Selection and Elimination.

    Also ignore the trailing Clear Answer buttons.

    """
    assert (isinstance(itemLog, pd.DataFrame))
    #    print >> logfile1, itemLog.iloc[0]['BookletNumber']

    # response history
    responseHistory = concatActions(itemLog)
    # drop trailing Clear Answers
    test = True;
    clearAnswer = False
    reversed_df = itemLog.iloc[::-1].reset_index()
    droppedrows = []
    for index, row in reversed_df.iterrows():
        if (row.Label == "Clear Answer"):
            droppedrows.append(index)
            clearAnswer = True
        else:
            break
    if (clearAnswer):
        reversed_df.drop(reversed_df.index[droppedrows], inplace=True)
    itemLog = reversed_df.iloc[::-1]
    #    assert("extInfo" in itemLog.columns)
    if ("extInfo" not in itemLog.columns):
        return None

    # init
    nchoice=0
    selection = {}
    elimination = {}
    for i in ["A", "B", "C", "D", "E"]:
        selection[i] = False
        elimination[i] = False
    alpha2num = dict(zip(string.letters, [ord(c) % 32 for c in string.letters]))
    num2alpha = dict(zip(range(1, 6), string.ascii_uppercase))
    # track states by looping through all actions from the top, less the trailing CAs
    for index, row in itemLog.iterrows():
        if (row['Label'] == 'Clear Answer'):
            # print >> logfile1, "Cleared Answer"
            for a in selection:
                selection[a] = False
        else:
            if (isinstance(row['extInfo'], str)):
                extInfostring = row['extInfo'].replace("'", '\"').replace('u"', '"')
                d = json.loads(extInfostring)
                for key, value in d.iteritems():
                    option = key.split("_")[1].replace('"', '')
                    action = value.replace('"', "")
                    s = num2alpha[int(option)]
                    if (row['Label'] == 'Eliminate Choice'):
                        if (action == 'eliminated'):
                            elimination[s] = True
                            selection[s] = False
                        elif (action == 'uneliminated'):
                            elimination[s] = False
                    elif (row['Label'] == 'Click Choice'):
                        if (action == 'checked'):
                            # selecting option X means 2 things :
                            # a), for MCSS all other options are cleared
                            for i in ["A", "B", "C", "D", "E"]:
                                selection[i] = False
                            # b), X cannot be in the eliminated state
                            elimination[s] = False
                            # now we set the selection to True
                            selection[s] = True
                        elif (action == 'unchecked'):
                            # for MCSS this should not happen. But let's put it here as a reminder
                            # that this can happen for MCMS scases.
                            selection[s] = False
            else:
                print  "error: no valid extInfo", index, row['BookletNumber'], row['extInfo']

    # now return
    res = {
        "responseHistory": responseHistory,
        "E1_Rule": "",
        "E3_Rule": "",
        "X_Rule": "",
        "Strict_Rule": "",
        "Answer":""
    }

    # response: if only one is chosen, regardless of trailing ClearAnswer buttons
    sel = [selection[k] for k in ["A", "B", "C", "D", "E"]]
    if sel.count(True) == 1:
        try:
            res["X_Rule"] = ["A", "B", "C", "D", "E"][sel.index(True)]
        except:
            pass
    # According to the strict rule where we treat Clear Answer literally
    res["Strict_Rule"] = "" if clearAnswer == True else res["X_Rule"]

    # Eliminate 1 Rule: use -D to indicate D as the option
    eli = [elimination[k] for k in ["A", "B", "C", "D", "E"]]
    if eli.count(True) == 1:
        try:
            res["E1_Rule"] = ["A", "B", "C", "D", "E"][eli.index(True)]
        except:
            pass
    # Eliminate 3 Rule: using -A, -B, -C to indicate D is the option
    # In math where there can be up to 5 choices, "E3" is a misnomer
    # We really meant eliminating all-but-one
    if eli.count(False) == 1:
        try:
            res["E3_Rule"] = ["A", "B", "C", "D", "E"][eli.index(False)]
        except:
            pass
    elist=[]
    for lt in ("A", "B", "C", "D", "E"):
        if (elimination[lt]==True):
            elist.append(alpha2num[lt])

    if(res['Strict_Rule']==''):
        res['Answer']=[{"Eliminations":elist}]
    else:
        s=alpha2num[res["Strict_Rule"]]
        res["Answer"]=[{nchoice:s},{"Eliminations":elist}]

    return pd.Series(res)

def main():
# # Running
# 
# Now let's get ready to run. The current data files are in 4 sub-folders. We will process each folder separately and save a CSV file for each folder.
# 
# We read the CSV, check whether the necessary columns are there to support the analysis. We will process all the files under the folder, and combine them as a single Pandas data frame. We will save it as a CSV file with the folder name as part of the file name. 
# 
# Note that saving to CSV may result in column names being arranged alphabetically. 

# In[192]:
#    start_time = time.time()
    csvpath = 'C:/Users/fyan/OneDrive - Educational Testing Service/Documents/NAEP Process Data/ProcessData/Math/Grade8/csv/'
    fileList = next(os.walk(csvpath))[2]
    listpath='C:/Users/fyan/OneDrive - Educational Testing Service/Documents/NAEP Process Data/ProcessData/Math/Grade8/Reconstructed/'
    errlog=open('C:/Users/fyan/OneDrive - Educational Testing Service/Documents/NAEP Process Data/ProcessData/Math/Grade8/Reconstructed/errorlog.txt','wb')
 #   wb = open_workbook(listpath + '2017Grade4_MST_BookletNumbers.xlsx')
    logfile = open(listpath + 'Grade8_check.txt', 'w+')
#    listpath=listpath+'Grade4MST/'
    inoblockcode=0
    for filename in fileList:
        fn=filename.split('.')[0]
        df = pd.read_csv(csvpath+filename, index_col=0,  parse_dates=[6])
        df = df.loc[(df['ItemType']=="MCSS") & (df['Label'].isin(["Click Choice","Eliminate Choice","Clear Answer"])),:]
        if "BlockCode" in df.columns:
            df=df.groupby(["BookletNumber", "BlockCode", "AccessionNumber"]).apply(parseResponses).reset_index()
            df.to_csv(listpath +fn  + "_reconstructed.csv", encoding='utf-8')
        else:
            inoblockcode = inoblockcode + 1
            errlog.write('BookletNumber '+ name+ ' has no BlockCode')
# # Validation
# 
# Now head over to the current directory for the output CSV files. Open in Excel and freeze the first row. Scan the data and check whether they make sense.
# 
# # Next steps
# 
# - Validate the algorithm
# - Do we see additional strategies that we need to cover?
# - How do we define `consistency`?
#     - for each booklet by block, the student used at least one method over __ % of time
#     - we will score the student based on the *primary* strategy
#     - we need to decide how to account for items the student may have skipped (and therefore not shown in the data)
#     
# - Running
#     - need to set up subfolders? or we can take a list and run them all
#     
# - Validation
#     - against the 'state info' method.

# In[ ]:
if __name__ == "__main__":
    main()


