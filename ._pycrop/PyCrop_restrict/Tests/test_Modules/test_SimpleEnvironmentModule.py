from PyCrop.Implementations.Environment.SimpleEnvironmentModule import SimpleEnvironmentModule,WM2TOPPFD
from PyCrop.Abstract.Core.AbstractModule import STEP_GRANULARITY
from decimal import Decimal
import pytest

params = {
    "Initial_temperature": 20,
    "Initial_solar_radiation": 500,
    "Temperature_delta": 0,
    "Temperature_amplitude": 1,
    "Solar_radiation_delta": 0,
    "Solar_radiation_amplitude": 1
}

def test_SimpleEnvironmentModule_initialization():
    try:
        env_module = SimpleEnvironmentModule("SimpleEnvTest",granularity=STEP_GRANULARITY["HOURLY"],params=params)
    except ValueError as e:
        assert str(e) == "Simple Environment module only supports HOURLY granularity."
    env_module = SimpleEnvironmentModule("SimpleEnvTest",granularity=STEP_GRANULARITY["HOURLY"],params=params)
    assert env_module is not None
    assert isinstance(env_module, SimpleEnvironmentModule)
    assert env_module.name == "SimpleEnvTest"
    assert env_module.granularity == STEP_GRANULARITY["HOURLY"]
    assert env_module.params["Initial_temperature"] == Decimal(str(params["Initial_temperature"]))
    assert env_module.params["Initial_solar_radiation"] == Decimal(str(params["Initial_solar_radiation"]))
    assert env_module.params["Temperature_delta"] == Decimal(str(params["Temperature_delta"]))
    assert env_module.params["Temperature_amplitude"] == Decimal(str(params["Temperature_amplitude"]))
    assert env_module.params["Solar_radiation_delta"] == Decimal(str(params["Solar_radiation_delta"]))
    assert env_module.params["Solar_radiation_amplitude"] == Decimal(str(params["Solar_radiation_amplitude"]))
    vars = env_module.get_variables()
    assert isinstance(vars, dict)
    assert "Temperature" in vars
    assert "Solar_radiation" in vars
    assert "Hour" in vars
    assert "Daily_Average_Temperature" in vars
    assert "Daily_Daytime_Average_Temperature" in vars
    assert "PPFD" in vars
    assert vars["Hour"] == 0
    assert vars["Temperature"] == Decimal(str(params["Initial_temperature"]))
    assert vars["Solar_radiation"] == Decimal(str(params["Initial_solar_radiation"]))
    assert vars["Daily_Average_Temperature"] == Decimal(0)
    assert vars["Daily_Daytime_Average_Temperature"] == Decimal(0)
    assert vars["PPFD"] == Decimal(str(params["Initial_solar_radiation"])) * WM2TOPPFD
    try:
        env_module.change_params([0])  # Should raise TypeError
    except TypeError as e:
        assert str(e) == "Input parameters must be a dictionary"
    try:
        env_module.change_params({"Initial_temperature":0,"Initial_solar_radiation":500,"Temperature_delta":0,"Temperature_amplitude":1,"Solar_radiation_delta":0})  # Missing Solar_radiation_amplitude  
    except ValueError as e:
        assert str(e) == "Missing required parameters. Required parameters are: ['Initial_temperature', 'Initial_solar_radiation', 'Temperature_delta', 'Temperature_amplitude', 'Solar_radiation_delta', 'Solar_radiation_amplitude']"
    try:
        env_module.change_params({"Initial_temperature":0,"Initial_solar_radiation":500,"Temperature_delta":0,"Temperature_amplitude":"not a number","Solar_radiation_delta":0,"Solar_radiation_amplitude":1})  # Invalid type
    except TypeError as e:
        assert str(e) == "All parameters must be numbers (int, float or Decimal)."
    del env_module

def test_SimpleEnvironmentModule_step():
    params = {
        "Initial_temperature": 20,
        "Initial_solar_radiation": 500,
        "Temperature_delta": 5,
        "Temperature_amplitude": 2,
        "Solar_radiation_delta": 10,
        "Solar_radiation_amplitude": 1
    }
    env_module = SimpleEnvironmentModule("SimpleEnvTest",granularity=STEP_GRANULARITY["HOURLY"],params=params)
    try:
        env_module.step("not a list")  # Should raise TypeError
    except TypeError as e:
        assert str(e) == "Input must be a list"
    try:
        env_module.step([0,1])  # Less than 3 values
    except ValueError as e:
        assert str(e) == "Input list must contain at least three values: Hour, Temperature and Solar_radiation"
    
    try:
        env_module.step([0, "not a number", 500])  # Non-numeric temperature
    except TypeError as e:
        assert str(e) == "Input values must be numbers (int, float or Decimal)."

    env_module.step([0, 25, 500])  # Hour, Temperature, Solar_radiation
    vars = env_module.get_variables()
    assert vars["Hour"] == 0
    assert vars["Temperature"] == Decimal(5 + 2*25)  # T_delta + T_amp * Temperature_input
    assert vars["Solar_radiation"] == Decimal(10 + 500)  # SR_delta + SR_amp * Solar_radiation_input
    assert vars["Daily_Average_Temperature"] == Decimal(5 + 2*25)  # Should be same as current temperature since it's the first step
    assert vars["Daily_Daytime_Average_Temperature"] == 0  # Should be 0 since it's nighttime (hour 0)
    assert vars["PPFD"] == Decimal((500+10)*WM2TOPPFD)  # Should be solar radiation input + delta multiplied by conversion factor

    t_sum = 0
    t_daysum = 0
    for i in range(1, 24):
        env_module.step([i*3600, 25+i, 500+i*10])  # Increment temperature and solar radiation each hour
        t_sum += Decimal(5 + 2*(25+i))
        if 6 <= i <= 18:  # Daytime hours
            t_daysum += Decimal(5 + 2*(25+i))
        vars = env_module.get_variables()
        assert vars["Daily_Average_Temperature"] == Decimal((5 + 2*25 + t_sum) / (i+1))  # Average temperature over all hours
        if i >= 6 and i <= 18:
            assert vars["Daily_Daytime_Average_Temperature"] == Decimal(t_daysum / (i - 5))  # Average daytime temperature
    assert env_module.daily_daytime_temperature_sum == 0
    assert env_module.daily_temperature_sum == 0
    assert env_module.state_variables["Hour"] == 23

    env_module.step([25*3600, 50, 1000])  # Next day, should reset daily sums
    assert env_module.state_variables["Hour"] == 1

    del env_module

def test_SimpleEnvironmentModule_reset():
   
    env_module = SimpleEnvironmentModule("SimpleEnvTest",granularity=STEP_GRANULARITY["HOURLY"],params=params)
    env_module.step([0, 25, 500])  # Hour, Temperature, Solar_radiation
    env_module.reset()
    vars = env_module.get_variables()
    assert vars["Temperature"] == Decimal(str(params["Initial_temperature"]))
    assert vars["Solar_radiation"] == Decimal(str(params["Initial_solar_radiation"]))
    assert vars["Daily_Average_Temperature"] == Decimal(0)
    assert vars["Daily_Daytime_Average_Temperature"] == Decimal(0)
    assert vars["PPFD"] == Decimal(0)
    del env_module

def test_SimpleEnvironmentModule_get_variable_names():
    env_module = SimpleEnvironmentModule("SimpleEnvTest",granularity=STEP_GRANULARITY["HOURLY"],params=params)
    var_names = env_module.get_variable_names()
    assert isinstance(var_names, list)
    expected_vars = ["Temperature", "Solar_radiation", "Daily_Average_Temperature", "Daily_Daytime_Average_Temperature", "PPFD","Hour"]
    for var in expected_vars:
        assert var in var_names
    del env_module

def test_SimpleEnvironmentModule_change_params():
    env_module = SimpleEnvironmentModule("SimpleEnvTest",granularity=STEP_GRANULARITY["HOURLY"],params=params)
    new_params = {
        "Initial_temperature": 25,
        "Initial_solar_radiation": 600,
        "Temperature_delta": 10,
        "Temperature_amplitude": 0.5,
        "Solar_radiation_delta": 20,
        "Solar_radiation_amplitude": 2
    }
    env_module.change_params(new_params)
    assert env_module.params["Initial_temperature"] == Decimal(str(new_params["Initial_temperature"]))
    assert env_module.params["Initial_solar_radiation"] == Decimal(str(new_params["Initial_solar_radiation"]))
    assert env_module.params["Temperature_delta"] == Decimal(str(new_params["Temperature_delta"]))
    assert env_module.params["Temperature_amplitude"] == Decimal(str(new_params["Temperature_amplitude"]))
    assert env_module.params["Solar_radiation_delta"] == Decimal(str(new_params["Solar_radiation_delta"]))
    assert env_module.params["Solar_radiation_amplitude"] == Decimal(str(new_params["Solar_radiation_amplitude"]))
    try:
        env_module.change_params([0])  # Should raise TypeError
    except TypeError as e:
        assert str(e) == "Input parameters must be a dictionary"
    try:
        env_module.change_params({"Initial_temperature": 25, "Initial_solar_radiation": 600, "Temperature_delta":10,"Temperature_amplitude":0.5,"Solar_radiation_delta":20})  # Missing Solar_radiation_amplitude
    except ValueError as e:
        assert str(e) == "Missing required parameters. Required parameters are: ['Initial_temperature', 'Initial_solar_radiation', 'Temperature_delta', 'Temperature_amplitude', 'Solar_radiation_delta', 'Solar_radiation_amplitude']"
    try:
        env_module.change_params({"Initial_temperature": 25, "Initial_solar_radiation": 600,"Temperature_delta":10,"Temperature_amplitude":"not a number","Solar_radiation_delta":20,"Solar_radiation_amplitude":2})  # Invalid type
    except TypeError as e:
        assert str(e) == "All parameters must be numbers (int, float or Decimal)."
    del env_module

if __name__ == "__main__":
    test_SimpleEnvironmentModule_initialization()
    test_SimpleEnvironmentModule_step()
    test_SimpleEnvironmentModule_reset()
    test_SimpleEnvironmentModule_get_variable_names()
    test_SimpleEnvironmentModule_change_params()