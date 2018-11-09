"""
created 10/19/2018
"""
import numpy as np
from MakeTopo import MakeTopo
from scipy import stats
from PMF import PMFData, PMF
import os

class FeedForward:
    """
    This class Generates real physical interpretations of the prior from the MCMC class and runs GeoClaw.
    Then Calculates the log likelihood probability based on the output.
    """

    def __init__(self):
        os.system('rm ./.output')
        os.system('make ./.output')
        pass

    def run_geo_claw(self, draws):
        """
        Runs Geoclaw
        :param draws: parameters
        :return:
        """
        mt = MakeTopo()
        # Run GeoClaw using draws
        mt.get_topo()
        mt.make_dtopo(draws)

        os.system('rm .output')
        os.system('make .output')

        return

    def read_gauges(self):
        """Read GeoClaw output and look for necessary conditions.
        This will find the max wave height

        Meaning of gauge<gauge_number>.txt file columns:
        - column 1 is time
        - column 2 is a scaled water height
        - column 5 is the graph that appears in plots

        Parameters:
            gauges (list): List of integers representing the gauge names
        Returns:
            arrivals (array): An array containing the arrival times for the
                highest wave for each gauge. arrivals[i] corresponds to the
                arrival time for the wave for gauges[i]
            max_heights (array): An array containing the maximum heights
                for each gauge. max_heights[i] corresponds to the maximum
                height for gauges[i]
        """
        data = np.loadtxt("./_output/fort.FG1.valuemax")
        arrivals = data[:, 4]
        max_heights = data[:, 3]
        return arrivals, max_heights

    def calculate_llh(self, gauges):
        """
        Calculate the log-likelihood of the data at each of the gauges
        based on our chosen distributions for maximum wave heights and
        arrival times. Return the sum of these log-likelihoods.

        Parameters:
            gauges (list): A list of gauge objects
        Returns:
            p (float): The sum of the log-likelihoods of the data of each
                gauge in gauges.
        """
        names = []
        for gauge in gauges:
            names.append(gauge.name)
        arrivals, heights = self.read_gauges()

        # Calculate p for the arrivals and heights
        llh = 0.  # init p
        # Calculate p for the heights, using the PMFData and PMF classes
        amplification_data = np.load('./Data/amplification_data.npy')
        row_header = amplification_data[:, 0]
        col_header = np.arange(len(amplification_data[0]) - 1) / 4
        pmfData = PMFData(row_header, col_header, amplification_data[:, 1:])
        for i, gauge in enumerate(gauges):
            if (gauge.kind[0]):
                # arrivals
                value = gauge.arrival_dist.pdf(arrivals[i])
                if np.abs(value) < 1e-20:
                    value = 1e-10
                #            llh += np.log(gauge.arrival_dist.pdf(arrivals[i]))
                llh += np.log(value)

            if (gauge.kind[1]):
                # heights
                pmf = pmfData.getPMF(gauge.distance, heights[i])
                if np.abs(heights[i]) > 999999999:
                    llh += -9999
                else:
                    llh_i = pmf.integrate(gauge.height_dist)
                    llh += np.log(llh_i)

            if (gauge.kind[2]):
                # inundation
                pmf = pmfData.getPMF(gauge.distance, heights[i])
                inun_values = np.power(pmf.vals, 4 / 3) * 0.06 * np.cos(gauge.beta) / (gauge.n ** 2)
                inun_probability = pmf.probs
                if len(inun_values) == 0:
                    print("WARNING: inun_values is zero length")
                    pmf_inundation = PMF([0., 1.], [0., 0.])
                else:
                    pmf_inundation = PMF(inun_values, inun_probability)
                llh_inundation = pmf_inundation.integrate(gauge.inundation_dist)
                llh += np.log(llh_inundation)

        return llh
