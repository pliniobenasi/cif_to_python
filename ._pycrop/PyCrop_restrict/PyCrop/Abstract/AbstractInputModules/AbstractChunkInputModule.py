from decimal import Decimal,InvalidOperation
from PyCrop.Abstract.Core.AbstractInputModule import AbstractInputModule
from abc import abstractmethod

class AbstractChunkInputModule(AbstractInputModule):
    """
    Abstract base class for chunked input modules in PyCrop.
    Defines the interface for reading input data in chunks.
    Inherits from AbstractInputModule.
    Attributes:
        MAX_ROWS (int): Maximum number of rows to store from input. Default is 2048. Values <=0 mean no limit.
        f_descriptor: File descriptor for the input file.

    """

    def __init__(self, name: str = "AbstractChunkInputModule", MAX_ROWS: int = 2048, granularity: int = 3600) -> None:
        super().__init__(name, granularity)
        self.MAX_ROWS:int = MAX_ROWS
        self.f_descriptor = None

    @abstractmethod
    def init_memory(self) -> list:
        """
        Initialize memory structures for chunked input module.
        """
        raise NotImplementedError("Subclasses must implement this method")

    def read_chunk(self,data:list,fd,offset:int=0)->int:
        """
        Read a chunk of data from the input file fd up to MAX_ROWS and put it into data list.
        If row contains non-numeric data, skip that row and log a warning.
        Only one data per row.

        :param data: List to store the read data.
        :param fd: File descriptor to read from.
        :param offset: Integer specifying the starting row offset. Default is 0.
        
        :return: Number of rows read.
        """
        row_count = offset
        
        if not fd:
            raise IOError("File descriptor is None")
        if not isinstance(data,list):
            raise TypeError("data must be a list")
        if not isinstance(offset,int):
            raise TypeError("offset must be an integer")
        if offset <0:
            raise ValueError("Offset must be a non-negative integer")
        while row_count < self.MAX_ROWS:
            line = fd.readline()
            if not line:
                break  # End of file reached
            try:
                data[row_count] = Decimal(line.strip())
            except InvalidOperation:
                #todo: log warning
                print(f"Warning: Non-numeric data encountered at row {row_count+1+self.current_timestep}. Skipping.")
                row_count -= 1  # Adjust row_count to not count this row
            row_count += 1   
        return row_count
    

    def read_chunk_columns(self,data:list,fd,offset:int=0,read_col:list=None)->int:
        """
        Read a chunk of data from the input file fd up to MAX_ROWS and put it into data list.
        Only col columns are read. If col is empty or None, no column is skipped.
        If row contains non-numeric data, skip that row and log a warning.

        :param data: List of lists where to store the read data.
        :param fd: File descriptor to read from.
        :param offset: Integer specifying the starting row offset. Default is 0.
        :param read_col: List specifying which column to keep when multiple data per row. Default is None (no skip).
        
        :return: Number of rows read.
         """
        row_count = offset
        if read_col==None or not read_col: #Single value case
            print("Warning: read_col is empty or None. Reading all columns.Next time use read_chunk instead")
            return self.read_chunk(data,fd,offset)
        if not fd:
            raise IOError("File descriptor is None")
        if not isinstance(data,list):
            raise TypeError("data must be a list")
        if not isinstance(offset,int):
            raise TypeError("offset must be an integer")
        if offset <0:
            raise ValueError("Offset must be a non-negative integer")
        if  len(data[0]) < self.MAX_ROWS:
            raise ValueError("data list must be at least MAX_ROWS long")
        
        while row_count < self.MAX_ROWS:
            line = fd.readline()
            if not line:
                break  # End of file reached
            values=line.split(",")
            if not len(values)==len(read_col):
                raise IOError(f"Error: row {row_count+1+self.current_timestep} has too few data")
            for i,val in enumerate(read_col):
                try:
                    data[i][row_count] = Decimal(values[val].strip())
                except InvalidOperation:
                    #todo: log warning
                    print(f"Warning: Non-numeric data encountered at row {row_count+1+self.current_timestep}, column {i+1}. Skipping row.")
                    row_count -= 1  # Adjust row_count to not count this row
            row_count += 1        
        return row_count

    def read_whole(self,data:list,fd)->int:
        """
        Read the entire input file into memory.
        If row contains non-numeric data, skip that row and log a warning.

        :param data: List to store the read data.
        :param fd: File descriptor to read from.

        :return: Number of rows read.
        """
        if not fd:
            raise IOError("File descriptor is None")
        if not isinstance(data,list):
            raise TypeError("data must be a list")
        row_count = 0
        for line in fd:
            try:
                data.append(Decimal(line.strip()))
            except InvalidOperation:
                #todo: log warning
                print(f"Warning: Non-numeric data encountered at row {row_count+1}. Skipping.")
                row_count -=1
            row_count += 1   
        return row_count
    
    def read_whole_columns(self,data:list,fd,read_col:list=None)->int:
        """
        Read the entire input file into memory. Only col columns are read.
        If row contains non-numeric data, skip that row and log a warning.
        read_col indicates which column to keep.

        :param data: List of lists where to store the read data.
        :param fd: File descriptor to read from.
        :param read_col: List specifying which column to keep when multiple data per row. Default is None (no skip).

        :return: Number of rows read.
        """
        if read_col==None or not read_col: #Single value case
            print("Warning: read_col is empty or None. Reading all columns.Next time use read_whole instead")
            return self.read_whole(data,fd)
        if not fd:
            raise IOError("File descriptor is None")
        if not isinstance(data,list):
            raise TypeError("data must be a list")
        row_count = 1
        for line in fd:
            values=line.split(",")
            if len(values)<len(self.data_titles):
                raise IOError(f"Error: row {row_count+1} has too few data")
            for i,val in enumerate(read_col):
                try:
                    data[i].append(Decimal(values[val].strip()))
                except InvalidOperation:
                    #todo: log warning
                    print(f"Warning: Non-numeric data encountered at row {row_count+1}, column {i}. Putting 0 instead.")
                    data[i].append(Decimal('0'))
            row_count += 1
        return row_count-1