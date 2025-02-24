
import re
import glob
import copy

import sys
import time
from datetime import datetime
from collections import Counter

import urllib2,urllib
from collections import defaultdict
import math
import json
import csv

startTime = datetime.now()
print "Start"

# --------------------------------------------

main_events = ["open-document", "search", "highlightText", "newconnection", "createNote"]
all_events = ["collapse-document", "scrunch-highlight-view", "open-document", "restore-from-scrunch", "search", "highlightText", "newconnection", "mouseenter-document" , "mouseexit-document" , "createNote", "enddrag-document"]
spam_events = ["mouseexit-document-minimized", "mouseenter-document-minimized", "startdrag-document"]
id_events = spam_events + ["collapse-document", "scrunch-highlight-view", "open-document", "mouseenter-document" , "mouseexit-document" , "enddrag-document"]
who_cares_events = ["end-study", "start-study"]
		
def save_as_js_file_push_to(obj, filename):
    fout = open(filename,"w")
    fout.write(json.dumps(obj,indent=1))
    fout.close()
		
def get_texts_from_log(log_json_lines,events_to_include,name,devideby): 
   
    from_log_to_id = {}
    doc_counts = {}
	
    ret = []
    start_open = []
    start_read = []
    start_hover = []
    bookmark = []
    start_drag = []
    highlighted_text = []
    scrunched = []	
    logdata = open(log_json_lines)
    start=0
    line_number=0
    last_doc = 0
    last_doc_ID	= ""
	
    last_search = ""
    last_time_search = 0
	
    last_stop= ""
    last_read= ""
    check = 0
    last_time = 0
    doc_drag = 0
    last_hover = 0	
    reading_document_time_out = 20
    null_duration = 10;    # two second # This duration is for these interactions: search, highlight,  createNote, connection
    brush_minimum = 5;      # half a second     # This duration is for mouseenter-document-minimized  
    reading_minimum = 10;      # half a second     # This duration is for mouseenter-document-minimized  
    
    for i in xrange(1,200):
        start_open.append(0)
        start_read.append(0)
        start_hover.append(0)
        highlighted_text.append("")
        bookmark.append(0)
        start_drag.append(0)
        scrunched.append(0)
	
    for line in logdata:
        
        text = ""
        entry = json.loads(line)

        if entry["type"] in id_events:
            mystring = entry["tags"][1]
            myarray = int(mystring.split(devideby)[1])		
            doc_name = name + " " + str(myarray)									
		
        if start == 0:
            start=1     
            start_time = entry["timestamp"]/100
		
        created_at = entry["timestamp"]/100 - start_time  # study time in seconds

        if entry["type"] == "end-study":
            end_at = entry["timestamp"]/100 - start_time  # study time in seconds
			
        if entry["type"] == "open-document" and "open-document" in events_to_include:
            start_open[myarray] = int(created_at)
            start_read[myarray] = int(created_at) + 1
 
            duration = int(created_at) - start_hover[myarray] - 1
            temp = {"time": float(start_hover[myarray])/10 , "Text":  doc_name, "duration": float(duration)/10, "ID":doc_name,"InteractionType" :"brush_document_title"}

            if int(duration) > brush_minimum and start_hover[myarray] > 0:
                ret.append(temp)            
            if start_hover[myarray] > 0:            
                start_hover[myarray] = 0			
			
        if entry["type"] == "collapse-document" and "collapse-document" in events_to_include:
            #mystring = entry["tags"][1]
            #myarray = int(mystring.split("y")[1])
            #if (myarray == 51 ):
               # print start_open[myarray]			
            duration = int(created_at) - start_open[myarray] 
            if int(duration) < brush_minimum:
                duration = brush_minimum

            if (bookmark[myarray] == 1):
                temp = {"time": float(start_open[myarray])/10 , "Text":  highlighted_text[myarray], "duration": float(duration)/10, "ID":doc_name,"InteractionType" :"resotre_bookmark"}			
            else: 
                temp = {"time": float(start_open[myarray])/10 , "Text":  doc_name, "duration": float(duration)/10, "ID":doc_name,"InteractionType" :"open_document"}			
            if start_open[myarray] > 0:            
                ret.append(temp);
                start_open[myarray] = 0;
                bookmark[myarray] = 0;				

			# Here is the Stop reading_document function after closing a Doc
            duration = int(created_at) - start_read[myarray] 
            # if int(duration) < brush_minimum:
                # duration = brush_minimum
            temp = {"time": float(start_read[myarray])/10 , "Text":  doc_name, "duration": float(duration)/10, "ID":doc_name,"InteractionType" :"reading_document"}
            if (int(duration) > reading_minimum) and (start_read[myarray] > 0) and (start_open[myarray] > 0):            
                start_read[myarray] = 0			
                ret.append(temp)			

        if entry["type"] == "restore-from-scrunch" and "restore-from-scrunch" in events_to_include:
            #mystring = entry["tags"][1]
            #myarray = int(mystring.split("g")[1])
            myarray = last_doc	
            scrunched[myarray] = 0
            start_open[myarray] = int(created_at)
            start_read[myarray] = int(created_at) + 1
                # Here brush_document_title ends with this interaction
            duration = int(created_at) - start_hover[myarray] 
            doc_name = name + " " + str(myarray)
            temp = {"time": float(start_hover[myarray])/10 , "Text":  doc_name, "duration": float(duration)/10, "ID":doc_name,"InteractionType" :"brush_document_title"}
            if int(duration) > brush_minimum and start_hover[myarray] > 0:
                ret.append(temp)            
            if start_hover[myarray] > 0:            
               start_hover[myarray] = 0
               bookmark[myarray] = 1;

        if entry["type"] == "scrunch-highlight-view" and "scrunch-highlight-view" in events_to_include:
            #mystring = entry["tags"][1]
            #myarray = int(mystring.split("y")[1])            
            duration = int(created_at) - start_open[myarray] 
            if int(duration) < brush_minimum:
                duration = brush_minimum
#            if (myarray == 51 ):
#                print start_open[myarray]
            scrunched[myarray] = 1
            temp = {"time": float(start_open[myarray])/10 , "Text": doc_name, "duration": float(duration)/10, "ID":doc_name,"InteractionType" :"open_document"}
            if start_open[myarray] > 0:            
                ret.append(temp)
                start_open[myarray] = 0
                temp = {"time": float(created_at)/10 , "Text": highlighted_text[myarray], "duration": 0, "ID":doc_name,"InteractionType" :"bookmark_highlights"}
                ret.append(temp)
			# Here is the Stop reading_document function after closing a Doc
            duration = int(created_at) - start_read[myarray] 
            # if int(duration) < brush_minimum:
                # duration = brush_minimum
            temp = {"time": float(start_read[myarray])/10 , "Text":  doc_name, "duration": float(duration)/10, "ID":doc_name,"InteractionType" :"reading_document"}
            if (int(duration) > reading_minimum) and (start_read[myarray] > 0) and (start_open[myarray] > 0):            
                start_read[myarray] = 0			
                ret.append(temp)			
				
        if entry["type"] == "enddrag-document" and "enddrag-document" in events_to_include:
            #mystring = entry["tags"][1]
            #myarray = int(mystring.split("y")[1])            
            doc_drag = 0			
            duration = int(created_at) - start_drag[myarray] 
            temp = {"time": float(start_drag[myarray])/10 , "Text":  doc_name, "duration": float(duration)/10, "ID":doc_name,"InteractionType" :"moving_document"}
            if int(duration) > brush_minimum and start_drag[myarray] > 0:
                ret.append(temp)            
            if start_drag[myarray] > 0:            
                start_drag[myarray] = 0

        if entry["type"] == "startdrag-document" and "startdrag-document" in events_to_include:
            #mystring = entry["tags"][1]
            #myarray = int(mystring.split("y")[1])
            start_drag[myarray] = int(created_at)
            doc_drag = 1			
			# Here brush_document_title ends with open_document interaction
            duration = int(created_at) - start_hover[myarray] - 1
#            print (myarray)			
#            print (start_hover[myarray])
            temp = {"time": float(start_hover[myarray])/10 , "Text":  doc_name, "duration": float(duration)/10, "ID":doc_name,"InteractionType" :"brush_document_title"}
            if int(duration) > brush_minimum and start_hover[myarray] > 0:
                ret.append(temp)            
                #print (start_hover[myarray])
            if start_hover[myarray] > 0:            
                start_hover[myarray] = 0

        if entry["type"] == "mouseenter-document" and "mouseenter-document" in events_to_include:
            #mystring = entry["tags"][1]
            #myarray = int(mystring.split("y")[1])
            if doc_drag == 0:			
                start_read[myarray] = int(created_at)
            last_doc = myarray
            last_doc_ID = doc_name

        if entry["type"] == "mouseexit-document" and "mouseexit-document" in events_to_include:
            #mystring = entry["tags"][1]
            #myarray = int(mystring.split("y")[1])            
            duration = int(created_at) - start_read[myarray] 
            # if int(duration) < brush_minimum:
                # duration = brush_minimum
            temp = {"time": float(start_read[myarray])/10 , "Text": doc_name, "duration": float(duration)/10, "ID":doc_name,"InteractionType" :"reading_document"}
            if (int(duration) > reading_minimum) and (start_read[myarray] > 0) and (scrunched[myarray] == 0) and (start_open[myarray] > 0):            
                start_read[myarray] = 0			
                ret.append(temp)
			
        if entry["type"] == "mouseenter-document-minimized" and "mouseenter-document-minimized" in events_to_include:
            #mystring = entry["tags"][1]
            #myarray = int(mystring.split("y")[1])
            start_hover[last_hover] = 0			
            last_hover = myarray
            if doc_drag == 0:						
                start_hover[myarray] = int(created_at)

        if entry["type"] == "mouseexit-document-minimized" and "mouseexit-document-minimized" in events_to_include:
            #mystring = entry["tags"][1]
            #myarray = int(mystring.split("y")[1])            
            duration = int(created_at) - start_hover[myarray] 
            temp = {"time": float(start_hover[myarray])/10 , "Text":  doc_name, "duration": float(duration)/10, "ID":doc_name,"InteractionType" :"brush_document_title"}
            if (int(duration) > brush_minimum) and (start_hover[myarray] > 0):
                ret.append(temp)
            if start_hover[myarray] > 0:            
                start_hover[myarray] = 0
					
        if entry["type"] == "createNote" and "createNote" in events_to_include:
            temp = {"time": float(created_at)/10, "Text":  "Note", "duration": float(null_duration)/10, "ID":0, "InteractionType" :"create_note"}
            ret.append(temp)
        if entry["type"] == "search" and "search" in events_to_include:
            temp = {"time": float(created_at)/10, "Text":  entry["message"], "duration": float(null_duration)/10, "ID":0,"InteractionType" :"search"}
            if not ((last_search == entry["message"]) and (created_at - last_time_search < 50)):  # if less than 5 seconds and search terms are the same, don't record it.
                ret.append(temp)
            last_search = entry["message"]						
            last_time_search = created_at
        if entry["type"] == "highlightText" and "highlightText" in events_to_include:
            temp = {"time": float(created_at)/10, "Text":  entry["message"], "duration": float(null_duration)/10, "ID":last_doc_ID,"InteractionType" :"highlight"}
            highlighted_text[last_doc] = highlighted_text[last_doc] + " " + entry["message"];
            ret.append(temp)
        if entry["type"] == "newconnection" and "newConnection" in events_to_include:
            temp = {"time": float(created_at)/10, "Text":  entry["tags"][1], "duration": float(null_duration)/10, "ID":entry["tags"][1],"InteractionType" :"connection"}
            mystring = entry["tags"][1]
            mystring = mystring.split(",")[0]
            myarray = int(mystring.split(devideby)[1])            			
            ret.append(temp)
			# Here brush_document_title ends with open_document interaction
            duration = int(created_at) - start_hover[myarray] 
            doc_name = name + " " + str(myarray)												
            if int(duration) < brush_minimum:
                duration = brush_minimum
            temp = {"time": float(start_hover[myarray])/10 , "Text":  doc_name, "duration": float(duration)/10, "ID":doc_name,"InteractionType" :"brush_document_title"}
            if start_hover[myarray] > 0:            
                start_hover[myarray] = 0
                ret.append(temp)
			
        line_number +=1
    #    print line_number		
    # Taking care of documents which left open at the end of study.
    
    for myarray in xrange(1,199):
        if start_open[myarray] > 0:
            duration = int(end_at) - start_open[myarray] 
            if int(duration) < brush_minimum:
                duration = brush_minimum
            doc_name = name + " " + str(myarray)				
            temp = {"time": float(start_open[myarray])/10 , "Text": doc_name, "duration": float(duration)/10, "ID": doc_name,"InteractionType" : "open_document"}
            ret.append(temp)
            #print "got you: ", temp
    return ret , null_duration

def extract_time(json):
    try:
        # Also convert to int since update_time will be string.  When comparing
        # strings, "10" is smaller than "2".
        return int(json['ID']['time'])
    except KeyError:
        return 0

def get_interaction_from_thinkaloud(csv_file, Interaction_list, null_duration):
			
    #--------------------CSV Thinkalouds------------
	
    #infiles = ["machine_parsable_transcripts.csv","machine_parsable_transcripts2_real.csv","machine_parsable_transcripts3.csv"]

    TopiChange = "User changed the topic"
    userNotes = "note"    
    thinkAloud =  "&quot" #  &#8220" #"&#34"
#	actions = "["
    ret = []
    inflection = {}
    
    timeOffset = []
    timeOffset.append([-78.6,-33.8,-105.4,-2.7,-113.6,-52.0,-4.4,-8.6])    #  Arms Dealing dataset time offset between think-alouds and captured user interactions 
    timeOffset.append([-10.5,5.0,-8.8,-7.2,59.0,-35.3,-40.0,-89.0])   # Terrorist Activity P2, P5 is positive time! 
    timeOffset.append([-205.0,5.0,9.1,15.2,4.9,8.0,4.7,-10.0])  # Disapearance P2, P3, P4, P5, P6, P7 are positive! 
    
    #for infile in infiles:
    print "Loading... ",csv_file
    rows = csv.DictReader(open(csv_file))
    seconds_offset = 0
    dynamic_offset = 0
    for row in rows:
        # print "row: ",row
        try:
            #print row
            if ((userNum == 2) & (datasetNum == 3)):
                timestamp = row["Timestamp"]
            else:
                timestamp = row["Timestamp"].split("[")[1].split("]")[0]
            
            #print timestamp
            hours,minutes,seconds = timestamp.split(":")
            seconds = (60*60*int(hours) + 60*int(minutes) + int(seconds))     # * 10
            # print "Time before: ", seconds
            seconds = float(seconds) + float(timeOffset[datasetNum-1][userNum-1])
            # print "Time after: ", seconds
            # print row["Transcript"]
            
            if TopiChange in row["Transcript"]:
          #      inflection[participant] += [seconds-seconds_offset]
                reason = row["Transcript"].split(":")[1]				 
                analysis_type = row["Transcript"].split("[")[1].split("]")[0].lower()
                if analysis_type[0] == type:
                    analysis_type = row["Transcript"].split("]")[1].split("[")[1].split("]")[0].lower()
                if ( (analysis_type != "top-down") and ( analysis_type != "bottom-up") and ( analysis_type != "break")):
                    print "Error on Analysis Type: ", row
                    print "     >>> ", analysis_type
                seconds = seconds  # + dynamic_offset
                if seconds < 0:
                    dynamic_offset = -1*seconds
                    print "Dynamic time alignment: ", dynamic_offset
                    seconds = seconds + dynamic_offset
                    
                temp = {"time": seconds , "Text": reason, "duration": 0, "ID": analysis_type, "InteractionType" :"topic_change"}			
                ret.append(temp)								
            elif (userNotes in row["Transcript"].lower()) and ("highlighting" not in row["Transcript"].lower())and ("think aloud" not in row["Transcript"].lower()) and ("picking" not in row["Transcript"].lower()) and ("prompt" not in row["Transcript"].lower()) and ("looking" not in row["Transcript"].lower()) and ("still" not in row["Transcript"].lower()) and  ("reveiw" not in row["Transcript"].lower()) and ("moving" not in row["Transcript"].lower()) and ("review" not in row["Transcript"].lower()) and  ("making" not in row["Transcript"].lower()):   #(["prompt ","looking"," review ","still"," moving"," making"," reviews"," reviewing"," highlighting" ,"think-aloud" ,"picking"] not in row["Transcript"].lower())
                note = row["Transcript"].split('"')[1].split('"')[0]
                seconds = seconds#  + dynamic_offset
                if seconds < 0:
                    dynamic_offset = -1*seconds
                    print "Dynamic time alignment: ",dynamic_offset
                    seconds = seconds + dynamic_offset
                temp = {"time": seconds , "Text": note, "duration": float(null_duration)/10, "ID": 0, "InteractionType" :"writing_notes"}			
                ret.append(temp)				
            # elif (row["Transcript"][:1] == "&quot;" ) :   #(["prompt ","looking"," review ","still"," moving"," making"," reviews"," reviewing"," highlighting" ,"think-aloud" ,"picking"] not in row["Transcript"].lower())
            elif ( ("Still reading" not in row["Transcript"].lower()) and ("highlighting" not in row["Transcript"].lower()) and ("picking" not in row["Transcript"].lower()) and ("prompt" not in row["Transcript"].lower()) and ("looking" not in row["Transcript"].lower()) and ("searching" not in row["Transcript"].lower()) and  ("making" not in row["Transcript"].lower()) and  ("changed" not in row["Transcript"].lower()) and  ("adding" not in row["Transcript"].lower())  and  ("user" not in row["Transcript"].lower())):    #  and ("moving" not in row["Transcript"].lower())and ("reviewing" not in row["Transcript"].lower())
                think = row["Transcript"] #.split('"')[1].split('"')[0]
                think = think.replace('"', '')
                seconds = seconds#  + dynamic_offset
                if seconds < 0:
                    dynamic_offset = -1*seconds
                    print "Dynamic time alignment: ",dynamic_offset                    
                    seconds = seconds + dynamic_offset
                # think = think.replace(0x92, ' ')
                # print "Here!!", think
                temp = {"time": seconds , "Text": think, "duration": float(null_duration)/10, "ID": 0, "InteractionType" :"think_aloud"}			
                ret.append(temp)
            # else:
                # print "Out!", row
        except:
            print "FAILED FOR", row
  
    #print ret    
    for i in ret:
        # print i
        Interaction_list.append(i)
   # print "\n", Interaction_list    	
    return Interaction_list
		
devideby1 = ""

for x in xrange(1,4):

    if x == 1:
        devideby1 = "g"
        dataset = "Arms"	
        name = "Armsdealing"
    if x == 2:
        devideby1 = "y"
        dataset = "Terrorist"
        name = "TerroristActivity"        
    if x == 3:
        devideby1 = "ce"		
        dataset = "Disappearance"
        name = "Disappearance"				
		
    for y in xrange(1,9):	
        datasetNum = x
        userNum = y
        print "\n", "../EventsToActions_Provenanace/provenance_datasets/Dataset_"+ str(x)+ "/Datalogs/"+str(dataset)+"_P"+str(y)+"_DataLogs.txt"	
        Interaction_list , null_duration= get_texts_from_log("d:/EventsToActions_Provenanace/provenance_datasets/Dataset_"+ str(x)+ "/Datalogs/"+str(dataset)+"_P"+str(y)+"_DataLogs.txt",all_events + spam_events, name, devideby1) 
        Interaction_list = get_interaction_from_thinkaloud("d:/EventsToActions_Provenanace/provenance_datasets/Dataset_"+ str(x)+ "/Think-aloud/"+str(dataset)+"_P"+str(y)+"_ThinkAlouds.csv", Interaction_list, null_duration)
        Interaction_list = sorted(Interaction_list, key=lambda k: k['time'])
        save_as_js_file_push_to(Interaction_list,"d:/EventsToActions_Provenanace/provenance_datasets/Dataset_"+str(x)+"/UserInteractions/"+str(dataset)+"_P"+str(y)+"_InteractionsLogs.json") 
	
print "\n \n End"
print "\n total time", datetime.now() - startTime

	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
