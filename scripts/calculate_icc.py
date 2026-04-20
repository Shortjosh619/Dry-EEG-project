import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pingouin as pg
import mne
import numpy as np
import glob
import matplotlib.pyplot as plt
import scipy.stats as stats
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


def calculate_assumptions():
    df = get_data()
    os.makedirs('outputs/plots', exist_ok=True)
    assumption_rows = []

    for pipeline in df['pipeline'].unique():
        for condition in df['condition'].unique():
            for metric in ['abs_alpha', 'rel_alpha']:
                filtered_df = df[(df['pipeline'] == pipeline) & (df['condition'] == condition)]

                pivot = filtered_df.pivot(index='subject', columns='session', values=metric).dropna()
                if len(pivot) < 3:
                    continue

                session1 = pivot.iloc[:, 0].values
                session2 = pivot.iloc[:, 1].values

                grand_mean = np.mean(np.concatenate([session1, session2]))
                row_means = (session1 + session2) / 2
                col_mean_s1, col_mean_s2 = np.mean(session1), np.mean(session2)
                residuals = np.concatenate([
                    session1 - row_means - (col_mean_s1 - grand_mean),
                    session2 - row_means - (col_mean_s2 - grand_mean)
                ])

                fig, ax = plt.subplots()
                stats.probplot(residuals, plot=ax)
                ax.set_title(f"Q-Q Plot: {pipeline} | {condition} | {metric}")
                plt.tight_layout()
                plt.savefig(f'outputs/plots/qq_{pipeline}_{condition}_{metric}.png', dpi=300)
                plt.close(fig)

                norm = pg.normality(residuals)
                homo = pg.homoscedasticity([session1, session2], method='levene')

                assumption_rows.append({
                    'pipeline': pipeline,
                    'condition': condition,
                    'metric': metric,
                    'SW_W': norm['W'].values[0],
                    'SW_p': norm['pval'].values[0],
                    'normal': norm['normal'].values[0],
                    'levene_W': homo['W'].values[0],
                    'levene_p': homo['pval'].values[0],
                    'equal_var': homo['equal_var'].values[0],
                })

    return pd.DataFrame(assumption_rows)


def calculate_bland_altman():
    df = get_data()
    os.makedirs('outputs/plots', exist_ok=True)
    ba_rows = []

    for pipeline in df['pipeline'].unique():
        for condition in df['condition'].unique():
            for metric in ['abs_alpha', 'rel_alpha']:
                filtered_df = df[(df['pipeline'] == pipeline) & (df['condition'] == condition)]

                pivot = filtered_df.pivot(index='subject', columns='session', values=metric).dropna()
                if len(pivot) < 3:
                    continue

                session1 = pivot.iloc[:, 0].values
                session2 = pivot.iloc[:, 1].values

                fig, ax = plt.subplots(figsize=(6, 5))
                pg.plot_blandaltman(session1, session2, agreement=1.96, confidence=0.95, ax=ax)
                ax.set_title(f'Bland-Altman: {pipeline} | {condition} | {metric}')
                ax.set_xlabel('Mean of Session 1 & Session 2')
                ax.set_ylabel('Session 1 − Session 2')
                plt.tight_layout()
                plt.savefig(f'outputs/plots/ba_{pipeline}_{condition}_{metric}.png', dpi=300)
                plt.close(fig)

                diff_vals = session1 - session2
                mean_diff = np.mean(diff_vals)
                sd_diff = np.std(diff_vals, ddof=1)
                ba_rows.append({
                    'pipeline': pipeline,
                    'condition': condition,
                    'metric': metric,
                    'mean_diff': mean_diff,
                    'sd_diff': sd_diff,
                    'loa_upper': mean_diff + 1.96 * sd_diff,
                    'loa_lower': mean_diff - 1.96 * sd_diff,
                    'n': len(pivot),
                })

    return pd.DataFrame(ba_rows)


if __name__ == '__main__':
    results = calculate_icc()
    icc2 = results[(results['Type'] == 'ICC2')]
    icc3 = results[(results['Type'] == 'ICC3')]
    icc2.to_csv('outputs/icc2_results.csv', index=False)
    icc3.to_csv('outputs/icc3_results.csv', index=False)
    print(results)

    assumptions = calculate_assumptions()
    assumptions.to_csv('outputs/assumptions_results.csv', index=False)
    print(assumptions)

    ba = calculate_bland_altman()
    ba.to_csv('outputs/ba_results.csv', index=False)
    print(ba)
