from commands import execute_command

command = input("Command: ")

if not execute_command(command):
    print("Unknown command.")