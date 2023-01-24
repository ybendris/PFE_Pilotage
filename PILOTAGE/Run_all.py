import subprocess
import signal
import rdp

processes = [subprocess.Popen(["python", "pilotage_central.py"]),
    subprocess.Popen(["python", "pilotage_log_collect.py"]),
    subprocess.Popen(["python", "pilotage_data_collect.py"]),
    subprocess.Popen(["python", "pilotage_procexec.py"]),
    subprocess.Popen(["python", "pilotage_hub_spv.py"]),
    subprocess.Popen(["python", "pilotage_ihm_spv.py"]),
    subprocess.Popen(["python", "pilotage_CAP.py"]),
    subprocess.Popen(["python", "pilotage_BAP.py"])
]

def handle_sigint(sig, frame):
    for process in processes:
        process.terminate()
    print("Processes terminated")
    exit(0)


# Connect the signal to the handler
signal.signal(signal.SIGINT, handle_sigint)

# Wait for the process to terminate
while any(process.poll() is None for process in processes):
    signal.pause()