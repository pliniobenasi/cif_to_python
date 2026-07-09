from decimal import Decimal
from PyCrop.Abstract.AbstractInputModules.AbstractChunkInputModule import AbstractChunkInputModule

class MFSCInputModule(AbstractChunkInputModule):
    """
    Class extending AbstractInputModule implementing Multi-File Single-Column input module for PyCrop.
    This class reads input data from a multiple file and provides methods to access the data.
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
        data_titles (list): Data headers read from the input files.
        f_descriptor: File descriptor for the input files.
        file_num: int: Number of files to read from.
    """
    file_num:int = 0

    def __init__(self,name:str="MFSCInputModule",MAX_ROWS:int=2048,granularity:int=3600)->None:
        super().__init__(name,MAX_ROWS,granularity)


    def read_input(self, input:list)->None:
        """
        Read input data from a list file.
        If MAX_ROWS >0, reads up to MAX_ROWS rows, otherwise reads the whole file.
        If the first row contains a string, it is treated as the column title.
        

        :param input: List with strings representing the file paths
        """
        if not isinstance(input,list): 
            raise TypeError("Input must be a list of  file path")
        if not input:
            raise ValueError("Input file list is empty")
        self.file_num = len(input)

        self.init_memory() #Initialize data storage in memory

        # Iterate over files, following same logic as SFSCInputModule
        for (i,file) in zip(range(self.file_num),input):
            #Check if file exists and is readable
            try:
                self.f_descriptor[i] = open(file,'r')
            except Exception as e:
                raise IOError(f"Error opening file {file}: {e}")
            if not self.f_descriptor[i] :
                raise IOError("File descriptor is None after attempting to open file")
            
            #Check first row for column titles
            first_row = self.f_descriptor[i].readline().split(',')
            if not len(first_row) == 1:
                raise IOError("MFSCInputModule only supports single column input files")

            if isinstance(first_row[0],str):
                self.data_titles[i] = first_row[0].strip() #Assign column title
            else:
                try:
                    self.data[i][0]= Decimal(first_row[0].strip()) #If no title, first row is data
                except ValueError:
                    raise ValueError("Row must be a numeric data") 
            #Read data rows
            row_count=0
            if self.MAX_ROWS >0:
                row_count =self.read_chunk(self.data[i],self.f_descriptor[i],1) #Start reading from row 1 (after title)
            else:
                row_count= self.read_whole(self.data[i],self.f_descriptor[i]) 
            #Update data_size to reflect total rows read across all files
            self.data_size = min(row_count,self.data_size) if self.data_size >0 else row_count
        

    def read_input_columns(self,input,col=[])->None:
        """
        Read input data from a file. Only col columns are read.

        :param input: String representing the file path
        
        :param col: List of indexes for columns to read, starting at zero
        """
        if not col:
            self.read_input(input)
        else: raise NotImplementedError("MFSCInputModule does not support column-specific reading.")
    

    def get_variables(self)->dict[str:Decimal]:
        """
        Return the data for the current timestep.
        

        :return: Data corresponding to the current timestep or None if no more data have finished.
        """
        if self.current_timestep > self.data_size:
            return None  #No more data available
        index = self.current_timestep % self.MAX_ROWS if self.MAX_ROWS >0 else self.current_timestep
        return {self.data_titles[i]:self.data[i][index] for i in range(self.file_num)}

    def reset(self)->None:
        """
        Reset the input module to its initial state.
        """
        self.current_timestep = 0
        for i in range(self.file_num):
            self.f_descriptor[i].seek(0)  # Reset file pointer to the beginning
            if self.MAX_ROWS >0:
                self.read_chunk(self.data[i],self.f_descriptor[i])  # Re-read the input file, if was divided in chunks

    def get_variable_names(self)->list[str]:
        """
        Return the data titles provided by the input module.
        

        :return: List of string representing the data titles.
        """
        return self.data_titles
    
    def assignHeader(self, header):
        """
        Add header (columns) names to read variables.
        Better called after first read, otherwise column names may be replaced with actual headers from file
        
        :param header: string (list of) representing new input
        """

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
            advance=self.read_chunk(self.data[0],self.f_descriptor[0],self.current_timestep)
            for i in range(1,self.file_num):
                advance=min(advance,self.read_chunk(self.data[i],self.f_descriptor[i],self.current_timestep))
            self.data_size+= advance
        return self.current_timestep

    def closeFile(self):
        for i in self.f_descriptor:
            i.close()

    def init_memory(self)->None:
        """
        Initialize memory structures for chunked input module. Also initializes data titles. 
        self.data is a list of lists, each sublist corresponds to a file.
        """
        self.data = [[] for _ in range(self.file_num)]
        self.file_descriptors = []*self.file_num
        if self.MAX_ROWS >0:
            for i in range(self.file_num):
                self.data[i] = [0.0]*self.MAX_ROWS #Preallocate lists with MAX_ROWS
                self.data_titles = ["File_"+str(i+1)]*self.file_num
        else :
            for i in range(self.file_num):
                self.data[i] = [0.0] #Allocate only first element, will expand as needed
                self.data_titles = ["File_"+str(i+1)]*self.file_num

    
