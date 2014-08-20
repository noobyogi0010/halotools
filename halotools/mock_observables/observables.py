""" 
Functions that compute statistics of a mock galaxy catalog in a periodic box. 
Still largely unused in its present form, and needs to be integrated with 
the pair counter and subvolume membership methods.
"""

#from __future__ import (absolute_import, division, print_function,
#                        unicode_literals)

__all__=['two_point_correlation_function']

import numpy as np
from math import pi, gamma
import pairs

def two_point_correlation_function(sample1, rbins, sample2 = None, randoms=None, 
                                   period = None, max_sample_size=int(1e4), 
                                   estimator='Natural'):
    """ Calculate the two-point correlation function. 

    Parameters 
    ----------
    sample1 : array_like
        Npts x k numpy array containing k-d positions of Npts. 

    rbins : array_like
        numpy array of boundaries defining the bins in which pairs are counted. 
        len(rbins) = Nrbins + 1.

    sample2 : array_like, optional
        Npts x k numpy array containing k-d positions of Npts.
    
    randoms : array_like, optional
        Nran x k numpy array containing k-d positions of Npts.

    period: array_like, optional
        length k array defining axis-aligned periodic boundary conditions. If only 
        one number, Lbox, is specified, period is assumed to be np.array([Lbox]*k).
        If none, PBCs are set to infinity.

    max_sample_size : int, optional
        Defines maximum size of the sample that will be passed to the pair counter. 

        If sample size exeeds max_sample_size, the sample will be randomly down-sampled 
        such that the subsamples are (roughly) equal to max_sample_size. 
        Subsamples will be passed to the pair counter in a simple loop, 
        and the correlation function will be estimated from the median pair counts in each bin.
    
    estimator: string, optional
        options: 'Natural', 'Davis-Peebles', 'Hewett' , 'Hamilton', 'Landy-Szalay'

    Returns 
    -------
    correlation_function : array_like
        array containing correlation function :math:`\\xi` computed in each of the Nrbins 
        defined by input `rbins`.

        :math:`1 + \\xi(r) \equiv DD / RR`, 
        where `DD` is calculated by the pair counter, and RR is counted by the internally 
        defined `randoms`.

        If sample2 is passed as input, three arrays of length Nrbins are returned: two for
        each of the auto-correlation functions, and one for the cross-correlation function. 

    """
    
    def list_estimators():
        estimators = ['Natural', 'Davis-Peebles', 'Hewett' , 'Hamilton', 'Landy-Szalay']
        return estimators
    estimators = list_estimators()
    
    #process input parameters
    sample1 = np.asarray(sample1)
    if sample2 != None: sample2 = np.asarray(sample2)
    else: sample2 = sample1
    if randoms != None: randoms = np.asarray(randoms)
    rbins = np.asarray(rbins)
    #Process period entry and check for consistency.
    if period is None:
            period = np.array([np.inf]*np.shape(data1)[-1])
    else:
        period = np.asarray(period).astype("float64")
        if np.shape(period) == ():
            period = np.array([period]*np.shape(data1)[-1])
        elif np.shape(period)[0] != np.shape(sample1)[-1]:
            raise ValueError("period should have shape (k,)")
            return None
    
    k = np.shape(sample1)[-1] #dimensionality of data
    
    #check for input parameter consistency
    if (period != None) & (np.max(rbins)>np.min(period)/2.0):
        raise ValueError('Cannot calculate for seperations larger than Lbox/2.')
    if (sample2 != None) & (sample1.shape[-1]!=sample2.shape[-1]):
        raise ValueError('Sample 1 and sample 2 must have same dimension.')
    if (randoms == None) & (min(period)==np.inf):
        raise ValueError('If no PBCs are specified, randoms must be provided.')
    if estimator not in estimators: 
        raise ValueError('Must specify a supported estimator. Supported estimators are:{0}'.value(estimators))

    #If PBCs are defined, calculate the randoms analytically. Else, the user must specify 
    #randoms and the pair counts are calculated the old fashion way.
    def random_counts(sample1, sample2, randoms, rbins, period, k=3):
        """
        Count random pairs.
        """
        def nball_volume(R,k):
            """
            Calculate the volume of a n-shpere.
            """
            return (pi**(k/2.0)/gamma(k/2.0+1.0))*R**k
        
        #If not using PBCs, you must have randoms.
        if np.min(period)==np.inf:
            RR = pairs.npairs(randoms, randoms, rbins, period=period)
            RR = np.diff(RR)
            D1R = pairs.npairs(sample1, randoms, rbins, period=period)
            D1R = np.diff(D1R)
            if sample1 != sample2: #if calculating the cross-correlation
                D2R = pairs.npairs(sample2, randoms, rbins, period=period)
                D2R = np.diff(D2R)
            else: D2R = D1R
            
            return D1R, D2R, RR
        elif randoms != None: #You have PBCs and randoms.
            pass
        else: #If you have PBCs, and no specified randoms--do analytic calculation.
            #do volume calculations
            dv = nball_volume(rbins,k)
            dv = np.diff(dv)
            global_volume = period.prod()
            
            #calculate randoms for sample1
            N1 = np.shape(sample1)[0]
            rho1 = N1/global_volume
            D1R = (N1)*(dv*rho1) #note pair counter counts self pairs.
            
            #if there is a sample2, calculate randoms for it.
            if np.all(sample1 != sample2):
                N2 = np.shape(sample2)[0]
                rho2 = N2/global_volume
                D2R = N2*(dv*rho2)
                #calculate the random-random pairs.
                NR = N1+N2
                rhor = NR/global_volume
                RR = NR*(dv*rhor)
            else: #if not calculating cross-correlation, set RR exactly equal to D1R.
                D2R = D1R #we don't really need this, but set it to something harmless.
                RR = D1R

            return D1R, D2R, RR
    
    def pair_counts(sample1, sample2, rbins, period):
        """
        Count data pairs.
        """
        D1D1 = pairs.npairs(sample1, sample1, rbins, period=period)
        D1D1 = np.diff(D1D1)
        if np.all(sample1 != sample2):
            D1D2 = pairs.npairs(sample1, sample2, rbins, period=period)
            D1D2 = np.diff(D1D2)
            D2D2 = pairs.npairs(sample2, sample2, rbins, period=period)
            D2D2 = np.diff(D2D2)
        else:
            D1D2 = D1D1
            D2D2 = D1D1

        return D1D1, D1D2, D2D2
        
    def TP_estimator(DD,DR,RR,factor,estimator):
        """
        two point correlation function estimator
        """
        if estimator == 'Natural':
            xi = (1.0/factor**2.0)*DD/RR - 1.0
        elif estimator == 'Davis-Peebles':
            xi = (1.0/factor)*DD/DR - 1.0
        elif estimator == 'Hewett':
            xi = (1.0/factor**2.0)*DD/RR - (1.0/factor)*DR/RR #(DD-DR)/RR
        elif estimator == 'Hamilton':
            xi = (DD*RR)/(DR*DR) - 1.0
        elif estimator == 'Landy-Szalay':
            xi = (1.0/factor**2.0)*DD/RR - (1.0/factor)*2.0*DR/RR + 1.0 #(DD - 2.0*DR + RR)/RR
        else: 
            raise ValueError("unsupported estimator!")
        return xi
              
    if randoms != None:
        factor1 = (len(sample1)*1.0)/len(randoms)
        factor2 = (len(sample2)*1.0)/len(randoms)
    else: 
        factor1 = 1.0
        factor2 = 1.0
    
    #count pairs    
    D1D1,D1D2,D2D2 = pair_counts(sample1, sample2, rbins, period)
    D1R, D2R, RR = random_counts(sample1, sample2, randoms, rbins, period, k=k) 
    
    if np.all(sample2==sample1):
        xi_11 = TP_estimator(D1D1,D1R,RR,factor1,estimator)
        return xi_11
    else:
        xi_11 = TP_estimator(D1D1,D1R,RR,factor1,estimator)
        xi_12 = TP_estimator(D1D2,D1R,RR,factor1,estimator)
        xi_22 = TP_estimator(D2D2,D2R,RR,factor2,estimator)
        return xi_11, xi_12, xi_22







