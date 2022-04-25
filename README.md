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
Linux native Amazon Games client, based on [this research](https://github.com/Lariaa/GameLauncherResearch/wiki/Amazon-Games)

Nile aims to be CLI and GUI tool for managing and playing games from Amazon. 

## Features
- Login to Amazon Account
- Download games
- Play games (with Wine/Proton on Linux)

## Might not work
- Online games, that use `FuelPump` (I don't have any game like that to test)

# Purpose
This is my attempt to make Amazon Games useful for Linux users, who want to play titles obtained thanks to [Prime](https://prime.amazon.com) membership.

# Dependencies
## Arch, Manjaro etc..
`sudo pacman -Sy pyqt5 python-pycryptodome python-zstandard python-requests`
## Ubuntu
`sudo apt install python3-pyqt5 python3-pycryptodome python3-requests python-zstd`
## With pip
> Do this after cloning the repo and cd into the directory

`pip3 install -r requirements.txt`

# Installation
Currently app is not packaged in any way so here are a few steps to download it:

- Clone repo using git or download the ZIP `git clone https://github.com/imLinguin/nile`
- CD into the directory `cd nile`
- Login `./bin/nile auth --login`
- Have fun

# Contributing

I'm always open for contributors

black is used for code formatting

## Setting up dev environment:
- Clone the repo `git clone https://github.com/imLinguin/nile`
- CD into the directory `cd nile`
- Setup virtual environment `python3 -m venv env`
- Install [dependencies](#dependencies)
- Run nile `./bin/nile`


# Prior work

This is based on Rodney's work here: https://github.com/derrod/twl.py
Some of his code is implemented in nile, since nothing changed since then in terms of downloading and patching
