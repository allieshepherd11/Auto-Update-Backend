import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
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
    # well_name = input("Enter Well Name: ")
    # df = data[data['Well Name'] == well_name].drop(columns=['Gas (MCF)', 'Water (BBLS)', 'TP', 'CP'])
    # df_filtered = df.drop(df.index[-1])
    # df_filtered.to_csv("dectest.csv", index=False)

    df_data = pd.read_csv('decCarol.csv')

    drop_index = None
    # Months_To_Check
    mtc = 5
    # Range (Checks for lowest number in a range=___ after drop_index)
    r = 10
    # Loop through indexes in df_data
    for i in range(len(df_data)-mtc):
        tally = 0 # Set counter to 0

        # Check the next 4 months and make sure they are not increasing
        for index, row in df_data.iloc[i:i+mtc].iterrows(): 
            if index==len(df_data)-1: # Break if index is at the very end of the loop (1 case)
                break
            if row["Oil (BBLS)"] < df_data.loc[index+1, "Oil (BBLS)"]: # If one of the values being checked is increasing (relative to value after), add a tally
                tally+=1
        
        if tally == 0: # If no values were found to be increasing, check the next 10 months for the one with the highest decrease
            highest_decrease = 0
            index = i
            loop = 0
            while loop < r:
                if df_data.loc[i+loop, "Oil (BBLS)"] - df_data.loc[i+loop+1, "Oil (BBLS)"] > highest_decrease:
                    highest_decrease = df_data.loc[i+loop, "Oil (BBLS)"] - df_data.loc[i+loop+1, "Oil (BBLS)"]
                    index = i + loop + 1
                    # print(index)
                    # print(highest_decrease)
                loop += 1
            drop_index = index
            # print(df_data.loc[index, "Oil (BBLS)"])

            # Check 1stmonth - 2ndmonth, if > highest_decrease, assign 2nd month as highest decrease
            # Check 2nd mont - 3rd month, if > highest_decrease, assign 3rd month as highest decrease
            # ...
            # Check 9th month - 10th month, if > highest_decrease, assign 10th month as highest decrease
            break
    
    actual_df = df_data.drop(df_data.index[0:drop_index])
    
    # actual_df.to_csv("dekAnswer.csv", index=False)
    
    # Check the next 5 months and make sure they are not increasing, if not move on to next month
    # Check the next 10 months from the month ^ loop ended on
    # Choose the one with the highest decrease (the month after the decrease happens)
    # Delete everything before said month

#============================================================================================================================#
    #exit()
    # actual_df = pd.read_csv('decCarol.csv')

    # Create time and production lists
    t = np.arange(len(actual_df))
    q = actual_df['Oil (BBLS)'].values.tolist()
    qi = q[0]

    initial_est = [qi, .8, .4]
    # Curve fit to hyperbolicEq, using t, q, and initial_est
    popt, pcov = curve_fit(hyperbolicEq, t, q, p0=initial_est)
    qi_est, b_est, Di_est = popt

    # print("Estimated qi: ", qi_est)
    # print("Estimated b: ", b_est)
    # print("Estimated Di: ", Di_est)

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

    delta_t = t_model[1] - t_model[0]  # Width of each subinterval
    area_under_curve = np.sum(q_model[:-1] * delta_t)  # Sum of the areas
    print("LRAM (Accurate to real world): ", area_under_curve)

    # Sum area under curve using trap. rule
    print('Trapezoidal (More accurate to curve): ', np.trapz(q_model, t_model))

    
main()

# Find date each well started
# Graph that shows total oil produced by new wells in the last year of any given date