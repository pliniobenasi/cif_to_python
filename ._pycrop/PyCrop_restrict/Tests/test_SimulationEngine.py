from PyCrop.Implementations.Engines.SimulationEngine import SimulationEngine
from PyCrop.Implementations.Inputs.SFMCInputModule import SFMCInputModule
from PyCrop.Abstract.Core.AbstractModule import STEP_GRANULARITY
from PyCrop.Implementations.TOMGRO.TOMGROBiomassModule import TOMGROBiomassModule, BIOMASS_DEFAULT_PARAMS
from PyCrop.Implementations.TOMGRO.TOMGROLaiModule import TOMGROLaiModule,LAI_DEFAULT_PARAMS
from PyCrop.Implementations.TOMGRO.TOMGRONodesModule import TOMGRONodesModule,NODES_DEFAULT_PARAMS
from PyCrop.Implementations.Environment.SimpleEnvironmentModule import SimpleEnvironmentModule
import pytest
import os
from decimal import Decimal

def test_SimulationEngine_initialization():
    engine = SimulationEngine("TestEngine")
    assert engine is not None
    assert isinstance(engine, SimulationEngine)
    assert engine.name == "TestEngine"
    assert engine.modules == {}
    assert engine.inputs == {}
    assert engine.input_bindings == {}
    assert engine.system_variables == {"TestEngine_Clock": Decimal("0")}
    assert engine.min_granularity == 0
    assert engine.clock == 0
    del engine

def test_SimulationEngine_add_input_module():
    test_file =  "./test_input.csv"
    with open(test_file, 'w') as f:
        f.write("SoilMoisture,Temperature,Radiation,CO2\n")
        f.write("0.12,15,200,400\n")
        f.write("0.15,16,210,410\n")
        f.write("0.20,18,220,420\n")
    engine = SimulationEngine("TestEngine")
    input_module = SFMCInputModule("TestInputModule",-1,3600)
    input_module.read_input(test_file,0,1)
    engine.add_input_module(input_module)
    assert "TestInputModule" in engine.inputs
    assert engine.inputs["TestInputModule"] == input_module
    assert engine.min_granularity == 3600
    assert "TestInputModule_SoilMoisture" in engine.system_variables
    assert "TestInputModule_Temperature" in engine.system_variables
    
    input_module2 = SFMCInputModule("TestInputModule2",-1,3600)
    input_module2.read_input(test_file,2)

    input_module3= SFMCInputModule("TestInputModule3", -1,400)
    input_module3.read_input(test_file,3)

    engine.add_input_module([input_module2, input_module3])
    assert engine.min_granularity == 400 # min granularity should be updated to the GCD of all modules granularities
    assert "TestInputModule2" in engine.inputs
    assert "TestInputModule3" in engine.inputs
    assert engine.inputs["TestInputModule2"] == input_module2
    assert engine.inputs["TestInputModule3"] == input_module3
    assert "TestInputModule2_Radiation" in engine.system_variables
    assert "TestInputModule3_CO2" in engine.system_variables    
    print(engine.system_variables)

    try:
        engine.add_input_module("NotAnInputModule")
    except TypeError as e:
        assert str(e) == "add_input_module method only supports AbstractInputModule or a list of AbstractInputModules"
    
    try:
        engine.add_input_module(input_module2)  # Adding duplicate module
    except ValueError as e:
        assert str(e) == f"Module {input_module2.get_name()} already present. Maybe the name is duplicated"

    del engine
    os.remove(test_file)

def test_SimulationEngine_add_module():
    engine=SimulationEngine("TestEngine")
    biomass = TOMGROBiomassModule("TestBiomassModule",params=BIOMASS_DEFAULT_PARAMS)
    lai = TOMGROLaiModule("TestLaiModule",params=LAI_DEFAULT_PARAMS)
    nodes = TOMGRONodesModule("TestNodesModule",params=NODES_DEFAULT_PARAMS)
    engine.add_module(biomass)
    assert "TestBiomassModule" in engine.modules
    assert engine.modules["TestBiomassModule"] == biomass
    assert engine.min_granularity == biomass.granularity
    engine.add_module([lai, nodes])
    assert "TestLaiModule" in engine.modules
    assert "TestNodesModule" in engine.modules
    assert engine.modules["TestLaiModule"] == lai
    assert engine.modules["TestNodesModule"] == nodes
    assert engine.min_granularity == biomass.granularity # min granularity should be updated to the GCD of all modules granularities
    assert engine.input_bindings["TestBiomassModule"] == {}
    assert engine.input_bindings["TestLaiModule"] == {}
    assert engine.input_bindings["TestNodesModule"] == {}
    for i  in biomass.state_variables:
        assert biomass.get_name()+"_"+i in engine.system_variables
    for i  in lai.state_variables:
        assert lai.get_name()+"_"+i in engine.system_variables
    for i  in nodes.state_variables:         
        assert nodes.get_name()+"_"+i in engine.system_variables
    print(engine.system_variables)
    try:
        engine.add_module("NotAModule")
    except TypeError as e:
        assert str(e) == "Add_modules method only supports AbstractCropModule or a list of AbstractCropModules"    

    try:        
        engine.add_module(biomass)  # Adding duplicate module
    except ValueError as e:
        assert str(e) == f"Module {biomass.get_name()} already present. Maybe the name is duplicated"
    del engine

def test_SimulationEngine_bind_variables():
    engine = SimulationEngine("TestEngine")
    biomass = TOMGROBiomassModule("TestBiomassModule",params=BIOMASS_DEFAULT_PARAMS)
    lai = TOMGROLaiModule("TestLaiModule",params=LAI_DEFAULT_PARAMS)
    nodes = TOMGRONodesModule("TestNodesModule",params=NODES_DEFAULT_PARAMS)
    engine.add_module([biomass, lai, nodes])
    engine.bindVariables("TestLaiModule", "LAI", "TestBiomassModule","LAI")
    assert engine.input_bindings["TestBiomassModule"]["LAI"]== "TestLaiModule_LAI"

    engine.bindVariables("TestNodesModule",["Nodes", "DN"], "TestBiomassModule",["Nodes","Delta_Nodes"])
    assert engine.input_bindings["TestBiomassModule"]["Nodes"]== "TestNodesModule_Nodes"
    assert engine.input_bindings["TestBiomassModule"]["Delta_Nodes"]== "TestNodesModule_DN"
    assert engine.input_bindings["TestBiomassModule"] == {"Nodes":"TestNodesModule_Nodes","Delta_Nodes":"TestNodesModule_DN","LAI":"TestLaiModule_LAI"}
    
    try:
        engine.bindVariables("NotAModule", "LAI", "TestBiomassModule","LAI")  
    except ValueError as e:
        assert str(e) == "Provider module not present in the system"
   
    try:
        engine.bindVariables("TestLaiModule","NotAVariable", "TestBiomassModule","LAI")
    except ValueError as e:
        assert str(e) == "Variable not present as system variable"

    try:
        engine.bindVariables("TestLaiModule", "LAI", "NotAModule","LAI")
    except ValueError as e:
        assert str(e) == "Target module not present in the system"

    try:
        engine.bindVariables("TestLaiModule", "LAI", "TestBiomassModule","NotAnInput")
    except ValueError as e:
        assert str(e) == "Receiver module does not have the specified input variable"

    try:
        engine.bindVariables("TestLaiModule",["LAI","NotAVariable"], "TestBiomassModule",["LAI","LAI","LAI"])
    except ValueError as e:
        assert str(e) == "Input variables and receiver module input names must have the same length"

    try:
        engine.bindVariables("TestLaiModule",["LAI","NotAVariable"], "TestBiomassModule","LAI")
    except TypeError as e:
        assert str(e) == "Input variables and receiver module input names must be both strings or both lists of the same length"
    del engine


def test_SimulationEngine_run():
    
    test_file =  "./test_input.csv"
    with open(test_file, 'w') as f:
        f.write("SoilMoisture,Temperature,Radiation,CO2\n")
        f.write("0.12,15,200,400\n")
        f.write("0.15,16,210,410\n")
        f.write("0.20,18,220,420\n")
    engine = SimulationEngine("TestEngine")
    input_module = SFMCInputModule("TestInputModule",-1,3600)
    input_module.read_input(test_file,0,1)
    engine.add_input_module(input_module)
    biomass = TOMGROBiomassModule("TestBiomassModule",params=BIOMASS_DEFAULT_PARAMS)
    lai = TOMGROLaiModule("TestLaiModule",params=LAI_DEFAULT_PARAMS)
    nodes = TOMGRONodesModule("TestNodesModule",params=NODES_DEFAULT_PARAMS)
    env = SimpleEnvironmentModule("SimpleEnvModule",granularity=STEP_GRANULARITY["HOURLY"],params={"Initial_temperature": 15,"Initial_solar_radiation": 200,"Temperature_delta": 10,"Temperature_amplitude": 1,"Solar_radiation_delta": 20,"Solar_radiation_amplitude": 2})
    engine.add_module([biomass, lai, nodes, env])

    engine.bindVariables("SimpleEnvModule","Daily_Average_Temperature", "TestBiomassModule","Daily_AVG_Temp")
    engine.bindVariables("SimpleEnvModule","Daily_Average_Temperature", "TestNodesModule","Daily_Average_Temperature")
    engine.bindVariables("SimpleEnvModule","Hour","TestBiomassModule","Hour")
    engine.bindVariables("TestNodesModule",["Nodes", "DN"], "TestBiomassModule",["Nodes","Delta_Nodes"])
    engine.bindVariables("TestNodesModule",["Nodes", "DN"], "TestLaiModule",["Nodes","Delta_Nodes"])
    engine.bindVariables("SimpleEnvModule",["Temperature","Solar_radiation"], "SimpleEnvModule",["Temperature","Solar_radiation"])
    engine.bindVariables("SimpleEnvModule","Temperature", "TestBiomassModule","Temperature")
    engine.bindVariables("TestLaiModule","LAI", "TestBiomassModule","LAI")
    engine.bindVariables("SimpleEnvModule","PPFD", "TestBiomassModule","PPFD")
    engine.bindVariables("SimpleEnvModule","CO2", "TestBiomassModule","CO2")
    engine.bindVariables("TestEngine","Clock", "SimpleEnvModule","Clock")
    engine.bindVariables("SimpleEnvModule","Daily_Daytime_Average_Temperature", "TestBiomassModule","Daytime_AVG_Temp")
    engine.bindVariables("TestInputModule","Temperature", "SimpleEnvModule","Temperature")
    engine.run()

    print(engine.system_variables_history)
    assert len(engine.system_variables_history["TestBiomassModule_W"]) == 4
    assert len(engine.system_variables_history["TestLaiModule_LAI"]) == 4
    assert len(engine.system_variables_history["TestNodesModule_Nodes"]) == 4
    assert len(engine.system_variables_history["SimpleEnvModule_PPFD"]) == 4
    assert len(engine.system_variables_history["SimpleEnvModule_Hour"]) == 4
    assert len(engine.system_variables_history["SimpleEnvModule_Daily_Daytime_Average_Temperature"]) == 4
    assert len(engine.system_variables_history["SimpleEnvModule_CO2"]) == 4
    assert len(engine.system_variables_history["SimpleEnvModule_Temperature"]) == 4
    assert len(engine.system_variables_history["SimpleEnvModule_Solar_radiation"]) == 4
    assert len(engine.system_variables_history["SimpleEnvModule_Daily_Average_Temperature"]) == 4
    assert len(engine.system_variables_history["SimpleEnvModule_Daily_Daytime_Average_Temperature"]) == 4
    assert len(engine.system_variables_history["SimpleEnvModule_PPFD"]) == 4
    assert engine.system_variables_history["TestEngine_Clock"] == [0,3600,7200,10800]
    assert engine.system_variables_history["SimpleEnvModule_Temperature"] == [15, 25, 26, 28] #Temperature should be updated by the environment module and not directly from the input module, since it's bound to the environment module variable
    del engine
    os.remove(test_file)


    #TODO:
