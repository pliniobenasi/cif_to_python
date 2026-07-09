from abc import  abstractmethod
from decimal import Decimal
from PyCrop.Abstract.Core.AbstractModule import AbstractModule, STEP_GRANULARITY

class AbstractCropModule(AbstractModule):
    """
    Astract base class for crop components in PyCrop.
    Attributes:
        params (dict): Dictionary containing component's parameters.
        state_variables (dict[str:Decimal]): Dictionary containing state variable(s).
     """
    def __init__(self,name:str="AbstractCropModule",granularity:int=3600,params:dict={})->None:
        super().__init__(name, granularity)
        self.params:dict = {}
        self.state_variables = {}
        self.reset_params(params)
   

    @abstractmethod
    def change_params(self,params:dict)->None:
        """
        Change the crop component parameters.
        

        :param params: Dictionary containing parameter names and values
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def show_required_inputs(self)->list[str]:
        """
        Show the required input variables for the crop component.
        

        :return: List of required input variable names
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def step(self,input:list)->None:
        """
        Advance the crop component by one timestep.

        :param input: Input data for the current timestep
        """
        raise NotImplementedError("Subclasses must implement this method")
    

    def show_variables(self)->dict:
        """
        Show the current state variables of the crop component.
        

        :return: Dictionary containing state variable names and values
        """
        return self.state_variables 
    
    def get_variable_names(self)->list[str]:
        """
        Show the names of the current state variables of the crop component.
        

        :return: List of state variable names
        """
        return list(self.state_variables.keys())
    
    def reset_params(self,params:dict)->None:
        """
        Reset the crop component parameters.
        

        :param params: Dictionary containing parameter names and values
        """
        self.change_params(params)
        self.reset()
        return
    
    def get_params(self)->dict[str:Decimal]:
        """
        Get the current crop component parameters.
        

        :return: Dictionary containing parameter names and values
        """
        return self.params

