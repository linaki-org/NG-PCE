# Next-Generation Point-n-Click Engine
## Introduction
NG-PCE is the next-generation successor of PCS-ANS.  
Its goal is to fill all problem that PCS-ANS had, like the lack of object-oriented resources management, or the not-so-easy JSON-based descriptive language, while keeping the SCUMM-like philosophy.

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