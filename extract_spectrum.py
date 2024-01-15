import pandas as pd
import os

def batch_extract_spectrum(batch_size, filename, output_directory_path):
    filename1 = filename
    filename2 = "wn(" + filename1 + ")"
    # filename2 = "wn(Si_AgFilm_2-Naphthalenethiol_532_round2.txt)"
    df = pd.read_csv(filename1, delimiter='\t', header=None, dtype=float)
    # remove the last \t
    df = df.iloc[:, :-1]
    wavenumber_col = df.iloc[:, 0]
    group_size = int((df.shape[1] - 1) / batch_size)
    averages = []
    for i in range(0, df.shape[1]-1, group_size):
        cols = df.columns[i: i+group_size]
        group_average = df[cols].mean(axis=1)
        averages.append(wavenumber_col)
        averages.append(group_average)
    result = pd.DataFrame(averages).T
    # add the first line
    # print(result.shape[1])
    # build the first row
    new_row = []
    for i in range(int(result.shape[1]/2)):
        new_row.append(filename2 + "area" + str(i) + "\t")
        new_row.append(filename1 + "area" + str(i) + "\t")

    # new_row = [filename2+"\t", filename1+"\t"] * int(result.shape[1]/2)
    first_line = pd.DataFrame(new_row)
    first_line = first_line.T
    # result.set_axis(range(40), axis=1, inplace=True)

    result = result.set_axis(labels=range(2*batch_size), axis="columns")
    result = pd.concat([first_line, result], axis=0)
    # last_backslash_pos = filename1.rfind('\\')
    last_backslash_pos = filename1.rfind(os.path.sep)+1
    # new_file = "result\\" + filename1[last_backslash_pos:]
    new_file = os.path.join(output_directory_path, filename1[last_backslash_pos:])
    # print(output_directory_path)
    # print(filename1[last_backslash_pos:])
    # print(new_file)
    result.to_csv(new_file, index=None, header=None, sep="\t")
    return new_file