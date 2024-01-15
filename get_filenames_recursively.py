import os

def get_filenames(root_path, filename_list):
    files = os.listdir(root_path)
    for file in files:
        file_path = os.path.join(root_path, file)
        if(os.path.isdir(file_path)):
            get_filenames(file_path, filename_list)
        else:
            filename_list.append(file_path)