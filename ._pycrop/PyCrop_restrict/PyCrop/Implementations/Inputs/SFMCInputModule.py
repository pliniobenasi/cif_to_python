from decimal import Decimal, InvalidOperation
from PyCrop.Abstract.AbstractInputModules.AbstractChunkInputModule import AbstractChunkInputModule

class SFMCInputModule(AbstractChunkInputModule):
    """
    Class extending AbstractInputModule implementing Single-File Multi-Column module for PyCrop.
    This class reads input data from a single file and provides methods to access the data.
    This class allows for column-specific reading. 
    Input file must contain one or more data points per line. Column titles are mandatory.
    Time step advancement is handled internally, starting from 0. This means that the order of operation should be get_variables() followed by step().
    Attributes:
        current_timestep (int): The current timestep being processed.
        MAX_ROWS (int): Maximum number of rows to store from input. Default is 2048.
        name (str): Name of the input module.
        granularity (int): How many seconds a time step has. Default is HOURLY (3600 seconds).
        data (list): List of list containing data for each column of input files.
        data_size (int): Size of the data read from the input file.
        data_titles (list): Data headers read from the input file.
        f_descriptor: File descriptor for the input file. 
        columns: List of colum's indexes to read
    """


    def __init__(self,name:str="SFMCInputModule",MAX_ROWS:int=2048,granularity:int=3600)->None:
        super().__init__(name,MAX_ROWS,granularity)
        self.columns=()
        self.data_titles = ["Var_1"]

    def read_input(self, input, *args)->None:
        """
        Read input data from a file. All columns are read.
        If MAX_ROWS >0, reads up to MAX_ROWS rows, otherwise reads the whole file.
        If the first row contains strings, they are treated as the column titles.

        :param input: String representing the file path
        :param args: List of indexes for columns to read, starting at zero
        """
        if not isinstance(input,str):
            raise TypeError ("Input must be a string representing the file path")

        #Check if file exists and is readable
        try:
            self.f_descriptor = open(input,'r')
        except Exception as e:
            raise IOError(f"Error opening file {input}: {e}")
        if self.f_descriptor is None:
            raise IOError("File descriptor is None after attempting to open file")
        #Check first row for column titles
        first_row = self.f_descriptor.readline().split(',')

        if not args:
            print("Warning: No columns specified for reading. All will be read.")
            args = tuple(range(len(first_row)))  # Default to reading all columns if no columns specified
        self.columns=args
        col_nums = len(first_row)
        print(col_nums, args)
        if  len(args) > col_nums:
            raise ValueError("Specified columns are more than actual columns in the file")
        if  max(args) > col_nums:
            raise ValueError("Maximum column index is bigger than actual columns in the file")

        self.data_titles = ["Var_"+str(i+1) for i in range(len(args))]
        self.init_memory()
        
        row_count=0
        try:
            for i in range(len(args)):
                self.data[i][0]= Decimal(first_row[args[i]].strip())
            row_count = 1 #If first row is data, we have already read one row
        except InvalidOperation:
            print("First row treated as column title: ", first_row)
            self.data_titles = [first_row[i].strip() for i in args] #Assign column title
 
        if self.MAX_ROWS >0:
            row_count =self.read_chunk_columns(self.data,self.f_descriptor,row_count,args) #Start reading from row 1 (after title)
        else:
            row_count= self.read_whole_columns(self.data,self.f_descriptor,args) 
        self.data_size = row_count


    def get_variables(self)->dict[str:Decimal]:
        """
        Return the data for the current timestep.
       

        :return: Data corresponding to the current timestep or None if no more data have finished.
        """
        if self.current_timestep > self.data_size-1:
            return None  #No more data available
        index = self.current_timestep % self.MAX_ROWS if self.MAX_ROWS >0 else self.current_timestep
        return {self.data_titles[i]: self.data[i][index] for i in range(len(self.data_titles))}


    def reset(self)->None:
        """
        Reset the input module to its initial state.
        """
        self.current_timestep = 0
        self.f_descriptor.seek(0)  # Reset file pointer to the beginning
        if self.MAX_ROWS >0:
            self.read_chunk_columns(self.data,self.f_descriptor,0,self.columns)  # Re-read the input file, if was divided in chunks

    def get_variable_names(self)->list[str]:
        """
        Return the data titles provided by the input module.
       

        :return: List of tring representing the data titles.
        """
        return self.data_titles
    
    def assignHeader(self, header):
        """
        Add header (columns) names to read variables.
        Better called after first read, otherwise column names may be replaced with actual headers from file
        
        :param header: string (list of) representing new input
        """
        if len(self.data_titles) == 1:
            if isinstance(header,str):
                header = [header]  # Convert to list if a single string is provided
            else:
                raise TypeError("Header must be a string or a list of strings")
        if  not isinstance(header,list):
            raise TypeError("Header must be a list of strings, one for each colum of file")
        if not header:
            raise ValueError("Header list is empty")
        if not len(header)==len(self.data_titles):
            raise ValueError("Header list lenght does not match current class headers")
        for i,title in enumerate(header):
            self.data_titles[i]=title


    def step(self)->int:
        """
        Advance to the next timestep.
        

        :return: Integer representing the new current timestep
        """
        self.current_timestep += 1
        #If MAX_ROWS is set, read next chunk when next index would loop back to zero (i.e we finished reading current chunk)
        if self.MAX_ROWS >0 and self.current_timestep % self.MAX_ROWS == 0:
                self.data_size+= self.read_chunk_columns(self.data,self.f_descriptor,0,self.columns)
        return self.current_timestep
    
    def closeFile(self):
        if not self.f_descriptor:
            return
        if self.f_descriptor and not self.f_descriptor.closed:
            self.f_descriptor.close()

    def init_memory(self):
        """
        Initialize memory structures for chunked input module.
        """
        self.data = [[] for _ in range(len(self.data_titles))]
        if self.MAX_ROWS > 0:
            for i in range(len(self.data_titles)):
                self.data[i]=[0]*self.MAX_ROWS #Initialize chunks for data
        else:
            for i in range (len(self.data_titles)):
                self.data[i]=[] #Initialize only first value

