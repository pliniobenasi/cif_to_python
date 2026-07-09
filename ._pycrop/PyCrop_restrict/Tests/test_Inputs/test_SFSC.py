from PyCrop.Implementations.Inputs.SFSCInputModule import SFSCInputModule
from PyCrop.Abstract.Core.AbstractModule import STEP_GRANULARITY
import pytest
from decimal import Decimal
import os


def test_SFSCInputModule_initialization():
    sfsc_input = SFSCInputModule("SFSCInputTest",MAX_ROWS=100,granularity=STEP_GRANULARITY["HOURLY"])
    assert sfsc_input is not None
    assert isinstance(sfsc_input, SFSCInputModule)
    assert sfsc_input.MAX_ROWS == 100
    assert sfsc_input.granularity == STEP_GRANULARITY["HOURLY"]
    assert sfsc_input.data_titles == ["Var_1"]
    del sfsc_input

def test_SFSCInputModule_read_input():
    # Create a temporary SFSC input file
    sfsc_file =  "./sfsc_input.csv"
    with open(sfsc_file, 'w') as f:
        f.write("SoilMoisture\n")
        f.write("0.12\n")
        f.write("0.15\n")
        f.write("0.20\n")

    sfsc_input = SFSCInputModule("SFSCInputTest",MAX_ROWS=2,granularity=STEP_GRANULARITY["HOURLY"])
    sfsc_input.read_input(str(sfsc_file))

    assert sfsc_input.data_size == 2
    assert sfsc_input.get_variable_names() == ["SoilMoisture"]
    assert sfsc_input.data[0] == Decimal('0.12')
    assert sfsc_input.data[1] == Decimal('0.15')

    fd = sfsc_input.f_descriptor
    del sfsc_input
    assert fd.closed
    os.remove(sfsc_file)


def test_SFSCInputModule_read_input_no_title():
    # Create a temporary SFSC input file without title
    sfsc_file =  "./sfsc_input_no_title.csv"
    with open(sfsc_file, 'w') as f:
        f.write("0.10\n")
        f.write("0.15\n")
        f.write("0.20\n")

    sfsc_input = SFSCInputModule("SFSCInputTest",MAX_ROWS=2,granularity=STEP_GRANULARITY["HOURLY"])
    sfsc_input.read_input(str(sfsc_file))

    assert sfsc_input.data_size == 2
    assert sfsc_input.get_variable_names() == ["Var_1"]
    assert sfsc_input.data[0] == Decimal('0.10')
    assert sfsc_input.data[1] == Decimal('0.15')

    fd = sfsc_input.f_descriptor
    del sfsc_input
    assert fd.closed
    os.remove(sfsc_file)

def test_SFSCInputModule_read_input_invalid_file():
    sfsc_input = SFSCInputModule("SFSCInputTest",MAX_ROWS=100,granularity=STEP_GRANULARITY["HOURLY"])
    try:
        sfsc_input.read_input(123)  # Invalid input type
    except TypeError as e:
        assert str(e) == "Input must be a string representing the file path"
    try:
        sfsc_input.read_input("non_existent_file.csv")  # Non-existent file
    except IOError as e:
        assert "Error opening file non_existent_file.csv" in str(e)
    del sfsc_input

def test_SFSCInputModule_read_input_columns():
    # Create a temporary SFSC input file
    sfsc_file =  "./sfsc_input.csv"
    with open(sfsc_file, 'w') as f:
        f.write("SoilMoisture,Temperature\n")
        f.write("0.12,15\n")
        f.write("0.15,16\n")
        f.write("0.20,18\n")

    sfsc_input = SFSCInputModule("SFSCInputTest",MAX_ROWS=2,granularity=STEP_GRANULARITY["HOURLY"])
    try:
        sfsc_input.read_input(str(sfsc_file), 0)  # Read only SoilMoisture column
    except IOError as e:
        assert str(e) == "SFSCInputModule only supports single column input files"
    del sfsc_input
    os.remove(sfsc_file)

def test_SFSCInputModule_step_whole():
    # Create a temporary SFSC input file
    sfsc_file =  "./sfsc_input.csv"
    with open(sfsc_file, 'w') as f:
        f.write("SoilMoisture\n")
        for i in range(10):
            f.write(f"{Decimal('0.1') + i*Decimal('0.05')}\n")
    sfsc_input = SFSCInputModule("SFSCInputTest",MAX_ROWS=0,granularity=STEP_GRANULARITY["HOURLY"])
    sfsc_input.read_input(str(sfsc_file))
    print(sfsc_input.data)
    assert sfsc_input.data_size == 10

    vars_t0 = sfsc_input.get_variables()
    assert vars_t0 == {"SoilMoisture": Decimal('0.1')}
    assert sfsc_input.get_current_timestep() == 0

    sfsc_input.step()
    vars_t1 = sfsc_input.get_variables()
    assert vars_t1 == {"SoilMoisture": Decimal('0.15')}
    assert sfsc_input.get_current_timestep() == 1

    sfsc_input.step()
    vars_t2 = sfsc_input.get_variables()
    assert vars_t2 == {"SoilMoisture": Decimal('0.20')}
    assert sfsc_input.get_current_timestep() == 2

    for i in range(3,11):
        sfsc_input.step()
    vars_t9 = sfsc_input.get_variables()
    assert vars_t9 == None
    assert sfsc_input.get_current_timestep() == 10

    del sfsc_input
    os.remove(sfsc_file)

def test_SFSCInputModule_step_chunk():
    sfsc_file =  "./sfsc_input.csv"
    with open(sfsc_file, 'w') as f:
        f.write("SoilMoisture\n")
        for i in range(10):
            f.write(f"{Decimal('0.1') + i*Decimal('0.05')}\n")
    sfsc_input = SFSCInputModule("SFSCInputTest",MAX_ROWS=3,granularity=STEP_GRANULARITY["HOURLY"])
    sfsc_input.read_input(str(sfsc_file))
    vars_t0 = sfsc_input.get_variables()
    assert vars_t0 == {"SoilMoisture": Decimal('0.1')}
    assert sfsc_input.get_current_timestep() == 0
    assert sfsc_input.data_size == 3

    sfsc_input.step()
    vars_t1 = sfsc_input.get_variables()
    assert vars_t1 == {"SoilMoisture": Decimal('0.15')}
    assert sfsc_input.get_current_timestep() == 1
    
    sfsc_input.step()
    vars_t2 = sfsc_input.get_variables()
    assert vars_t2 == {"SoilMoisture": Decimal('0.20')}
    assert sfsc_input.get_current_timestep() == 2
    assert sfsc_input.data_size == 3

    sfsc_input.step()
    vars_t3 = sfsc_input.get_variables()
    assert sfsc_input.get_current_timestep() == 3
    assert sfsc_input.data_size == 6
    assert vars_t3 =={"SoilMoisture": Decimal('0.25')}

    for i in range(4,9):
        sfsc_input.step()
    
    vars_t8 = sfsc_input.get_variables()
    assert vars_t8 == {"SoilMoisture": Decimal('0.50')}
    assert sfsc_input.get_current_timestep() == 8
    assert sfsc_input.data_size == 9

    sfsc_input.step()
    assert sfsc_input.data_size == 10
    assert sfsc_input.get_current_timestep() == 9
    vars_t9 = sfsc_input.get_variables()
    assert vars_t9 == {"SoilMoisture": Decimal('0.55')}

    sfsc_input.step()
    assert sfsc_input.get_current_timestep() == 10
    vars_t10 = sfsc_input.get_variables()
    assert vars_t10 is None

    del sfsc_input
    os.remove(sfsc_file)

def test_SFSCInputModule_reset():
    # Create a temporary SFSC input file
    sfsc_file =  "./sfsc_input.csv"
    with open(sfsc_file, 'w') as f:
        f.write("SoilMoisture\n")
        for i in range(5):
            f.write(f"{Decimal('0.1') + i*Decimal('0.1')}\n")
    sfsc_input = SFSCInputModule("SFSCInputTest",MAX_ROWS=2,granularity=STEP_GRANULARITY["HOURLY"])
    sfsc_input.read_input(str(sfsc_file))

    sfsc_input.step()  # Timestep 1
    sfsc_input.step()  # Timestep 2
    assert sfsc_input.get_current_timestep() == 2

    sfsc_input.reset()
    assert sfsc_input.get_current_timestep() == 0
    vars_t0 = sfsc_input.get_variables()
    assert vars_t0 == {"SoilMoisture": Decimal('0.1')}

    del sfsc_input
    os.remove(sfsc_file)

def test_SFSCInputModule_assignHeader():
    # Create a temporary SFSC input file
    sfsc_file =  "./sfsc_input.csv"
    with open(sfsc_file, 'w') as f:
        f.write("SoilMoisture\n")
        f.write("0.12\n")
        f.write("0.15\n")

    sfsc_input = SFSCInputModule("SFSCInputTest",MAX_ROWS=2,granularity=STEP_GRANULARITY["HOURLY"])
    sfsc_input.read_input(str(sfsc_file))

    # Assign new header
    sfsc_input.assignHeader("NewSoilMoisture")
    assert sfsc_input.get_variable_names() == ["NewSoilMoisture"]

    del sfsc_input
    os.remove(sfsc_file)


def test_SFSCInputModule_malformedFile():
    # Create a temporary malformed SFSC input file
    sfsc_file =  "./sfsc_input_malformed.csv"
    with open(sfsc_file, 'w') as f:
        f.write("SoilMoisture\n")
        f.write("0.12\n")
        f.write("abc\n")  # Non-numeric value
        f.write("0.20\n")

    sfsc_input = SFSCInputModule("SFSCInputTest",MAX_ROWS=3,granularity=STEP_GRANULARITY["HOURLY"])
    sfsc_input.read_input(str(sfsc_file))

    assert sfsc_input.data_size == 2  # Only two valid rows should be read
    assert sfsc_input.data[0] == Decimal('0.12')
    assert sfsc_input.data[1] == Decimal('0.20')

    del sfsc_input
    os.remove(sfsc_file)