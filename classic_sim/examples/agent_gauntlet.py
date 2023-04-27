import sys
sys.path.append('../')

from enums import *
from strategy import GreedyActionSmart
from game_manager import GameManager
from zones import Deck
from statistics import mean
from mpi4py import MPI
from random import uniform, gauss

basic_mage = [
    "Arcane Missiles",
    "Arcane Missiles",
    "Murloc Raider",
    "Murloc Raider",
    "Arcane Explosion",
    "Arcane Explosion",
    "Bloodfen Raptor",
    "Bloodfen Raptor",
    "Novice Engineer",
    "Novice Engineer",
    "River Crocolisk",
    "River Crocolisk",
    "Arcane Intellect",
    "Arcane Intellect",
    "Raid Leader",
    "Raid Leader",
    "Wolfrider",
    "Wolfrider",
    "Fireball",
    "Fireball",
    "Oasis Snapjaw",
    "Oasis Snapjaw",
    "Polymorph",
    "Polymorph",
    "Sen'jin Shieldmasta",
    "Sen'jin Shieldmasta",
    "Nightblade",
    "Nightblade",
    "Boulderfist Ogre",
    "Boulderfist Ogre"
]
basic_warrior = [
    "Boulderfist Ogre",
    "Boulderfist Ogre",
    "Charge",
    "Charge",
    "Dragonling Mechanic",
    "Dragonling Mechanic",
    "Execute",
    "Execute",
    "Fiery War Axe",
    "Fiery War Axe",
    "Frostwolf Grunt",
    "Frostwolf Grunt",
    "Gurubashi Berserker",
    "Gurubashi Berserker",
    "Heroic Strike",
    "Heroic Strike",
    "Lord of the Arena",
    "Lord of the Arena",
    "Murloc Raider",
    "Murloc Raider",
    "Murloc Tidehunter",
    "Murloc Tidehunter",
    "Razorfen Hunter",
    "Razorfen Hunter",
    "Sen'jin Shieldmasta",
    "Sen'jin Shieldmasta",
    "Warsong Commander",
    "Warsong Commander",
    "Wolfrider",
    "Wolfrider"
]
basic_hunter = [
    "Arcane Shot",
    "Arcane Shot",
    "Stonetusk Boar",
    "Stonetusk Boar",
    "Timber Wolf",
    "Timber Wolf",
    "Tracking",
    "Tracking",
    "Bloodfen Raptor",
    "Bloodfen Raptor",
    "River Crocolisk",
    "River Crocolisk",
    "Ironforge Rifleman",
    "Ironforge Rifleman",
    "Raid Leader",
    "Raid Leader",
    "Razorfen Hunter",
    "Razorfen Hunter",
    "Silverback Patriarch",
    "Silverback Patriarch",
    "Houndmaster",
    "Houndmaster",
    "Multi-Shot",
    "Multi-Shot",
    "Oasis Snapjaw",
    "Oasis Snapjaw",
    "Stormpike Commando",
    "Stormpike Commando",
    "Core Hound",
    "Core Hound"
]

agents = {
  'uniform_random_agent': [uniform(-10, 10) for i in range(21)],
  'gaussian_random_agent': [gauss(0, 1) for i in range(21)],
  'uniform_big_range_agent': [uniform(-20, 20) for i in range(21)],
  'gaussian_big_random_agent': [gauss(0, 10) for i in range(21)],
  'handmade_agent': [-0.1, 1, -1, 1, 1, 2, 2, 1.5, 3, -3, 1, -1, 1, -1, 1, -1, 1, -1, -1, 0, 1],
  'mage_agent': [-6.30930064220375, 3.091874348044037, -6.790822546926796, -4.378467750148789, -0.8574207485421077, 9.089306035290257, 8.03074509395254, 6.504327063311184, 9.965734991863016, -4.592153540775539, -2.6633526968654087, -9.440514068705866, -9.354643495575266, -0.6833605761973534, 3.761689862095949, 6.369749949507067, -1.1518607311441968, 0.5478485048174786, 1.548645735116839, -3.437208480581903, -7.424767157011272],
  'hunter_agent': [-4.058971271031244, 2.1097634416195774, -1.8912384626642584, -0.05767500466243369, -1.6842945838523846, 7.262959220816892, 3.1318965653591295, 3.99463564279354, 9.901794307893734, 2.0026365717083667, 4.506207187306231, 9.159092434572809, 0.39961053565188465, -2.7335121257341033, 0.43248792231032773, -2.713591214930224, -1.0126169802546432, 6.444766518351983, 9.434699741664662, 3.6748772341665, 5.300157254256423],
  'warrior_agent': [-9.206668925240766, 0.46439987693736207, -4.243421070296598, 2.500776867990586, -0.3650013841396067, -0.9365588564010352, 9.169870100641706, 8.554686947411533, 6.498323223590283, 7.535773901931282, -0.5256028433840054, -1.793645091119327, 4.7372734059884625, -6.217831834179792, -5.484159837998648, 5.732531168240643, -6.268097913929314, 1.5790775714886767, -2.0947944907594866, -7.590179691483694, 5.289212641484882],
  'magev3smarter': [-9.854581441763525, 2.657496233411372, -3.6072743836534915, -0.6478507131609952, -5.088893271660031, 7.887471404722554, 3.7086334661485125, 1.548993522919302, -5.93328226799545, -8.05241041210411, 2.913315742740263, -5.514530992036361, -0.8364601792409374, 3.1159253138681677, 2.561393716573111, -8.593355960935654, -7.591839617288403, 3.7209453403110366, -2.04326490991847, 1.0229424944333392, -5.473427125141708],
  'hunterv3smarter': [-9.245836563752468, 6.535637553159926, 5.854314844973796, 9.057238865246468, -4.791810370896094, 4.64469557202265, 8.699578386559658, 7.502711397905475, 2.292278716637421, 8.190804827802953, -0.3459011100584526, -4.977193082239277, 8.216475885171619, -2.311341131108609, -6.968293150693105, 4.263720118140705, -1.8990974760107466, 3.9559629257655526, -3.879377391895275, -7.005762213538096, -8.236311859528769],
  'warriorv3smarter': [-7.636410158099602, -5.289945697148861, -1.882124283690505, -4.975148150421651, -1.701047943799317, 7.868744892576615, 3.9166519184732103, 6.337684467437011, 4.4234049016361325, 1.2589507924678962, 6.401783861312502, -7.543752886934783, -1.8591074526400497, -8.928997965329588, -6.43569418290501, -4.530507363337004, 8.699927098013287, -6.509241118388016, -7.206145512039443, 0.07572489321879772, 6.291185934210294],
}

def main():
  comm = MPI.COMM_WORLD
  num_cores = comm.Get_size()
  rank = comm.Get_rank()
  for player_agent in ["gaussian_random_agent", "uniform_big_range_agent", "gaussian_big_random_agent"]:
    enemy_agent = "handmade_agent"
    player_class = "W"
    for enemy_class in ["M", "H", "W"]:
      my_results = evaluate(rank, player_class, enemy_class, agents[player_agent], agents[enemy_agent])
      all_results = comm.gather(my_results, root=0)
      if rank == 0:
        means = tuple(map(mean, zip(*all_results)))
        print(f"{player_agent}({player_class}) vs {enemy_agent}({enemy_class}) => {means}")

def evaluate(rank, agent_class, enemy_class, player_agent, enemy_agent):
  games_to_play = 10

  class_setups = {
    "M": (Classes.MAGE, [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_MAGE], Deck.generate_from_decklist(basic_mage)),
    "H": (Classes.HUNTER, [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_HUNTER], Deck.generate_from_decklist(basic_hunter)),
    "W": (Classes.WARRIOR, [CardSets.CLASSIC_NEUTRAL, CardSets.CLASSIC_WARRIOR], Deck.generate_from_decklist(basic_warrior))
  }

  game_manager = GameManager()
  player_class_enum, player_cardset, player_decklist = class_setups[agent_class]
  enemy_class_enum, enemy_cardset, enemy_decklist = class_setups[enemy_class]
  game_manager.build_full_game_manager(player_cardset, enemy_cardset, player_class_enum, player_decklist, GreedyActionSmart(player_agent), enemy_class_enum, enemy_decklist, GreedyActionSmart(enemy_agent))
  return game_manager.simulate(games_to_play, silent=True, parralel=1, rng=True, rank=rank)

if __name__ == '__main__':
  main()