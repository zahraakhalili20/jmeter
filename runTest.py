#!/usr/bin/python
import os
import sys
import requests
import io
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import time


home = os.getcwd()
report_gen_dir='%s\\apache-jmeter-5.5\\apache-jmeter-5.5\\lib\\ext' %(home)
Jmeter_run_dir='%s\\apache-jmeter-5.5\\apache-jmeter-5.3\\bin' %(home)
run_no=1
row_count=8
threads=1;
test_file="";
increase=100;
err=10;
loops=1;

def runTest(test_file,threads,loops):
    run=1;
    continue_running=True
    load=int(threads) * int(loops)
    end_run=False
    while run<4:
        aggregate_report='%s\\reports\\%s_%s.csv' %(home, threads,run)
        xml_file='%s\\results_logs\\%s_%s.xml' %(home, threads,run)
        
        if not os.path.isdir('%s\\results_logs'%(home)):
            os.makedirs('%s\\results_logs'%(home))
        # cd to the path of jmeter bin
        os.chdir(Jmeter_run_dir)  
        
        #command to run jmeter
        os.system('jmeter -n -t %s -l %s -Jthreads=%s -Jloops=%s' %(test_file, xml_file, threads, loops))
        # run finished, generating reports
        if not os.path.isdir('%s\\reports'%(home)):
            os.makedirs('%s\\reports'%(home))
            
        # Generate aggregate report 
        os.chdir(report_gen_dir)
        os.system('java -jar CMDRunner.jar --tool Reporter --generate-csv %s --input-jtl %s --plugin-type AggregateReport ' %(aggregate_report, xml_file))
        print('Jmeter finished running %s threads' %threads)
        
        #read output data and generate our report
        end_run=read_data(aggregate_report,xml_file,threads,loops,run)
        run=run+1
    return end_run   

def read_data(aggregate_report,xml_file,threads,loops,run):
    os.chdir(home)
    global row_count
    global run_no
    with open(aggregate_report) as aggregate:
        #read the last line where there is total:
        for line in reversed(list(aggregate)):
            if(re.search('TOTAL,',line)):
                data=line.split(',')
                num_of_run_samples=data[1]
                average_latency=data[2]
                line_90=data[4]
                line_95=data[5]
                line_99=data[6]
                min_value=data[7]
                max_value=data[8]
                error_percentage=data[9]
                throughput=data[10]
                received=data[11]
                    

    with open(xml_file, encoding='UTF-8') as xml:
        data=xml.read()
        exceeded_duration=data.count('lasted too long')
        error_500=data.count('1.1 500')
        error_502=data.count('1.1 502')
        error_503=data.count('1.1 503')
        error_504=data.count('1.1 504')
        non_http=data.count('Non HTTP response code')
        response_assertion=data.count('<name>Response Assertion</name>\n    <failure>true</failure>')
        load = int(threads) * int(loops)
        
    if load == int(num_of_run_samples):
        ran_all=True
    else:
        ran_all=False
        
    # use creds to create a client to interact with the Google Drive API
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('client.json', scope)
    client = gspread.authorize(creds)

    # Find a workbook by name and open the first sheet
    # Make sure you use the right name here.
    sheet = client.open("Template Report")
    sheet_id=sheet.worksheet("test_run_1").id
    spreadsheet_id=sheet.id
    sheet=sheet.worksheet("test_run_1")
    if float(error_percentage.replace('%','')) > err and load < 3000:
        sheet.update_acell('A1:B1','Test Status: FAILED')
    if threads <500 and threads >300 and float(error_percentage.replace('%','')) > err: 
        sheet.update_acell('A1:B1','Test Status: PASSED')
    if threads == 1: 
        if float(error_percentage.replace('%','')) >10 or int(average_latency) > 450:
            end_run=True
            
        #insert as is
        sheet.update_acell('C3:Q3','Test: Sending Request with %s Threads looping %s times' %(threads,loops))
        sheet.update_acell('B3:B4','Load: %s' %(load))
        sheet.update_cell(3,1,'%s'%(run_no))
        

        row = 5+int(run)
        #insert values for runs
        column=3
        sheet.update_cell(row,column,min_value)
        sheet.update_cell(row,column+1,average_latency)
        sheet.update_cell(row,column+2,max_value)
        sheet.update_cell(row,column+3,throughput)
        sheet.update_cell(row,column+4,line_90)
        sheet.update_cell(row,column+5,line_95)
        sheet.update_cell(row,column+6,line_99)
        sheet.update_cell(row,column+7,error_percentage)
        sheet.update_cell(row,column+8,received)
        #filling errors
        sheet.update_cell(row,column+9,non_http)
        sheet.update_cell(row,column+10,response_assertion)
        sheet.update_cell(row,column+11,error_500)  
        sheet.update_cell(row,column+12,error_502)
        sheet.update_cell(row,column+13,error_503)    
        sheet.update_cell(row,column+14,error_504)
        sheet.update_cell(row,column+15,ran_all)
        if run ==3:
                    run_no=run_no+1
    
    else:
        if run == 1:
        #copy the first run template
            print(row_count)
            headers = {
                "Authorization": "Bearer " + creds.get_access_token().access_token,
                "Content-Type": "application/json",
            }
            reqs = [
                {
                    "copyPaste": {
                        "source": {
                            "sheetId": sheet_id,
                            "startRowIndex": 2,
                            "endRowIndex": 8,
                            "startColumnIndex": 0,
                            "endColumnIndex": 18,
                        },
                        "destination": {
                            "sheetId": sheet_id,
                            "startRowIndex": row_count,
                            "endRowIndex": row_count + 7,
                            "startColumnIndex": 0,
                            "endColumnIndex": 18,
                        },
                        "pasteType": "PASTE_NORMAL",
                        "pasteOrientation": "NORMAL",
                    }
                }
            ]

            r = requests.post(
    f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}:batchUpdate",
    headers=headers,
    data=json.dumps({"requests": reqs}),
)
            #insert values
            sheet.update_cell(row_count+1,3,'Test: Sending Request with %s Threads looping %s times' %(threads,loops))
            sheet.update_cell(row_count+1,2,'Load: %s' %(load))
            sheet.update_cell(row_count+1,1,'%s'%(run_no))
        row = row_count+3+int(run)
        #insert values for runs
        column=3

        sheet.update_cell(row,column,min_value)
        sheet.update_cell(row,column+1,average_latency)
        sheet.update_cell(row,column+2,max_value)
        sheet.update_cell(row,column+3,throughput)
        sheet.update_cell(row,column+4,line_90)
        sheet.update_cell(row,column+5,line_95)
        sheet.update_cell(row,column+6,line_99)
        sheet.update_cell(row,column+7,error_percentage)
        sheet.update_cell(row,column+8,received)
        #filling errors
        time.sleep(2)
        sheet.update_cell(row,column+9,non_http)
        sheet.update_cell(row,column+10,response_assertion)
        sheet.update_cell(row,column+11,error_500)  
        sheet.update_cell(row,column+12,error_502)
        sheet.update_cell(row,column+13,error_503)    
        sheet.update_cell(row,column+14,error_504)
        sheet.update_cell(row,column+15,ran_all)

        if run ==3:
            row_count=row_count+6
            run_no=run_no+1
        
    if ran_all == False:
        end_run=True
    else:
        end_run=False
    return end_run
# read args from command ( threads, loops, test files)
options = sys.argv
## we need to parse options here and set variables to use 

#create paths we need for storing outputs and test files
if not os.path.exists("test\\Reports"):
    os.makedirs("test\\Reports")



#-test : path to jmeter test file
#threads: threads count to start with
#increase: no of threads to increase by every run
#err: error percentage to stop at, default 10%
#loops: number of iterations per run
for option in options:
    #if option is test
    value=option.split("=");
    if value[0] == "-threads":
        threads=int(value[1])
    if value[0] =="-test_file":
        test_file=value[1];
    if value[0] == "increase":
        increase=int(value[1]);
    if value[0] == "-err":
        err=value[1];
    if value[0] == "-loops":    
        loops=int(value[1]);
    print(option)

#Run the test on 1 thread, reject if time > 400ms, error rate=100%
print('Running test %s on 1 thread \n' %(test_file))
test_file=home+'\\'+test_file
end_run=False
end_run = runTest(test_file,1,1)
end_run = False
while not end_run:
 
    end_run = runTest(test_file,threads,loops)
    threads = threads+increase
    