from decimal import Decimal
from PyCrop.Implementations.TOMGRO.TOMGRONodesModule import TOMGRONodesModule
from PyCrop.Abstract.Core.AbstractModule import STEP_GRANULARITY
import pytest

params={"N_0":5,
        "Nm":0.66,
        "T0":5,
        "T1":Decimal(14),
        "T2":28,
        "T3":42
}
    

def test_TOMGRONodes_initialization():
    try:
        tomgro_nodes = TOMGRONodesModule("TOMGRONodesTest",granularity=STEP_GRANULARITY["HOURLY"],params=params)
    except ValueError as e:
        assert str(e) == "TOMGRO Nodes module only supports DAILY granularity."
    tomgro_nodes = TOMGRONodesModule("TOMGRONodesTest",granularity=STEP_GRANULARITY["DAILY"],params=params)
    assert tomgro_nodes is not None
    assert isinstance(tomgro_nodes, TOMGRONodesModule)
    for i in params:
        assert tomgro_nodes.params[i]==Decimal(str(params[i]))
    vars = tomgro_nodes.get_variables()
    assert isinstance(vars, dict)
    assert "Nodes" in vars
    assert "DN" in vars
    assert vars["Nodes"] == (params["N_0"])
    assert vars["DN"] == Decimal(0)
    try:
        tomgro_nodes.change_params([0])  # Should raise TypeError
    except TypeError as e:
        assert str(e) == "Input parameters must be a dictionary"
    try:
        tomgro_nodes.change_params({"N_0":5,"Nm":0.66,"T0":5,"T1":14,"T2":28})  # Missing T3
    except ValueError as e:
        assert str(e) == "Missing required TOMGRO parameters"
    try:
        tomgro_nodes.change_params({"N_0":5,"Nm":"not a number","T0":5,"T1":14,"T2":28,"T3":42})  # Invalid type
    except TypeError as e:
        assert str(e) == "All parameters must be numbers (int, float or Decimal)."
    try:
        tomgro_nodes.change_params({"N_0":5,"Nm":0.66,"T0":5,"T1":4,"T2":28,"T3":42})  # Invalid temperature order
    except ValueError as e:
        assert str(e) == "Temperature parameters must satisfy T0 < T1 < T2 < T3"
    del tomgro_nodes

def test_TOMGRONodes_step():
    
    tomgro_nodes = TOMGRONodesModule("TOMGRONodesTest",granularity=STEP_GRANULARITY["DAILY"],params=params)
    
    try:
        tomgro_nodes.step("not a list")  # Should raise TypeError
    except TypeError as e:
        assert str(e) == "Input must be a list"
    try:
        tomgro_nodes.step([ "not a number"])  # Should raise TypeError
    except TypeError as e:
        assert str(e) == "Input value must be a number (int, float or Decimal)."
    # Test with valid temperature input
    tomgro_nodes.step([10])  # T_in between T0 and T1
    output = tomgro_nodes.get_variables()
    assert len(output) == 2
    assert output["DN"] > 0  # Expecting positive growth rate
    print(output["Nodes"])
    print(tomgro_nodes.state_variables["Nodes"])
    assert output["Nodes"] == int(params["N_0"] + output["DN"]) # Expecting positive growth rate

    tomgro_nodes.step([30])  # T_in between T2 and T3
    output = tomgro_nodes.get_variables()
    assert len(output) == 2
    assert output["DN"] > 0  # Expecting positive growth rate
    assert output["Nodes"] > 0  # Expecting positive growth rate
    old_nodes = output["Nodes"]
    tomgro_nodes.step([50])  # T_in above T3
    output = tomgro_nodes.get_variables()
    assert len(output) == 2
    assert output["DN"] == Decimal(0)  # Expecting zero growth rate
    assert output["Nodes"] == old_nodes  # Expecting zero growth rate
    del tomgro_nodes

def test_TOMGRONodes_required_inputs():
    tomgro_nodes = TOMGRONodesModule("TOMGRONodesTest",granularity=STEP_GRANULARITY["DAILY"],params=params)
    required_inputs = tomgro_nodes.show_required_inputs()
    assert isinstance(required_inputs, list)
    assert required_inputs == ["Daily_Average_Temperature"]
    del tomgro_nodes

def test_TOMGRONodes_reset():
    tomgro_nodes = TOMGRONodesModule("TOMGRONodesTest",granularity=STEP_GRANULARITY["DAILY"],params=params)
    tomgro_nodes.step([10])  # Advance state
    tomgro_nodes.reset()  # Reset to initial state
    vars = tomgro_nodes.get_variables()
    assert vars["Nodes"] == int(params["N_0"])
    assert vars["DN"] == Decimal(0)
    del tomgro_nodes

if __name__ == "__main__":
    test_TOMGRONodes_initialization()
    test_TOMGRONodes_step()
    test_TOMGRONodes_required_inputs()
    test_TOMGRONodes_reset()
    print("All tests passed.")