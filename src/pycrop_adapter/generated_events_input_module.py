from __future__ import annotations

import csv
from pathlib import Path

try:
    from PyCrop.Abstract.Core.AbstractInputModule import AbstractInputModule, STEP_GRANULARITY
except ImportError:
    class AbstractInputModule:
        def __init__(self, name='AbstractInputModule', granularity=1):
            self.name=name
            self.granularity=granularity
            self.current_timestep=0
            self.data_size=-1
        def get_name(self):
            return self.name
    STEP_GRANULARITY={"SECONDLY": 1}


class GeneratedEventsCsvInputModule(AbstractInputModule):
    def __init__(self, file_path: str, name: str = 'GeneratedEventsInput', granularity: int = STEP_GRANULARITY['SECONDLY']):
        super().__init__(name=name, granularity=granularity)
        self.file_path = str(file_path)
        self.events_by_time: dict[int, list[dict]] = {}

    def get_name(self):
        return self.name

    def read_input(self, input=None, *args) -> None:
        path = Path(input or self.file_path)
        self.events_by_time = {}

        with path.open('r', newline='') as f:
            sample = f.read(2048)
            f.seek(0)
            try:
                has_header = csv.Sniffer().has_header(sample)
            except csv.Error:
                has_header = True
            reader = csv.reader(f)
            header = [col.strip() for col in next(reader)] if has_header else []

            for row in reader:
                row = [cell.strip() for cell in row]
                if not row or all(not cell for cell in row):
                    continue
                event_record = self._parse_row(row, header)
                timestep = int(event_record.pop('timestep'))
                self.events_by_time.setdefault(timestep, []).append(event_record)

        self.data_size = max(self.events_by_time.keys(), default=-1) + 1

    def _parse_row(self, row: list[str], header: list[str]) -> dict:
        if header:
            lowered = [h.lower() for h in header]
            data = dict(zip(lowered, row))
            if {'step', 'event'} <= set(lowered):
                return {'timestep': int(data['step']), 'event': data['event'], 'target': data.get('target') or None}
            if {'timestep', 'event'} <= set(lowered):
                return {'timestep': int(data['timestep']), 'event': data['event'], 'row': int(data.get('row',0) or 0), 'col': int(data.get('col',0) or 0), 'target': data.get('target') or None}
            if {'time', 'event'} <= set(lowered):
                return {'timestep': int(data['time']), 'event': data['event'], 'target': data.get('target') or None}
        if len(row) == 4:
            return {'timestep': int(row[0]), 'row': int(row[1]), 'col': int(row[2]), 'event': row[3], 'target': None}
        if len(row) >= 2:
            return {'timestep': int(row[0]), 'event': row[1], 'target': row[2] if len(row) >= 3 and row[2] else None}
        raise ValueError(f'Unsupported event row format: {row!r}')

    def get_variables(self):
        return {'events': self.events_by_time.get(self.current_timestep, [])}

    def get_variable_names(self):
        return ['events']

    def step(self) -> int:
        self.current_timestep += 1
        return self.current_timestep

    def closeFile(self) -> None:
        self.events_by_time = {}

    def assignHeader(self, header) -> None:
        return None

    def reset(self) -> None:
        self.current_timestep = 0
