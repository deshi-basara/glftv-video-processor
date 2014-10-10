import subprocess

def profile_job(cmd):
    # Start the video conversion cmd
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    print(process.communicate())