from decimal import Decimal
from PyCrop.Implementations.TOMGRO.TOMGROLaiModule import TOMGROLaiModule
from PyCrop.Abstract.Core.AbstractModule import STEP_GRANULARITY
import pytest

params_Lai= {
    "L_0":0.015,
    "a":Decimal(0.001),
    "b":250000,
    "c":1.435,
    "d":3.6
}

def test_TOMGROLai_initialization():
    try:
        tomgro_lai = TOMGROLaiModule("TOMGROLaiTest",granularity=STEP_GRANULARITY["HOURLY"],params=params_Lai)
    except ValueError as e:
        assert str(e) == "TOMGRO LAI module only supports DAILY granularity."
    tomgro_lai = TOMGROLaiModule("TOMGROLaiTest",granularity=STEP_GRANULARITY["DAILY"],params=params_Lai)
    assert tomgro_lai is not None
    assert isinstance(tomgro_lai, TOMGROLaiModule)
    for i in params_Lai:
        assert tomgro_lai.params[i] == Decimal(str(params_Lai[i]))
    vars = tomgro_lai.get_variables()
    assert isinstance(vars, dict)
    assert "LAI" in vars
    assert vars["LAI"] == Decimal(str(params_Lai["L_0"]))
    try:
        tomgro_lai.change_params([0])  # Should raise TypeError
    except TypeError as e:
        assert str(e) == "param argument must be a dictionary"
    try:
        tomgro_lai.change_params({"a":0.001,"b":250000,"c":1.435,"d":3.6})  # Missing L_0
    except ValueError as e:
        assert str(e) == "Missing required TOMGRO LAI parameter: L_0"
    try:
        tomgro_lai.change_params({"L_0":-1,"a":0.001,"b":250000,"c":1.435,"d":3.6})  # Negative L_0
    except ValueError as e:
        assert str(e) == "All parameters must be non-negative."
    del tomgro_lai

def test_TOMGROLai_step():
    
    tomgro_lai = TOMGROLaiModule("TOMGROLaiTest",granularity=STEP_GRANULARITY["DAILY"],params=params_Lai)
    
    try:
        tomgro_lai.step("not a list")  # Should raise TypeError
    except TypeError as e:
        assert str(e) == "Input must be a list"

    try:
        tomgro_lai.step([10])  # Missing DN
    except ValueError as e:
        assert str(e) == "Input list must contain at least two elements"
    
    try:
        tomgro_lai.step([10.5,5])  # Non-integer Nodes
    except TypeError as e:
        assert str(e) == "Current node number must be an Integer."

    try:
        tomgro_lai.step([-2,3])  # Extra input values
    except ValueError as e:
        assert str(e) == "Current node number must be non-negative."

    try:
        tomgro_lai.step([10,"not a number"])  # Non-numeric DN
    except TypeError as e:
        assert str(e) == "Daily increment of nodes (DN) must be a number."

    try:
        tomgro_lai.step([10,-1])  # Negative DN
    except ValueError as e:
        assert str(e) == "Daily increment of nodes (DN) must be non-negative."
    
    # Test with valid input
    tomgro_lai.step([10,2.0])  # Nodes=10, DN=2.0
    output = tomgro_lai.get_variables()
    assert len(output) == 1
    assert output["LAI"] >= 0  # LAI should be non-negative

    del tomgro_lai

def test_TOMGROLai_required_inputs():
    tomgro_lai = TOMGROLaiModule("TOMGROLaiTest",granularity=STEP_GRANULARITY["DAILY"],params=params_Lai)
    required_inputs = tomgro_lai.show_required_inputs()
    assert isinstance(required_inputs, list)
    assert "Nodes" in required_inputs
    assert "Delta_Nodes" in required_inputs
    del tomgro_lai

def test_TOMGROLai_reset():
    tomgro_lai = TOMGROLaiModule("TOMGROLaiTest",granularity=STEP_GRANULARITY["DAILY"],params=params_Lai)
    tomgro_lai.step([10,2.0])  # Advance state
    tomgro_lai.reset()
    vars = tomgro_lai.get_variables()
    assert vars["LAI"] == Decimal(str(params_Lai["L_0"]))
    del tomgro_lai

if __name__ == "__main__":
    test_TOMGROLai_initialization()
    test_TOMGROLai_step()
    test_TOMGROLai_required_inputs()
    test_TOMGROLai_reset()