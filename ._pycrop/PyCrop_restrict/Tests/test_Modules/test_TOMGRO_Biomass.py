from PyCrop.Implementations.TOMGRO.TOMGROBiomassModule import TOMGROBiomassModule
from PyCrop.Abstract.Core.AbstractModule import STEP_GRANULARITY
import pytest
from decimal import Decimal

#Some paramters are float, other decimal, to test type checking
params_Biomass= {
    "W_0":0,
    "W_f0":0,
    "W_m0":0,
    "p1": 1,
    "rho" : 1,
    "Vmax": 2,
    "alphaF": Decimal('0.47'),
    "theta": Decimal('0.22'),
    "krm": Decimal('0.005'),
    "NFF": 13,
    "KFF": 16,
    "Tcrit": 30,
    "cfngt": 7,
    "dfmax": Decimal('0.062'),
    "E": 0.06,
    "LAI_MAX": 2
}

def test_TOMGROBiomass_initialization():
    try:
        tomgro_biomass = TOMGROBiomassModule("TOMGROBiomassTest",granularity=STEP_GRANULARITY["DAILY"],params=params_Biomass)
    except ValueError as e:
        assert str(e) == "TOMGRO Biomass module only supports HOURLY granularity."
    tomgro_biomass = TOMGROBiomassModule("TOMGROBiomassTest",granularity=STEP_GRANULARITY["HOURLY"],params=params_Biomass)
    assert tomgro_biomass is not None
    assert isinstance(tomgro_biomass, TOMGROBiomassModule)
    for i in params_Biomass:
        assert tomgro_biomass.params[i] == Decimal(str(params_Biomass[i]))
    vars = tomgro_biomass.get_variables()
    assert isinstance(vars, dict)
    assert "W" in vars
    assert vars["W"] == Decimal(str(params_Biomass["W_0"]))
    assert "W_f" in vars
    assert vars["W_f"] == Decimal(str(params_Biomass["W_f0"]))
    assert "W_m" in vars
    assert vars["W_m"] == Decimal(str(params_Biomass["W_m0"]))

def test_TOMGROBiomass_change_params():
    tomgro_biomass = TOMGROBiomassModule("TOMGROBiomassTest",granularity=STEP_GRANULARITY["HOURLY"],params=params_Biomass)
    try:
        tomgro_biomass.change_params([0])  # Should raise TypeError
    except TypeError as e:
        assert str(e) == "param argument must be a dict"
    try:
        tomgro_biomass.change_params({"W_0":0,"W_f0":0,"W_m0":0,"p1": 1,"rho" : 1,"Vmax": 2,"alphaF": 0.47,\
                                      "theta": 0.22,"krm": 0.005,"NFF": 13,"KFF": 16,"Tcrit": 30,"cfngt": 7,\
                                        "dfmax": 0.062,"E": 0.06})  # Missing LAI_MAX
    except ValueError as e:
        assert str(e) == "Parameter 'LAI_MAX' is required but missing."

    try:
        tomgro_biomass.change_params({"W_0":0,"W_f0":0,"W_m0":0,"p1": 1,"rho" : 1,"Vmax": 2,"alphaF": Decimal('0.47'),\
                                      "theta": Decimal('0.22'),"krm": Decimal('0.005'),"NFF": "13","KFF": 16,"Tcrit": 30,"cfngt": 7,\
                                        "dfmax": Decimal('0.062'),"E": 0.06,"LAI_MAX": Decimal('-2')})  # non-numeric NFF
    except TypeError as e:
        assert str(e) == "Parameter 'NFF' must be a number."

    try:
        tomgro_biomass.change_params({"W_0":-1,"W_f0":0,"W_m0":0,"p1": 1,"rho" : 1,"Vmax": 2,"alphaF": 0.47,\
                                      "theta": 0.22,"krm": 0.005,"NFF": 13,"KFF": 16,"Tcrit": 30,"cfngt": 7,\
                                        "dfmax": 0.062,"E": 0.06,"LAI_MAX": 2})  # Negative W_0
    except ValueError as e:
        assert str(e) == "Parameter 'W_0' must be non-negative."
    try:
        tomgro_biomass.change_params({"W_0":0,"W_f0":0,"W_m0":0,"p1": 1,"rho" : 1,"Vmax": 2,"alphaF": 0.47,\
                                      "theta": 0.22,"krm": 0.005,"NFF": 17,"KFF": Decimal(16),"Tcrit": 30,"cfngt": 7,\
                                        "dfmax": 0.062,"E": 0.06,"LAI_MAX": 2})  # NFF >= KFF
    except ValueError as e:
        assert str(e) == "Parameter NFF must be smaller than KFF."
    del tomgro_biomass

def test_TOMGROBiomass_step():
    
    tomgro_biomass = TOMGROBiomassModule("TOMGROBiomassTest",granularity=STEP_GRANULARITY["HOURLY"],params=params_Biomass)
    
    try:
        tomgro_biomass.step("not a list")  # Should raise TypeError
    except TypeError as e:
        assert str(e) == "Input must be a list"

    try:
        tomgro_biomass.step([10,25,20,21,Decimal(400),800,5,2])  # Missing LAI
    except ValueError as e:
        assert str(e) == "Input list must contain at least 9 elements"
    
    try:
        tomgro_biomass.step([10,25,"20",21,Decimal(400),800,5,2,1])  # Non-numeric Daily_AVG_Temp
    except TypeError as e:
        assert str(e) == "Input values must be int, float, or Decimal."
    
    try:
        tomgro_biomass.step([5.5,25,20,21,Decimal(400),800,5,2,1])  # Non-integer Hour
    except TypeError as e:
        assert str(e) == "Hour must be an integer."

    try:
        tomgro_biomass.step([24,25,20,21,Decimal(400),800,5,2,1])  # Hour out of range
    except ValueError as e:
        assert str(e) == "Hour must be in the range [0, 23]."

    try:
        tomgro_biomass.step([10,25,20,21,Decimal(400),800,5.5,2,1])  # Non-integer Nodes
    except TypeError as e:
        assert str(e) == "Nodes must be an integer."

    try:
        tomgro_biomass.step([10,25,20,21,400,800,-5,2,1]) # Negative Nodes
    except ValueError as e:
        assert str(e) == "Nodes (N) must be non-negative."
    try:
        tomgro_biomass.step([10,25,20,21,400,800,5,-2,1]) # Negative Delta_Nodes
    except ValueError as e:
        assert str(e) == "Delta_Nodes (DN) must be non-negative."
    try:
        tomgro_biomass.step([10,25,20,21,400,800,5,2,-1])# Negative LAI
    except ValueError as e:
        assert str(e) == "Leaf Area Index (LAI) must be non-negative."
    # Test with valid input
    # Hour=10, T_air=25, Daily_AVG_Temp=20, Daytime_AVG_Temp=21, CO2=400,
    #  PPFD=800, Nodes=5, Delta_Nodes=2, LAI=1
    tomgro_biomass.step([10,25,20,21,400,800,5,2,1])  
    output = tomgro_biomass.get_variables()
    assert len(output) == 5
    assert output["W"] >= 0  # Biomass should be non-negative
    assert output["W_f"] >= 0  # Fruit Biomass should be non-negative
    assert output["W_m"] >= 0  # Mature Fruit Biomass should be non-negative
    assert output["Pg"] >= 0  # Gross Photosynthesis should be non-negative
    assert output["Rm"] >= 0  # Maintenance Respiration should be non-negative
    del tomgro_biomass

def test_TOMGROBiomass_required_inputs():
    tomgro_biomass = TOMGROBiomassModule("TOMGROBiomassTest",granularity=STEP_GRANULARITY["HOURLY"],params=params_Biomass)
    required_inputs = tomgro_biomass.show_required_inputs()
    assert isinstance(required_inputs, list)
    assert "Hour" in required_inputs
    assert "Temperature" in required_inputs
    assert "Daily_AVG_Temp" in required_inputs
    assert "Daytime_AVG_Temp" in required_inputs
    assert "CO2" in required_inputs
    assert "PPFD" in required_inputs
    assert "Nodes" in required_inputs
    assert "Delta_Nodes" in required_inputs
    assert "LAI" in required_inputs
    del tomgro_biomass

def test_TOMGROBiomass_reset():
    tomgro_biomass = TOMGROBiomassModule("TOMGROBiomassTest",granularity=STEP_GRANULARITY["HOURLY"],params=params_Biomass)
    tomgro_biomass.step([10,25,20,21,400,800,5,2,1])  # Perform a step to change state
    tomgro_biomass.reset()
    vars = tomgro_biomass.get_variables()
    assert "W" in vars
    assert vars["W"] == Decimal(params_Biomass["W_0"])
    assert "W_f" in vars
    assert vars["W_f"] == Decimal(params_Biomass["W_f0"])
    assert "W_m" in vars
    assert vars["W_m"] == Decimal(params_Biomass["W_m0"])
    assert "Pg" in vars
    assert vars["Pg"] == Decimal(0)
    assert "Rm" in vars
    assert vars["Rm"] == Decimal(0)
    del tomgro_biomass

if __name__ == "__main__":
    test_TOMGROBiomass_initialization()
    test_TOMGROBiomass_change_params()
    test_TOMGROBiomass_step()
    test_TOMGROBiomass_required_inputs()
    test_TOMGROBiomass_reset()