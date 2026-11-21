<p align="center">
    <img width="180px" src="assets/icon.svg" alt="Logo" />
</p>

<p align="center">
    <a href="https://github.com/imLinguin/nile/stargazers">
        <img src="https://img.shields.io/github/stars/imLinguin/nile?color=d98e04" alt="stars"/>
    </a>
    <img src="https://img.shields.io/github/license/imLinguin/nile?color=d98e03" alt="loicense"/>
    <a href="https://ko-fi.com/imlinguin" target="_blank">
        <img src="https://img.shields.io/badge/Ko--Fi-Donate-d98e04?style=flat&logo=ko-fi" />
    </a>
</p>

# Nile
Cross platform Amazon Games client, based on [this research](https://github.com/Lariaa/GameLauncherResearch/wiki/Amazon-Games)

Nile aims to be CLI and GUI tool for managing and playing games from Amazon. 

## Features
- Login to Amazon Account
- Download games
- Play games (with Wine/Proton on Linux)
- Play games using [Bottles](https://usebottles.com) (`--bottle` parameter)

## Might not work
- Online games, that use `FuelPump` (I don't have any game like that to test)

## Purpose
This is my attempt to make Amazon Games useful for Linux users, who want to play titles obtained thanks to [Prime](https://prime.amazon.com) membership.

## Usage

At the moment, Nile is a command line application. If you are looking for graphical user interface, make sure to checkout

- [Heroic Games Launcher](https://heroicgameslauncher.com) - uses Nile as a backend for Amazon Games
- [Lutris](https://lutris.net) - has implementation really similar to what Nile provides

(Recommended) The bundled program is available on the [releases page](https://github.com/imLinguin/nile/releases/latest)  

If you wish to run nile from source, see instructions below.


## Dependencies
### Arch and derivatives (Manjaro, Garuda, EndeavourOS)
`sudo pacman -S python-pycryptodome python-zstandard python-requests python-protobuf python-json5`
### Debian and derivatives (Ubuntu, Pop!_OS)
`sudo apt install python3-pycryptodome python3-requests python3-zstandard python3-protobuf python3-json5`

### With pip
> Do this after cloning the repo and cd into the directory
> Do not install if you installed dependencies through your package manager  

This is **NOT** recommended as it can potentially collide with distribution packages [source](https://peps.python.org/pep-0668/)  
new versions of `pip` will prevent you from doing it outside of virtual environment

`pip3 install -r requirements.txt`

## Building PyInstaller executable

If you wish to test nile in Heroic flatpak you likely need to build the `nile` executable using pyinstaller

- Get pyinstaller

```
pip install pyinstaller
```

- Build the binary (assuming you are in the nile directory)

```
pyinstaller --onefile --name nile nile/cli.py
```

## Portable mode

By default nile stores its config in the user config directory
(`%APPDATA%\nile` on Windows, `~/.config/nile` on Linux,
`~/Library/Application Support/nile` on macOS).

To keep everything next to the executable instead, create an empty file named
`portable` in the same folder as the bundled `nile` executable:

```
nile_windows_x86_64.exe
portable
```

On startup nile creates a `config` directory beside the executable and stores
all of its data there (account tokens, library, manifests, SDK). In this mode
`NILE_CONFIG_PATH` is ignored.

This applies to the bundled builds (PyInstaller executables and the Linux
zipapp). Running from source always uses the user config directory.

## Contributing

I'm always open for contributors

black is used for code formatting

## Setting up dev environment:
- Clone the repo `git clone https://github.com/imLinguin/nile`
- CD into the directory `cd nile`
- Setup virtual environment `python3 -m venv env`
- Install [dependencies](#dependencies)
- Run nile `./bin/nile`


## Prior work

This is based on Rodney's work here: https://github.com/derrod/twl.py
Some of his code is implemented in nile, since nothing changed since then in terms of downloading and patching
