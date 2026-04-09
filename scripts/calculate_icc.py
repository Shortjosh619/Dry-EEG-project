import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pingouin as pg 
import mne
import numpy as np 
import glob 
from src.dryeeg.settings import RESULTS_DIRNAME
import pandas as pd 

def get_data():
    data = glob.glob(f'{RESULTS_DIRNAME}/*/*/*/*/*.csv')

    results = []

    for col in data:
        columns = col.split(os.sep)
        #print(columns) this print statemrnt was just for me to debug. my glob didnt collect anything initially because it couldnt find the results folder with my import 
        #what i forgot was that this file is contained in the scripts folder of the repo, not in src, so added the sys line at the top.
        df = pd.read_csv(col, index_col=0)
        occ = df.loc[['PO7', 'Oz', 'PO8']]

        row = {
            "pipeline": columns[1],
            "subject": columns[2],
            "session": columns[3],
            "condition": columns[4],
            "abs_alpha": occ['alpha'].mean(),
            "rel_alpha": occ['rel_alpha'].mean()
        }

        results.append(row)

    return pd.DataFrame(results)




def calculate_icc():
    df = get_data()
    #print(df) another print statement solely for debugging
    icc_table = []

    for pipeline in df['pipeline'].unique():
          for condition in df['condition'].unique():
                for metric in ['abs_alpha','rel_alpha']:
                      filtered_df = df[(df['pipeline'] == pipeline) & (df['condition'] == condition)]
                      icc = pg.intraclass_corr(data=filtered_df, targets='subject', raters='session', ratings=metric, nan_policy= 'omit')
                      
                      icc['pipeline'] = pipeline
                      icc['condition'] = condition
                      icc['metric'] = metric
                      icc_table.append(icc) 

    return pd.concat(icc_table)


if __name__ == '__main__':
    results = calculate_icc()
    icc2 = results[(results['Type'] == 'ICC2') | (results['Type'] == 'ICC3')]
    icc2.to_csv('outputs/icc2_results.csv', index=False)
    print(results)
