import os
import numpy as np

def extract_list(path):
    print(path)
    new_file = 'name_list.txt'
    index = 0
    with open(path, 'r') as file :
        lines = file.readlines()
        name_list = []
        test_loop = 0

        with open(new_file, 'w', encoding='utf-8') as file2:

            for line in lines:
                # print(line)
                words = line.split('.')
                ext = words[-1]
                name = words[0][len(words[0])-11 : ]
                name = name.replace(' ', '')
                print(name, ext)
                name_list.append(name)
                file2.write(name + '\n')

                # index += 1
                # if index > 10 :
                #     break

    print(len(name_list))

def file_convert(path) :
    with open(path, 'rb') as file:
        contents = file.read()
        decode = contents.decode('utf-8')

        econde = decode.encode('utf-8')

        with open('clc_filelist_utf8.log', 'wb') as file:
            file.write(econde)

if __name__ == '__main__':
    path = 'clc_filelist.log'
    path1 = 'list.txt'
    extract_list(path1)
    # file_convert(path)