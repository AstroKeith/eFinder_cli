# eFinder cli

![IMG_6790](https://github.com/user-attachments/assets/15d95f3e-2b0b-4bfa-b234-c52bd2c7e699)

## Basics

Code for AltAz telescopes (primarily Dobsonians) to utilise plate-solving to improve pointing accuracy.

Requires:

- microSd card loaded with Raspberry Pi 64bit Bookworm OS Lite (No desktop)
- Raspberry Pi Zero 2W. 
- A custom box 
- A Nexus DSC with optical encoders. USB cable from Nexus port to the UART port on the Pi Zero.
- A Camera, either the RP HQ Camera module (recommended) of an ASI Camera (Suggest ASI120MM-mini)
- Camera lens, either 25 or 50mm. f1.8 or faster cctv lens

Full details at [
](https://astrokeith.com/equipment/efinder/efinder-lite)https://astrokeith.com/equipment/efinder/efinder-lite

## Compatibility

The eFinder cli is designed to operate alongside a Nexus DSC Pro.


## Operation
Plug the eFinder into the Nexus DSC port.
Turn on the Nexus DSC which will power up the eFinder cli.
The eFinder cli will autostart on power up.

ssh & Samba file sharing is enabled at efinder.local, or whatever hostname you have chosen.

The eFinder.config file is accessible via a browser at "efinder.local", or whatever hostname you have chosen.

A forum for builders and users can be found at https://groups.io/g/eFinder

## Acknowledgements and Licences

The eFinder Lite uses Tetra3, Cedar-Detect & Cedar-Solve. Please refer to the licence and other notes in the Tetra3 folder

