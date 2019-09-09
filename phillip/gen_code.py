"""Generate gecko code for booting into match."""

import enum

template = """
$Match Setup
C21B148C 00000025 #BootToMatch.asm
3C608048 60630530
48000021 7C8802A6
38A000F0 3D808000
618C31F4 7D8903A6
4E800421 480000F8
4E800021 0808024C
00000000 000000FF
000000{stage} 00000000
00000000 00000000
00000000 FFFFFFFF
FFFFFFFF 00000000
3F800000 3F800000
3F800000 00000000
00000000 00000000
00000000 00000000
00000000 00000000
00000000 00000000
00000000 {char1}{player1}0400
00FF0000 09007800
400004{cpu1} 00000000
00000000 3F800000
3F800000 3F800000
{char2}{player2}0400 00FF0000
09007800 400004{cpu2}
00000000 00000000
3F800000 3F800000
3F800000 09030400
00FF0000 09007800
40000401 00000000
00000000 3F800000
3F800000 3F800000
09030400 00FF0000
09007800 40000401
00000000 00000000
3F800000 3F800000
3F800000 BB610014
60000000 00000000
"""

char_ids = {
  'falcon': 0x0,
  'dk': 0x1,
  'fox': 0x2,
  'gaw': 0x3,
  'kirby': 0x4,
  'bowser': 0x5,
  'link': 0x6,
  'luigi': 0x7,
  'mario': 0x8,
  'marth': 0x9,
  'mewtwo': 0xA,
  'ness': 0xB,
  'peach': 0xC,
  'pikachu': 0xD,
  'ics': 0xE,
  'puff': 0xF,
  'samus': 0x10,
  'yoshi': 0x11,
  'zelda': 0x12,
  'sheik': 0x13,
  'falco': 0x14,
  'ylink': 0x15,
  'doc': 0x16,
  'roy': 0x17,
  'pichu': 0x18,
  'ganon': 0x19,
}

stage_ids = {
  'fod': 0x2,
  'stadium': 0x3,
  'PeachsCastle': 0x4,
  'KongoJungle': 0x5,
  'Brinstar': 0x6,
  'Corneria': 0x7,
  'yoshis_story': 0x8,
  'Onett': 0x9,
  'MuteCity': 0xA,
  'RainbowCruise': 0xB,
  'jungle_japes': 0xC,
  'GreatBay': 0xD,
  'HyruleTemple': 0xE,
  'BrinstarDepths': 0xF,
  'YoshiIsland': 0x10,
  'GreenGreens': 0x11,
  'Fourside': 0x12,
  'MushroomKingdomI': 0x13,
  'MushroomKingdomII': 0x14,
  'Akaneia': 0x15,
  'Venom': 0x16,
  'PokeFloats': 0x17,
  'BigBlue': 0x18,
  'IcicleMountain': 0x19,
  'IceTop': 0x1A,
  'FlatZone': 0x1B,
  'dream_land': 0x1C,
  'yoshis_island_64': 0x1D,
  'KongoJungle64': 0x1E,
  'battlefield': 0x1F,
  'final_destination': 0x20,
}


class PlayerStatus(enum.IntEnum):
  HUMAN = 0
  CPU = 1


def byte_str(x):
  return '{0:02X}'.format(x)


def setup_match_code(
    stage='final_destination',
    player1=PlayerStatus.CPU,
    char1='falcon',
    cpu1=9,
    player2=PlayerStatus.HUMAN,
    char2='falcon',
    cpu2=9,
  ):
  kwargs = dict(
    stage=stage_ids[stage],
    player1=player1,
    char1=char_ids[char1],
    cpu1=cpu1,
    player2=player2,
    char2=char_ids[char2],
    cpu2=cpu2,
  )
  kwargs = {k: byte_str(v) for k, v in kwargs.items()}
  return template.format(**kwargs)

