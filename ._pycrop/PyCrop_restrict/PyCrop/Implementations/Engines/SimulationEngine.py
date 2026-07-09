from math import gcd
from PyCrop.Abstract.Core.AbstractSimulationEngine import AbstractSimulationEngine
from PyCrop.Abstract.Core.AbstractInputModule import AbstractInputModule,STEP_GRANULARITY
from PyCrop.Abstract.Core.AbstractCropModule import AbstractCropModule
from PyCrop.Abstract.Core.AbstractModule import AbstractModule
class SimulationEngine(AbstractSimulationEngine):
    """
    Class implementing a simulation engine for crop growth. Extends AbstractSimulationEngine.
    Attributes:
        input (list[AbstractInputModule]): The input modules for the simulation.
        modules (list[AbstractCropModule]): List of crop modules in the simulation.
        name (str): Name of the simulation engine
        min_granularity (int): minimum step granualrity
        clock (int): internal simulation clock. Computed as GCD of all module granularities (min step = 1 second)
    """
    def __init__(self, name="SimulationEngine"):
        super().__init__(name)
        self.min_granularity = 0
        self.clock = 0
        self.system_variables_history = {self.name+"_Clock": [0]} #List of system variables at each timestep, used to store results of the simulation
        self.system_variables = {self.name+"_Clock":0} #Current values of system variables, updated at each timestep. Keys are variable names, values are variable values. This is the main data structure used to exchange data between modules and store results.

    def add_input_module(self, input_modules):
        """
        Add one or more input modules for the simulation engine.
        Can not add two input modules with the same name

        :param input_module: An instance of AbstractInputModule or a list of AbstractInputModules
        """
        if not isinstance(input_modules,AbstractInputModule) and \
             not isinstance(input_modules,list):
            raise TypeError("add_input_module method only supports AbstractInputModule or a list of AbstractInputModules")
        if isinstance(input_modules,list) and not all(isinstance(i,AbstractInputModule) for i in input_modules):
            raise TypeError("add_input_module method only supports AbstractInputModule or a list of AbstractInputModules")
        if isinstance(input_modules,AbstractInputModule):
            self.add_one(input_modules,self.inputs)

        else: 
            for i in input_modules:
                self.add_one(i,self.inputs)

    def add_module(self, modules):
        """
        Add one or more crop modules to the simulation engine.
        Can not add two modules with the same name

        :param modules: An instance of AbstractCropModule r a list of AbstractCropModule instances
        """
        if not isinstance(modules,AbstractCropModule) and \
            not isinstance(modules,list):
            raise TypeError("Add_modules method only supports AbstractCropModule or a list of AbstractCropModules")
        if isinstance(modules,AbstractCropModule):
            self.add_one(modules,self.modules)
            self.input_bindings[modules.get_name()]={}
        else : 
            for module in modules:
               self.add_one(module,self.modules)
               self.input_bindings[module.get_name()]={}

    
    def add_one(self,module:AbstractModule,target):
        """
        Add one module to specified target.
        Function checks if module is duplicate, and update system granularity accordingly
        Module's variables are added to system' own variables
        
        :param module: The module to add to the system
        :param target: Which dictionary update with the module
        """
        if module.get_name() in target:
            raise ValueError(f"Module {module.get_name()} already present. Maybe the name is duplicated")
        target[module.get_name()]=module
        if self.min_granularity ==0:
            self.min_granularity = module.granularity
        else : self.min_granularity = gcd(self.min_granularity,module.granularity)
        for key,item in module.get_variables().items():
            self.system_variables[module.get_name()+"_"+key]=item #Add module variable to system
            self.system_variables_history[module.get_name()+"_"+key]=[item] #Initialize variable history for results storage


    def bindVariables(self,provider_module:str, input_variables, receiver_module:str, receiver_module_input_name):
        """
        Bind variables provided as inputs to receiver_module(s)
        
        :param provider_module: Name of the module providing the variables. This is used to check that the variables are present in the system variables.
        :param input_variables: Variable name or a list of variable names
        :param receiver_module: Name of the module which will use the variables as inputs
        :param receiver_module_input_name: Name or list of the variable as expected by the receiver module. This is used to map system variables to module input variables.
        """
        if not isinstance(provider_module,str):
            raise TypeError("Provider module name must be a string")
        if not isinstance(receiver_module,str):
            raise TypeError("Receiver module name must be a string")
        if isinstance(input_variables,str) and isinstance(receiver_module_input_name,str):
            self.bindOne(provider_module,input_variables,receiver_module,receiver_module_input_name)
        elif isinstance(input_variables,list) and isinstance(receiver_module_input_name,list):
            if len(input_variables) != len(receiver_module_input_name):
                raise ValueError("Input variables and receiver module input names must have the same length")
            for var, input_name in zip(input_variables, receiver_module_input_name):
                self.bindOne(provider_module,var,receiver_module,input_name)
        else:
            raise TypeError("Input variables and receiver module input names must be both strings or both lists of the same length")

    def bindOne(self,provider_module:str, input_variable:str, receiver_module:str, receiver_module_input_name:str):
        """
        Bind one variable to a receiver module
        
        :param provider_module: Name of the module providing the variable. This is used to check that the variable is present in the system variables.
        :param input_variable: The input variable name
        :type input_variable: str
        :param receiver_module: Name of the module which will use the variable
        :type receiver_module: str
        :param receiver_module_input_name: Name of the variable as expected by the receiver module. This is used to map system variables to module input variables.
        :type receiver_module_input_name: str
        """
        if provider_module not in self.modules and provider_module not in self.inputs and provider_module != self.name:
            raise ValueError("Provider module not present in the system")
        if provider_module+"_"+input_variable not in self.system_variables:
            raise ValueError("Variable not present as system variable")
        if receiver_module not in self.modules:
            raise ValueError("Target module not present in the system")
        if receiver_module_input_name not in self.modules[receiver_module].show_required_inputs():
            raise ValueError("Receiver module does not have the specified input variable")
        self.input_bindings[receiver_module][receiver_module_input_name]=provider_module+"_"+input_variable

    def run(self, save_every=1)->None:
        """
        Run the simulation with the given parameters.
        
        :param save_every: The number of timesteps where we'll save the data (1 = every timesteps, 2 = every 2 timesteps,.. and so on)
        """
        self.run_till_timestep(-1, save_every)
        

    def run_till_timestep(self, timestep:int, save_every:int=1)->None:
        """
        Run the simulation until a specific timestep, expressed in seconds.

        :param timestep: The timestep until which to run the simulation. If timestep < 0 the simulation run unil input modules have no more data.
        :type timestep: int
        
        :param save_every: The number of timesteps where we'll save the data (1 = every timesteps, 2 = every 2 timesteps,.. and so on)
        :type save_every: int
        """
        if not isinstance(timestep,int):
            raise TypeError("Timestep must be an integer")
        if timestep ==0:
            return #No simulation to run
        if timestep >0 and timestep < self.min_granularity:
            raise ValueError("Timestep must be greater than current minimum granularity")
            
        
        
        simulation_run=True
        step_counter=0
        while simulation_run :
            step_counter+=1 # increment the number of step, to know when it's time to store data
            #1) Collect input data from input modules in system_variables
            for input_module in self.inputs:
                input_data = self.inputs[input_module].get_variables()
                if not input_data:
                    simulation_run=False #At leas one input module has no more data to provide -> stop simulation
                    break
                for key,item in input_data.items():
                    self.system_variables[input_module+"_"+key]=item #Input data collected
                    if step_counter % save_every == 0:
                    	self.system_variables_history[input_module+"_"+key].append(item) #Store variable history
            if not simulation_run:
                break
            #2) Update crop modules
            for module_name in self.modules:
                module = self.modules[module_name]
                if self.clock % module.granularity !=0:
                    continue #Module does not step at this clock tick
                #Prepare input data for the module
                input_data = []
                module_inputs = self.modules[module_name].show_required_inputs()
                for var_name in module_inputs:
                    input_data.append(self.system_variables[self.input_bindings[module_name][var_name]]) #Map system variables to module input variables
                #Update module with input data
                module.step(input_data)
            #3) Update Input Modules            
            self.clock +=self.min_granularity
            if step_counter % save_every == 0:
            	self.system_variables_history[self.name+"_Clock"].append(self.clock) #Store clock history
            self.system_variables[self.name+"_Clock"]=self.clock #Update system variable clock
            for input_module in self.inputs:
                clock=self.inputs[input_module].step()
                #5) Advance clock
                if not self.clock == clock*self.inputs[input_module].granularity:
                    raise ValueError("Input module step returned inconsistent clock value")
            #4) Collect output data from crop modules into system_variables
            for module_name in self.modules:
                module = self.modules[module_name]
                for key,item in module.get_variables().items():
                    self.system_variables[module_name+"_"+key]=item #Module data collected
                    if step_counter % save_every == 0:
                    	self.system_variables_history[module_name+"_"+key].append(item) #Store variable history
            if timestep >0 and self.clock >= timestep:
                simulation_run=False #Reached target timestep
    
    def get_results(self)->dict:
        """
        Get the results of the simulation.

        :return: Dictionary containing simulation results
        """
        return self.system_variables_history
    
    def update_module_params(self,module_name:str, params:dict)->None:
        """
        Update the parameters of a module in the system.

        :param module_name: Name of the module to update
        :param params: Dictionary containing the parameters to update
        """
        if module_name not in self.modules:
            raise ValueError("Module not present in the system")
        self.modules[module_name].change_params(params)


    def reset_module_params(self,module_name:str, params:dict)->None:
        """
        Reset the parameters of a module in the system.

        :param module_name: Name of the module to reset
        :param params: Dictionary containing the parameters to reset
        """
        if module_name not in self.modules:
            raise ValueError("Module not present in the system")
        self.modules[module_name].reset_params(params)
    
    def reset(self)->None:
        """
        Reset the simulation engine to its initial state.
        """
        self.clock=0
        self.system_variables[self.name+"_Clock"]=0 #Reset current variable values
        self.system_variables_history[self.name+"_Clock"] = [0] #List of system variables at each timestep, used to store results of the simulation

        for module_name in self.modules:
            self.modules[module_name].reset()
            for key in self.modules[module_name].get_variables():
                self.system_variables_history[module_name+"_"+key]=[self.modules[module_name].get_variables()[key]] #Reset variable history for results storage
                self.system_variables[module_name+"_"+key]=self.modules[module_name].get_variables()[key] #Reset current variable value
            
            for input_module in self.inputs:
                self.inputs[input_module].reset()
                for key in self.inputs[input_module].get_variables():
                    self.system_variables_history[input_module+"_"+key]=[self.inputs[input_module].get_variables()[key]] #Reset variable history for results storage
                    self.system_variables[input_module+"_"+key]=self.inputs[input_module].get_variables()[key] #Reset current variable value
