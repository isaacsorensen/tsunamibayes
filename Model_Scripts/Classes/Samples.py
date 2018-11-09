"""
Created 10;/19/2018
"""

import numpy as np
import sys
import matplotlib

matplotlib.use('agg', warn=False, force=True)

from matplotlib import pyplot as plt
import pandas
from pandas.tools.plotting import scatter_matrix
import operator


class Samples:
    """
    This class handles the saving and loading for generated, samples, priors, and observations
    """

    def __init__(self, scenario_title, sample_cols=None, proposal_cols=None):
        """

        :param scenario_title:
        :param sample_cols:
        :param proposal_cols:
        """
        self.scenario_title = scenario_title
        self.save_path = './ModelOutput/' + self.scenario_title + "_"

        if (not sample_cols and not proposal_cols):
            sample_cols = ['Strike', 'Length', 'Width', 'Depth', 'Split', 'Rake', 'Dip', 'Longitude', 'Latitude']
            proposal_cols = ['P-Strike', 'P-Length', 'P-Width', 'P-Depth', 'P-Split', 'P-Rake', 'P-Dip', 'P-Logitude',
                             'P-Latitude']

        okada_cols = ['O-Strike', 'O-Length', 'O-Width', 'O-Depth', 'O-Split', 'O-Rake', 'O-Dip', 'O-Logitude',
                      'O-Latitude']
        proposal_okada_cols = ['OP-Strike', 'OP-Length', 'OP-Width', 'OP-Depth', 'OP-Split', 'OP-Rake', 'OP-Dip',
                               'OP-Logitude', 'OP-Latitude']
        mcmc_cols = sample_cols + proposal_cols + okada_cols + proposal_okada_cols + \
                    ["Wins"] + \
                    ["Sample Prior", "Sample LLH", "Sample Posterior"] + \
                    ["Proposal Prior", "Proposal LLH", "Proposal Posterior"] + \
                    ["Acceptance ratio", "Proposal Accept/Reject"]

        observation_cols = ["Mw"]  # , "Gauge Max Wave Height", "Gauge Arrival Time"]

        self.samples = pd.DataFrame(columns=sample_cols)
        self.proposals = pd.DataFrame(columns=sample_cols)
        self.okada = pd.DataFrame(columns=okada_cols)
        self.mcmc = pd.DataFrame(columns=mcmc_cols)
        self.observations = pd.DataFrame(columns=observation_cols)

        self.wins = 0

        self.sample_llh = None
        self.sample_prior_llh = None
        self.sample_posterior_llh = None

        self.proposal_llh = None
        self.proposal_prior_llh = None
        self.proposal_posterior_llh = None

    def save_sample(self, saves):
        """
        Saves the accepted sample to the samples dataframe
        :param saves:
        """
        self.samples.loc[len(self.samples)] = saves

    def get_sample(self):
        """
        Returns the current sample parameters
        :return: dataframe row: current sample parameters
        """
        return self.samples.loc[len(self.samples) - 1]

    def save_proposal(self, saves):
        """
        Save the proposal parameters for saving if the proposal is accepted
        Parameters Proposal is row 0 of the 'proposals' dataframe
        :param saves: list: proposal parameters
        """
        self.proposals.loc[0] = saves

    def get_proposal(self):
        """
        Returns the proposal parameters
        :return: dataframe row: proposal parameters
        """
        return self.proposals.loc[0]

    def save_sample_okada(self, saves):
        """
        Saves the accepted samples okada parameters to the dataframe
        :param saves: list: samples okada parameters
        """
        self.okada.loc[len(self.okada)] = saves

    def get_sample_okada(self):
        """
        Returns the sample okada parameters
        :return: dataframe row: sample okada parameters
        """
        return self.okada.loc[len(self.okada)-1]

    def save_proposal_okada(self, saves):
        """
        Saves the 9 okada parameters for the proposal
        Okada Parameters Proposal is row 1 of the 'proposals' dataframe
        :param saves: list: okada parameters
        :return:
        """
        self.proposals.loc[1] = saves

    def get_proposal_okada(self):
        """
        Returns the 9 okada parameters for the proposal
        :return: dataframe row:  9 okada parameters for the proposal
        """
        return self.proposals.loc[1]

    def save_sample_llh(self, llh):
        """
        Saves the current sample loglikelihood
        :param llh: float: current sample loglikelihood
        """
        self.sample_llh = llh

    def get_sample_llh(self):
        """
        Returns the current sample loglikelihood
        :return: float: current sample loglikelihood
        """
        return self.sample_llh

    def save_proposal_llh(self, llh):
        """
        Save the proposed loglikelihood for debugging and if accepted
        :param llh:
        :return:
        """
        self.proposal_llh = llh

    def get_proposal_llh(self):
        """
        Returns the proposed Loglikelihood
        :return: list: proposed Loglikelihood
        """
        return self.proposal_llh

    def save_sample_prior_llh(self, saves):
        """
        Saves the sample prior loglikelihood
        :param saves:
        :return:
        """
        self.save_sample_prior_llh = saves

    def get_sample_prior_llh(self):
        """
        Returns the sample prior loglikelihood
        :return:
        """
        return self.save_sample_prior_llh

    def save_proposal_prior_llh(self, saves):
        """
         Saves the proposal prior loglikelihood
        :param saves:
        :return:
        """
        self.proposal_prior_llh = saves

    def get_proposal_prior_llh(self):
        """
         Returns the sample prior loglikelihood
        :return:
        """
        return self.proposal_prior_llh

    def save_sample_posterior_llh(self, saves):
        """
         Saves the sample posterior loglikelihood
        :param saves:
        :return:
        """
        self.sample_posterior_llh = saves

    def get_sample_posterior_llh(self):
        """
         Returns the sample posterior loglikelihood
        :return:
        """
        return self.sample_posterior_llh

    def save_proposal_posterior_llh(self, saves):
        """
         Saves the proposal posterior loglikelihood
        :param saves:
        :return:
        """
        self.proposal_posterior_llh = saves

    def get_proposal_posterior_llh(self):
        """
         Returns the proposal posterior loglikelihood
        :return:
        """
        return self.proposal_posterior_llh

    def increment_wins(self):
        """
        Increment the counter for the number of times a sample wins
        """
        self.wins += 1

    def reset_wins(self):
        """
        Reset the number of wins when a new proposal is accepted
        """
        self.wins = 0

    def save_debug(self):
        """
        Saves all the parameters into a list to save for the debug file
        :return:
        """
        print("Sample okada", self.get_sample_okada().tolist())
        saves = self.get_sample().tolist() + self.get_proposal().tolist() + self.get_sample_okada().tolist() \
                + self.get_proposal_okada().tolist()
        saves += [self.wins]
        saves += [self.sample_prior_llh, self.sample_llh, self.sample_posterior_llh]
        saves += [self.proposal_prior_llh, self.proposal_llh, self.proposal_posterior_llh]
        saves += [(self.wins / (self.wins + 1))]
        if self.wins > 0:
            saves += ['Accepted']
        else:
            saves += ['Rejected']
        self.mcmc.loc[len(self.mcmc)] = saves

        self.save_obvs()

    def save_obvs(self):
        """
        Saves the data for the observation files
        """
        saves = self.compute_mw(*self.get_proposal()[['Length', 'Width', 'Slip']])
        self.observations.loc[len(self.observations)] = saves

    def compute_mw(self, L, W, slip, mu=30.e9):
        """
        Computes the Magnitude for a set of porposal parameters for saving
        :param L: float: Length of Earthquake
        :param W: float: Width of Earthquake
        :param slip: float: Slip of Earthquake
        :param mu:
        :return: Magnitude of Earthquake
        """
        unitConv = 1e7  # convert from Nm to 1e-7 Nm
        Mw = (2 / 3) * np.log10(L * W * slip * mu * unitConv) - 10.7
        return Mw

    def save_to_csv(self):
        """
        Saves the current dataframes to csv files
        :return:
        """
        self.samples.to_csv(self.save_path + "samples.csv")
        self.okada.to_csv(self.save_path + "okada.csv")
        self.mcmc.to_csv(self.save_path + "mcmc.csv")
        self.observations.to_csv(self.save_path + "observations.csv")

    def read(self, todo):
        if todo == "read":
            print(self.A)
        elif todo == "reset":
            B = np.zeros((2, 11))
            B[0] = self.A[1]
            B[1] = self.A[1]
            B[0][-1] = 1
            B[1][-1] = 1
            np.save("samples.npy", B)
            print(B)
        return

    def add_axis_label(self, param, axis):
        # label = param + ' '
        label = ''
        if param == 'strike' or param == 'dip' or param == 'rake' or param == 'longitude' or param == 'latitude':
            label += 'degrees'
        elif param == 'length' or param == 'width' or param == 'slip':
            label += 'meters'
        elif param == 'depth':
            label += 'kilometers'

        if axis == 'x':
            plt.xlabel(label)
        elif axis == 'y':
            plt.ylabel(label)
        return

    def make_hist(self, param, bins=30):
        if param not in self.d.keys():
            print("{} is not a valid parameter.".format(param))
            return
        column = self.d[param]
        freq = self.A[1:, -1]
        values = self.A[1:, column]

        L = []
        for i in range(len(freq)):
            L += ([values[i]] * int(freq[i] - 1))  # -1 to get rid of rejected

        # Can add other things to the plot if desired, like x and y axis
        # labels, etc.
        plt.hist(L, bins)
        plt.title(param)
        self.add_axis_label(param, 'x')

    def make_2dhist(self, param1, param2, bins):
        """Make a 2d histogram of two parameters with the specified number
        of bins. Loads data from 'samples.npy'.
        Parameters:
            param (str): The name of the parameters for the histogram.
            bins (int): The number of bins to use for the histogram. Defaults to 20.
        """
        if param1 not in self.d.keys():
            print("{} is not a valid parameter value.".format(param1))
        elif param2 not in self.d.keys():
            print("{} is not a valid parameter value.".format(param2))
        else:
            column1 = self.d[param1]
            column2 = self.d[param2]
            freq = self.A[1:, -1]
            values1 = self.A[1:, column1]
            values2 = self.A[1:, column2]

            L1 = []
            L2 = []
            for i in range(len(freq)):
                L1 += ([values1[i]] * int(freq[i] - 1))  # -1 to get rid of rejected
                L2 += ([values2[i]] * int(freq[i] - 1))  # -1 to get rid of rejected

            # Can add other things to the plot if desired, like x and y axis
            # labels, etc.
            plt.hist2d(L1, L2, bins, cmap="coolwarm")
            # plt.xlabel(param1)
            # plt.ylabel(param2)
            self.add_axis_label(param1, 'x')
            self.add_axis_label(param2, 'y')
            plt.title('%s vs %s' % (param1, param2))
            plt.colorbar()

    def make_change_plot(self, param):
        if param not in self.d.keys():
            print("{} is not a valid parameter.".format(param))
            return
        column = self.d[param]
        x = [0] + [i - 1 for i in range(2, len(self.A)) if self.A[i, -1] > 1]
        y = [self.A[1, column]] + [self.A[i + 1, column] for i in range(1, len(self.A) - 1) if self.A[i + 1, -1] > 1]
        plt.plot(x, y)
        plt.xlabel("Iteration")
        # plt.ylabel("Value")
        self.add_axis_label(param, 'y')
        plt.title(param)

    def make_scatter_matrix(self):
        sorted_d = sorted(self.d.items(), key=operator.itemgetter(1))
        names = [row[0] for row in sorted_d]
        df = pandas.DataFrame(data=self.A[1:, :-2], columns=names)
        scatter_matrix(df, alpha=0.2, diagonal="hist")

    def make_correlations(self):
        sorted_d = sorted(self.d.items(), key=operator.itemgetter(1))
        names = [row[0] for row in sorted_d]
        df = pandas.DataFrame(data=self.A[1:, :-2], columns=names)
        correlations = df.corr()
        fig = plt.figure()
        ax = fig.add_subplot(111)
        cax = ax.matshow(correlations, vmin=-1, vmax=1)
        fig.colorbar(cax)
        ticks = np.arange(0, 9, 1)
        ax.set_xticks(ticks)
        ax.set_yticks(ticks)
        ax.set_xticklabels(names)
        ax.set_yticklabels(names)

    def generate_subplots(self, kind, bins=30):
        if kind not in ["values", "change"]:
            print("{} is not a valid plot type.".format(kind))
            return
        for i, key in enumerate(self.d.keys()):
            plt.subplot(3, 3, int(i + 1))
            if kind == "values":
                self.make_hist(key, bins)
            elif kind == "change":
                self.make_change_plot(key)
        plt.tight_layout()
        # plt.show()
        plt.savefig("all_" + kind + ".pdf")

    def plot_stuff(self, param1, param2, kind, bins=30):
        if param2 is not None:
            self.make_2dhist(param1, param2, bins)
            # plt.show()
            plt.savefig("hist2d_" + param1 + "_" + param2 + ".pdf")
        elif param1 == "all":
            self.generate_subplots(kind, bins)
        elif kind == "change":
            self.make_change_plot(param1)
            # plt.show()
            plt.savefig(kind + "_" + param1 + ".pdf")
        elif param1 == "scatter_matrix":
            self.make_scatter_matrix()
            # plt.show()
            plt.savefig("scatter_matrix.pdf")
        elif param1 == "correlations":
            self.make_correlations()
            # plt.show()
            plt.savefig("correlations.pdf")
        else:
            self.make_hist(param1, bins)
            # plt.show()
            plt.savefig("hist_" + param1 + ".pdf")

    def run(self, param1, param2, kind, bins):
        # TODO Add flag to automatically generate .png files
        # Can be set to any of the 9 parameters in the dictionary, or
        # to "all"
        if param1 == "long" or param1 == "lat":  # allow for shorthand
            param1 += "itude"

        # initialze values (kind to "values" and bins to 30)
        param2 = None
        kind = "values"
        bins = 30

        # extract other command line arguments
        if len(sys.argv) > 3:  # gets kind and bins
            kind = sys.argv[2]
            bins = int(sys.argv[3])
        elif len(sys.argv) > 2:
            if sys.argv[2].isdigit():  # gets bins
                bins = int(sys.argv[2])
            else:  # gets kind
                kind = sys.argv[2]

        if kind == "long" or kind == "lat":
            kind += "itude"
        if kind in self.d.keys():
            param2 = kind

        self.plot_stuff(param1, param2, kind, bins)

from Custom import Custom
from RandomWalk import RandomWalk
import pandas as pd

if __name__ == "__main__":
    mcmc = RandomWalk(1)
    samples = Samples("1852", mcmc.sample_cols, mcmc.proposal_cols)
    mcmc.set_samples(samples)
    guesses = mcmc.init_guesses("manual")
    samples.save_sample(guesses)
    sample = samples.get_sample()
    print(sample[['Longitude', 'Latitude', 'Strike']])
    sample['Longitude'] = 0
    print(sample)
    samples.save_sample(sample)
    print(samples.samples)



