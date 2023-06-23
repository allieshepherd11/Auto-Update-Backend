import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from datetime import datetime, timedelta
from itertools import zip_longest
from dateutil.relativedelta import relativedelta

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
    # params.to_csv("../prod/data/declineCurves/1params.csv", index=False)
    #----------------^^^^^--------------------------------------------------------------------#
    
def declineCurve(name):
    data = pd.read_csv('monthlyDataST.csv')
    # Drop unused columns, exclude data from the current month
    df = data[data['Well Name'] == name].drop(columns=['Gas (MCF)', 'Water (BBLS)', 'TP', 'CP'])
    df_format = df.drop(df.index[-1])
    df_format.to_csv("dectest.csv", index=False)
    df_data = pd.read_csv('dectest.csv')

    # CREATE REAL DATA ARRAYS TO BE USED ON FINAL GRAPH
    # t_real = np.arange(len(df_data))
    t_real = df_data['Date'].values.tolist()
    q_real = df_data['Oil (BBLS)'].values.tolist()

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
        dates_model = actual_df['Date'].values.tolist()
        actual_df.to_csv("dekAnswer.csv", index=False)

        # Create time and production lists
        t = np.arange(len(actual_df))
        q = actual_df['Oil (BBLS)'].values.tolist()
        qi = q[0]

        initial_estimate = [qi, .8, .4]

        # Curve fit to hyperbolicEq, using t, q, and initial_estimate
        popt, pcov = curve_fit(hyperbolicEq, t, q, p0=initial_estimate)
        qi_est, b_est, Di_est = popt

        # Generate the model curve
        extr_mo = 40 # # of extrapolated months
        t_model = np.linspace(min(t), max(t)+extr_mo, 1+max(t)+extr_mo)  # Time range for the model curve & number of elements within range
        q_model = hyperbolicEq(t_model, qi_est, b_est, Di_est)

        # RUN ECONOMICS
        q_eco, qm_eco, fp_eco, moUntilEcoLimit = economics(q, q_model, t, qi_est, b_est, Di_est, extr_mo)

        # Pad the arrays with None values to match the maximum length
        padded = list(zip_longest(t_real,q_real,dates_model,q_model,fillvalue=None))
        transposed = list(zip(*padded))
        # Create separate lists for each index
        result = [list(column) for column in transposed]

        t_real = result[0]
        q_real = result[1]
        dates_model = result[2]
        q_model = result[3]

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

        # CREATE FINAL DATAFRAME
        dict_final = {'t': t_real, 'q': q_real, 't_model': dates_model, 'q_model': q_model}
        df_final = pd.DataFrame(dict_final)

        name = name.replace("#", "").replace(" ", "")
        # FILE DESTINATION, CHANGE TO FIT YOUR LOCAL GITHUB FOLDER. File name: "dataMonthlyST.json"
        # df_final.to_csv(f"../prod/data/declineCurves/{name}.csv", index=False)
        #------------------^^^^^^^----------------------------------------------------------------#
        return {"qi":qi_est, "di":Di_est, "b":b_est, "extr_mo":extr_mo, "q_sum": q_eco, "qm_sum": qm_eco, "future_prod":fp_eco, "eco_limit_mo": moUntilEcoLimit}
    
    # except RuntimeWarning:
    #     print("Error: Invalid conversion to integer.")

    except:
        exclList.append(name)
        # print("excluded: ", name)
        return None


def hyperbolicEq(t, qi, b, Di):
    return qi/(1+b*Di*t)**(1/b)

# Find when it hits 140
# 
def economics(q, q_model, time, qi_est, b_est, Di_est, extr_mo):
    q_sum = sum(q)
    q_model_sum = sum(q_model)
    future_prod = q_model_sum - q_sum

    extra_months = list(range(len(time), len(time) + extr_mo))  # Generate a range of values based on the length of t
    time = time.tolist()
    time += extra_months  # Concatenate the original list with the extra months)

    moUntilEcoLimit = None
    for i in time:
        if qi_est/(1+b_est*Di_est*i)**(1/b_est) <= 140:
            moUntilEcoLimit = i
            break

    return q_sum, q_model_sum, future_prod, moUntilEcoLimit

    
    
main()

# OLD CODE =========================================================================================

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