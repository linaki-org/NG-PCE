# Next-Generation Point-n-Click Engine
## Introduction
NG-PCE is a modern Point & Click engine inspired by SCUMM, the engine Lucasart used to create games such as DOTT, Sam & Max HTR or CMI.  
NG-PCE is the next-generation successor of PCS-ANS and its goal is to fill all problem that PCS-ANS had,
like the lack of object-oriented resources management, or the not-so-easy JSON-based descriptive language.

As I am now actively working on Bad Tentacle, my take on making a sequel to the Day of the Tentacle game, I needed a powerful game engine, and PCS-ANS just didn't fit anymore.

To do so without reinventing everything, NG-PCE is based on PyCAPGE, an excellent Python-powered Point & Click engine.
I love PyCAPGE, but as it is primarily an engine made for education, in my opinion it lacks some features necessary to create a "real" game such as Bad Tentacle.
That is why I decided to tinker with it a lot to perfectly fit my needs. I plan to implement:
- A full and clean separation between the main engine, the game logic and the scenes/interactions management
- A simple and intuitive descriptive scripting language to fasten game programming, called PCScript
- A set of tools for developers to make coding life easy
- Build tools to automatically compile your games for desktop, mobile and web
- Fully and easily customisable UI
- And a lot more !!

I originally wanted to contribute to the original PyCAPGE project, but as I basically want to completely change the way a game is made, I don't think it'll fit its original education purposes.

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