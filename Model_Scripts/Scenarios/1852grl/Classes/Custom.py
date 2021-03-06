"""
Created By Cody Kesler
Created 10/19/2018
Property of BYU Mathematics Dept.
"""
import pandas as pd
from scipy.stats import gaussian_kde
import numpy as np
from scipy import stats

from MCMC import MCMC
from Prior import Prior

from scipy.stats import truncnorm

class Custom(MCMC):
    """
    Use this class to create a custom prior and custom earthquake parameters MCMC draws
    When the Variable for use_custom is set to true, this class will be used as the main MCMC class for the Scenario
    """
    def __init__(self):
        MCMC.__init__(self)
        #self.sample_cols = ['Strike', 'Length', 'Width', 'Depth', 'Slip', 'Rake', 'Dip', 'Longitude', 'Latitude']
        #self.proposal_cols = ['P-Strike', 'P-Length', 'P-Width', 'P-Depth', 'P-Slip', 'P-Rake', 'P-Dip', 'P-Logitude', 'P-Latitude']
        self.sample_cols = ['Strike', 'Length', 'Width', 'Slip', 'Longitude', 'Latitude']
        self.proposal_cols = ['P-Strike', 'P-Length', 'P-Width', 'P-Slip', 'P-Logitude', 'P-Latitude']
        self.observation_cols = ['Mw', 'gauge 1 arrival', 'gauge 1 height', 'gauge 2 arrival', 'gauge 2 height', 'gauge 3 arrival', 'gauge 3 height', 'gauge 4 arrival', 'gauge 4 height', 'gauge 5 arrival', 'gauge 5 height', 'gauge 6 arrival', 'gauge 6 height']

    def get_length(self, mag):
        """ Length is sampled from a truncated normal distribution that
		is centered at the linear regression of log10(length_meters) and magnitude.
        Linear regression was calculated from wellscoppersmith data.

		Parameters:
		mag (float): the magnitude of the earthquake

		Returns:
		length (float): a sample from the normal distribution centered on the regression
	    """
        m1 = 0.6423327398       # slope
        c1 = 0.1357387698       # y intercept
        e1 = 0.4073300731874614 # Error bar

        #Calculate bounds on error distribution
        a = mag * m1 + c1 - e1
        b = mag * m1 + c1 + e1
        return 10**truncnorm.rvs(a,b,size=1)[0] #regression was done on log10(length)

    def get_width(self, mag):
	    """ Width is sampled from a truncated normal distribution that
		is centered at the linear regression of log10(width_meters) and magnitude
        Linear regression was calculated from wellscoppersmith data.

		Parameters:
		mag (float): the magnitude of the earthquake

		Returns:
		width (float): a sample from the normal distribution centered on the regression
	    """
	    m2 = 0.4832185193       # slope
	    c2 = 0.1179508532       # y intercept
	    e2 = 0.4093407095518345 # error bar

	    #Calculate bounds on error distribution
	    a = mag * m2 + c2 - e2
	    b = mag * m2 + c2 + e2
	    return 10**truncnorm.rvs(a, b, size=1)[0] #regression was done on log10(width)

    def get_slip(self, length, width, mag):
        """Calculated from magnitude and rupture area, Ron Harris gave us the equation
            Parameters:
            Length (float): meters
            Width (float): meters
            mag (float): moment magnitude
            
            Return:
            slip (float): meters
            """
        #Dr. Harris' rigidity constant : 32e11 dynes/cm^2 
        mu = 3.2e15 # changing cm^2 to m^2
        slip = 10**(3/2 * ( mag + 6.06 )) / (mu * length * width)
        return slip

    def acceptance_prob(self, cur_prior_lpdf, prop_prior_lpdf):
        """
        Calculate the acceptance probability given the lpdf for the current and proposed parameters

        :param prop_prior_lpdf: proposed parameters likelihood
        :param cur_prior_lpdf: current parameters likelihood
        :return:
        """
        change_llh = self.change_llh_calc()

        # Log-Likelihood
        change_prior_lpdf = prop_prior_lpdf - cur_prior_lpdf

        print("prop_prior_lpdf is:")
        print(prop_prior_lpdf)
        print("cur_prior_lpdf is:")
        print(cur_prior_lpdf)

        # Note we use np.exp(new - old) because it's the log-likelihood
        return min(1, np.exp(change_llh+change_prior_lpdf))

    def draw(self, prev_draw):
        """
        Draw with the random walk sampling method, using a multivariate_normal
        distribution with the following specified std deviations to
        get the distribution of the step size.

        Returns:
            draws (array): An array of the 9 parameter draws.
        """
        # Std deviations for each parameter, the mean is the current location
        strike_std = 5.  # strike_std    = 1.
        length_std = 5.e3  # length_std    = 2.e4
        width_std = 2.e3  # width_std     = 1.e4
        slip_std = 0.5  # slip_std      = 0.5
        longitude_std = 0.15  # longitude_std = .025
        latitude_std = 0.15  # latitude_std  = .025
        mean = np.zeros(6)
        # square for std => cov
        cov = np.diag(np.square([strike_std, length_std, width_std, slip_std, 
                                 longitude_std, latitude_std]))

        cov *= 0.25;

        # random draw from normal distribution
        e = stats.multivariate_normal(mean, cov).rvs()

        # does sample update normally
        vals = prev_draw.values + e
        new_draw = pd.DataFrame(columns=self.sample_cols)
        new_draw.loc[0] = vals
        print("Random walk difference:", e)
        print("New draw:", new_draw)

        # return new draw (pandas series)
        return new_draw.loc[0]

        #stub for magnitude sampling
        #strike_std = 5.
        #longitude_std = 0.15
        #latitude_std = 0.15
        #magnitude_std = 0.1 #garret arbitraily chose this

        ## square for std => cov
        #cov = np.diag(np.square([strike_std, longitude_std, latitude_std, magnitude_std]))
        #mean = np.zeros(4)
        #cov *= 0.25

        ## random draw from normal distribution
        #e = stats.multivariate_normal(mean, cov).rvs()

        ## does sample update normally
        #print("Random walk difference:", e)
        #print("New draw:", prev_draw.values + e)

        ##prev_draw should be a pandas but we will change to arrays until we get it all worked out
        #temp = prev_draw.values + e

        #length = self.get_length(temp['Magnitude']) #these are floats so the hstack below will break
        #width = self.get_width(temp['Magnitude'])

        #return np.hstack((temp,length,width))



    def build_priors(self):
        """
        Builds the priors
        :return:
        """
        samplingMult = 50
        bandwidthScalar = 2.0
        # build longitude, latitude and strike prior
        data = pd.read_excel('./InputData/Fixed92kmFaultOffset50kmgapPts.xlsx')
        data = np.array(data[['POINT_X', 'POINT_Y', 'Strike']])
        distrb0 = gaussian_kde(data.T)

        # build dip, rake, depth, length, width, and slip prior
        vals = np.load('./InputData/6_param_bootstrapped_data.npy')
        vals_1852=vals[:,3:]
        vals_1852 = np.log(vals_1852)
        distrb1 = gaussian_kde(vals_1852.T)
        distrb1.set_bandwidth(bw_method=distrb1.factor * bandwidthScalar)

        dists = [distrb0, distrb1]

        # DEPRICATED?
        # dists = {}
        # dists[distrb0] = ['Longitude', 'Latitude', 'Strike']
        # dists[distrb1] = ['Dip', 'Rake', 'Depth', 'Length', 'Width', 'Slip'] # 'Dip', 'Rake', 'Depth', 'Length', 'Width', 'Slip'

        return Prior(dists)

    def map_to_okada(self, draws):
        """
        TODO: JARED AND JUSTIN map to okada space
        :param draws:
        :return: okada_params
        """
        #GRL-style 6-parameter sampling
        lon    = draws["Longitude"]
        lat    = draws["Latitude"]
        strike = draws["Strike"]
        length = draws["Length"]
        width  = draws["Width"]
        slip   = draws["Slip"]

        ##stub for magnitude sampling
        ##mw = draw["Magnitude"]
        #mw = 8.0 #PLACEHOLDER
        #length = self.get_length(mw)
        #width = self.get_width(mw)
        #slip = self.get_slip(length, width, mw)

        #deterministic okada parameters
        rake = 90
        dip = 13
        depth = self.doctored_depth_1852_adhoc(lon, lat, dip)

        #vals = np.array([strike, length, width, depth, slip, rake, dip, lon, lat])
        #okada_params = pd.DataFrame(columns=self.sample_cols)
        #okada_params.loc[0] = vals
        okada_params = np.array([strike, length, width, depth, slip, rake, dip, lon, lat])
        return okada_params

    def make_observations(self, params, arrivals, heights):
        """
        Computes the observations to save to the observations file based off the earthqauke parameters
        and the wave heights and arrival times at each gauge.  The default setting is to save the
        earthquake magnitude, and the arrival times and wave heights at each gauge.
        :param params: numpy array of Okada parameters
        :param arrivals: list of arrival times for the specified gauges
        :param heights: list of Geoclaw produced wave heights at each gauge
        :return: a list that provides the observations in the correct ordering
        """
        obvs = []
        #obvs[0] = self.compute_mw(params[1], params[2], params[4]) #first the magnitude
        obvs.append(self.compute_mw(params["Length"], params["Width"], params["Slip"])) #first the magnitude
        for ii in range(len(arrivals)): #alternate arrival times with wave heights
            obvs.append(arrivals[ii])
            obvs.append(heights[ii])

        return obvs


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

    def haversine_distance(self, p1, p2):
        """
        This function  is set up separately because the haversine distance
        likely will still be useful after we're done with this adhoc approach.

        Note, this does not account for the oblateness of the Earth. Not sure if
        this will cause a problem.
        """
        r = 6371000

        # Setting up haversine terms of distance expansion
        hav_1 = np.power(np.sin((p2[1] - p1[1]) / 2 * np.pi / 180), 2.0)
        hav_2 = np.cos(p2[1] * np.pi / 180) * np.cos(p1[1] * np.pi / 180) * np.power(
            np.sin((p2[0] - p1[0]) / 2 * np.pi / 180), 2.0)

        # taking the arcsine of the root of the sum of the haversine terms
        root = np.sqrt(hav_1 + hav_2)
        arc = np.arcsin(root)

        # return final distance between the two points
        return 2 * r * arc

    def doctored_depth_1852_adhoc(self, longitude, latitude, dip):
        """
        This is a function written specifically for our 1852 depth fix.
        We make use of the fault points used in generating our prior as
        jumping off point for fixing the depth of an event. We use a
        simple trig correction based on a 20degree dip angle and the haversine distance
        to get the depth of the earthquake in question.

        Note, this will do the dip correction regardless of which side
        of the trench our sample is on. Recognizing when the sample is
        on the wrong side seems nontrivial, so we have not implemented
        a check for this here.
        """
        ## set up sample point and fault array
        #p1 = np.array([longitude, latitude])
        #fault_file = './InputData/fault_array.npy'
        #fault_array = np.load(fault_file)
        ## will store haversine distances for comparison
        #dist_array = np.zeros(len(fault_array)//2)
        #for i in range(len(dist_array)):
        #    x = fault_array[2 * i]
        #    y = fault_array[2 * i + 1]
        #    p2 = np.array([x, y])
        #    dist_array[i] = self.haversine_distance(p1, p2)

        #dist = np.amin(dist_array)

        ## need to add trig correction
        #return (20000 + dist * np.tan(20 * np.pi / 180))
        #set up sample point and fault array
        p1 = np.array([longitude,latitude])
        fault_file = './InputData/fault_array.npy'
        fault_array = np.load(fault_file)
        #will store haversine distances for comparison
        dist_array = np.zeros(len(fault_array)//2)
        for i in range(len(dist_array)):
            x = fault_array[2*i]
            y = fault_array[2*i + 1]
            p2 = np.array([x,y])
            dist_array[i] = self.haversine_distance(p1, p2)

        dist    = np.amin(dist_array)
        distind = np.argmin(dist_array)
        arcpt = np.array([fault_array[2*distind],fault_array[2*distind + 1]])

        #arcmidpt = np.array([129.,-6.])
        #dist_array = np.zeros(len(fault_array)//2)
        #for i in range(len(dist_array)):
        #    x = fault_array[2*i]
        #    y = fault_array[2*i + 1]
        #    p2 = np.array([x,y])
        #    dist_array[i] = self.haversine_distance(arcmidpt, p2)
        #midptdist = np.amin(dist_array)
        
        #midpoint of prior arc
        arcmidpt = np.array([129.,-6.])
        #distance between midpoint and point
        distpt = self.haversine_distance(p1, arcmidpt)
        #distance between midpoint and arc
        distarc = self.haversine_distance(arcpt, arcmidpt)
        slope = 1. if distpt < distarc else -1.
        print("distpt is:")
        print(distpt)
        print("distarc is:")
        print(distarc)

        #need to add trig correction
        return (21316. + slope*dist*np.tan(dip*np.pi/180))

    def init_guesses(self, init):
        """
        Initialize the sample parameters
        :param init: String: (manual, random or restart)
        :return:
        """
        guesses = None
        if init == "manual":
            # initial guesses taken from sample 49148 of 20190320_chains/007
            #strike =  1.90000013e+02
            #length =  1.33325981e+05
            #width  =  8.45009646e+04
            #depth  =  5.43529311e+04
            #slip   =  2.18309283e+01
            #rake   =  9.00000000e+01
            #dip    =  1.30000000e+01
            #long   =  1.30850829e+02
            #lat    = -5.45571375e+00
  
            #guesses = np.array([strike, length, width, depth, slip, rake, dip,
            #  long, lat])
            strike =  1.90000013e+02
            length =  1.33325981e+05
            width  =  8.45009646e+04
            slip   =  2.18309283e+01
            lon    =  1.30850829e+02
            lat    = -5.45571375e+00
  
            #guesses = np.array([strike, length, width, slip, long, lat])
            vals = np.array([strike, length, width, slip, lon, lat])
            guesses = pd.DataFrame(columns=self.sample_cols)
            guesses.loc[0] = vals

        elif init == "random":
            prior = self.build_priors()
            guesses = prior.rvs(1)
            #guesses = pd.DataFrame(columns=self.sample_cols)
            #guesses.loc[0] = vals
            print("initial sample is:")
            print(guesses)
            #raise Exception('random initialization not currently tested')

        elif init == "restart":
            #guesses = np.load('../samples.npy')[0][:9]

            ## np.save("guesses.npy", self.guesses)
            #print("initial sample is:")
            #print(guesses)
            raise Exception('restart initialization not currently implemented')

        print("initial sample:")
        print(guesses)

        return guesses
