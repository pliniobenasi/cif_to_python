
from decimal import Decimal
from PyCrop.Abstract.Core.AbstractCropModule import AbstractCropModule


class AbstractNodeModule(AbstractCropModule):
    """
    Abstract base class for crop node components.
    Inherits from AbstractModule.
    Attributes:
        name (str): name of the crop component
        granularity (int): How many seconds a time step has. Default is HOURLY (3600 seconds).
        params (dict): Dictionary containing component parameters. Must include:
            N_0 (float/Decimal): Initial node number
        state_variables (dict): Dictionary containing state variables. Includes:
            Nodes (int): Current node number
    """
   

    def __init__(self,name:str="AbstractNodeModule",granularity:int=3600,params:dict={})->None:
        if not isinstance(params,dict):
            raise TypeError("Module parameters is not a dictionary")
        if "N_0" not in params:
            raise ValueError("Parameter N_0 (initial node number) is required")
        if not isinstance(params["N_0"],(int,float,Decimal)):
            raise TypeError("Parameter N_0 must be a number")
        if params["N_0"]<0:
            raise ValueError("Parameter N_0 must be non-negative")
        super().__init__(name,granularity,params)
        self.state_variables["Nodes"] = int(self.params["N_0"])
        
    def reset(self)->None:
        """
        Reset the Module to its initial state.
        """
        self.state_variables["Nodes"] = int(self.params["N_0"])        