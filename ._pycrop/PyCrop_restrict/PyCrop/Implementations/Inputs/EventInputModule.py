from PyCrop.Abstract.Core.AbstractInputModule import (
    AbstractInputModule,
    STEP_GRANULARITY
)

class EventInputModule(AbstractInputModule):

    def __init__(self, file_path: str):
        super().__init__(
            name="EventInputModule",
            granularity=STEP_GRANULARITY["SECONDLY"]
        )

        self.file_path = file_path

        # timestep -> list of events
        self.events_by_time = {}

    # Read file
    def read_input(self, input=None, *args) -> None:

        with open(self.file_path, "r") as f:

            for line in f:

                line = line.strip()

                if not line:
                    continue

                t, r, c, event = line.split(",")

                t = int(t)
                r = int(r)
                c = int(c)

                if t not in self.events_by_time:
                    self.events_by_time[t] = []

                self.events_by_time[t].append({
                    "row": r,
                    "col": c,
                    "event": event
                })

        self.data_size = len(self.events_by_time)

    # Get current event
    def get_variables(self) -> dict:

        return {
            "events": self.events_by_time.get(
                self.current_timestep,
                []
            )
        }


    def get_variable_names(self) -> list[str]:
        return ["events"]


    def step(self) -> int:
        self.current_timestep += 1
        return self.current_timestep


    def closeFile(self) -> None:
        self.events_by_time = {}


    def assignHeader(self, header) -> None:
        pass


    def reset(self) -> None:
        self.current_timestep = 0
