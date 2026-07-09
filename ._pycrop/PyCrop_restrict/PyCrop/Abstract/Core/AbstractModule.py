from abc import ABC, abstractmethod
from decimal import Decimal

"""
    Possible values for time step granularity, expressed in seconds
"""
STEP_GRANULARITY={"DAILY":86400,"HOURLY":3600,"QUARTERLY":900,"MINUTELY":60,"SECONDLY":1}

class AbstractModule(ABC):
    """
    Abstract base class for modules in PyCrop.  
    Attributes:
        name (str): name of the module
        granularity (int): How many seconds a time step has. Default is HOURLY (3600 seconds).
     """
    def __init__(self,name:str = "AbstractModule",granularity:int=3600)->None:
        super().__init__()
        if not isinstance(name,str):
            raise TypeError("Module name is not a string")
        if not isinstance(granularity,int):
            raise TypeError("Module granularity is not an integer")
        if granularity  <= 0:
            raise ValueError("Granularity must be a positive integer representing seconds")
        self.name = name
        self.granularity = granularity

    @abstractmethod
    def reset(self)->None:
        """
        Reset the input module to its initial state.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def get_variable_names(self)->list[str]:
        """
        Display the variables available in the module.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def get_variables(self)->dict[str:Decimal]:
        """
        Show the current variables of the module.
        
        :return: Dictionary containing variable names and values
        """
        raise NotImplementedError("Subclasses must implement this method")

    def get_name(self)->str:
        """
        Get the name of the crop component.

        :return: name of the crop component
        """
        return self.name
    
    def get_granularity(self)->int:
        """
        Get the granularity of the crop component.

        :return: granularity of the crop component in seconds
        """
        return self.granularity