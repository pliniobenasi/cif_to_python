from decimal import Decimal
from PyCrop.Abstract.AbstractCropModules.AbstractNodeModule import AbstractNodeModule
from PyCrop.Abstract.Core.AbstractInputModule import STEP_GRANULARITY   

NODES_DEFAULT_PARAMS={"N_0":Decimal("5"),
        "Nm":Decimal("0.66"),
        "T0":Decimal("5"),
        "T1":Decimal("14"),
        "T2":Decimal("28"),
        "T3":Decimal("42")
}


class TOMGRONodesModule(AbstractNodeModule):
    """
    TOMGRO crop component implementation.
    Inherits from AbstractNodeModule.
    Attributes:
        name (str): name of the crop component
        granularity (int): How many seconds a time step has. Default is DAILY (86400 seconds).
        name (str): name of the crop component
        granularity (int): How many seconds a time step has. Default is HOURLY (3600 seconds).
        params (dict): Dictionary containing component parameters. Must include:
            N_0 (Decimal): Initial node number
            Nm (Decimal): Maximum node appearance rate per day
            T0 (Decimal): Lower sub-optimal temperature for node development 
            T1 (Decimal): Lower optimal temperature for node development
            T2 (Decimal): Upper optimal temperature for node development
            T3 (Decimal): Maximum sub-temperature for node development
        K0, C0, K1, C1, K2, C2 (Decimal): Are Coefficients computed from params    
        state_variables (dict): Dictionary containing state variables. Includes:
            Nodes (int): Current node number
            DN (Decimal): Daily increment of nodes
        Required Inputs:
            T_avg (float/Decimal): Daily average temperature
    """
    
    def __init__(self,name:str="TOMGRONodesModule",granularity:int=STEP_GRANULARITY["DAILY"],params:dict={})->None:
        if not granularity == STEP_GRANULARITY["DAILY"]:
            raise ValueError("TOMGRO Nodes module only supports DAILY granularity.")
        super().__init__(name,granularity,params)
        self.state_variables["DN"]= Decimal(0)
    
    def change_params(self,params:dict)->None:
        """
        Change the TOMGRO model parameters.
        

        :param params: Dictionary containing parameter names and values
        """
        if not isinstance(params,dict):
             raise TypeError("Input parameters must be a dictionary")
        if  not all(i in params for i in["N_0", "Nm","T0","T1","T2","T3"]):
            raise ValueError("Missing required TOMGRO parameters")
        if not all(isinstance(params[i],(float,Decimal,int)) for i in["N_0", "Nm","T0","T1","T2","T3"]):
            raise TypeError("All parameters must be numbers (int, float or Decimal).")
        if not(params["T0"] < params["T1"] < params["T2"] < params["T3"]):
            raise ValueError("Temperature parameters must satisfy T0 < T1 < T2 < T3")
        for i in params:
            self.params[i] = Decimal(params[i]) if isinstance(params[i],(int,Decimal)) else Decimal(str(params[i]))
        self.K0 = Decimal(0.55) / (self.params["T1"] - self.params["T0"])
        self.C0 = -self.K0 * self.params["T0"]
        self.K1 = Decimal(0.45) / (self.params["T2"] - self.params["T1"])
        self.C1 = Decimal(0.55) - self.K1 * self.params["T1"]
        self.K2 = Decimal(-1.0) / (self.params["T3"] - self.params["T2"])
        self.C2 = -self.K2 * self.params["T3"]
        
        

    def step(self,input:list)->None:
        """
        Advance the TOMGRO model by one timestep.
        

        :param input: List containing only Daily average temperature
        """
        if not isinstance(input,list):
            raise TypeError("Input must be a list")
        if not isinstance(input[0],(float,Decimal,int)):
            raise TypeError("Input value must be a number (int, float or Decimal).")
        if len(input) > 1:
            print(f"Warning: Multiple values provided as input for class {self.name}. Only firts one will be used.")
        T_in = Decimal(input[0]) if isinstance(input[0],(Decimal,int)) else Decimal(str(input[0]))
        dN=Decimal(0)
        if T_in <= self.params["T0"] or T_in >= self.params["T3"]:
            dN =Decimal(0)
        elif T_in > self.params["T0"] and T_in < self.params["T1"]:
                dN =self.params["Nm"]*(self.C0+self.K0*T_in)
        elif T_in >= self.params["T1"] and T_in <= self.params["T2"]:
                dN =self.params["Nm"]*(self.C1+self.K1*T_in)
        elif T_in > self.params["T2"] and T_in < self.params["T3"]:
                dN =self.params["Nm"]*(self.C2+self.K2*T_in)
        assert dN >= 0, "Computed daily node increment must be non-negative."
        self.state_variables["DN"]= dN
        self.state_variables["Nodes"]+= dN

    def show_required_inputs(self)->list:
        """
        Return a list of required input variable names for the TOMGRO model.
        

        :return: List of required input variable names
        """
        return ["Daily_Average_Temperature"]
    
    def get_variables(self)->dict[str:Decimal]:
         return {"Nodes": int(self.state_variables["Nodes"]), "DN": self.state_variables["DN"]}
    
    def reset(self)->None:
        """
        Reset the Module to its initial state.
        """
        super().reset()
        self.state_variables["DN"] = Decimal(0)