#!/home/lab/einatbo/.miniconda3/bin/python
# 
import pandas
# import argparse
from glob import glob
import numpy as np
import os
import subprocess
from pathlib import Path

is_windows = os.name == "nt"

if is_windows:
    PATH_SPLITTER = "\\"
else:
    PATH_SPLITTER = "/"

root_dir = Path(f"../percolation/{PATH_SPLITTER}data")

def process_csv_dir(dir_name):
    print(f"processing {dir_name}...")
    d, d_typ = {}, {}
    for path in glob(pathname=f"{dir_name}{PATH_SPLITTER}N*{PATH_SPLITTER}data*.csv"):
        if os.path.getsize(path) > 0:
            N = int(path.split(PATH_SPLITTER)[-2][1:])

            if N not in d.keys():
                d[N], d_typ[N] = [], []
            try:
                df = pandas.read_csv(path, header=[0, 1, 2, 3], index_col=0, dtype=float)
            except:
                df = pandas.read_csv(path, header=[0, 1, 2, 3], index_col=0)
            
            df.columns.names = ["p", "q", "r", "kind"]
            df.index.name = "iteration"
            df_typ = df.stack(['p', 'q', 'r'])
            df_typ = df_typ.query("is_path == True").unstack(['p', 'q', 'r'])
            d[N].append(df)
            d_typ[N].append(df_typ)
        
    if len(d) == 0:
        print("there are no csv files in this project, which is not supported right now")
        return
    
    for N in d.keys():
        d[N] = pandas.concat(d[N]).reset_index(drop=True)
        d_typ[N] = pandas.concat(d_typ[N]).reset_index(drop=True)

    par_df = pandas.concat(d, names=("N"), axis=1)
    typ_df = pandas.concat(d_typ, names=("N"), axis=1).reorder_levels([0, 2, 3, 4, 1], axis=1).sort_index(axis=1)
    
    nit = par_df.notnull().sum().replace({0: 1})
    print(nit.unstack(['p','q','r','kind']).iloc[:, 0].sort_index())
    data_df = pandas.concat({'data': par_df.mean(),
                                    'error': par_df.std() / np.sqrt(nit),
                                    'nit': nit,
                                    'typ_data': typ_df.mean(),
                                    'typ_error': typ_df.std() / np.sqrt(nit)}).unstack('N').T.sort_index()
    for l in range(1, 4):
        data_df.columns = data_df.columns.set_levels(data_df.columns.levels[l].astype(float), level=l)

    processed_data = data_df.reorder_levels([4, 0, 1, 2, 3], axis=1).sort_index(axis=1)
    processed_data.stack(['p', 'q', 'r']).to_csv(path_or_buf=f"{dir_name}{PATH_SPLITTER}full_data.csv")
    
    print(f"processing {dir_name} is done")


print("directories which will be proccessed:")
update_list, ignore_list = [], []
for run_script in glob(f"data{PATH_SPLITTER}*{PATH_SPLITTER}run_script.sh"):
    dir_name = os.path.dirname(run_script)
    if not os.path.exists(f"{dir_name}/full_data.csv"):
        update_list.append(dir_name)
        print("\t", dir_name)
    else:
        all_files = glob(f"{dir_name}/N*/data*.csv")
        all_files.append(f"{dir_name}/full_data.csv")
        all_files.sort(key=os.path.getmtime)
        if not all_files[-1].endswith("full_data.csv"): # or args.process_all:
            update_list.append(dir_name)
            print("\t", dir_name)
if not update_list:
    print("no files to update")
else:
    for dir_name in update_list:
        try:
            process_csv_dir(dir_name)
        except Exception as e:
            update_list.remove(dir_name)
            print(f"an error occured at {dir_name}: {e}")


    if is_windows:
        print("please git and commit manually")
    else:
        subprocess.run('''
            git add data/*/full_data.csv
            git commit -m"simulations update"''',
            shell=True, check=True,
            executable='/bin/bash')

# ls data/*/full_data.csv -ltrh
# git add  data/*/full_data.csv
# git commit -m"simulations update"
