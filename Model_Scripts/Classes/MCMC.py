"""
Created 10/19/2018
"""
import pandas as pd
from scipy.stats import gaussian_kde
import numpy as np

from Prior import Prior

class MCMC:
    """
    This Parent Class takes care of generating prior and calculating the probability given the prior and the observation
    Random Walk and Independent Sampler Inherit from this interface
    """

    def __init__(self):
        self.samples = None
        self.sample_cols = None
        self.proposal_cols = None

    def set_samples(self, Samples):
        """
        Sets the samples loading class
        :param Samples: Sample: Sample class
        :return:
        """
        self.samples = Samples

    def change_llh_calc(self):
        """
        Calculates the change in loglikelihood between the current and the proposed llh
        :return:
        """
        sample_llh = self.samples.get_sample_llh()
        proposal_llh = self.samples.get_proposal_llh()

        if np.isneginf(proposal_llh) and np.isneginf(sample_llh):
            change_llh = 0
        elif np.isnan(proposal_llh) and np.isnan(sample_llh):
            change_llh = 0
            # fix situation where nan in proposal llh results in acceptance, e.g., 8855 [-52.34308085] -10110.84699320795 [-10163.19007406] [-51.76404079] nan [nan] 1 accept
        elif np.isnan(proposal_llh) and not np.isnan(sample_llh):
            change_llh = np.NINF
        elif not np.isnan(proposal_llh) and np.isnan(sample_llh):
            change_llh = np.inf
        else:
            change_llh = proposal_llh - sample_llh
        return change_llh

    def accept_reject(self, accept_prob):
        """
        Decides to accept or reject the proposal. Saves the accepted parameters as new current sample
        :param accept_prob: float Proposal acceptance probability
        :return:
        """
        if np.random.random() < accept_prob:
            # Accept and save proposal
            self.samples.reset_wins()
            self.samples.save_sample(self.samples.get_proposal())
            self.samples.save_sample_okada(self.samples.get_proposal_okada())
            self.samples.save_sample_llh(self.samples.get_proposal_llh())
        else:
            # Reject Proposal and Save current winner to sample list
            self.samples.increment_wins()
            self.samples.save_sample(self.samples.get_sample())
            self.samples.save_sample_okada(self.samples.get_sample_okada())

    def map_to_okada(self):
        pass

    def draw(self, prev_draw):
        pass

    def acceptance_prob(self):
        pass

    def build_priors(self):
        samplingMult = 50
        bandwidthScalar = 2
        # build longitude, latitude and strike prior
        data = pd.read_excel('./Data/Fixed92kmFaultOffset50kmgapPts.xls')
        data = np.array(data[['POINT_X', 'POINT_Y', 'Strike']])
        distrb0 = gaussian_kde(data.T)

        # build dip, rake, depth, length, width, and slip prior
        vals = np.load('./Data/6_param_bootstrapped_data.npy')
        distrb1 = gaussian_kde(vals.T)
        distrb1.set_bandwidth(bw_method=distrb1.factor * bandwidthScalar)

        dists = {}
        dists[distrb0] = ['Longitude', 'Latitude', 'Strike']
        dists[distrb1] = ['Dip', 'Rake', 'Depth', 'Length', 'Width', 'Slip']

        return Prior(dists)

    def init_guesses(self, init):
        """
        Initialize the sample parameters
        :param init: String: (manual, random or restart)
        :return:
        """
        guesses = None
        if init == "manual":
          #initial guesses taken from final sample of 260911_ca/001
          strike     =  2.77152900e+02
          length     =  3.36409138e+05
          width      =  3.59633559e+04
          depth      =  2.50688161e+04
          slip       =  9.17808160e+00
          rake       =  5.96643293e+01
          dip        =  1.18889907e+01
          longitude  =  1.31448175e+02
          latitude   = -4.63296475e+00

          guesses = np.array([strike, length, width, depth, slip, rake, dip,
              longitude, latitude])

        elif init == "random":
            # draw initial sample at random from prior (kdes)
            priors = self.build_priors()
            p0 = priors[0].resample(1)[:, 0]
            longitude = p0[0]
            latitude = p0[1]
            strike = p0[2]

            # draw from prior but redraw if values are unphysical
            length = -1.
            width = -1.
            depth = -1.
            slip = -1.
            rake = -1.
            dip = -1.
            while length <= 0. or width <= 0. or depth <= 0. or slip <= 0.:
                p1 = priors[1].resample(1)[:, 0]
                length = p1[3]
                width = p1[4]
                depth = p1[2]
                slip = p1[5]
                rake = p1[1]
                dip = p1[0]

            guesses = np.array([strike, length, width, depth, slip, rake, dip,
                                     longitude, latitude])

        elif init == "restart":
            guesses = np.load('../samples.npy')[0][:9]

            # np.save("guesses.npy", self.guesses)
            print("initial sample is:")
            print(guesses)

        return guesses
