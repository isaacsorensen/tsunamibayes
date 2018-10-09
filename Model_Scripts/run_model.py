# File for running GeoClaw model after initial setup using setup.py
import sys
import os
import maketopo as mt
from scipy import stats
import gauge
import numpy as np
import json
from gauge import Gauge
from build_priors import build_priors

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
        self.priors = build_priors()

        with open('gauges.txt') as json_file:
            gauges_json = json.load(json_file)
        gauges = []
        for g in gauges_json:
            G = Gauge(None, None, None, None, None, None, None, None, None, None, None)
            G.from_json(g)
            gauges.append(G)
        self.gauges = gauges
    

	def haversine_distance(p1,p2):
		"""
		This function  is set up separately because the haversine distance
		likely will still be useful after we're done with this adhoc approach.
		
		Note, this does not account for the oblateness of the Earth. Not sure if
		this will cause a problem.
		"""
		r = 6371000
		
		#Setting up haversine terms of distance expansion
		hav_1 = np.power(np.sin((p2[1] - p1[1])/2*np.pi/180),2.0)
		hav_2 = np.cos(p2[1]*np.pi/180)*np.cos(p1[1]*np.pi/180)*np.power(np.sin((p2[0] - p1[0])/2*np.pi/180),2.0)

		#taking the arcsine of the root of the sum of the haversine terms
		root = np.sqrt(hav_1 + hav_2)
		arc = np.arcsin(root)

		#return final distance between the two points
		return 2*r*arc

	def doctored_depth_1852_adhoc(longitude,latitude,dip):
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
		#set up sample point and fault array
		p1 = np.array([longitude,latitude])
		fault_file = 'fault_array.npy'
		fault_array = np.load(fault_file)
		#will store haversine distances for comparison
		dist_array = np.zeros(0.5*len(fault_array))
		for i in range(len(dist_array)):
			x = fault_array[2*i]
			y = fault_array[2*i + 1]
			p2 = np.array([x,y])
			dist_array[i] = haversine_distance(p1, p2)

		dist = np.amin(dist_array)

		#need to add trig correction
		return (20000 + dist*np.tan(20*np.pi/180))
        
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
    def random_walk_draw(self, u):
        """
        Draw with the random walk sampling method, using a multivariate_normal
        distribution with the following specified std deviations to
        get the distribution of the step size.

        Returns:
            draws (array): An array of the 9 parameter draws.
        """
        # Std deviations for each parameter, the mean is the current location
        #strike = .375
        #length = 4.e3
        #width = 3.e3
        #depth = .1875
        #slip = .01
        #rake = .25
        #dip = .0875
        #longitude = .025
        #latitude = .01875
        strike_std    = 5.       #strike_std    = 1.
        length_std    = 5.e3     #length_std    = 2.e4
        width_std     = 2.e3     #width_std     = 1.e4
        depth_std     = 1.e3     #depth_std     = 2.e3
        slip_std      = 0.5      #slip_std      = 0.5
        rake_std      = 0.5      #rake_std      = 0.5
        dip_std       = 0.1      #dip_std       = 0.1
        longitude_std = 0.15     #longitude_std = .025
        latitude_std  = 0.15     #latitude_std  = .025
        mean = np.zeros(9)
        #square for std => cov
        cov = np.diag(np.square([strike_std, length_std, width_std, depth_std, slip_std, rake_std,
                        dip_std, longitude_std, latitude_std]))
        
        cov *= 0.25;

        # random draw from normal distribution
        e = stats.multivariate_normal(mean, cov).rvs()

		#does sample update normally
        print("Random walk difference:", e)
        print("New draw:", u+e)
		new_draw = u + e

		"""
		Here we make some fixed changes to the dip and depth according 
		to a simple rule documented elsewhere. This fix will likely
		depreciate upon finishing proof of concept paper and work on 1852
		event.
		"""
		#doctor dip to 20 degrees as discussed
		new_draw[6] = 20
		#doctor depth according to adhoc fix
		new_draw[3] = doctored_depth_1852_adhoc(new_draw[7],new_draw[8],new_draw[6])
		
		
		#return appropriately doctored draw
        return new_draw

    def one_run(self):
        """
        Run the model one time all the way through.
        """
        # Clear previous files
        os.system('rm dtopo.tt3')
        os.system('rm dtopo.data')

        # Draw new proposal
        if self.method == 'is':
            draws = self.independant_sampler_draw()
        elif self.method == 'rw':
            u = np.load('samples.npy')[0][:9]
            draws = self.random_walk_draw(u)

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
        samp_llh = samples[0][-2]
        if np.isneginf(prop_llh) and np.isneginf(samp_llh):
            change_llh = 0
        elif np.isnan(prop_llh) and np.isnan(samp_llh):
            change_llh = 0
        #fix situation where nan in proposal llh results in acceptance, e.g., 8855 [-52.34308085] -10110.84699320795 [-10163.19007406] [-51.76404079] nan [nan] 1 accept
        elif np.isnan(prop_llh) and not np.isnan(samp_llh):
            change_llh = np.NINF
        elif not np.isnan(prop_llh) and np.isnan(samp_llh):
            change_llh = np.INF
        else:
            change_llh = prop_llh - samp_llh

        # Change entry in samples.npy
        samples = np.load('samples.npy')
        samples[-1][-2] = prop_llh

        if self.method == 'is':
            # Find probability to accept new draw over the old draw.
            # Note we use np.exp(new - old) because it's the log-likelihood
            accept_prob = min(np.exp(change_llh), 1)

        elif self.method == 'rw':
            prop_prior = self.priors[0].logpdf(samples[-1,[7,8,0]]) #Prior for longitude, latitude, strike
            prop_prior += self.priors[1].logpdf(samples[-1,[6,5,3,1,2,4]]) #Prior for dip, rake, depth, length, width, slip
            
            samp_prior = self.priors[0].logpdf(samples[0,[7,8,0]]) #As above
            samp_prior += self.priors[1].logpdf(samples[0,[6,5,3,1,2,4]])
            #DEPRECATED
            """# Log-Likelihood of prior
            prop_prior = -sum(((samples[-1][:9] - self.prior[:,0])/self.prior[:,1])**2)/2
            samp_prior = -sum(((samples[0][:9] - self.prior[:,0])/self.prior[:,1])**2)/2
            """
            change_prior = prop_prior - samp_prior # Log-Likelihood

            # DEPRICATED (before changed to log-likelihood)
            # change_prior = 1.
            # for i, param in enumerate(self.prior):
            #     dist = stats.norm(param[0], param[1])
            #     prop_prior = dist.pdf(samples[-1][i])
            #     samp_prior = dist.pdf(samples[0][i])
            #     change_prior *= (prop_prior/samp_prior)

            # Note we use np.exp(new - old) because it's the log-likelihood
            accept_prob = min(1, np.exp(change_llh+change_prior))

        # Increment wins. If new, change current 'best'.
        if np.random.random() < accept_prob: # Accept new
            samples[0] = samples[-1]
            samples[-1][-1] += 1
            samples[0][-1] = len(samples) - 1
            result = "accept"
        else: # Reject new
            samples[int(samples[0][-1])][-1] += 1 # increment old draw wins
            result = "reject"
        np.save('samples.npy', samples)

        #print some results for debugging purposes
        samp_post = samp_prior + samp_llh
        prop_post = prop_prior + prop_llh
        print( "result:", len(samples), samp_prior, samp_llh, samp_post, prop_prior, prop_llh, prop_post, accept_prob, result)


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