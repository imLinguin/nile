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

Nile is not ready for use yet. I barerly scratched the authentication flow.

# Purpose
This is my attempt to make Amazon Games useful for Linux users that want to play titles obtained thanks to [Prime](https://prime.amazon.com) membership.


# Contributing

I'm always open for contributors

## Setting up dev environment:
- Clone the repo `git clone https://github.com/imLinguin/nile`
- CD into the directory `cd nile`
- Setup virtual environment `python3 -m venv env`
- Install dependencies `pip3 install -r requirenments.txt`
- Export PYTHONPATH variable `export PYTHONPATH=.`
- Run nile `python3 nile/cli.py`