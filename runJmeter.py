#!/usr/bin/python
import os
import requests
from os import listdir
from os.path import isfile, join
import time
from datetime import datetime
import io
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def run_jmeter_test(test_dir,test_name,num_of_threads,i):
    output_file='%s\\results_logs\\%s\\%s_%s_%s_out.txt' %(test_dir, test_name, test_name, num_of_threads,i)
    aggregate_report='%s\\reports\\%s\\%s_%s_%s.csv' %(test_dir, test_name, test_name, num_of_threads,i)
    xml_file='%s\\results_logs\\%s\\%s_%s_%s.xml' %(test_dir, test_name, test_name, num_of_threads,i)
    
    if not os.path.isdir('%s\\results_logs\\%s'%(test_dir,test_name)):
        os.makedirs('%s\\results_logs\\%s'%(test_dir,test_name))
    # run the test
    run_dir='C:\\Users\\Soum-Account\\Desktop\\Jmeter_automation\\apache-jmeter-5.5\\apache-jmeter-5.3\\bin'
    os.chdir(run_dir)
    
    start_time= time.strftime('%Y-%m-%d %H:%M:%S')
    os.system('jmeter -n -t %s\\test_files\\%s.jmx -l %s -Jthreads=%s > %s' %(test_dir, test_name, xml_file, num_of_threads, output_file))
    end_time=time.strftime('%Y-%m-%d %H:%M:%S')
    print("finished")
    
    with open('%s' %output_file,'a') as out_f:
        out_f.write('Start_time: %s\n' %start_time)
        out_f.write('End_time: %s' %end_time)
        
        
    # Generate aggregate report 
    if not os.path.isdir('%s\\reports\\%s'%(test_dir,test_name)):
        os.makedirs('%s\\reports\\%s'%(test_dir,test_name))
        
    report_gen_dir='C:\\Users\\Soum-Account\\Desktop\\Jmeter_automation\\apache-jmeter-5.5\\apache-jmeter-5.5\\lib\\ext'
    os.chdir(report_gen_dir)
    os.system('java -jar CMDRunner.jar --tool Reporter --generate-csv %s --input-jtl %s --plugin-type AggregateReport ' %(aggregate_report, xml_file))
    print('Jmeter finished running %s' %test_name)
    
    
    ran_all_samples=get_output_data(test_name,output_file, aggregate_report, xml_file)
       
    return ran_all_samples

def get_data_files():
    mypath='C:\\Users\\Soum-Account\\Desktop\\Jmeter_automation\\test\\test_files'
    testfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    return testfiles
          

def get_output_data(test_name,output_file,aggregate_report,xml_file):

    client_dir='C:\\Users\\Soum-Account\\Desktop'
    os.chdir(client_dir)
    
    
    #for example requests_overtime_daily_10_out.txt
    n=output_file.split('_')
    num_of_threads=n[len(n)-3]
    with open(output_file) as console_out:
        for line in reversed(list(console_out)):
            if re.search("Start_time:",line):
                start_time=line[12:len(line)-1]
            if re.search("End_time:",line):
                end_time=line[10:]
            if ("summary = " in line):
                num_of_errors=line[line.index('Err:')+5: line.index('(')-1]
                break
    with open(aggregate_report) as aggregate:
        #read the last line where there is total, then read the api request name from the previous line:
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
            
    
    with open(xml_file, encoding='UTF-8') as xml:
        data=xml.read()
        exceeded_duration=data.count('lasted too long')
        error_500=data.count('1.1 500')
        error_502=data.count('1.1 502')
        error_503=data.count('1.1 503')
        error_504=data.count('1.1 504')
        non_http=data.count('Non HTTP response code')
        response_assertion=data.count('<name>Response Assertion</name>\n    <failure>true</failure>')

    os.chdir("C:\\Users\\Soum-Account\\Desktop\\Jmeter_automation")         
    # use creds to create a client to interact with the Google Drive API
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('client.json', scope)
    client = gspread.authorize(creds)

    # Find a workbook by name and open the first sheet
    # Make sure you use the right name here.
    sheet = client.open("Api Stress Testing Results").sheet1            
    run_all_samples=False
    print(num_of_run_samples)
    print("Helloo \n")
    print(num_of_threads);
    if int(num_of_run_samples) == int(num_of_threads)*10:
        run_all_samples=True
    
 
    row_vals=[test_name,start_time,end_time,num_of_threads,int(num_of_threads)*10,num_of_run_samples,num_of_errors,average_latency,min_value,max_value,throughput,error_percentage,line_90,line_95,line_99,exceeded_duration,response_assertion,run_all_samples,error_500,error_502,error_503,error_504,non_http]
   
    sheet.insert_row(row_vals,sheet.row_count)
    print(sheet.row_count)
    
    return run_all_samples


# read args from command ( threads, loops, test files, data files
# set the entered ones
# set default values if args not entered
# move the jmx file to a created dir 
# make loops dynamic 
# make thread increase dynamic
# make stop criteria dynamic
# ------------------------------------------------

# to search for: 
## make request dynamic ( headers) 
## pass data files for response assertions
## pass input files 
#-------------------------------
#to decide: 
## report format 


dir_path='C:\\Users\\Soum-Account\\Desktop\\Jmeter_automation\\test'       
test_files=get_data_files()
print(test_files)

for test_file in test_files:
    threads=0

    ran_all_samples=True
    while ran_all_samples:
        if(threads > 500):
            threads+=500
        else:
            threads+=50
        print('Running test %s , threads = %s \n' %(test_file, threads))
        i=1
        while i<4:
            ran_all_samples=run_jmeter_test(dir_path,test_file.split('.',1)[0],threads,i)
            i+=1
       
       
print("Finished!!")       