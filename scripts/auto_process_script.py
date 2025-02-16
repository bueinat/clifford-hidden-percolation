#!/home/lab/einatbo/.miniconda3/bin/python
# %%
from glob import glob
import os
from pathlib import Path
import subprocess
import argparse

# %%
parser = argparse.ArgumentParser()
parser.add_argument('--process_all', action='store_true', help='flag to remove all existing files and process them all over again')
parser.add_argument('--nocommit', action='store_true')
args = parser.parse_args()

# %%
root_dir = Path("../mi/data")

ignore_list = []
# %%
# Specify the root directory you want to start from
print("directories which will be proccessed:")
update_list = []
for subfolder in root_dir.rglob('*'):
    if subfolder.is_dir() and str(subfolder) not in ignore_list: # and not any(subfolder.rglob('*')):
            all_files = glob(f"{subfolder}/*.jld2")
            raw_data_files = set(all_files).difference([f"{subfolder}/current_data.jld2", f"{subfolder}/full_data.jld2"])
            if raw_data_files:
                all_files.sort(key=os.path.getmtime)
                if not all_files[-1].endswith("current_data.jld2") or args.process_all:
                    update_list.append(subfolder)
                    print("\t", subfolder)

# %%
# write an update file

temp_file_name = "temp_file.sh"
with open(temp_file_name, "w") as temp_file:
    # Write data to the temporary file
    print("#!/bin/bash\n", file=temp_file)
    for filename in update_list:
        print(f"julia ../scripts/process_script.jl {filename} &", file=temp_file)
        
    print("\nwait\n", file=temp_file)
    print("echo done processing", file=temp_file)

subprocess.run(['bash', temp_file_name], check=True)

to_be_commited = []
with open(temp_file_name, "w") as temp_file:
    for filename in update_list:
        cdata_filename = f"{filename}/current_data.jld2"
        if not os.path.exists(cdata_filename):
            print(f"{filename} was not processed properly")
        else:
            filesize = os.path.getsize(cdata_filename)
            if filesize / (1024 ** 2) > 10:
                print(f"{filename}'s data is too big to be commited and pushed")
            else:
                to_be_commited.append(filename)
                print(f"git add {filename}/current_data.jld2", file=temp_file)
    if to_be_commited:
        print("\ngit commit -m\"simulations update\"", file=temp_file)
        print("echo done.", file=temp_file)

if to_be_commited and not args.nocommit:
    subprocess.run(['bash', temp_file_name], check=True)
# os.remove(temp_file_name)
