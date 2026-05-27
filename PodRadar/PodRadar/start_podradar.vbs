' start_podradar.vbs
' Launches PodRadar silently without needing VS Code or PATH setup.
' Uses hardcoded Python path.

Dim pythonPath
Dim scriptPath
pythonPath = "C:\Users\sumas\AppData\Local\Programs\Python\Python311\python.exe"
scriptPath = "C:\Users\sumas\Downloads\PodRadar\PodRadar\main.py"

' Check if already running
Set objWMI = GetObject("winmgmts:\\.\root\cimv2")
Set objProcesses = objWMI.ExecQuery("SELECT * FROM Win32_Process WHERE Name='python.exe'")

Dim alreadyRunning
alreadyRunning = False

For Each proc In objProcesses
    If InStr(proc.CommandLine, "main.py") > 0 Then
        alreadyRunning = True
    End If
Next

' Only launch if not already running
If Not alreadyRunning Then
    Set objShell = CreateObject("WScript.Shell")
    objShell.Run """" & pythonPath & """ """ & scriptPath & """", 0, False
End If