
from PyCrop.Abstract.Core.AbstractCropModule import AbstractCropModule
from decimal import Decimal

class AbstractBiomassModule(AbstractCropModule):
    """
    Abstract base class for crop LAI models.
    Inherits from AbstractModule.
    Attributes:
        name (str): name of the crop component
        granularity (int): How many seconds a time step has. Default is HOURLY (3600 seconds).
        params (dict): Dictionary containing component parameters. Must include:
            W_0 (float/Decimal): Initial biomass value
        state_variables (dict): Dictionary containing state variables. Includes:
            W (Decimal): Current biomass value
    """
   

    def __init__(self,name:str="AbstractBiomassModule",granularity:int=3600,params:dict={})->None:
        if not isinstance(params,dict):
            raise TypeError("Module parameters is not a dictionary")
        if "W_0" not in params:
            raise ValueError("Parameter W_0 (initial biomass number) is required")
        if params["W_0"]<0:
         raise ValueError("Parameter W_0 must be non-negative")
        if not isinstance(params["W_0"],(float,Decimal,int)):
            raise TypeError("Parameter W_0 must be a number")
        super().__init__(name,granularity,params)
        if isinstance(self.params["W_0"],float):
            self.state_variables["W"]=Decimal(str(self.params["W_0"]))
        else: self.state_variables["W"]= Decimal(self.params["W_0"])

    def reset(self)->None:
        """
        Reset the Module to its initial state.
        """
        self.state_variables["W"] = self.params["W_0"]        