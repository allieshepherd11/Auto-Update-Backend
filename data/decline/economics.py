import pandas as pd
import os


if __name__ == "__main__":
    root = './data/decline/data'
    for well in os.listdir(root):
        print(well)
        exit()    