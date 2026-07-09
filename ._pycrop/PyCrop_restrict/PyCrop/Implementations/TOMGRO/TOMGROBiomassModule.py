from decimal import Decimal
from PyCrop.Abstract.AbstractCropModules.AbstractBiomassModule import AbstractBiomassModule
from PyCrop.Abstract.Core.AbstractInputModule import STEP_GRANULARITY
from math import log, exp
"""
    TOMGRO CONSTANTS
"""
QE= Decimal("0.0645")
Q10= Decimal("1.4")
D= Decimal("2.593")
K= Decimal("0.58")
tau= Decimal("0.0693")
m= Decimal("0.1")

BIOMASS_DEFAULT_PARAMS= {
    "W_0":Decimal("0.0"),
    "W_f0":Decimal("0.0"),
    "W_m0":Decimal("0.0"),
    "p1": Decimal("1"),
    "rho" : Decimal("1"),
    "Vmax": Decimal("2"),
    "alphaF": Decimal('0.47'),
    "theta": Decimal('0.22'),
    "krm": Decimal('0.005'),
    "NFF": Decimal('13'),
    "KFF": Decimal('16'),
    "Tcrit": Decimal('30'),
    "cfngt": Decimal('7'),
    "dfmax": Decimal('0.062'),
    "E": Decimal('0.06'),
    "LAI_MAX": Decimal('2')
}

class TOMGROBiomassModule(AbstractBiomassModule):
    """
    TOMGRO Biomass crop component implementation.
    Inherits from AbstractBiomassModule.
    Attributes:
        name (str): name of the crop component
        granularity (int): How many seconds a time step has. Default is Hourly (3600 seconds).
        params (dict): Dictionary containing component parameters. Must include:
            W_0 (Decimal): Initial biomass value
            W_f0 (Decimal): Initial fruit biomass value
            W_m0 (Decimal): Initial mature fruit biomass value
            p1 (Decimal): Parameter for biomass computation,
            rho (Decimal): Parameter for biomass computation,
            Vmax (Decimal): Parameter for biomass computation,
            alphaF (Decimal): Parameter for biomass computation,
            theta (Decimal): Parameter for biomass computation,
            krm (Decimal): Parameter for biomass computation
            NFF (Decimal): Parameter for biomass computation,
            Tcrit (Decimal): Parameter for biomass computation,
            cfngt (Decimal): Parameter for biomass computation,
            KFF (Decimal): Parameter for biomass computation,
            dfmax (Decimal): Parameter for biomass computation,
            E (Decimal): Parameter for biomass computation,
            LAI_MAX (Decimal): Maximum Leaf Area Indexs
        state_variables (dict): Dictionary containing state variables. Includes:
            W (Decimal): Current biomass value
            W_f (Decimal): Fruit biomass value
            W_m (Decimal): Mature Fruit biomass value
            Pg (Decimal): Growth photosynthesis 
            Rm (Decimal): Maintenance respiration
        Required Inputs:
            PAR (float/Decimal): Photosynthetically Active Radiation (µmol m^-2 s^-1)
            T_air (float/Decimal): Air Temperature (°C)
            N_leaf (float/Decimal): Leaf Nitrogen Content (g m^-2)
            LAI (float/Decimal): Leaf Area Index
    """

    def __init__(self, name = "TOMGROBiomassModule", granularity = STEP_GRANULARITY["HOURLY"], params = {} ) -> None:
        if not granularity == STEP_GRANULARITY["HOURLY"]:
            raise ValueError("TOMGRO Biomass module only supports HOURLY granularity.")
        super().__init__(name, granularity, params)
        if "W_f0" not in params:
            raise ValueError("Parameter W_f0 (initial fruit biomass number) is required")
        if not isinstance(params["W_f0"], (int,float,Decimal)):
            raise TypeError("Parameter W_f0 must be a number")
        if params["W_f0"]<0:
         raise ValueError("Parameter W_f0 must be non-negative") 
        if "W_m0" not in params:
            raise ValueError("Parameter W_m0 (initial mature fruit biomass number) is required")
        if not isinstance(params["W_m0"], (int,float,Decimal)):
            raise TypeError("Parameter W_m0 must be a number")
        if params["W_m0"]<0:
         raise ValueError("Parameter W_m0 must be non-negative")

        if isinstance(self.params["W_f0"],float):
            self.state_variables["W_f"]=Decimal(str(self.params["W_f0"]))
        else: self.state_variables["W_f"]= Decimal(self.params["W_f0"])
        if isinstance(self.params["W_m0"],float):
            self.state_variables["W_m"]=Decimal(str(self.params["W_m0"]))
        else: self.state_variables["W_m"]= Decimal(self.params["W_m0"])
        self.state_variables["Pg"] = Decimal(0)
        self.state_variables["Rm"] = Decimal(0)
        self.p1=Decimal(0)

    
    def reset(self) -> None:
        """
        Reset the Module to its initial state.
        """
        super().reset()
        self.state_variables["W_f"] = self.params["W_f0"]
        self.state_variables["W_m"] = self.params["W_m0"]
        self.state_variables["W"] = self.params["W_0"]
        self.state_variables["Pg"] = Decimal(0)
        self.state_variables["Rm"] = Decimal(0)
    
    def change_params(self, params):
        """
        Change the TOMGRO Biomass model parameters.

        :param params: Dictionary containing parameter names and values. Parameters must be either float or Decimal.
        parameters required:
            W_0 (float/Decimal)
            W_f0 (float/Decimal)
            W_m0 (float/Decimal)
            p1 (float/Decimal)
            rho (float/Decimal)
            Vmax (float/Decimal)
            alphaF (float/Decimal)
            theta (float/Decimal)
            krm (float/Decimal)
            NFF (float/Decimal)
            Tcrit (float/Decimal)
            cfngt (float/Decimal)
            KFF (float/Decimal)
            dfmax (float/Decimal)
            E (float/Decimal)
            LAI_MAX (float/Decimal)
        """
        if not isinstance(params,dict):
            raise TypeError("param argument must be a dict")
        required_params = [
            "W_0","W_f0", "W_m0", "p1", "rho", "Vmax", "alphaF", "theta","krm",
            "NFF", "Tcrit", "cfngt", "KFF", "dfmax", "E", "LAI_MAX"
        ]

        for param in required_params:
            if param not in params:
                raise ValueError(f"Parameter '{param}' is required but missing.")
            if not isinstance(params[param], (int, float,Decimal)):
                raise TypeError(f"Parameter '{param}' must be a number.")
            if  params[param] < 0:
                raise ValueError(f"Parameter '{param}' must be non-negative.")
        if params["NFF"] >= params["KFF"]:
            raise ValueError("Parameter NFF must be smaller than KFF.")

        for i in params:
            if isinstance(params[i], float):
                self.params[i] = Decimal(str(params[i]))
            else:
                self.params[i] = Decimal(params[i])
        
    def show_required_inputs(self):
        """
        Return a list of required input variable names.

        :return: List of required input variable names
        """
        return ["Hour","Temperature", "Daily_AVG_Temp", "Daytime_AVG_Temp", "CO2", "PPFD", "Nodes","Delta_Nodes", "LAI"]
    
    def step(self, input: list) -> None:
        """
        Perform a simulation step for the TOMGRO Biomass model.
        

        :param input: List containing required input variables:
            Hour (int): Current hour of the day (0-23)
            Temperature (float/Decimal): Air Temperature (°C)
            Daily_AVG_Temp (float/Decimal): Daily Average Temperature (°C),
            Daytime_AVG_Temp (float/Decimal): Daytime Average Temperature (°C),
            CO2 (float/Decimal): Leaf Area Index,
            PPFD (float/Decimal): Photosynthetically Flux Density (µmol m^-2 s^-1),
            Nodes (int): Number of nodes,
            Delta_Nodes (float/Decimal): Daily increment of nodes,
            LAI (float/Decimal): Leaf Area Index
        """
        if not isinstance(input,list): raise TypeError("Input must be a list")
        if len(input) < 9 : raise ValueError("Input list must contain at least 9 elements")
        if len(input) >9:  print(f"Warning: More values provided as input for class {self.name} than needed. Only firts 9 will be used.")

        if any(not isinstance(input[i], (int,float,Decimal)) for i in range(1,9)):
            raise TypeError("Input values must be int, float, or Decimal.")
        if not input[0]%1==0:
            raise TypeError("Hour must be an integer.")
        hour = Decimal(input[0])
        if hour < 0 or hour >= 24:
            raise ValueError("Hour must be in the range [0, 23].")
        T_air = Decimal(input[1]) if not isinstance(input[1], (float)) else Decimal(str(input[1]))
        T_avg = Decimal(input[2]) if not isinstance(input[2], (float)) else Decimal(str(input[2]))
        T_day = Decimal(input[3]) if not isinstance(input[3], (float)) else Decimal(str(input[3]))
        CO2 = Decimal(input[4]) if not isinstance(input[4], (float)) else Decimal(str(input[4]))
        PPFD = Decimal(input[5]) if not isinstance(input[5], (float)) else Decimal(str(input[5]))
        if not input[6]%1==0:
            raise TypeError("Nodes must be an integer.")
        N = Decimal(input[6])
        if N < 0:
            raise ValueError("Nodes (N) must be non-negative.")
        DN = Decimal(input[7]) if not isinstance(input[7], (float)) else Decimal(str(input[7]))
        if DN < 0:
            raise ValueError("Delta_Nodes (DN) must be non-negative.")
        LAI = Decimal(input[8]) if not isinstance(input[8], (float)) else Decimal(str(input[8]))
        if LAI < 0:
            raise ValueError("Leaf Area Index (LAI) must be non-negative.")

        self.state_variables["Pg"] += ((D*tau*CO2*self.pgr(T_air))/K) * Decimal(log(((1-m)*tau*CO2+QE*K*PPFD)/( (1-m)*tau*CO2+QE*K*PPFD*Decimal(exp(-K* LAI)))))
        self.state_variables["Rm"] += (Decimal(pow(Q10,(T_air*Decimal(0.1)-2)))*self.params["krm"]*self.state_variables["W"])
        if self.state_variables["Pg"] <0:
            raise ValueError("Growth photosynthesis (Pg) must be non-negative.")
        if self.state_variables["Rm"] <0:
            raise ValueError("Maintenance respiration (Rm) must be non-negative.")
        if hour >0:
            return
        
        if LAI > self.params["LAI_MAX"]:
            self.p1=self.params["p1"]

        Dwf = self.dwf(T_avg,T_day,N)
        dwm=0
        if (N > (self.params["NFF"]+self.params["KFF"])):
            dwm = (self.state_variables["W_f"]-self.state_variables["W_m"])*self.params["dfmax"]*Decimal(max(0,min(1,Decimal("0.0714")*(T_avg-9))))
        self.state_variables["W_m"] += dwm
        self.state_variables["W_f"] += Dwf
        dW = Decimal(max(0,Decimal(min(self.grnet(N)-self.p1*self.params["rho"]*DN,Dwf+(self.params["Vmax"]-self.p1)*self.params["rho"]*DN))))
        self.state_variables["W"] +=dW

        if self.state_variables["W"] < 0:
            raise ValueError("Total biomass (W) must be non-negative.")
        if self.state_variables["W_f"] < 0:
            raise ValueError("Fruit biomass (W_f) must be non-negative.")
        if self.state_variables["W_m"] < 0:
            raise ValueError("Mature fruit biomass (W_m) must be non-negative.")
        self.state_variables["Pg"] = Decimal(0)
        self.state_variables["Rm"] = Decimal(0)

    def pgr(self, T_in:Decimal):
        """
        Internal method to compute potential growth rate based on temperature.
        
        :param T_in: Input temperature
        :type T_in: Decimal
        """
        if  0<=T_in and T_in < 9: return Decimal(0.074)*T_in
        elif (9<=T_in and T_in<12): return  Decimal(0.11)*T_in-Decimal(0.32)
        elif (12 <=T_in and T_in<= 28): return  Decimal(1)
        elif (28 < T_in and T_in <35): return  Decimal(5)-T_in/Decimal(7)
        return  Decimal(0)

    def grnet(self,N):
        """
        Internal method to compute gross net assimilation rate.
        
        :param N: number of nodes
        :return: gross net assimilation rate
        :rtype: Decimal
        """
        fr = Decimal(0.07)
        if (N<1) : fr=Decimal(0); 
        if (1<=N and N <12):
            fr=Decimal(0.205)-Decimal(0.0045)*N
        if (12 <=N and N <21):
            fr= Decimal(0.217)-Decimal(0.006)*N
        if (21<=N and N <= 30): 
            fr= Decimal(0.17)-Decimal(0.003)*N
        g=self.params["E"]*(self.state_variables["Pg"] - self.state_variables["Rm"])*(1-fr)
        return Decimal(max(0,g))
    
    def dwf(self, tmean, daily_tmean, N):
        """
        Internal method to compute daily fruit biomass increment.
        
        :param tmean: daily mean temperature
        :param daily_tmean: daytime average temperature
        :param N: number of nodes
        :return: daily fruit biomass increment
        :rtype: Decimal
        """
        if (N < self.params["NFF"]):
            return Decimal(0)
        ff = Decimal(max(0,min(1,Decimal(0.0625)*(tmean-self.params["cfngt"]))))
        dwf = Decimal(max(0,self.grnet(N)*self.params["alphaF"]*ff*Decimal(1-exp(-self.params["theta"]*(N-self.params["NFF"])))))
        if (daily_tmean > self.params["Tcrit"]):
            dwf = dwf * Decimal(1 - Decimal(0.015) * (daily_tmean - self.params["Tcrit"]))
        return dwf
    
    def get_variables(self) -> dict[str: Decimal]:
        """
        Return the current state variables.
        
        :return: Current state variables
        :rtype: dict(str: Decimal)
        """
        return self.state_variables