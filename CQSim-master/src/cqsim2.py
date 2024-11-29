import optparse
import os
import sys
from datetime import datetime
import time
import re
import cqsim_path
import cqsim_main
import argparse
from CqSim.Basic_algorithm import *

def datetime_strptime (value, format):
    """Parse a datetime like datetime.strptime in Python >= 2.5"""
    return datetime(*time.strptime(value, format)[0:6])

def parse_swf(file_path):
    """
    Function to parse the SWF file and extract workload information.
    Modify this function as per the structure of your SWF files.
    """
    with open(file_path, 'r') as file:
        #process SWF file contents here
        workload_data = file.readlines()  #read file contents
    return workload_data

def run_scheduling_algorithm(algorithm, workload_data):
    """
    Run the selected scheduling algorithm on the provided workload data.
    """
    if algorithm == "Gavel":
        scheduler = GavelScheduling(workload_data)
    elif algorithm == "FCFS":
        scheduler = FCFS(workload_data)
    else:
        raise ValueError("Unsupported scheduling algorithm.")

    # Simulate the scheduling and get results
    results = scheduler.schedule()
    return results

def run_algorithm(algorithm_name, workload_data):
    """
    Dynamically run the selected algorithm from Basic_algorithm.py
    """
    algorithms = {
        "Gavel": GavelScheduling,
        "FCFS": FCFS,
        "RoundRobin": RoundRobin,
        "SJF": SJF,
        "SRTF": SRTF,
        "Priority": PriorityScheduling,
        "MultilevelFeedbackQueue": MultilevelFeedbackQueue,
        "EDF": EDF,
    }

    if algorithm_name not in algorithms:
        raise ValueError(f"Algorithm {algorithm_name} is not supported.")

    if algorithm_name in ["RoundRobin", "MultilevelFeedbackQueue"]:
        instance = algorithms[algorithm_name](time_quantum=2 if algorithm_name == "RoundRobin" else [1, 2, 3])
    else:
        instance = algorithms[algorithm_name]()

    print(f"Running {algorithm_name} scheduling...")
    results = instance.schedule_jobs(workload_data, currentTime=0)
    return results

class Option (optparse.Option):
    
    """An extended optparse option with cbank-specific types.
    
    Types:
    date -- parse a datetime from a variety of string formats
    """
    
    DATE_FORMATS = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%y-%m-%d",
        "%y-%m-%d %H:%M:%S",
        "%y-%m-%d %H:%M",
        "%m/%d/%Y",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%m/%d/%y",
        "%m/%d/%y %H:%M:%S",
        "%m/%d/%y %H:%M",
        "%Y%m%d",
    ]
    
    def check_date (self, opt, value):
        """Parse a datetime from a variety of string formats."""
        for format in self.DATE_FORMATS:
            try:
                dt = datetime_strptime(value, format)
            except ValueError:
                continue
            else:
                #python can't translate dates before 1900 to a string,
                
                if dt < datetime(1900, 1, 1):
                    raise optparse.OptionValueError(
                        "option %s: date must be after 1900: %s" % (opt, value))
                else:
                    return dt
        raise optparse.OptionValueError(
            "option %s: invalid date: %s" % (opt, value))
    
    TYPES = optparse.Option.TYPES + ( "date", )
    
    TYPE_CHECKER = optparse.Option.TYPE_CHECKER.copy()
    TYPE_CHECKER['date'] = check_date

def callback_alg (option, opt_str, value, parser):
    temp_opt['alg'].append(value)
    return
def callback_alg_sign (option, opt_str, value, parser):
    temp_opt['alg_sign'].append(value)
    return
def callback_bf_para (option, opt_str, value, parser):
    temp_opt['bf_para'].append(value)
    return
def callback_win_para (option, opt_str, value, parser):
    temp_opt['win_para'].append(value)
    return
def callback_ad_win_para (option, opt_str, value, parser):
    temp_opt['ad_win_para'].append(value)
    return
def callback_ad_bf_para (option, opt_str, value, parser):
    temp_opt['ad_bf_para'].append(value)
    return
def callback_ad_alg_para (option, opt_str, value, parser):
    temp_opt['ad_alg_para'].append(value)
    return

def get_raw_name (file_name):
    output_name = ""
    length = len(file_name)
    i = 0
    while (i < length):
        if (file_name[i] == '.'):
            break
        output_name+=file_name[i]
        i += 1
    return output_name

def alg_sign_check (alg_sign_t,leng):
    alg_sign_result=[]
    temp_len=len(alg_sign_t)
    i=0
    while i<leng:
        if i<temp_len:
            alg_sign_result.append(int(alg_sign_t[i]))
        else:
            #alg_sign_result.append(int(alg_sign_t[temp_len-1]))
            alg_sign_result.append(0)
        i+=1
    return alg_sign_result

def get_list (inputstring,regex):
    return re.findall(regex,inputstring)

def read_config(fileName):
    nr_sign =';'    #not read sign. Mark the line not the job data
    sep_sign ='='   #the sign seperate data in a line
    readData={}
    configFile = open(fileName,'r')

    while (1):
        tempStr = configFile.readline()
        if not tempStr :    #break when no more line
            break
        if tempStr[0] != nr_sign:   #job trace line
            strNum = len(tempStr)
            newWord = 1
            k = 0
            dataName = ""
            dataValue = ""     
            
            for i in range(strNum):
                if (tempStr[i] == '\n'):
                    break
                if (tempStr[i] == sep_sign):
                    if (newWord == 0):
                        newWord = 1
                        k = k+1
                else:
                    newWord = 0
                    if k == 0:
                        dataName=dataName+ tempStr[i] 
                    elif k == 1:
                        dataValue = dataValue + tempStr[i] 
            readData[dataName]=dataValue
    configFile.close()
    
    return readData


if __name__ == "__main__":
    temp_opt={'alg':[],'alg_sign':[],'bf_para':[],'win_para':[],'ad_win_para':[],'ad_bf_para':[],'ad_alg_para':[]}
    p = optparse.OptionParser(option_class=Option)
    

    #add new option to specify the algorithm
    p.add_option("-A", "--algorithm", dest="algorithm", type="string", help="Specify the scheduling algorithm to use")
    opts, args = p.parse_args()

    #parsing SWF file for workload data
    workload_data = parse_swf(opts.job_trace)

    if opts.algorithm:
        results = run_algorithm(opts.algorithm, workload_data)
        print(f"Algorithm {opts.algorithm} results: {results}")

