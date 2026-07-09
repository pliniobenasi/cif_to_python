from decimal import Decimal
from PyCrop.Abstract.AbstractInputModules.AbstractChunkInputModule import AbstractChunkInputModule

class MFMCInputModule(AbstractChunkInputModule):
    """
    Class extending AbstractInputModule implementing Multi-File Multi-Column module for PyCrop.
    This class reads input data from a multiple files and provides methods to access the data.
    This class allows for per-file column-specific reading. 
    Input files must contain one or more data points per line. Column titles are mandatory.
    Time step advancement is handled internally, starting from 0. This means that the order of operation should be get_variables() followed by step().
    Attributes:
        current_timestep (int): The current timestep being processed.
        MAX_ROWS (int): Maximum number of rows to store from input. Default is 2048.
        name (str): Name of the input module.
        granularity (int): How many seconds a time step has. Default is HOURLY (3600 seconds).
        data (list): List of list of lists containing data for each column, for each input files.
        data_size (int): Size of the data read from the input file.
        data_titles (list): Data headers read from the input file.
        f_descriptor: File descriptor for the input file. 
        file_num: int: Number of files to read from.
        columns: List lists containinf colum's indexes to read per file
    """
    file_num:int = 0
    columns:list=[]

    def __init__(self, name = "MFMCInputModule", MAX_ROWS = 2048, granularity = 3600):
        super().__init__(name, MAX_ROWS, granularity)

    def read_input(self, input):
        """
        Read input data from a list file. All columns are read
        If MAX_ROWS >0, reads up to MAX_ROWS rows, otherwise reads the whole file.
        If the first row contains strings, they are treated as the columns titles.
        
        :param input: List with strings representing the file paths
        """
        if not isinstance(input,list[str]):
            raise TypeError("Input file is not a list of string")
        if not input:
            raise ValueError("Input file list is empty")
        self.file_num = len(input)
        self.columns=None
        self.f_descriptor = []*self.file_num #initialize file descriptors
        self.data_titles=[]*self.file_num #initialize list of titles

        offsets=[]*self.file_num

        # Iterate over files, to get number of columns for each file
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
            if all(isinstance(item.strip(),str) for item in first_row):
                for i,col_title in enumerate(first_row):
                    self.data_titles[i]= col_title.strip() #Assign column titles
                offsets[i]=1
            else:
                self.data_titles[i] = ["Var_"+str(i+1) for i in range(len(first_row))]
                self.f_descriptor[i].seek(0) #return back if first row does not have title
                offsets[i]=0
        self.init_memory()
        row_count=0
        for i in len(self.file_descriptors):
            if self.MAX_ROWS >0:
              row_count =self.read_chunk(self.data[i],self.f_descriptor[i],offsets[i]) #Start reading from row 1 (after title)
            else:
              row_count= self.read_whole(self.data[i],self.f_descriptor[i]) 
            self.data_size = min(row_count,self.data_size) if self.data_size >0 else row_count


    def read_input_columns(self, input,col=[]):
        """
        Read input data from a list file. Only col columns are read.
        If MAX_ROWS >0, reads up to MAX_ROWS rows, otherwise reads the whole file.
        If the first row contains strings, they are treated as the columns titles.
        
        :param input: List with strings representing the file paths

        :param col: List of lists representing indexes for columns to read for each file, starting at zero

        """
        if not col:
            self.read_input(input)
            return
        if not isinstance(input,list[str]):
            raise TypeError("Input file is not a list of string")

        if not isinstance(col,list):
            raise TypeError("Col must be a list representing columns to read")

        self.columns=col
 
        self.file_descriptors = []*self.file_num #initialize file descriptors
        self.data_titles=[]*self.file_num #initialize list of titles

        offsets=[]*self.file_num

        # Iterate over files, to get number of columns for each file
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
            col_nums = len(first_row)
            if not  isinstance(col[i],list):
                raise TypeError("Columns indexes must be specified for each file as a list")
            if len(col[i]) > len(col_nums):
                raise ValueError(f"Specified columns for file {file} are more than actual columns in the file")
            if max(col[i])> len(col_nums):
                raise ValueError(f"Maximum column index for file {file} is bigger than actual columns in the file")

            if all(isinstance(item.strip(),str) for item in first_row):
                for i in range(len(col[i])):
                    self.data_titles[i]= first_row[col[i]].strip() #Assign column titles
                offsets[i]=1
            else:
                self.data_titles[i] = [f"File_{file}_Var_{j}" for j in range(len(col[i]))]
                self.f_descriptor[i].seek(0) #return back if first row does not have title
                offsets[i]=0

        self.init_memory()
        row_count=0
        for i in len(self.file_descriptors):
            if self.MAX_ROWS >0:
              row_count =self.read_chunk(self.data[i],self.f_descriptor[i],offsets[i],col[i]) #Start reading from row 1 (after title)
            else:
              row_count= self.read_whole(self.data[i],i,col[i]) 
            self.data_size = min(row_count,self.data_size) if self.data_size >0 else row_count
 
    def get_variables(self)->dict[str:Decimal]:
        """
        Return the data for the current timestep.
       

        :return: Data corresponding to the current timestep or None if no more data have finished.
        """
        if self.current_timestep > self.data_size:
            return None  #No more data available
        index = self.current_timestep % self.MAX_ROWS if self.MAX_ROWS >0 else self.current_timestep
        return {self.data_titles[i][j]:self.data[i][j][index] for i in range(len(self.f_descriptor)) for j in range(len(self.data_titles[i])) }

    def reset(self)->None:
        """
        Reset the input module to its initial state.
        """
        self.current_timestep = 0
        for i in range(self.file_num):
            self.f_descriptor[i].seek(0)  # Reset file pointer to the beginning
            if self.MAX_ROWS >0:
                self.read_chunk(self.data[i],self.f_descriptor[i],0,self.columns)  # Re-read the input file, if was divided in chunks

    def get_variable_names(self)->list[str]:
        """
        Return the data titles provided by the input module.
        

        :return: List of string representing the data titles.
        """
        return [j for i in range(self.file_num) for j in self.data_titles[i]]
    
    def assignHeader(self, header):
        """
        Add header (columns) names to read variables.
        Better called after first read, otherwise column names may be replaced with actual headers from file
        
        :param header: list of lists, each one storing headers for a specific file
        """

        if  not isinstance(header,list):
            raise TypeError("Header must be a list of lists, one for each file and for each column")
        for i,l in enumerate(header):
            if  not isinstance(l,list[str]):
                raise TypeError("Header must be a list of lists, one for each file and for each column")            
            if not l:
                raise ValueError("Header has a empty list")
            if not len(l)==len(self.data_titles[i]):
                raise ValueError(f"Header list {i} lenght does not match corresponding class headers")
            for j,title in enumerate(l):
                self.data_titles[i][j]=title

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
                advance=min(advance,self.read_chunk(self.data[i],self.f_descriptor[i],self.current_timestep,self.columns))
            self.data_size+= advance
        return self.current_timestep
    
    def closeFile(self):
        for i in self.f_descriptor:
            i.close()

    def init_memory(self)->None:
        """
        Initialize memory structures for chunked input module. Also initializes data titles. 
        self.data is a cubic list: each list refers to a single file, and for each file we have a list of columns, each one being a list of data.
        """
        self.data = []*self.file_num #Initialize list of data per file
        if self.MAX_ROWS >0:
            for i in range(self.file_num):
                self.data[i] = []*len(self.data_titles[i]) #Preallocate lists for each column
                for j in range(len(self.data_titles[i])):
                    self.data[i][j]=[0.0]*self.MAX_ROWS
        else :
            for i in range(self.file_num):
                self.data[i] = []*len(self.data_titles[i]) #Preallocate lists for each column
                for j in range(len(self.data_titles[i])):
                    self.data[i][j]=[0.0]

    
