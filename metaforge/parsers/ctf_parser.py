from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Callable, Dict, Final, Generator, List, Tuple
from pathlib import Path
from uuid import UUID

from metaforge.common.parser_units import MICRONS_UNITS, DEGREES_UNITS, ANGSTROM_UNITS
from metaforge.common.hkl_constants import CTF_LAUE_CLASS_MAP
from metaforge.parsers.metaforgeparser import MetaForgeParser, MetaForgeMetadata
from metaforge.utilities.path_utilities import file_line_generator

__all__ = ['CtfPhase', 'CtfHeader', 'parse_header', 'parse_header']

CTF_DELIMITER: Final[str] = '\t'

CTF_CHANNEL_TEXT_FILE: Final[str] = 'Channel Text File'
CTF_COLON_CHANNEL_TEXT_FILE: Final[str] = ':Channel Text File'
CTF_PRJ: Final[str] = 'Prj'
CTF_PHASES: Final[str] = 'Phases'

CTF_LONG_TEXT: Final[str] = 'Euler angles refer to Sample Coordinate system (CS0)!'
CTF_MAG: Final[str] = 'Mag'
CTF_COVERAGE: Final[str] = 'Coverage'
CTF_DEVICE: Final[str] = 'Device'
CTF_KV: Final[str] = 'KV'
CTF_TILT_ANGLE: Final[str] = 'TiltAngle'
CTF_TILT_AXIS: Final[str] = 'TiltAxis'

CTF_AUTHOR: Final[str] = 'Author'
CTF_JOB_MODE: Final[str] = 'JobMode'
CTF_X_CELLS: Final[str] = 'XCells'
CTF_Y_CELLS: Final[str] = 'YCells'
CTF_Z_CELLS: Final[str] = 'ZCells'
CTF_X_STEP: Final[str] = 'XStep'
CTF_Y_STEP: Final[str] = 'YStep'
CTF_Z_STEP: Final[str] = 'ZStep'
CTF_ACQ_E1: Final[str] = 'AcqE1'
CTF_ACQ_E2: Final[str] = 'AcqE2'
CTF_ACQ_E3: Final[str] = 'AcqE3'
CTF_EULER: Final[str] = 'Euler'

def euro_to_us_dec_string(text: str) -> str:
  return text.replace(',', '.')

def parse_float(text: str) -> float:
  return float(euro_to_us_dec_string(text))

CTF_HEADER_PARSE_MAP: Final[Dict[str, Callable[[str], Any]]] = {
  CTF_AUTHOR : str,
  CTF_JOB_MODE : str,
  CTF_X_CELLS : int,
  CTF_Y_CELLS : int,
  CTF_Z_CELLS : int,
  CTF_X_STEP : parse_float,
  CTF_Y_STEP : parse_float,
  CTF_Z_STEP : parse_float,
  CTF_ACQ_E1 : parse_float,
  CTF_ACQ_E2 : parse_float,
  CTF_ACQ_E3 : parse_float,
  CTF_EULER : str,
}

CTF_HEADER_UNITS_MAP: Final[Dict[str, str]] = {
  CTF_X_STEP : MICRONS_UNITS,
  CTF_Y_STEP : MICRONS_UNITS,
  CTF_Z_STEP : MICRONS_UNITS,
}

@dataclass
class CtfPhase:
  index: int = 0
  lattice_constants: Tuple[float, float, float] = (0.0, 0.0, 0.0)
  lattice_angles: Tuple[float, float, float] = (0.0, 0.0, 0.0)
  name: str = ''
  group: int = 0
  space_group: int = 0
  comment: str = ''
  internal1: str = ''
  internal2: str = ''

class LaueGroup(IntEnum):
  TRICLINIC = 1
  MONOCLINIC = 2
  ORTHORHOMBIC = 3
  TETRAGONAL_LOW = 4
  TETRAGONAL_HIGH = 5
  TRIGONAL_LOW = 6
  TRIGONAL_HIGH = 7
  HEXAGONAL_LOW = 8
  HEXAGONAL_HIGH = 9
  CUBIC_LOW = 10
  CUBIC_HIGH = 11
  UNKNOWN_SYMMETRY = 12

class CtfHeader:
  def __init__(self) -> None:
    self.phases: Dict[int, CtfPhase] = {}
    self.entries: List[MetaForgeMetadata] = []
    self.unknown_entries: List[MetaForgeMetadata] = []

class CtfParser(MetaForgeParser):

  def __init__(self) -> None:
    self.ext_list: list = ['.ctf']


  def human_label(self) -> str:
    return "Ctf Parser"

  def version(self) -> str:
    return '1.0'
  
  def uuid(self) -> UUID:
    return UUID('{ec915113-8e3e-4e01-b6bc-029c5e2c3518}')

  def supported_file_extensions(self) -> list:
    return self.ext_list
  
  def accepts_extension(self, extension: str) -> bool:
    if extension in self.ext_list:
      return True
    return False

  def parse_float_triplet(self, text: str) -> Tuple[float, float, float]:
    tokens = euro_to_us_dec_string(text).split(';')
    return (float(tokens[0]), float(tokens[1]), float(tokens[2]))

  def parse_phases(self, file: Generator[str, None, None], num_phases: int) -> List[CtfPhase]:
    phases: List[CtfPhase] = []

    for i in range(num_phases):
      line = next(file).strip()
      tokens = line.split('\t')
      lattice_constants = self.parse_float_triplet(tokens[0].strip())
      lattice_angles = self.parse_float_triplet(tokens[1].strip())
      name = tokens[2].strip()
      group = LaueGroup(int(tokens[3]))

      comment = ''
      space_group = 0
      internal1 = ''
      internal2 = ''

      if len(tokens) == 5:
        comment = tokens[4].strip()
      elif len(tokens) == 8:
        space_group = int(tokens[4].strip())
        internal1 = tokens[5].strip()
        internal2 = tokens[6].strip()
        comment = tokens[7].strip()

      phase = CtfPhase(i+1, lattice_constants, lattice_angles, name, group, space_group, comment, internal1, internal2)
      phases.append(phase)

    return phases

  def parse_ctf_long_text(self, tokens: List[str]) -> Dict[str, Any]:
    mag = int(tokens[2].strip())
    coverage = int(tokens[4].strip())
    device = int(tokens[6].strip())
    kv = int(float(tokens[8].strip()))
    tilt_angle = float(tokens[10].strip())
    tilt_axis = float(tokens[12].strip())
    entries = [
      MetaForgeMetadata(f'SOURCE/{CTF_MAG}', mag),
      MetaForgeMetadata(f'SOURCE/{CTF_COVERAGE}', coverage),
      MetaForgeMetadata(f'SOURCE/{CTF_DEVICE}', device),
      MetaForgeMetadata(f'SOURCE/{CTF_KV}', kv),
      MetaForgeMetadata(f'SOURCE/{CTF_TILT_ANGLE}', tilt_angle),
      MetaForgeMetadata(f'SOURCE/{CTF_TILT_AXIS}', tilt_axis),
    ]
    return entries

  def _parse_header(self, filepath: Path) -> CtfHeader:
    file_gen = file_line_generator(filepath)

    ctf_header = CtfHeader()
    for line in file_gen:
      line = line.strip()
      tokens = line.split(CTF_DELIMITER)
      keyword = tokens[0]
      if line.startswith(CTF_CHANNEL_TEXT_FILE) or line.startswith(CTF_COLON_CHANNEL_TEXT_FILE):
        continue
      elif line.startswith(CTF_PRJ):
        ctf_header.entries.append(MetaForgeMetadata(f'SOURCE/{CTF_PRJ}', line[len(CTF_PRJ) + 1:]))
      elif line.startswith(CTF_LONG_TEXT):
        entries = self.parse_ctf_long_text(tokens)
        ctf_header.entries += entries
      elif line.startswith(CTF_PHASES):
        phase_num = int(tokens[1])
        ctf_header.phases = self.parse_phases(file_gen, phase_num)
        break
      elif keyword in CTF_HEADER_PARSE_MAP:
        value = None
        if len(tokens) > 1:
          value = CTF_HEADER_PARSE_MAP[keyword](CTF_DELIMITER.join(tokens[1:]))
        units = CTF_HEADER_UNITS_MAP.get(keyword, '')
        ctf_header.entries.append(MetaForgeMetadata(f'SOURCE/{keyword}', value, '', units))
      else:
        ctf_header.unknown_entries.append(MetaForgeMetadata(f'SOURCE/{keyword}', CTF_DELIMITER.join(tokens[1:])))
    return ctf_header

  def parse_header(self, filepath: Path) -> List[MetaForgeMetadata]:
    header = self._parse_header(filepath)
    entries = header.entries
    phases = header.phases
        
    for phase in phases:
      annotations = f'Phase {phase.index}, {CTF_LAUE_CLASS_MAP.get(phase.index, "Unknown")}'
      entries.append(MetaForgeMetadata(f'SOURCE/Phases/Phase {phase.index}/LaueGroup', str(phase.group.name), annotations))
      entries.append(MetaForgeMetadata(f'SOURCE/Phases/Phase {phase.index}/Internal1', phase.internal1, annotations))
      entries.append(MetaForgeMetadata(f'SOURCE/Phases/Phase {phase.index}/Internal2', phase.internal2, annotations))
      entries.append(MetaForgeMetadata(f'SOURCE/Phases/Phase {phase.index}/LatticeAngles', phase.lattice_angles, annotations, DEGREES_UNITS))
      entries.append(MetaForgeMetadata(f'SOURCE/Phases/Phase {phase.index}/LatticeConstants', phase.lattice_constants, annotations, ANGSTROM_UNITS))
      entries.append(MetaForgeMetadata(f'SOURCE/Phases/Phase {phase.index}/Name', phase.name, annotations))
      entries.append(MetaForgeMetadata(f'SOURCE/Phases/Phase {phase.index}/SpaceGroup', phase.space_group, annotations))
      entries.append(MetaForgeMetadata(f'SOURCE/Phases/Phase {phase.index}/Comment', phase.comment, annotations))

    return entries
