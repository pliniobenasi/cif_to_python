from decimal import Decimal, InvalidOperation
from PyCrop.Abstract.AbstractInputModules.AbstractChunkInputModule import AbstractChunkInputModule

class SFSCInputModule(AbstractChunkInputModule):
    """
    Class extending AbstractInputModule implementing Single-File Single-Column module for PyCrop.
    This class reads input data from a single file and provides methods to access the data.
    This class does not allow for column-specific reading. 
    Input file must contain one data point per line. Column title are mandatory.
    Time step advancement is handled internally, starting from 0. This means that the order of operation should be get_variables() followed by step().
    Attributes:
        current_timestep (int): The current timestep being processed.
        MAX_ROWS (int): Maximum number of rows to store from input. Default is 2048.
        name (str): Name of the input module.
        granularity (int): How many seconds a time step has. Default is HOURLY (3600 seconds).
        data (list): List of stored input data.
        data_size (int): Size of the data read from the input file.
        data_titles (list): Data headers read from the input file.
        f_descriptor: File descriptor for the input file.
    """
    def __init__(self,name:str="SFSCInputModule",MAX_ROWS:int=2048,granularity:int=3600)->None:
        super().__init__(name,MAX_ROWS,granularity)
        self.data_titles = ["Var_1"]


    def read_input(self, input, *args)->None:
        """
        Read input data from a file.
        If MAX_ROWS >0, reads up to MAX_ROWS rows, otherwise reads the whole file.
        If the first row contains a string, it is treated as the column title.

        :param input: String representing the file path
        """
        if not isinstance(input,str):
            raise TypeError("Input must be a string representing the file path")
        if args:
            print("Warning: SFSCInputModule read_input does not support additional arguments. Ignoring them.")
        #Check if file exists and is readable
        try:
            self.f_descriptor = open(input,'r')
        except Exception as e:
            raise IOError(f"Error opening file {input}: {e}")
        if self.f_descriptor is None:
            raise IOError("File descriptor is None after attempting to open file")
        #Initialize data storage in memory
        self.init_memory()
        #Read data rows
        row_count =0
        #Check first row for column titles
        first_row = self.f_descriptor.readline().split(',')
        if len(first_row)> 1:
            raise  IOError("SFSCInputModule only supports single column input files")
        try:            
            self.data[0]=Decimal(first_row[0].strip())  #If no title, first row is data
            row_count += 1
        except InvalidOperation:
            print("First row treated as column title: ", first_row[0])
            self.data_titles = [first_row[0].strip()] #Assign column title
        if self.MAX_ROWS >0:
            row_count =self.read_chunk(self.data,self.f_descriptor,row_count) #Start reading from row 1 (after title)
        else:
            row_count= self.read_whole(self.data,self.f_descriptor) 
        self.data_size = row_count
        

    def get_variables(self)->dict[str:Decimal]:
        """
        Return the data for the current timestep.
       

        :return: Data corresponding to the current timestep or None if no more data have finished.
        """
        if self.current_timestep > self.data_size-1:
            return None  #No more data available
        index = self.current_timestep % self.MAX_ROWS if self.MAX_ROWS >0 else self.current_timestep
        return {self.data_titles[0]:self.data[index]}

    def reset(self)->None:
        """
        Reset the input module to its initial state.
        """
        self.current_timestep = 0
        self.f_descriptor.seek(0)  # Reset file pointer to the beginning
        if self.MAX_ROWS >0:
            self.read_chunk(self.data,self.f_descriptor)  # Re-read the input file, if was divided in chunks

    def get_variable_names(self)->list[str]:
        """
        Return the data titles provided by the input module.
       

        :return: String representing the data titles.
        """
        return self.data_titles

    def step(self)->int:
        """
        Advance to the next timestep.
        

        :return: Integer representing the new current timestep
        """
        #If MAX_ROWS is set, read next chunk when next index would loop back to zero (i.e we finished reading current chunk)
        self.current_timestep += 1
        if self.MAX_ROWS >0 and self.current_timestep % self.MAX_ROWS == 0:
            self.data_size+= self.read_chunk(self.data,self.f_descriptor,0)
        return self.current_timestep

    def assignHeader(self, header):
        """
        Add header (columns) names to read variables.
        Better called after first read, otherwise column names may be replaced with actual headers from file
        
        :param header: string (list of) representing new input
        """

        if  not isinstance(header,str):
            raise TypeError("Header must be a string type")
        self.data_titles[0]=header

    def init_memory(self)->None:
        """
        Initialize memory structures for chunked input module.
        """
        if self.MAX_ROWS >0:
            self.data = [0.0]*self.MAX_ROWS #Preallocate list with MAX_ROWS
        else :
            self.data = [] #Allocate only first element, will expand as needed

    def closeFile(self)->None:
        """
        Close file descriptor(s)
        """
        if self.f_descriptor and not self.f_descriptor.closed:
            self.f_descriptor.close()
    
