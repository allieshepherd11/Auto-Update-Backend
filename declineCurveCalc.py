import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from datetime import datetime, timedelta
from lxml import html
import requests
from collections import OrderedDict
import json
from itertools import zip_longest

# RUN prodMonthly.py BEFORE THIS TO HAVE UPDATED DECLINE CURVES
def main():
    df_wells = pd.read_json('everyWell.json')
    my_list = df_wells.values.tolist()

    oneDList = [element for sublist in my_list for element in sublist]
    params = {}
    for i in oneDList:
        well_params = declineCurve(i) 
        if well_params != None:
            params[i] = well_params

    params = pd.DataFrame(params)
    # FILE DESTINATION, CHANGE TO FIT YOUR LOCAL GITHUB FOLDER. File name: "dataMonthlyST.json"
    params.to_csv("../prod/data/declineCurves/#params.csv", index=False)
    #----------------^^^^^--------------------------------------------------------------------#
    
def declineCurve(name):
    print(name)
    data = pd.read_csv('monthlyDataST.csv')
    # Drop unused columns, exclude current month data
    df = data[data['Well Name'] == name].drop(columns=['Gas (MCF)', 'Water (BBLS)', 'TP', 'CP'])
    df_format = df.drop(df.index[-1])
    df_format.to_csv("dectest.csv", index=False)
    df_data = pd.read_csv('dectest.csv')

    exclList = []

    try:
        # FOR LOOP SUMMARY
        """
        # Check the next 5 months and make sure they are not increasing, if not move on to next month
        # Check the next 10 months from the month ^ loop ended on
            # Check 1stmonth - 2ndmonth, if > highest_decrease, assign 2nd month as highest decrease
            # Check 2nd mont - 3rd month, if > highest_decrease, assign 3rd month as highest decrease
            # ...
            # Check 9th month - 10th month, if > highest_decrease, assign 10th month as highest decrease
        # Choose the one with the highest decrease (the month after the decrease happens)
        # Delete everything before said month
        """
        drop_index = None # Index such that everything before will be dropped
        mtc = 5 # Months_To_Check
        r = 10 # Range of Months to check for the highest decreasing

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

                # Loop starting at 0 until reaches range r
                for loop in range(r):
                    if df_data.loc[i+loop, "Oil (BBLS)"] - df_data.loc[i+loop+1, "Oil (BBLS)"] > highest_decrease: # Check if row has the highest decrease
                        highest_decrease = df_data.loc[i+loop, "Oil (BBLS)"] - df_data.loc[i+loop+1, "Oil (BBLS)"] # save highest decrease
                        index = i + loop + 1 # save index of highest decrease (the row after the current one)
                # Assign drop_index to be the index after the for loop
                drop_index = index
                break

        actual_df = df_data.drop(df_data.index[0:drop_index])
        actual_df.to_csv("dekAnswer.csv", index=False)

        # Create time and production lists
        t = np.arange(len(actual_df))
        q = actual_df['Oil (BBLS)'].values.tolist()
        qi = q[0]

        initial_est = [qi, .8, .4]

        # Curve fit to hyperbolicEq, using t, q, and initial_est
        popt, pcov = curve_fit(hyperbolicEq, t, q, p0=initial_est)
        qi_est, b_est, Di_est = popt

        # Generate the model curve
        t_model = np.linspace(min(t), max(t)+40, 1+max(t)+40)  # Time range for the model curve & number of elements within range
        q_model = hyperbolicEq(t_model, qi_est, b_est, Di_est)

        # Pad the arrays with None values to match the maximum length
        padded = list(zip_longest(t,q,t_model,q_model,fillvalue=None))
        transposed = list(zip(*padded))
        # Create separate lists for each index
        result = [list(column) for column in transposed]

        t = result[0]
        q = result[1]
        t_model = result[2]
        q_model = result[3]

        dict_final = {'t': t, 'q': q, 't_model': t_model, 'q_model': q_model}
        
        df_final = pd.DataFrame(dict_final)
        # FILE DESTINATION, CHANGE TO FIT YOUR LOCAL GITHUB FOLDER. File name: "dataMonthlyST.json"
        df_final.to_csv(f"../prod/data/declineCurves/{name}DC.csv", index=False)
        #------------------^^^^^^^----------------------------------------------------------------#
        
        return {"qi":qi_est, "di":Di_est, "b":b_est}
    
    # except RuntimeWarning:
    #     print("Error: Invalid conversion to integer.")

    except:
        exclList.append(name)
        print("excluded: ", name)
        return None


def hyperbolicEq(t, qi, b, Di):
    return qi/(1+b*Di*t)**(1/b)

# def economics(q, q_model, t_model):
    print("BBLS produced so far: ", sum(q))

    delta_t = t_model[1] - t_model[0]  # Width of each subinterval
    area_under_curve = np.sum(q_model[:-1] * delta_t)  # Sum of the areas
    print("LRAM (Accurate to real world): ", area_under_curve)

    # Sum area under curve using trap. rule
    print('Trapezoidal (More accurate to curve): ', np.trapz(q_model, t_model))
    
main()

# OLD CODE =========================================================================================

# economics(q, q_model, t_model)

# Plot the existing data + model using matplotlib
# plt.semilogy(t, q)
# plt.plot(t, q, 'ro', label='Data')  # Data points
# plt.plot(t_model, q_model, 'b-', label='Model')  # Model curve
# plt.xlabel('Time')
# plt.ylabel('Production Rate (log scale)')
# plt.legend()
# plt.show()