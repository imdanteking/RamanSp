import pandas as pd
import os

def merge_spectrum(input_path, output_filename):
    files = os.listdir(input_path)
    # print(files)
    if(len(files) != 0):
        first_file = os.path.join(input_path, files[0])
        first_df = pd.read_csv(first_file, header=None)
        first_df = first_df.iloc[0:1, :]
    dfs = pd.DataFrame()
    dfs = pd.concat([dfs, first_df])
    for file in files:
        # print(file)
        file = os.path.join(input_path, file)
        df = pd.read_csv(file, header=None)
        df = df.iloc[1:, :]
        dfs = pd.concat([dfs, df])
    # print(dfs)
    dfs.to_csv(output_filename, index=None, header=None)
