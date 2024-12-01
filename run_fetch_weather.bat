@echo off
echo "Current Directory: %cd%" > debug_log.txt
echo "PATH: %PATH%" >> debug_log.txt
echo "USER: %USERNAME%" >> debug_log.txt
echo "TEMP: %TEMP%" >> debug_log.txt

cd C:\Users\ayman\Desktop\Projects\ETL_Pipeline
C:/Users/ayman/AppData/Local/Programs/Python/Python310/python.exe extract2.py >> debug_log.txt 2>&1
