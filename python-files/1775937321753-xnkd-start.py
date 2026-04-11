import os

nickname = "Username" -cp "client.jar;coremods\\\\*;libraries\\\\*;libraries\\\\forge\\\\*;libraries\\\\ic2\\\\*;libraries\\\\jinput\\\\*;libraries\\\\log4j\\\\*;libraries\\\\loliland\\\\core\\\\*;libraries\\\\loliland\\\\*;libraries\\\\loliland\\\\msw\\\\*;libraries\\\\lwjgl\\\\*;libraries\\\\twitch\\\\*" -Djava.library.path=".\\\\natives" net.minecraft.launchwrapper.Launch -username={nickname} --version 1.7.10 --gameDir ".\\\\" --assetsDir ".\\\\asset1.7.10" --assetIndex 1.7.10 --uuid 00000000-0000-0000-0000-000000000000 --accessToken null --userProperties [] --userType legacy --tweakClass cpw.mods.fml.common.launcher.FMLTweaker --width 1110 --height 636"""

os.system(cmd)
