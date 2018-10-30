# File for running GeoClaw model after initial setup using setup.py
import sys
import os
import maketopo as mt
from scipy import stats
import gauge
import numpy as np
import json
import Gauge
import pandas as pd

class RunModel:
    """
    A class for running the model.

    Attributes:
        iterations (int): The number of iterations to run.
        method (str): The method of sampling to use.
            Can be one of the following:
                'rw': Random walk method
                'is': Independent sampler method
        prior (2d array): Information on the prior distributions
            of the parameters for making the draws.
        gauges (list): List of gauge objects.
    """
    def __init__(self, iterations, method):
        self.iterations = iterations
        self.method = method
        self.priors = self.build_priors()

        with open('gauges.txt') as json_file:
            gauges_json = json.load(json_file)
        gauges = []
        for g in gauges_json:
            G = Gauge(None, None, None, None, None, None, None, None, None, None, None)
            G.from_json(g)
            gauges.append(G)
        self.gauges = gauges


    """ DEPRECIATED
    def independant_sampler_draw(self):
        
        Draw with the independent sampling method, using the prior
        to make each of the draws.

        Returns:
            draws (array): An array of the 9 parameter draws.
        
        # Load distribution parameters.
        params = self.prior

        # Take a random draw from the distributions for each parameter.
        # For now assume all are normal distributions.
        draws = []
        for param in params:
            dist = stats.norm(param[0], param[1])
            draws.append(dist.rvs())
        draws = np.array(draws)
        print("independent sampler draw:", draws)
        return draws
    """


    def one_run(self):
        """
        Run the model one time all the way through.
        """
        # Clear previous files
        os.system('rm dtopo.tt3')
        os.system('rm dtopo.data')

        # ---------------------------------------------------------------
        # e_params = ['Strike', 'Length', 'Width', "Depth", "Slip", "Rake", "Longitude", "Latitude"]
        # samples_loc = './ModelOutput/samples.csv'
        # samples_df = pd.read_csv(samples_loc)
        # ---------------------------------------------------------------

        # Draw new proposal Scenario
        if self.method == 'is':
            draws = self.independant_sampler_draw()
        elif self.method == 'rw':
            cur_params = np.load('samples.npy')[0][:9]

            # ---------------------------------------------------------------
            # cur_params = samples_df.get(e_params).tail(1)
            # ---------------------------------------------------------------

            draws = self.random_walk_draw(cur_params)

        # ---------------------------------------------------------------
        #TODO: WE ONLY WANT THE SAMPLE WHEN IT WINS CORRECT??
        # samples_df.loc[len(samples_df)] = draws
        # samples_df.to_csv(samples_loc)
        # ---------------------------------------------------------------

        # Append draws and initialized p and w to samples.npy
        init_p_w = np.array([0,1])
        sample = np.hstack((draws, init_p_w))
        samples = np.vstack((np.load('samples.npy'), sample))
        np.save('samples.npy', samples)


        # Run GeoClaw using draws
        mt.get_topo()
        mt.make_dtopo(draws)

        #os.system('make clean')
        #os.system('make clobber')
        os.system('rm .output')
        os.system('make .output')

        ## Compute log-likelihood of results
        #p = gauge.calculate_probability(self.gauges)
        # Compute log-likelihood of results
        prop_llh = gauge.calculate_probability(self.gauges)
        cur_samp_llh = samples[0][-2]

        if np.isneginf(prop_llh) and np.isneginf(cur_samp_llh):
            change_llh = 0
        else:
            change_llh = prop_llh - cur_samp_llh

        # Change entry in samples.npy TODO: TAKE OUT
        samples = np.load('samples.npy')
        samples[-1][-2] = prop_llh

        if self.method == 'is':
            # Find probability to accept new draw over the old draw.
            # Note we use np.exp(new - old) because it's the log-likelihood
            accept_prob = min(np.exp(change_llh), 1)

        elif self.method == 'rw':

            prop_prior = self.priors[0].logpdf(samples[-1,[7,8,0]]) #Prior for longitude, latitude, strike
            prop_prior += self.priors[1].logpdf(samples[-1,[6,5,3,1,2,4]]) #Prior for dip, rake, depth, length, width, slip
            cur_samp_prior = self.priors[0].logpdf(samples[0,[7,8,0]]) #As above
            cur_samp_prior += self.priors[1].logpdf(samples[0,[6,5,3,1,2,4]])

            change_prior = prop_prior - cur_samp_prior # Log-Likelihood

            # Note we use np.exp(new - old) because it's the log-likelihood
            accept_prob = min(1, np.exp(change_llh+change_prior))

        # Increment wins. If new, change current 'best'.
        if np.random.random() < accept_prob: # Accept new
            samples[0] = samples[-1]
            samples[-1][-1] += 1
            samples[0][-1] = len(samples) - 1
        else: # Reject new
            samples[int(samples[0][-1])][-1] += 1 # increment old draw wins
        np.save('samples.npy', samples)



    def run_model(self):
        """
        Run the model as many times as desired.
        """
        for _ in range(self.iterations):
            self.one_run()


if __name__ == "__main__":
    iterations = int(sys.argv[1])
    method = sys.argv[2]

    model = RunModel(iterations, method)
    model.run_model()
