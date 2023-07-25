from dotenv import load_dotenv
from pathlib import Path
import json
import time
from textwrap import dedent
import os

dotenv_path = Path('.env')
load_dotenv(dotenv_path=dotenv_path)

# load json file
config = json.load(open('config.json'))

def menu_1():
    print("Please select the group you would like to use:")
    print("")
    for i, db in enumerate(config.get("groups")):
        print(f"{i+1}. {db.get('name')}")
    print("")
    print("0. Exit")

    selection = await_input()
    if selection == 0:
        exit()
    if selection > len(config.get("groups")):
        print("Invalid selection")
        menu_1()
    group = config.get("groups")[selection-1]
    menu_2(group)

def menu_2(group):
    print(f"Selected {group.get('name')}")

    db_list = ""

    for i, db in enumerate(group.get("databases")):
        db_list += f"{i+1}. {db.get('name')}\n"

    print(dedent(f'''
        Please select the database you would like to use:
                 
        {db_list}
        
        0. Back
    '''))

    selection = await_input()
    if selection == 0:
        menu_1()
    if selection > len(group.get("databases")):
        print("Invalid selection")
        menu_2(group)
    database = group.get("databases")[selection-1]
    menu_3(database, group)

def menu_3(database, group):
    print(f"Selected {database.get('name')}")
    print(dedent('''
        Please select the action you would like to perform:
    
        1. Backup database
        2. Clone database
        3. Restore database
          
        0. Back
    '''))
    selection = await_input()
    if selection == 0:
        menu_2(group)

    if selection == 1:
        backup_database(database, group)
    elif selection == 2:
        clone_database(database, group)
    elif selection == 3:
        restore_database(database, group)
    else:
        print("Invalid selection")
        menu_3(database, group)

def backup_database(database, group):
    print("Backing up database")
    print("Please wait...")
    dump_database(database, group)
    print("Backup complete")
    menu_3(database, group)

def clone_database(database, group):
    db_list = ""

    dbs = group.get("databases")
    dbs.remove(database)

    for i, db in enumerate(dbs):
        db_list += f"{i+1}. {db.get('name')}\n"

    print(dedent(f'''
        Please select the database you would like to clone to:
        (This will backup and then overwrite the database you select)
                 
        {db_list}    
        0. Back
    '''))

    selection = await_input()
    if selection == 0:
        menu_3(database)
    if selection > len(dbs):
        print("Invalid selection")
        clone_database(database)
    destination_database = group.get("databases")[selection-1]

    print("Backing up " + destination_database.get("name"))
    print("Please wait...")
    dest_db_file = dump_database(destination_database, group)
    print("Backup complete")

    print("Backing up " + database.get("name"))
    print("Please wait...")
    source_db_file = dump_database(database, group)
    print("Backup complete")

    print("Nuking " + destination_database.get("name"))
    os.system(f"psql {destination_database.get('url')} -c 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;'")
    print("Nuke complete")

    print("Cloning " + database.get("name") + " to " + destination_database.get("name"))
    os.system(f"psql {destination_database.get('url')} < backups/{group.get('name')}/{database.get('name')}/{source_db_file}")
    print("Clone complete")

def restore_database(database, group):
    pass

def dump_database(database, group):
    if not Path(f"backups/{group.get('name')}/").is_dir():
        Path(f"backups/{group.get('name')}/").mkdir()

    if not Path(f"backups/{group.get('name')}/{database.get('name')}/").is_dir():
        Path(f"backups/{group.get('name')}/{database.get('name')}/").mkdir()

    new_file_name = time.strftime("%d-%m-%y-%H-%M-%S", time.localtime())
    os.system(f"pg_dump {database.get('url')} > backups/{group.get('name')}/{database.get('name')}/{new_file_name}.sql")

    return new_file_name + ".sql"

def await_input():
    while True:
        try:
            selection = int(input("Selection: "))
            break
        except ValueError:
            print("Invalid selection")
            continue
    return selection

if not len(config.get("groups")) > 0:
    print("No groups found in config.json")
    exit()

print("Welcome to Database Switcher")
menu_1()