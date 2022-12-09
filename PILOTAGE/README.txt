# PILOTAGE:

Ce projet représente les applications Python à lancer pour faire les différentes fonction de la partie pilotage du projet CASYOPE

## Prérequis

- Python 3.10.8 ou supérieur (Nous n'avons pas testé avec des versions inférieurs)
https://www.python.org/downloads/release/python-3108/

## Installation

1. Installez les dépendances:
	pip install -r requirements.txt

2. Lancez les applications dans cet ordre:
	#Lancer le central en 1er
		py pilotage_central.py

	#Lancer les collecteurs en 2ème
		py pilotage_log_collect.py
		py pilotage_data_collect.py

	#Lancer les superviseurs en  3ème
		py pilotage_ihm_spv.py
	
	TODO parler des spv des capteurs.


## Installation de l'environnement de développement
Un environnement de développement a été mis en place pendant de développement pour l'activer, il faut:

1. Ouvrir une console dans le dossier PILOTAGE/:

2. Activer le virtual env:
	# Sur windows, dans cmd.exe
	venv\Scripts\activate.bat

	# Sur windows, dans un PowerShell
	venv\Scripts\Activate.ps1
		Si une erreur apparait car l’exécution de scripts est désactivée sur ce système.
		2.1. Démarrer Windows Powershell, en tant qu’Administrateur.
		2.2. Taper la commande suivante :
			set-executionpolicy unrestricted

3. Pour mettre à jour le fichier requirements.txt
	pip freeze > requirements.txt

4. Pour désactiver le virtual env:
	deactivate





# IHM:
Installer Node.js sur https://nodejs.org/en/
	Version utilisée: 18.12.1 LTS

Installer Angular CLI:
	npm install -g @angular/cli

Lancer le serveur de développement:
	ng serve --open



Utilisation:
Lancer le central en premier:
	py .\pilotage_central.py
	