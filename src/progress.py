import util
import os
import matplotlib.pyplot as plt
from datetime import datetime

users_json = util.read_json(os.path.join(util.getUsersPath(), "credentials.json"))
data_json = util.read_json(os.path.join(util.getUsersPath(), "data2.json"))

users_list = [user["username"] for user in users_json]

while True:
    print("Available users:")
    for i in range(len(users_list)):
        print(f"{i+1}. {users_list[i]}")
    user_index = int(input("Select a user: ")) - 1

    if user_index < 0 or user_index >= len(users_list):
        print("\nInvalid user!")
    else:
        break

if not users_list[user_index] in data_json.keys():
    print("\nNo data available for this user!")
else:
    while True:
        exercises_list = []
        for date in data_json[users_list[user_index]]:
            exercises_list += data_json[users_list[user_index]][date].keys()
        exercises_list = list(set(exercises_list))

        print("\n")
        print("Available exercises:")
        for i in range(len(exercises_list)):
            print(f"{i+1}. {exercises_list[i]}")
        exercise_index = int(input("Select an exercise: ")) - 1

        if exercise_index < 0 or exercise_index >= len(exercises_list):
            print("\nInvalid exercise!")
        else:
            break

    #dates = list(data_json[users_list[user_index]].keys())
    # ricavo una lista dates che contiene tutte le date (chiavi del dizionario) in cui l'utente ha eseguito l'esercizio selezionato
    dates = [date for date in data_json[users_list[user_index]].keys() if exercises_list[exercise_index] in data_json[users_list[user_index]][date].keys()]
    dates.sort()
    durations = []
    accuracy = []

    for date in dates:
        if exercises_list[exercise_index] in data_json[users_list[user_index]][date].keys():
            durations.append(data_json[users_list[user_index]][date][exercises_list[exercise_index]]["avg_time"])
            accuracy.append(data_json[users_list[user_index]][date][exercises_list[exercise_index]]["accuracy"])

    # Conversione delle date in formato DD/MM/YYYY HH:MM
    dates = [datetime.strptime(date, "%d-%m-%Y-%H-%M-%S").strftime("%d/%m/%Y %H:%M") for date in dates]

    # Crea la figura e due assi per i due grafici affiancati
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))  # Disposizione orizzontale

    print(dates)
    print(accuracy)

    # Grafico 1: Accuratezza
    ax1.plot(dates, accuracy, color='tab:red', marker='o')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Accuracy')
    ax1.set_title(f"Accuracy over Time for {exercises_list[exercise_index].replace('_', ' ')}")
    ax1.grid(True)
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=-45, ha="left")

    # Grafico 2: Tempo Medio
    ax2.plot(dates, durations, color='tab:blue', marker='o')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Avg Time (s)')
    ax2.set_title(f"Average Time over Time for {exercises_list[exercise_index].replace('_', ' ')}")
    ax2.grid(True)
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=-45, ha="left")

    # Layout e visualizzazione
    plt.tight_layout()
    plt.show()