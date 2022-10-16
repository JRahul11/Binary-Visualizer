
import base64
import csv
import math
import urllib.request
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import os
from urllib.request import urlopen


class BinaryVisualizer():
    
    def __init__(self):
        self.getURLs()
        
    def getURLs(self):
        with open('phish_data.csv', encoding='utf-8') as file:
            heading = next(file)
            rows = csv.reader(file)
            index = 1
            for row in rows:
                index = index + 1
                # if(index > 3):
                #     break
                try:
                    if not os.path.exists(f'binaryFiles\\binaryFiles{index}.bin'):
                        if index > 50011:           #TODO: Change this index
                            self.createBinaryFiles(index, row)
                except Exception as e:
                    print(index, e)
        
    def createBinaryFiles(self, index, row):
        url = 'http://' + row[0]
        sourceCode = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        # sourceCode = urllib.request.urlopen(url)
        binaryCode = str(base64.b64encode(urlopen(sourceCode).read()))[2:-1]
        binFilePath = f'binaryFiles\\binaryFiles{index}.bin'
        binFile = open(binFilePath, 'w')
        binFile.write(binaryCode)
        binFile.close()
        self.createImages(index, row, binFilePath)
    
    def createImages(self, index, row, binFilePath):
        
        # Convert binary file to array with numbers
        arr = np.fromfile(binFilePath, dtype=np.ubyte)
        linelength = math.ceil(math.sqrt(len(arr)))
        len_missing = (linelength**2 - len(arr))
        
        # Padding array with 0's to make perfect square
        arr_padded = np.pad(arr, (0, len_missing), mode="constant", constant_values=0)
        del arr
        
        # Reshaped array to matrix
        matrix = arr_padded.reshape(linelength, linelength)
        del arr_padded
        
        if row[1] == 'bad':
            output_filename = f'imageFiles\\badImages\\{index}.png'
        else:
            output_filename = f'imageFiles\\goodImages\\{index}.png'
        fig, ax = plt.subplots()
        
        # Visualize matrix to image
        ax.matshow(matrix)
        del matrix
        
        ax.set_xlabel("URL: " + row[0][:45] + "\nResult: " + row[1])
        plt.title(binFilePath, loc="left", fontweight="bold")
        plt.savefig(output_filename)
        
        # Crop the image
        # left = 150
        # top = 60
        # right = 510
        # bottom = 425
        # img = Image.open(output_filename)
        # img = img.crop((left, top, right, bottom))
        # img.save(output_filename)
        print(str(index) + ' passed')


BinaryVisualizer()

# Explaination
# 1 2 3 4 5

# 3 x 3 Matrix

# Padding
# 1 2 3 4 5 0 0 0 0 

# Final Matrix
# 1 2 3
# 4 5 0
# 0 0 0