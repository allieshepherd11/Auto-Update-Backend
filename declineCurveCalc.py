import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit, root_scalar
from datetime import datetime, timedelta
from itertools import zip_longest
from dateutil.relativedelta import relativedelta
import json

# RUN prodMonthly.py BEFORE THIS TO HAVE UPDATED DECLINE CURVES
def main():
    # List of every well w/ production data
    df_wells = pd.read_json('everyWell.json')
    my_list = df_wells.values.tolist()
    oneDList = [element for sublist in my_list for element in sublist]

    # Run declineCurve(), assign returned params to df, then export to csv
    params = {}
    for well in oneDList:
        well_params = declineCurve(well)
        well = well.replace("#", "").replace(" ", "").lower()
        params[well] = well_params
    params = pd.DataFrame(params)

    # FILE DESTINATION, CHANGE TO FIT YOUR LOCAL GITHUB FOLDER. File name: "dataMonthlyST.json"
    params.to_csv("../prod/data/declineCurves/1params.csv", index=False)
    #----------------^^^^^--------------------------------------------------------------------#


    
def declineCurve(name):
    data = pd.read_csv('db/prod/monthlyDataST.csv')
    # Drop unused columns, exclude data from the current month
    df = data[data['Well Name'] == name].drop(columns=['Gas (MCF)', 'Water (BBLS)', 'TP', 'CP'])
    df_format = df.drop(df.index[-1])
    df_format.to_csv("dz.csv", index=False)
    df_data = pd.read_csv('dz.csv') # This csv needs to be kept to run

    # CREATE REAL DATA ARRAYS TO BE USED ON FINAL GRAPH
    # t_real = np.arange(len(df_data))
    t_real = df_data['Date'].values.tolist()
    q_real = df_data['Oil (BBLS)'].values.tolist()


    # Any errors ran will return None to params
    try:
        # Check if well is in dManualEntries.csv
        dfManual = pd.read_csv('declStartManual.csv')
        formatted_name = name.replace("#", "").replace(" ", "").lower()
        if formatted_name in dfManual['Well Name'].tolist():
            drop_index = dfManual.loc[dfManual['Well Name']==formatted_name, 'Start'].values[0]

        # If not manual entry, run algorithm
        else:
            drop_index = None # Index such that everything before will be dropped
            mtc = 5 # Months_To_Check
            r = 10 # Range of Months to check for the highest decreasing
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
            # Loop through indexes in df_data
            for i in range(len(df_data)-mtc):
                tally = 0 # Set counter to 0

                # Check the next 4 months and make sure they are not increasing
                for index, row in df_data.iloc[i:i+mtc].iterrows(): 
                    if index==len(df_data)-1: # Break if index is at the very end of the loop (1 case)
                        break
                    if row["Oil (BBLS)"] <= df_data.loc[index+1, "Oil (BBLS)"]: # If one of the values being checked is increasing (relative to value after), add a tally
                        tally+=1
                
                if tally == 0: # If no values were found to be increasing, check the next 10 months for the one with the highest decrease
                    highest_decrease = 0
                    index = i

                    # Loop starting at 0 until reaches range r
                    for loop in range(r):
                        if df_data.loc[i+loop, "Oil (BBLS)"] - df_data.loc[i+loop+1, "Oil (BBLS)"] > highest_decrease: # Check if row has the highest decrease
                            highest_decrease = df_data.loc[i+loop, "Oil (BBLS)"] - df_data.loc[i+loop+1, "Oil (BBLS)"] # save highest decrease
                            index = i + loop # save index of highest decrease (the row after the current one)
                    # Assign drop_index to be the index after the for loop
                    drop_index = index
                    break

        # Check if well is in dEndList.csv, true: drop the data after given end_index
        df_temp = df_data
        end_index = None
        df_end_data = pd.read_csv('deEndManual.csv')
        if formatted_name in df_end_data['Well Name'].tolist():
            end_index = df_end_data.loc[df_end_data['Well Name']==formatted_name, 'End'].values[0]
            df_temp = df_data.drop(df_data.index[end_index+1:len(df)-1])
            # endDate = df_data.iloc[end_index, 2]
            
        # Drop data before drop_index (given by manual entry or algorithm)
        actual_df = df_temp.drop(df_temp.index[0:drop_index])
        dates_model = actual_df['Date'].values.tolist()


        # Create time & production lists
        t = np.arange(len(actual_df)) # List of indexes of dates
        q = actual_df['Oil (BBLS)'].values.tolist() # list of production data
        qi = q[0]

        # Curve fit to hyperbolicEq, using t, q, and initial_estimate
        initial_estimate = [qi, .8, .4]
        popt, pcov = curve_fit(hyperbolicEq, t, q, p0=initial_estimate)
        qi_est, b_est, Di_est = popt

        extr_mo = 100 # extrapolated months
        t_model = np.linspace(min(t), max(t)+extr_mo, 1+max(t)+extr_mo)  # Array of time indexes (start, stop, # of data points)
        q_model = hyperbolicEq(t_model, qi_est, b_est, Di_est) # Generate the model curve from best fit data

        # RUN economics() ======================================================================================
        q_eco, qm_eco, fp_eco, ecoLimit, modelEcoLimit = economics(q_real, q_model, t_model, qi_est, b_est, Di_est, extr_mo, drop_index)
        # ======================================================================================================

        # Format lists
        padded = list(zip_longest(t_real,q_real,dates_model,q_model,fillvalue=None)) # Pad the arrays with None values to match the maximum length
        transposed = list(zip(*padded))
        # Create separate lists for each index
        result = [list(column) for column in transposed]
        t_real, q_real, dates_model, q_model = result[0], result[1], result[2], result[3]

        # EXTRAPOLATE THE DATES FOR dates_model
        # Find the last non-blank date in the array
        last_index = len(dates_model) - 1
        while dates_model[last_index] == None:
            last_index -= 1
        last_date = datetime.strptime(dates_model[last_index], '%Y-%m-%d')
        # Generate and replace the None values with new dates
        for i in range(last_index + 1, len(dates_model)):
            last_date += relativedelta(months=1)  # Increment by one month
            dates_model[i] = last_date.strftime('%Y-%m-%d')

        # CREATE FINAL CSVs PER EACH WELL
        dict_final = {'t': t_real, 'q': q_real, 't_model': dates_model, 'q_model': q_model}
        df_final = pd.DataFrame(dict_final)
        # FILE DESTINATION, CHANGE TO FIT YOUR LOCAL GITHUB FOLDER. File name: "{formatted_name}.csv"
        df_final.to_csv(f"../prod/data/declineCurves/{formatted_name}.csv", index=False)
        #------------------^^^^^^^----------------------------------------------------------------#

        # RETURNS 'PARAMATERS'
        return {"qi":qi_est, "D":Di_est, "b":b_est, "extr_mo":extr_mo, "q_sum": q_eco, "qm_sum": qm_eco, "future_prod":fp_eco, "eco_limit": ecoLimit, "end_index": end_index, "model_eco_limit": modelEcoLimit}
    
    except:
        return None
        # excluded = pd.DataFrame({'Well Name': [name]})
        # dfExcl = pd.concat([dfExcl, excluded])
        # dfExcl.to_csv('exclList.csv', index=False)
        # print("excluded: ", name)

def hyperbolicEq(t, qi, b, Di):
    return qi/(1+b*Di*t)**(1/b)

def economics(q_real, q_model, t_model, qi_est, b_est, Di_est, extr_mo, drop_index):
    q_sum = sum(q_real)
    q_model_sum = sum(q_model)

    modelPassedMo = len(q_real)-drop_index # Number of months of the model that have passed

    q_model_past_sum = sum(q_model[:modelPassedMo]) # Sums from the beginning of model to the current month (sum is exclusive of end index)
    # Future Production = Entire model - Section of model from the past
    future_prod = q_model_sum - q_model_past_sum

    # Economic Limit in years
    ecoLimit = 'infinity' # Default
    modelEcoLimit = 'infinity'
    mo_list = list(range(601)) # 600 months
    for i in mo_list:
        if hyperbolicEq(i, qi_est, b_est, Di_est) <=140:
            modelEcoLimit = i
            ecoLimit = (i-modelPassedMo)/12
            break

    # Need to Calculate the amt of barrels produced in the rest of the lifetime
    def BBLStoUSD(bbls):
        gasPrice = 70
        royalties = .75
        tax = .954
        operCost = 10000
        usd = (bbls * gasPrice * royalties * tax) - operCost
        return usd
    # print(BBLStoUSD(???))

    return q_sum, q_model_sum, future_prod, ecoLimit, modelEcoLimit

main()

# OLD CODE
"""
# Plot the existing data + model using matplotlib
# plt.semilogy(t, q)
# plt.plot(t, q, 'ro', label='Data')  # Data points
# plt.plot(t_model, q_model, 'b-', label='Model')  # Model curve
# plt.xlabel('Time')
# plt.ylabel('Production Rate (log scale)')
# plt.legend()
# plt.show()

# delta_t = t_model[1] - t_model[0]  # Width of each subinterval
# area_under_curve = np.sum(q_model[:-1] * delta_t)  # Sum of the areas
# print("LRAM (Accurate to real world): ", area_under_curve)
    
# Sum area under curve using trap. rule
# print('Trapezoidal (More accurate to curve): ', np.trapz(q_model, t_model))

def manualEntry():
    dfManual = pd.read_csv('dManualEntries.csv')
    name = input("Enter well name: ")
    name = name.replace("#", "").replace(" ", "").lower()
    startMonth = input("Enter starting month: ")

    dfNew = pd.DataFrame({'Well Name': [name], 'Start': [startMonth]})
    dfManual = pd.concat([dfManual, dfNew])
    # dfManual.to_csv("dManualEntries.csv", index=False)
"""

# netValue = (oil*70*.70875*30) - 10000
    
# discount_rate = 0.1
# cash_flows = [-1000, 500, 300, 200, 100]

# npv = sum(cf / (1 + discount_rate) ** n for n, cf in enumerate(cash_flows))