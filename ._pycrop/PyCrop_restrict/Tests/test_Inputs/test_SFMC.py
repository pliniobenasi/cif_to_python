from PyCrop.Implementations.Inputs.SFMCInputModule import SFMCInputModule
from PyCrop.Abstract.Core.AbstractModule import STEP_GRANULARITY
import pytest
from decimal import Decimal
import os


def test_SFMCInputModule_initialization():
    sfmc_input = SFMCInputModule("SFMCInputTest",MAX_ROWS=100,granularity=STEP_GRANULARITY["HOURLY"])
    assert sfmc_input is not None
    assert isinstance(sfmc_input, SFMCInputModule)
    assert sfmc_input.MAX_ROWS == 100
    assert sfmc_input.granularity == STEP_GRANULARITY["HOURLY"]
    assert sfmc_input.data_titles == ["Var_1"]
    del sfmc_input

def test_SFMCInputModule_read_input():
    # Create a temporary SFMC input file
    sfmc_file =  "./sfmc_input.csv"
    with open(sfmc_file, 'w') as f:
        f.write("SoilMoisture\n")
        f.write("0.12\n")
        f.write("0.15\n")
        f.write("0.20\n")

    sfmc_input = SFMCInputModule("SFMCInputTest",MAX_ROWS=2,granularity=STEP_GRANULARITY["HOURLY"])
    sfmc_input.read_input(str(sfmc_file))

    assert sfmc_input.data_size == 2
    assert sfmc_input.get_variable_names() == ["SoilMoisture"]
    assert sfmc_input.data[0][0] == Decimal('0.12')
    assert sfmc_input.data[0][1] == Decimal('0.15')

    fd = sfmc_input.f_descriptor
    del sfmc_input
    assert fd.closed
    os.remove(sfmc_file)


def test_SFMCInputModule_read_input_no_title():
    # Create a temporary sfmc input file without title
    sfmc_file =  "./sfmc_input_no_title.csv"
    with open(sfmc_file, 'w') as f:
        f.write("0.10\n")
        f.write("0.15\n")
        f.write("0.20\n")

    sfmc_input = SFMCInputModule("SFMCInputTest",MAX_ROWS=2,granularity=STEP_GRANULARITY["HOURLY"])
    sfmc_input.read_input(str(sfmc_file))

    assert sfmc_input.data_size == 2
    assert sfmc_input.get_variable_names() == ["Var_1"]
    assert sfmc_input.data[0][0] == Decimal('0.10')
    assert sfmc_input.data[0][1] == Decimal('0.15')

    fd = sfmc_input.f_descriptor
    del sfmc_input
    assert fd.closed
    os.remove(sfmc_file)

def test_SFMCInputModule_read_input_invalid_file():
    sfmc_input = SFMCInputModule("SFMCInputTest",MAX_ROWS=100,granularity=STEP_GRANULARITY["HOURLY"])
    try:
        sfmc_input.read_input(123)  # Invalid input type
    except TypeError as e:
        assert str(e) == "Input must be a string representing the file path"
    try:
        sfmc_input.read_input("non_existent_file.csv")  # Non-existent file
    except IOError as e:
        assert "Error opening file non_existent_file.csv" in str(e)
    del sfmc_input


def test_SFMCInputModule_read_input_columns():
    # Create a temporary sfmc input file
    sfmc_file =  "./sfmc_input.csv"
    with open(sfmc_file, 'w') as f:
        f.write("SoilMoisture,Temperature\n")
        f.write("0.12,15\n")
        f.write("0.15,16\n")
        f.write("0.20,18\n")

    sfmc_input = SFMCInputModule("sfmcInputTest",MAX_ROWS=2,granularity=STEP_GRANULARITY["HOURLY"])

    sfmc_input.read_input(str(sfmc_file))  # Read only SoilMoisture column
    assert sfmc_input.data_size == 2
    assert sfmc_input.get_variable_names() == ["SoilMoisture", "Temperature"]
    assert sfmc_input.data[0][0] == Decimal('0.12')
    assert sfmc_input.data[1][0] == Decimal('15')
    del sfmc_input
    os.remove(sfmc_file)

def test_SFMCInputModule_step_whole():
    # Create a temporary SFMC input file
    sfmc_file =  "./sfmc_input.csv"
    with open(sfmc_file, 'w') as f:
        f.write("SoilMoisture\n")
        for i in range(10):
            f.write(f"{Decimal('0.1') + i*Decimal('0.05')}\n")
    sfmc_input = SFMCInputModule("SFMCInputTest",MAX_ROWS=0,granularity=STEP_GRANULARITY["HOURLY"])
    sfmc_input.read_input(str(sfmc_file))
    assert sfmc_input.data_size == 10

    vars_t0 = sfmc_input.get_variables()
    assert vars_t0 == {"SoilMoisture": Decimal('0.1')}
    assert sfmc_input.get_current_timestep() == 0

    sfmc_input.step()
    vars_t1 = sfmc_input.get_variables()
    assert vars_t1 == {"SoilMoisture": Decimal('0.15')}
    assert sfmc_input.get_current_timestep() == 1

    sfmc_input.step()
    vars_t2 = sfmc_input.get_variables()
    assert vars_t2 == {"SoilMoisture": Decimal('0.20')}
    assert sfmc_input.get_current_timestep() == 2

    for i in range(3,11):
        sfmc_input.step()
    vars_t9 = sfmc_input.get_variables()
    assert vars_t9 == None
    assert sfmc_input.get_current_timestep() == 10

    del sfmc_input
    os.remove(sfmc_file)

def test_SFMCInputModule_step_chunk():
    sfmc_file =  "./sfmc_input.csv"
    with open(sfmc_file, 'w') as f:
        f.write("SoilMoisture\n")
        for i in range(10):
            f.write(f"{Decimal('0.1') + i*Decimal('0.05')}\n")
    sfmc_input = SFMCInputModule("SFMCInputTest",MAX_ROWS=3,granularity=STEP_GRANULARITY["HOURLY"])
    sfmc_input.read_input(str(sfmc_file))
    vars_t0 = sfmc_input.get_variables()
    assert vars_t0 == {"SoilMoisture": Decimal('0.1')}
    assert sfmc_input.get_current_timestep() == 0
    assert sfmc_input.data_size == 3
    sfmc_input.step()
    vars_t1 = sfmc_input.get_variables()
    assert vars_t1 == {"SoilMoisture": Decimal('0.15')}
    assert sfmc_input.get_current_timestep() == 1
    
    sfmc_input.step()
    vars_t2 = sfmc_input.get_variables()
    assert vars_t2 == {"SoilMoisture": Decimal('0.20')}
    assert sfmc_input.get_current_timestep() == 2
    assert sfmc_input.data_size == 3

    sfmc_input.step()
    vars_t3 = sfmc_input.get_variables()
    assert sfmc_input.get_current_timestep() == 3
    assert sfmc_input.data_size == 6
    assert vars_t3 =={"SoilMoisture": Decimal('0.25')}

    for i in range(4,9):
        sfmc_input.step()
    
    vars_t8 = sfmc_input.get_variables()
    assert vars_t8 == {"SoilMoisture": Decimal('0.50')}
    assert sfmc_input.get_current_timestep() == 8
    assert sfmc_input.data_size == 9

    sfmc_input.step()
    assert sfmc_input.data_size == 10
    assert sfmc_input.get_current_timestep() == 9
    vars_t9 = sfmc_input.get_variables()
    assert vars_t9 == {"SoilMoisture": Decimal('0.55')}

    sfmc_input.step()
    assert sfmc_input.get_current_timestep() == 10
    vars_t10 = sfmc_input.get_variables()
    assert vars_t10 is None

    del sfmc_input
    os.remove(sfmc_file)

def test_SFMCInputModule_reset():
    # Create a temporary sfmc input file
    sfmc_file =  "./sfmc_input.csv"
    with open(sfmc_file, 'w') as f:
        f.write("SoilMoisture\n")
        for i in range(5):
            f.write(f"{Decimal('0.1') + i*Decimal('0.1')}\n")
    sfmc_input = SFMCInputModule("sfmcInputTest",MAX_ROWS=2,granularity=STEP_GRANULARITY["HOURLY"])
    sfmc_input.read_input(str(sfmc_file))

    sfmc_input.step()  # Timestep 1
    sfmc_input.step()  # Timestep 2
    assert sfmc_input.get_current_timestep() == 2

    sfmc_input.reset()
    assert sfmc_input.get_current_timestep() == 0
    vars_t0 = sfmc_input.get_variables()
    assert vars_t0 == {"SoilMoisture": Decimal('0.1')}

    del sfmc_input
    os.remove(sfmc_file)

def test_SFMCInputModule_assignHeader():
    # Create a temporary sfmc input file
    sfmc_file =  "./sfmc_input.csv"
    with open(sfmc_file, 'w') as f:
        f.write("SoilMoisture,Temperature\n")
        f.write("0.12,25.0\n")
        f.write("0.15,26.0\n")

    sfmc_input = SFMCInputModule("sfmcInputTest",MAX_ROWS=2,granularity=STEP_GRANULARITY["HOURLY"])
    sfmc_input.read_input(str(sfmc_file))

    # Assign new header
    sfmc_input.assignHeader(["NewSoilMoisture", "NewTemperature"])
    assert sfmc_input.get_variable_names() == ["NewSoilMoisture", "NewTemperature"]

    del sfmc_input
    os.remove(sfmc_file)


def test_SFMCInputModule_malformedFile():
    # Create a temporary malformed sfmc input file
    sfmc_file =  "./sfmc_input_malformed.csv"
    with open(sfmc_file, 'w') as f:
        f.write("SoilMoisture,Temperature\n")
        f.write("0.12,25.0\n")
        f.write("0.15,26zzz\n")  # Non-numeric value
        f.write("0.20,27.0\n")

    sfmc_input = SFMCInputModule("sfmcInputTest",MAX_ROWS=3,granularity=STEP_GRANULARITY["HOURLY"])
    sfmc_input.read_input(str(sfmc_file))

    assert sfmc_input.data_size == 2
    assert sfmc_input.data[0][0] == Decimal('0.12')
    assert sfmc_input.data[1][0] == Decimal('25.0')
    assert sfmc_input.data[0][1] == Decimal('0.20')
    assert sfmc_input.data[1][1] == Decimal('27.0')

    del sfmc_input
    os.remove(sfmc_file)