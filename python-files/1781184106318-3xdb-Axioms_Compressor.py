import os
import subprocess

file_path = r"F:\AirQuants\Groups\Axioms\E1_Ecosystem\Training_Command_Files\a.mp4"
FFMPEG_File_Path = r"F:\AirQuants\Groups\Axioms\E1_Ecosystem\Training_Command_Files\ffmpeg.exe"

if not os.path.exists(file_path):
    print("File Not Found")
    exit()


print("Passing Through Compressing Pipeline\n Please Wait Till File Get Converted")

def Compress_MP4():
    output_file = "compressed_" + os.path.basename(file_path)

    commands = [
             FFMPEG_File_Path,
            "-i", file_path,
            "-vcodec", "libx264",
            "-crf", "28",
            "-preset", "fast",
            "-acodec", "aac",
            "-b:a", "128k",
            output_file
        ]

    subprocess.run(commands)
    print(f"Process Ended\nYour MP4 Is Compressed Through Axiom`s Compressor {output_file}")

    
def Compress_MP3():
    output_file = "compressed_" + os.path.basename(file_path)

    commands = [
            FFMPEG_File_Path,
            "-i", file_path,
            "-b:a", "128k",
            output_file
        ]   

    subprocess.run(commands)
    print(f"Process Ended\nYour MP3 Is Compressed Through Axiom`s Compressor {output_file}")


if file_path.endswith(".mp4"):
    Compress_MP4()

elif file_path.endswith(".mp3"):
    Compress_MP3()

else:
    print("Only MP4 and MP3 files are supported.")

# -- Rudra --
#  - By Owner Of Axiom Group Of Developers Pvt. Ltd.