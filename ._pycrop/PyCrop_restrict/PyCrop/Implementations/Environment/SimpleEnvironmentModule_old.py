from PyCrop.Abstract.Core.AbstractCropModule import AbstractCropModule
from decimal import Decimal

WM2TOPPFD = Decimal("2.11") # Conversion factor from W/m^2 to PPFD (Photosynthetic Photon Flux Density) in μmol/m^2/s

class SimpleEnvironmentModule(AbstractCropModule):
    """
    Simple environment module that provides basic environmental data which computes daily average from hourly data.
    
    Attributes:
        name (str): name of the module
        granularity (int): How many seconds a time step has. Default is HOURLY (3600 seconds).
        Initial_temperature (Decimal): Initial temperature value
        Initial_solar_radiation (Decimal): Initial solar radiation value
        Temperature_delta (Decimal): Modifier for temperature values
        T_amp (Decimal): Amplitude for temperature values
        SR_delta (Decimal): Modifier for solar radiation values
        SR_amp (Decimal): Amplitude for solar radiation values
        state_variables (dict): Dictionary containing state variables. Includes:
            Hour (int) : Current hour of the day (0-23)
            Temperature (Decimal): Current temperature value
            Solar_radiation (Decimal): Current solar radiation value
            Daily_Average_Temperature (Decimal): Daily average temperature
            Daily_Daytime_Average_Temperature (Decimal): Daily average temperature during daytime
            PPFD (Decimal): Photosynthetic Photon Flux Density, computed from Solar Radiation
    Required Inputs:
        Clock (int): Current simulation clock in seconds
        Temperature (float/Decimal): Current temperature value
        Solar_radiation (float/Decimal): Current solar radiation value
    """
    def __init__(self, name:str="SimpleEnvironmentModule",granularity:int=3600,params:dict={})->None:
        """
        Initializes the SimpleEnvironmentModule with the provided environmental data.
        Module works hourly, and compute daily average temperature and daily daytime averages.
        
        :param name: Name of the module
        :param granularity: Time step granularity in seconds. Default is 3600 (hourly).
        :param params: A dictionary containing modifiers for environmental parameters.
        Should include:
            - Temperature_delta
            - Temperature_amplitude
            - Solar_radiation_delta
            - Solar_radiation_amplitude
        """
        if granularity != 3600:
            raise ValueError("Simple Environment module only supports HOURLY granularity.")
        super().__init__(name,granularity,params)
        self.state_variables["Hour"] = 0
        self.state_variables["Temperature"] = self.params["Initial_temperature"]
        self.state_variables["Solar_radiation"] = self.params["Initial_solar_radiation"]
        self.state_variables["Daily_Average_Temperature"] = Decimal(0)
        self.state_variables["Daily_Daytime_Average_Temperature"] = Decimal(0)
        self.state_variables["PPFD"] = self.params["Initial_solar_radiation"] * WM2TOPPFD
        self.state_variables["CO2"] = Decimal(400)
        self.daily_temperature_sum = Decimal(0)
        self.daily_daytime_temperature_sum = Decimal(0)

    def change_params(self,params:dict)->None:
        """
        Change the environment module parameters.
        
        :param params: Dictionary containing parameter names and values. Should include:
            - Initial temperature
            - Initial solar radiation
            - Temperature_delta
            - Temperature_amplitude
            - Solar_radiation_delta
            - Solar_radiation_amplitude
        """
        if not isinstance(params,dict):
            raise TypeError("Input parameters must be a dictionary")
        req_params = ["Initial_temperature","Initial_solar_radiation","Temperature_delta","Temperature_amplitude","Solar_radiation_delta","Solar_radiation_amplitude"]
        if not all(i in params for i in req_params):
            raise ValueError(f"Missing required parameters. Required parameters are: {req_params}")
        if not all(isinstance(params[i],(float,Decimal,int)) for i in req_params):
            raise TypeError("All parameters must be numbers (int, float or Decimal).")
        
        if isinstance(params["Initial_temperature"],(Decimal,int)):
            self.params["Initial_temperature"] = Decimal(params["Initial_temperature"])
        else : self.params["Initial_temperature"] = Decimal(str(params["Initial_temperature"]))
        
        self.params["Initial_solar_radiation"] = Decimal(params["Initial_solar_radiation"]) if isinstance(params["Initial_solar_radiation"],(Decimal,int)) else Decimal(str(params["Initial_solar_radiation"]))

        self.params["Temperature_delta"] = Decimal(params["Temperature_delta"])
        self.params["Temperature_amplitude"] = Decimal(params["Temperature_amplitude"])
        self.params["Solar_radiation_delta"] = Decimal(params["Solar_radiation_delta"])
        self.params["Solar_radiation_amplitude"] = Decimal(params["Solar_radiation_amplitude"])

    
    def step(self,input:list)->None:
        """
        Advance the environment module by one timestep.
        
        :param input: List containing current temperature and solar radiation values. Should be in the format:
            [Clock, Temperature, Solar_radiation]
        """
        if not isinstance(input,list):
            raise TypeError("Input must be a list")
        if len(input) < 3:
            raise ValueError("Input list must contain at least three values: Hour, Temperature and Solar_radiation")
        if len(input) > 3:
            print(f"Warning: Multiple values provided as input for class {self.name}. Only first three will be used.")
        if not all(isinstance(i,(float,Decimal,int)) for i in input[:3]):
            raise TypeError("Input values must be numbers (int, float or Decimal).")
        
        hour = int(input[0])/3600 % 24
        temp = Decimal(input[1]) * self.params["Temperature_amplitude"] + self.params["Temperature_delta"]
        sr = Decimal(input[2]) * self.params["Solar_radiation_amplitude"] + self.params["Solar_radiation_delta"]
        
        self.state_variables["Temperature"] = temp
        self.state_variables["Solar_radiation"] = sr
        self.state_variables["PPFD"] = sr * WM2TOPPFD
        self.state_variables["Hour"] = hour
        self.daily_temperature_sum += temp
        self.state_variables["Daily_Average_Temperature"] = (self.daily_temperature_sum) / (Decimal(hour) + 1)
        if hour >= 6 and hour <= 18: # Assuming daytime is from 6 AM to 6 PM
            self.daily_daytime_temperature_sum += temp
            self.state_variables["Daily_Daytime_Average_Temperature"] = (self.daily_daytime_temperature_sum) / (Decimal(hour) - 5) # Number of daytime hours passed

        if hour == 23: # Reset daily sums at the end of the day
            self.daily_temperature_sum = Decimal(0)
            self.daily_daytime_temperature_sum = Decimal(0)
        

    def reset(self)->None:
        """
        Reset the environment module to its initial state.
        """
        self.state_variables["Temperature"] = self.params["Initial_temperature"]
        self.state_variables["Solar_radiation"] = self.params["Initial_solar_radiation"]
        self.state_variables["Daily_Average_Temperature"] = Decimal(0)
        self.state_variables["Daily_Daytime_Average_Temperature"] = Decimal(0)
        self.state_variables["PPFD"] = Decimal(0)
        self.daily_temperature_sum = Decimal(0)
        self.daily_daytime_temperature_sum = Decimal(0)

    
    def get_variable_names(self)->list[str]:
        """
        Display the variables available in the module.
        
        :return: List of variable names
        """
        return list(self.state_variables.keys())
    
    def get_variables(self)->dict[str:Decimal]:
        """
        Show the current variables of the module.
        
        :return: Dictionary containing variable names and values
        """
        return self.state_variables
    
    def show_required_inputs(self)->list:
        """
        Return a list of required input variable names for the environment module.
        
        :return: List of required input variable names
        """
        return ["Clock","Temperature","Solar_radiation"]
    
