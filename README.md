# Next-Generation Point-n-Click Engine
## Introduction
NG-PCE is a modern Point & Click engine inspired by SCUMM, the engine Lucasart used to create games such as DOTT, Sam & Max HTR or CMI.  
NG-PCE has really been designed to become the next-generation successor to SCUMM, but with cool features such as easy cross-platform deployment, builtin object animation, modern assets and a big layer of abstraction in the scripting language.

To do so without reinventing everything, NG-PCE is based on PyCAPGE, an excellent Python-powered Point & Click engine.
I love PyCAPGE, but as it is primarily an engine made for education, in my opinion it lacks some features necessary to create a "real" game and to make it really SCUMM-like.  

That is why I decided to tinker with it a lot to perfectly fit my needs. I plan to implement:
- A full and clean separation between the main engine, the game logic and the scenes/interactions management
- A simple and intuitive descriptive scripting language to fasten game programming, called PCScript
- A set of tools for developers to make coding life easy
- Build tools to automatically compile your games for desktop, mobile and web
- Fully and easily customisable UI
- And a lot more !!


**P.S.** : I know NG-PCE is an ugly name, don't worry, this is a temporary name used while the engine is in developement.  
It will get a very cool name once it will be released !

## Installation
> [!WARNING]
> NG-PCE is still in beta version. The provided releases are not guaranteed to work on all systems and the software is still full of bugs.

NG-PCE is available on  **PyPi** for easy installation.  
To get it on your machine, simply open a terminal and run `pip install ng-pce`

> [!NOTE]
> If you get problems with building or running pygame or some of its dependencies, you can try to uninstall it with `pip uninstall pygame` then use your system package manager with `sudo apt-get install python-pygame`
## Making a game with NG-PCE
### Vocabulary

NG-PCE's vocabulary is a combination of PCS-ANS and PyCAPGE vocabulary.
I thought a lot about it so it is as simple and intuitive as possible.  
Here is an *as complete as possible* list of the vocabulary we will be using in the documentation and manual:

- A **Game** means the entirety of what you will create. It consists of the scripts, the assets, the language patches, the config files and everything that is specific to your game (the engine, for example is not part of the game)
- A **Scene** is a sub-part of a **game**. It is the equivalent of a **room** in PCS-ANS. It consists of a background image and can contain **objects**.
- A **Hotspot** is an object in a **scene** with which the player can interact.
- An **Item** is anything that can be in the player's inventory.
- An **Ambient** is an animated object in a **scene** which isn't interactable at all.
- An **Object** is a generic-term used to design the **hotspots**, the **ambients**, the **animations** and everything like that. It is basically everything that is in a **scene**.