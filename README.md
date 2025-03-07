<img src="[https://cdn.discordapp.com/attachments/606154391405199380/828385308672393216/GossHaragIconFull.fw.png](https://raw.githubusercontent.com/AsteriskAmpersand/MHWs_Tex_Chopper/refs/heads/main/MH_Tex_Chop.fw.png)" width="150"> 

# Monster Hunter Wilds Tex Chopper  

A Python library and application for converting from MH Wilds textures to DDS and back. [The original library for all non-Wilds RE Engine games is here.](https://github.com/AsteriskAmpersand/MHR_Tex_Chopper/tree/main)

## Credit
#### Silvris
- For the code for unpacking the streaming versions of textures taken from his MHR-Texture-Scripts Repository (https://github.com/Silvris/MHR-Texture-Scripts). 
- For his documentation in the multiple tex variants used in other RE Engine games. 
- And the many very productive discussions on the format and the swizzling procedure.  
#### K0lb3
- For the astc_decomp library which I modified to have ASTC decompression (the code is bundled with the modified version of his library to remove the PIL dependency).  
#### Ando
- For his mapping of the MHRise texture format codes.  
- For his GDeflate Python wrapper

## Usage
The exe versions are drag and drop. Download the exe appropiate to your intended game.

## Setting Up
### Requirements
- Python 3.7
- PyInstaller
- PyEnv (Python Environment setup)
- astc_decomp (a modified wheel without PIL dependency is provided on the repo)
- construct

### Compilation
Setup a virtual environment on the project folder and install the dependencies. Construct can be installed through `pip install construct`, however astc_decomp (if you want to compile a light weight version that doesn't require the entirety of PIL) needs to be installed from the modified wheel provided in the repo through `pip install astc_decomp-1.0.3-cp37-cp37m-win_amd64.whl`. If this wheel is not compatible, unzip the astc-decomp-clean.zip file and recompile it into a wheel suitable to your operating system and install said wheel.

The mainFactory.py file generates PyInstaller spec files, main.py files and the List_Compiler.bat. This file in turn generates the distributable executables for every game supported game version. The mainFactory builds this files based on main.py and main.spec. main.spec requires changing the path to the project to the correct location.

### Tests
The file tests.py needs to be edited to the correct path of the MHWs chunk and run at least once to generate a list of test cases for verifying the correct functioning of the MHRise side of the converter code.

### Issue Reporting
The core purpose of this library is MH Wilds texture handling. MH Wilds issues should provide eitther a link to a problematic file or the game asset path and an explanation of what the issue is. Please check the following list of common issues before raising an issue:
- Textures SHOULD have power of 2 dimensions on each dimension. There are exceptions but unless you know exactly what you are doing don't try.

## License
GPL 3.0
