[![Python Versions](https://github.com/primetimetank21/tank-template/actions/workflows/python-versions.yml/badge.svg)](https://github.com/primetimetank21/tank-template/actions/workflows/python-versions.yml)

# Instagram Scanner

## Purpose
This repo goes to my instagram and gets a list of who is not following me back (tag/name and link)

## How to Create Browser Context
1. Install dependencies by running `make format`
1. Run `playwright open --save-storage instagram.json`
1. With the browser that opens up, navigate to https://www.instagram.com and sign in
1. Close the browser. A new file should be created. In this example, the file created is `instagram.json`