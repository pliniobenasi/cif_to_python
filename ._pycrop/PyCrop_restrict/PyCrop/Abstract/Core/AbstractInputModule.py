from abc import abstractmethod
from decimal import Decimal
from PyCrop.Abstract.Core.AbstractModule import AbstractModule, STEP_GRANULARITY

class AbstractInputModule(AbstractModule):
    """
    Abstract base class for input modules in PyCrop.
    Defines the interface for reading input data.

    General uses for this class is the following:
        - Read input data from a source file via read_input or read_input_columns methods
        - Retrieve data for the current timestep via get_variables method
        - Advance to the next timestep via step method
        - Repeat from point 2 until None is returned by step method
    Attributes:
        current_timestep (int): The current timestep being processed.
        data_size (int): Size of the data read from the input file.
    """


    def __init__(self,name:str="AbstractInputModule",granularity:int=STEP_GRANULARITY["HOURLY"])->None:
        super().__init__(name, granularity)
        self.current_timestep:int = 0
        self.data :list = list()
        self.data_size = -1
        self.data_titles :list = list()

    @abstractmethod
    def read_input(self, input, *args)->None:
        """
        Load Input data from source file.

        :param input: String with path to input file
        :param args: Additional arguments for input reading, such as column names to read, etc. Depends on implementation.
         """
        raise NotImplementedError("Subclasses must implement this method")
    
    @abstractmethod
    def get_variables(self)->dict[str:Decimal]:
        """
        Get the data for the current timestep.

        :return: Dictionary  corresponding to the current timestep in form Name:Value
        """
        raise NotImplementedError("Subclasses must implement this method")

        
    @abstractmethod
    def get_variable_names(self)->list[str]:
        """
        Display the variables available in the input module.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def step(self)->int:
        """
        Advance to the next timestep.
        

        :return: Integer representing the new current timestep
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    @abstractmethod
    def closeFile(self)->None:
        """
        Close file descriptor(s)
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def assignHeader(self,header)->None:
        """
        Add header (columns) names to read variables.
        Better called after first read, otherwise column names may be replaced with actual headers from file
        
        :param header: string (list of) representing new input
        """

    def get_current_timestep(self)->int:
        """
        Get the current timestep being processed.
        
        :return: Integer representing the current timestep
        """
        return self.current_timestep
        
    def __del__(self):
        """
        Destroy the object. Close open files
        """
        self.closeFile()