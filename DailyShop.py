import CaseCards
import json
from datetime import *
import random
import os

today = date.today()
now = str(date.today()) + '_' + str(datetime.now().hour)

def generate():
  now = str(date.today()) + '_' + str(datetime.now().hour)
  global generated
  try:
    with open(f'shop/{now}.json', 'r') as file:
      global data
      data = json.load(file)
      generated = True
  except FileNotFoundError:
    data = {}
    generated = False

generate()

def save_data():
  with open(f'shop/{now}.json', 'w') as file:
    json.dump(data, file)

def add_item(id, card): 
    data[id] = card
    save_data()


def main():
  global generated
  if not generated:
    
    path = 'shop/'
    
    for file in os.listdir(path):
      delete = path + file
      os.remove(delete)
    
    common = random.randint(6, 8)
    uncommon = random.randint(4, 6)
    rare = random.randint(2, 4)
    epic = random.randint(1, 2)
    
    for i in range(1, common + 1):
      card = random.randint(0, len(CaseCards.PackableCommon) - 1)
      add_item(i, CaseCards.PackableCommon[card])
      CaseCards.PackableCommon.pop(card)
  
    for i in range(1, uncommon + 1):
      card = random.randint(0, len(CaseCards.PackableUncommon) - 1)
      add_item(i + common, CaseCards.PackableUncommon[card])
      CaseCards.PackableUncommon.pop(card)
    
    rare = random.randint(1, 2)
    for i in range(1, rare + 1):
      card = random.randint(0, len(CaseCards.PackableRare) - 1)
      add_item(i + common + uncommon, CaseCards.PackableRare[card])
      CaseCards.PackableRare.pop(card)
  
    for i in range(1, epic + 1):
      card = random.randint(0, len(CaseCards.PackableEpic) - 1)
      add_item(i + common + uncommon + rare, CaseCards.PackableEpic[card])
      CaseCards.PackableEpic.pop(card)

    generated = True
