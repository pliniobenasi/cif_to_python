
from decimal import Decimal
from PyCrop.Abstract.Core.AbstractCropModule import AbstractCropModule


class AbstractLAIModule(AbstractCropModule):
    """
    Abstract base class for crop LAI models.
    Inherits from AbstractModule.
    Attributes:
        name (str): name of the crop component
        granularity (int): How many seconds a time step has. Default is HOURLY (3600 seconds).
        params (dict): Dictionary containing component parameters. Must include:
            L_0 (float/Decimal): Initial LAI value
        state_variables (dict): Dictionary containing state variables. Includes:
            LAI (Decimal): Current LAI value
    """
   

    def __init__(self,name:str="AbstractLAIModule",granularity:int=3600,params:dict={})->None:
        if not isinstance(params,dict):
            raise TypeError("Module parameters is not a dictionary")
        if "L_0" not in params:
            raise ValueError("Parameter L_0 (initial LAI value) is required")
        if not isinstance(params["L_0"],(int,float,Decimal)):
            raise TypeError("Parameter L_0 must be a number")
        if params["L_0"]<0:
            raise ValueError("Parameter L_0 must be non-negative")
        super().__init__(name,granularity,params)
        if not isinstance(self.params["L_0"],(int,float,Decimal)):
            raise TypeError("Parameter L_0 must be a number")
        if isinstance(self.params["L_0"],float):
            self.state_variables["LAI"]=Decimal(str(self.params["L_0"]))
        else: self.state_variables["LAI"] = Decimal(self.params["L_0"])

    def reset(self)->None:
        """
        Reset the Module to its initial state.
        """
        self.state_variables["LAI"] = self.params["L_0"]