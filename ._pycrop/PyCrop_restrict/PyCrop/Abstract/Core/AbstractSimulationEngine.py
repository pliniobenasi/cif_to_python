from abc import ABC, abstractmethod
from PyCrop.Abstract.Core.AbstractInputModule import AbstractInputModule
from PyCrop.Abstract.Core.AbstractCropModule import AbstractCropModule
class AbstractSimulationEngine(ABC):
    """
    Abstract base class for simulation engines in PyCrop.
    Defines the interface for running simulations.
    Attributes:
        input (dict[AbstractInputModule]): The input modules for the simulation, referenced by their name.
        modules (dict[str:AbstractCropModule]): Dictionary of crop modules in the simulation, storted by name.
        name (str): Name of the simulation engine
        input_bindings (dict): Dictionary containing binding between a crop module and who provide its input variables.
        system_varaibles (dict): Dictionary containing all system's variables 
    """

    def __init__(self,name:str="AbstractSimulationEngine")->None:
        super().__init__()
        if not isinstance(name,str):
            raise TypeError("Module name is not a string")

        self.inputs = {}
        self.modules = {}
        self.name = name
        self.input_bindings={}
        self.system_variables={}

    @abstractmethod 
    def add_input_module(self, input_modules)->None:
        """
        Add one or more input modules for the simulation engine.
        Can not add two input modules with the same name

        :param input_module: An instance of AbstractInputModule or list of AbstractInputModule
        """
        raise NotImplementedError("Subclasses must implement this method")
    
        
    @abstractmethod
    def add_module(self, modules)->None:
        """
        Add one or more crop modules to the simulation engine.
        Can not add two modules with the same name

        :param modules: An instance of AbstractCropModule r a list of AbstractCropModule instances
        """
        raise NotImplementedError("Subclasses must implement this method")
    

    @abstractmethod
    def bindVariables(self,provider_module,input_variables, receiver_module, receiver_module_input_name)->None:
        """
        Bind variables provided as inputs to receiver_module
        
        :param input_variables: Variable name or a list of variable names
        :param receiver_module: Name of the module which will use the variables as inputs
        :param receiver_module_input_name: Name of the input variable in the receiver module
        """        
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def run(self)->None:
        """
        Run the simulation with the given parameters.

        """
        raise NotImplementedError("Subclasses must implement this method")
    

    @abstractmethod
    def run_till_timestep(self, timestep:int)->None:
        """
        Run the simulation until a specific timestep, expressed in seconds.

        :param timestep: Integer specifying the timestep to run until
        """
        raise NotImplementedError("Subclasses must implement this method")
    

    def run_till_day(self, day:int)->None:
        """
        Run the simulation until a specific day.

        :param day: Integer specifying the day to run until
        """
        timestep = day * 86400  # Convert days to seconds
        self.run_till_timestep(timestep)
    
    @abstractmethod
    def get_results(self)->dict:
        """
        Get the results of the simulation.

        :return: Dictionary containing simulation results
        """
        raise NotImplementedError("Subclasses must implement this method")

    def get_modules(self)->dict[str:AbstractCropModule]:
        """
        Get the crop modules of the simulation engine.

        :return: List of current crop modules
        """
        return self.modules
    
    def get_module_names(self)->list[str]:
        """
        Get the names of the crop modules in the simulation engine.

        :return: List of names of current crop modules
        """
        return [module.get_name() for module in self.modules]
    
    def get_input_module(self)->list[AbstractInputModule]:
        """
        Get the input module of the simulation engine.

        :return: The current input module
        """
        return self.inputs.items()
    
    def get_system_variables(self)->dict:
        """
        Get all the system variables
        
        :return: A dictionary containing all the system variable by name and value
        :rtype: dict
        """
        return self.system_variables

    def get_input_module_name(self)->list[str]:
        """
        Get the input module of the simulation engine.

        :return: The current input module
        """
        return [i.name for i in self.inputs]
    
    def get_name(self)->str:
        """
        Get the name of the simulation engine.

        :return: name of the simulation engine
        """
        return self.name