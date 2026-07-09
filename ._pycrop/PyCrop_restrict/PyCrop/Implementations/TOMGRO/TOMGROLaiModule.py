from decimal import Decimal
from PyCrop.Abstract.AbstractCropModules.AbstractLAIModule import AbstractLAIModule
from PyCrop.Abstract.Core.AbstractInputModule import STEP_GRANULARITY   
LAI_DEFAULT_PARAMS= {
    "L_0":Decimal("0.015"),
    "a":Decimal("0.001"),
    "b":Decimal("250000"),
    "c":Decimal("1.435"),
    "d":Decimal("3.6")
}

class TOMGROLaiModule(AbstractLAIModule):
    """
    TOMGRO LAI crop component implementation.
    Inherits from AbstractLAIModule. 
    Attributes:
        name (str): name of the crop component
        granularity (int): How many seconds a time step has. Default is DAILY (86400 seconds).
        params (dict): Dictionary containing component parameters. Must include:
            L_0 (Decimal): Initial LAI value
            a (Decimal): Parameter a for LAI calculation
            b (Decimal): Parameter b for LAI calculation
            c (Decimal): Parameter c for LAI calculation
            d (Decimal): Parameter d for LAI calculation
        state_variables (dict): Dictionary containing state variables. Includes:
            LAI (Decimal): Current LAI value
        Required Inputs:
            Nodes (int): Current node number
            DN (float/Decimal): Daily increment of nodes
    """

    def __init__(self,name:str="TOMGROLaiModule",granularity:int=STEP_GRANULARITY["DAILY"],params:dict={})->None:
        if not granularity == STEP_GRANULARITY["DAILY"]:
            raise ValueError("TOMGRO LAI module only supports DAILY granularity.")
        super().__init__(name,granularity,params)

    def change_params(self,params:dict)->None:
        """
        Change the TOMGRO LAI model parameters.
        

        :param params: Dictionary containing parameter names and values
        """
        if not isinstance(params,dict):
            raise TypeError("param argument must be a dictionary")
        if "L_0" not in params:
            raise ValueError("Missing required TOMGRO LAI parameter: L_0")
        if "a" not in params:
            raise ValueError("Missing required TOMGRO LAI parameter: a")
        if "b" not in params:
            raise ValueError("Missing required TOMGRO LAI parameter: b")
        if "c" not in params:
            raise ValueError("Missing required TOMGRO LAI parameter: c")
        if "d" not in params:
            raise ValueError("Missing required TOMGRO LAI parameter: d")
        if any(params[i] < 0 for i in ["L_0","b","c","d"]):
            raise ValueError("All parameters must be non-negative.")
        for i in params:
            if isinstance(params[i],float):
                self.params[i] = Decimal(str(params[i]))
            else:
                self.params[i] = Decimal(params[i])

    def step(self, input:list)->None:
        """
        Perform a simulation step for the TOMGRO LAI model.
        

        :param input: List containing curent Node number (int/Decimal) and Daily increment of nodes (float/Decimal/int) (DN)
        """
        if not isinstance(input,list): raise TypeError("Input must be a list")
        if len(input) <2 : raise ValueError("Input list must contain at least two elements")
        if len(input) >2:  print(f"Warning: More values provided as input for class {self.name} than needed. Only firts two will be used.")
        if not input[0]%1==0: raise TypeError("Current node number must be an Integer.")
        if input[0]< 0: raise ValueError("Current node number must be non-negative.")
        if not isinstance(input[1],(float,Decimal,int)): raise TypeError("Daily increment of nodes (DN) must be a number.")
        if input[1] < 0: raise ValueError("Daily increment of nodes (DN) must be non-negative.")
        N = Decimal(input[0])
        DN = Decimal(input[1]) if isinstance(input[1],(Decimal,int)) else Decimal(str(input[1]))
        a = self.params["a"]
        b = self.params["b"]
        c = self.params["c"]
        d = self.params["d"]
        DLAI=((b*d*(c-a)*Decimal(pow(N,(d-1))))/Decimal(pow(b+pow(N,d),2)))*DN
        if  DLAI < 0: raise ValueError("Computed DLAI must be non-negative.")
        self.state_variables["LAI"]+= DLAI

    def show_required_inputs(self):
        """
        Return a list of required input variable names.
        
        :return: List of required input variable names
        :rtype: list[str]
        """
        return ["Nodes","Delta_Nodes"]
    
    def get_variables(self)->dict[str:Decimal]:
        """
        Return the current state variables.

        :return: Current state variables
        :rtype: dict(str: Decimal)
        """
        return self.state_variables
    