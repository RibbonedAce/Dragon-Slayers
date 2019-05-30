
from scipy import *
import sys, time
import pickle
import os.path
import numpy as np
from dataset import DataSet
import traceback

from sklearn.linear_model import LinearRegression

class FileIO():
    def load_data(file_name):
        current_path = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(current_path,file_name)
        print("Loading from: " + file_path)
        if os.path.getsize(file_path) <= 0:
            return
        file = open(file_path,'rb')
        print("File loaded.")
        return pickle.load(file)

    def save_data(file_name,data):
        current_path = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(current_path,file_name)
        print("Saving to: " + file_path)
        file = open(file_path,'wb')
        pickle.dump(data, file)
        print("File saved.")

    def get_model():
        try:
            return FileIO.load_data("model")
        except:
            print("Model could not be loaded.  Using default LinearRegression().")
            traceback.print_exc()
            return LinearRegression()

    def get_data_set():
        try:
            return FileIO.load_data("dataset")
        except:
            print("DataSet could not be loaded.  Using empty DataSet().")
            traceback.print_exc()
            return DataSet()



