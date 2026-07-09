from PyCrop.Implementations.Engines.SimulationEngine import SimulationEngine
from PyCrop.Implementations.Inputs.SFMCInputModule import SFMCInputModule
from PyCrop.Abstract.Core.AbstractModule import STEP_GRANULARITY
from PyCrop.Implementations.TOMGRO.TOMGROBiomassModule import TOMGROBiomassModule, BIOMASS_DEFAULT_PARAMS
from PyCrop.Implementations.TOMGRO.TOMGROLaiModule import TOMGROLaiModule, LAI_DEFAULT_PARAMS
from PyCrop.Implementations.TOMGRO.TOMGRONodesModule import TOMGRONodesModule, NODES_DEFAULT_PARAMS
from PyCrop.Implementations.Environment.SimpleEnvironmentModule import SimpleEnvironmentModule
import csv
import matplotlib.pyplot as plt
import time
import os

SAVE_EVERY = 24

def export_benchmark(
    rows,
    cols,
    simulation_time,
    filename="benchmark_results.csv"
):

    write_header = not os.path.exists(filename)

    with open(filename, "a", newline="") as f:

        writer = csv.writer(f)

        if write_header:

            writer.writerow([
                "rows",
                "cols",
                "plants",
                "simulation_time_seconds"
            ])

        writer.writerow([
            rows,
            cols,
            rows * cols,
            simulation_time
        ])

    print(f"Benchmark exported to {filename}")
    

def plot_field_heatmap(
    filename="field_results.csv",
    variable="biomass",
    output_file="field_heatmap.png"
):
    data = []

    with open(filename, "r") as f:
        reader = csv.DictReader(f)

        for row in reader:
            data.append(row)

    rows = max(int(r["row"]) for r in data) + 1
    cols = max(int(r["col"]) for r in data) + 1

    grid = [[0 for _ in range(cols)] for _ in range(rows)]

    for r in data:
        i = int(r["row"])
        j = int(r["col"])
        grid[i][j] = float(r[variable])

    plt.figure()
    plt.imshow(grid)
    plt.colorbar(label=variable)
    plt.title(f"Field heatmap - {variable}")
    plt.xlabel("Column")
    plt.ylabel("Row")
    plt.savefig(output_file, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Heatmap saved to {output_file}")
    
   
def export_field_results(results, rows, cols, filename="field_results.csv"):

    with open(filename, "w", newline="") as f:

        writer = csv.writer(f)

        writer.writerow([
            "row",
            "col",
            "plant_id",
            "nodes",
            "lai",
            "biomass",
            "fruit_biomass",
            "mature_fruit_biomass",
            "avg_temperature",
            "max_ppfd"
        ])

        for i in range(rows):
            for j in range(cols):

                plant_id = f"P{i}_{j}"

                temps = results[f"Env_{plant_id}_Temperature"]
                ppfd = results[f"Env_{plant_id}_PPFD"]

                writer.writerow([
                    i,
                    j,
                    plant_id,

                    results[f"Nodes_{plant_id}_Nodes"][-1],

                    results[f"LAI_{plant_id}_LAI"][-1],

                    results[f"Biomass_{plant_id}_W"][-1],

                    results[f"Biomass_{plant_id}_W_f"][-1],

                    results[f"Biomass_{plant_id}_W_m"][-1],

                    sum(temps) / len(temps),

                    max(ppfd)
                ])

    print(f"\nResults exported to {filename}")

# dimensione campo
rows = int(input("Numero righe: "))
cols = int(input("Numero colonne: "))

print(f"\nCampo creato: {rows} x {cols}")
print(f"Totale piante: {rows * cols}\n")

# engine principale
engine = SimulationEngine("Engine")

# un solo csv condiviso da tutte le piante
csv_path = "input_pyCrop.csv"

# Climate input for the shared environment
input_module = SFMCInputModule(
    "SharedInput",
    -1,
    STEP_GRANULARITY["HOURLY"]
)

input_module.read_input(csv_path, 0, 1)

engine.add_input_module(input_module)

# creazione piante
for i in range(rows):

    for j in range(cols):

        plant_id = f"P{i}_{j}"

        print(f"Creo pianta {plant_id}")

        """
        # input climatico
        input_module = SFMCInputModule(
            f"Input_{plant_id}",
            -1,
            STEP_GRANULARITY["HOURLY"]
        )

        input_module.read_input(csv_path, 0, 1)

        engine.add_input_module(input_module)
		"""
		
        # environment
        env = SimpleEnvironmentModule(
            f"Env_{plant_id}",
            granularity=STEP_GRANULARITY["HOURLY"],
            params={

                "Initial_temperature": 15,
                "Initial_solar_radiation": 200,

                "Temperature_delta": 0,
                "Temperature_amplitude": 1,

                "Solar_radiation_delta": 0,
                "Solar_radiation_amplitude": 1,

                # posizione pianta
                "row": i,
                "col": j,

                # dimensioni serra
                "rows": rows,
                "cols": cols,
            },
        )

        # moduli TOMGRO
        nodes = TOMGRONodesModule(
            f"Nodes_{plant_id}",
            params=NODES_DEFAULT_PARAMS
        )

        lai = TOMGROLaiModule(
            f"LAI_{plant_id}",
            params=LAI_DEFAULT_PARAMS
        )

        biomass = TOMGROBiomassModule(
            f"Biomass_{plant_id}",
            params=BIOMASS_DEFAULT_PARAMS
        )

        # aggiunta moduli
        engine.add_module([
            env,
            nodes,
            lai,
            biomass
        ])

        # input -> environment
        """
        engine.bindVariables(
            f"Input_{plant_id}",
            "Temperature",
            f"Env_{plant_id}",
            "Temperature"
        )

        engine.bindVariables(
            f"Input_{plant_id}",
            "Solar_radiation",
            f"Env_{plant_id}",
            "Solar_radiation"
        )
        """
        
        engine.bindVariables(
            "SharedInput",
            "Temperature",
            f"Env_{plant_id}",
            "Temperature"
        )

        engine.bindVariables(
            "SharedInput",
            "Solar_radiation",
            f"Env_{plant_id}",
            "Solar_radiation"
        )

        engine.bindVariables(
            "Engine",
            "Clock",
            f"Env_{plant_id}",
            "Clock"
        )

        # environment -> nodes
        engine.bindVariables(
            f"Env_{plant_id}",
            "Daily_Average_Temperature",
            f"Nodes_{plant_id}",
            "Daily_Average_Temperature"
        )

        # environment -> biomass
        engine.bindVariables(
            f"Env_{plant_id}",
            "Daily_Average_Temperature",
            f"Biomass_{plant_id}",
            "Daily_AVG_Temp"
        )

        engine.bindVariables(
            f"Env_{plant_id}",
            "Daily_Daytime_Average_Temperature",
            f"Biomass_{plant_id}",
            "Daytime_AVG_Temp"
        )

        engine.bindVariables(
            f"Env_{plant_id}",
            "Hour",
            f"Biomass_{plant_id}",
            "Hour"
        )

        engine.bindVariables(
            f"Env_{plant_id}",
            "Temperature",
            f"Biomass_{plant_id}",
            "Temperature"
        )

        engine.bindVariables(
            f"Env_{plant_id}",
            "PPFD",
            f"Biomass_{plant_id}",
            "PPFD"
        )

        engine.bindVariables(
            f"Env_{plant_id}",
            "CO2",
            f"Biomass_{plant_id}",
            "CO2"
        )

        # nodes -> lai
        engine.bindVariables(
            f"Nodes_{plant_id}",
            ["Nodes", "DN"],
            f"LAI_{plant_id}",
            ["Nodes", "Delta_Nodes"]
        )

        # nodes -> biomass
        engine.bindVariables(
            f"Nodes_{plant_id}",
            ["Nodes", "DN"],
            f"Biomass_{plant_id}",
            ["Nodes", "Delta_Nodes"]
        )

        # lai -> biomass
        engine.bindVariables(
            f"LAI_{plant_id}",
            "LAI",
            f"Biomass_{plant_id}",
            "LAI"
        )

# init benchmark
start_time = time.perf_counter()

# esecuzione simulazione
print("\nStarting simulation...\n")
engine.run(save_every=SAVE_EVERY)

end_time = time.perf_counter()

simulation_time = end_time - start_time

print("\nSimulation completed.\n")
print(f"\nSimulation time: {simulation_time:.4f} seconds\n")

# risultati finali
results = engine.get_results()

export_benchmark(
    rows,
    cols,
    simulation_time
)

# check
"""
for i in range(rows):
    for j in range(cols):
        plant_id = f"P{i}_{j}"

        temps = results[f"Env_{plant_id}_Temperature"]
        ppfd = results[f"Env_{plant_id}_PPFD"]

        print(f"\n===== ENV SUMMARY {plant_id} =====")
        print("Avg Temp:", sum(temps) / len(temps))
        print("Max PPFD:", max(ppfd))
        """

for i in range(rows):

    for j in range(cols):

        plant_id = f"P{i}_{j}"

        print(f"\n===== {plant_id} =====")

        print(
            "Nodes:",
            results[f"Nodes_{plant_id}_Nodes"][-1]
        )

        print(
            "LAI:",
            results[f"LAI_{plant_id}_LAI"][-1]
        )

        print(
            "Biomass:",
            results[f"Biomass_{plant_id}_W"][-1]
        )

        print(
            "Fruit Biomass:",
            results[f"Biomass_{plant_id}_W_f"][-1]
        )

        print(
            "Mature Fruit Biomass:",
            results[f"Biomass_{plant_id}_W_m"][-1]
        )

# esportazione dati         
export_field_results(results, rows, cols)

plot_field_heatmap(
    filename="field_results.csv",
    variable="biomass",
    output_file="biomass_heatmap.png"
)
