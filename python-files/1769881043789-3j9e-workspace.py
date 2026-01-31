import subprocess
workspace_str = "1"
workspaces = ["I","II","III","IV"]
workspace = subprocess.run("komorebic query focused-workspace-name", shell=True, capture_output=True,text=True).stdout.strip()
if workspace in workspaces:
    workspace_str = str(workspaces.index(workspace) +1)
with open(r"C:\Users\Alexander\Documents\Rainmeter\Skins\catppuccin\@resources\inc\workspace.txt", "w") as f:
    f.write(workspace_str)
