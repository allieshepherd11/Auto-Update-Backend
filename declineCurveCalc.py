import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.integrate import simps
from datetime import datetime, timedelta
from lxml import html
import requests
from collections import OrderedDict
import json

def main():
    declineCurve()

def declineCurve():
    # data = pd.read_csv('monthlyDataST.csv')
    # # Drop unused columns, exclude first month data & current month data
    # df = data[data['Well Name'] == "Carolpick #1"].drop(columns=['Gas (MCF)', 'Water (BBLS)', 'TP', 'CP'])
    # df_filtered = df.drop(df.index[-1])
    # df_filtered.to_csv("dectest.csv", index=False)

    df_data = pd.read_csv('dectest.csv')
    # Create time and production lists
    t = np.arange(len(df_data))
    q = df_data['Oil (BBLS)'].values.tolist()
    qi = q[0]

    # HOW DO YOU CREATE INITIAL_EST FOR ALL WELLS?
    initial_est = [qi, .8, .4]
    # Curve fit to hyperbolicEq, using t, q, and initial_est
    popt, pcov = curve_fit(hyperbolicEq, t, q, p0=initial_est)
    qi_est, b_est, Di_est = popt

    # print("Estimated qi: ", qi_est)
    # print("Estimated b: ", b_est)
    # print("Estimated Di: ", Di_est)

    print(max(t))
    print(min(t))
    # Generate the model curve
    t_model = np.linspace(min(t), max(t), max(t))  # Time range for the model curve & number of elements within range
    q_model = hyperbolicEq(t_model, qi_est, b_est, Di_est)

    # print(q_model)
    economics(q, q_model, t_model)

    # Plot the existing data + model using matplotlib
    plt.semilogy(t, q)
    plt.plot(t, q, 'ro', label='Data')  # Data points
    plt.plot(t_model, q_model, 'b-', label='Model')  # Model curve
    plt.xlabel('Time')
    plt.ylabel('Production Rate (log scale)')
    plt.legend()
    plt.show()

def hyperbolicEq(t, qi, b, Di):
    return qi/(1+b*Di*t)**(1/b)

def economics(q, q_model, t_model):
    print("BBLS produced so far: ", sum(q))

    t_start = 
    # Sum area under curve using trap. rule
    print('Area under the curve: ', np.trapz(q_model, t_model))
    
main()
