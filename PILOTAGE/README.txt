https://www.python.org/downloads/release/python-3108/


Pilotage:

Activer le virtual env:
Sur windows:
	# Dans cmd.exe
	venv\Scripts\activate.bat

	# Dans un PowerShell
	venv\Scripts\Activate.ps1
		Si une erreur apparait car l’exécution de scripts est désactivée sur ce système.
		1. Démarrer Windows Powershell, en tant qu’Administrateur.
		2. Taper la commande suivante :
			set-executionpolicy unrestricted

Les commandes suivantes ont été installée dans le virtual environnement:
	pip install Flask, Flask_cors, Flask_socketio


Pour désactiver le virtual env:
	deactivate

IHM:
Installer Node.js sur https://nodejs.org/en/
	Version utilisée: 18.12.1 LTS

Installer Angular CLI:
	npm install -g @angular/cli

Lancer le serveur de développement:
	ng serve --open



Utilisation:
Lancer le central en premier:
	py .\pilotage_central.py
	