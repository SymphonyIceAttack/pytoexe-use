import argparse
import os
import struct
path = ""

typing = {"Type 1":2.0,"Type 2":10.0,"Type 3":20.0} # You can edit this to get different ranges of length (Type 1 are demos that are less than 2.0 seconds).
typing["Type 4/5"] = "+"+str(typing["Type 3"]) # Just for avoiding errors.

def get_files(path):
    return os.listdir(path)

def filter_files(files):
    filtered_files = []
    for file in files:
        if os.path.splitext(file)[1] == ".dem":
            filtered_files.append(file)
    return filtered_files

def hex_to_float(hex_string):
    # Convert hexadecimal string to bytes
    hex_bytes = bytes.fromhex(hex_string)
    # Unpack bytes to get the float value
    float_value = struct.unpack('f', hex_bytes)[0]
    return float_value

def organize_demos(files):
    demo_types = {"Type 1":[],"Type 2":[],"Type 3":[],"Type 4/5":[]}

    for filename in files:
        file = open(path+'/'+filename,'rb')
        map = ""
        length = 0
        try:
            file.seek(0x420)
            length = file.read(4).hex()
            length = hex_to_float(length)
            file.seek(0x218)
            map = file.read(140).decode("utf-8").rstrip('\x00')
        except UnicodeDecodeError:
            print(str(filename)+" is either broken, or is not a source engine demo!")
            continue
        info = {'name':filename,'length':float(round(length * 100)) / 100,'map':map}

        if length <= typing["Type 1"]:
            demo_types["Type 1"].append(info)
        elif length <= typing["Type 2"]:
            demo_types["Type 2"].append(info)
        elif length <= typing["Type 3"]:
            demo_types["Type 3"].append(info)
        else:
            demo_types["Type 4/5"].append(info)
    return demo_types

def save_results(final_report):
    file = open("./interloper_report.txt",'w')
    file.write("NOTICE: The demo typing might not be accurate! This report is based on the length of a demo and not it's contents, so longer Type 3 demos might be classified as Type 4/5.\n")
    file.write("\n")
    write_type(file,final_report,"Type 1")
    write_type(file,final_report,"Type 2")
    write_type(file,final_report,"Type 3")
    write_type(file,final_report,"Type 4/5")
    file.close()

def write_type(file,report,type):
    if type == "Type 4/5":
        file.write(type+" ("+str(typing[type])+" seconds):\n")
    else:
        file.write(type+" (<"+str(typing[type])+" seconds):\n")
    
    for info in report[type]:
        file.write("\t"+str(info['name']+': '+str(info['length'])+" seconds"))
        if str(info['map']).startswith("data"):
            file.write(" \t <- This demo file uses a data map.\tMap: "+info['map'])
        file.write("\n")
    file.write("\n")



parser = argparse.ArgumentParser()
parser.add_argument("-p","--DemPath")

args = parser.parse_args()

if args.DemPath:
    path = args.DemPath
    files = get_files(args.DemPath)
    files = filter_files(files)
    final_report = organize_demos(files)
    save_results(final_report)