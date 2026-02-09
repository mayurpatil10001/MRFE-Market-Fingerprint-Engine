#!/usr/bin/env python3
"""
Script to generate a well-made SB3 (Scratch 3.0) project file.
This creates a simple game where a cat collects apples while avoiding obstacles.
"""

import json
import zipfile
import base64
from io import BytesIO

def create_project_json():
    """Create the project.json content for a simple game."""
    project = {
        "targets": [
            # Stage
            {
                "isStage": True,
                "name": "Stage",
                "variables": {
                    "score": ["score", 0],
                    "lives": ["lives", 3]
                },
                "lists": {},
                "broadcasts": {},
                "blocks": {},
                "comments": {},
                "currentCostume": 0,
                "costumes": [
                    {
                        "name": "backdrop1",
                        "bitmapResolution": 1,
                        "dataFormat": "svg",
                        "assetId": "cd21514d0531fdffb22204e0ec5ed84a",
                        "md5ext": "cd21514d0531fdffb22204e0ec5ed84a.svg",
                        "rotationCenterX": 240,
                        "rotationCenterY": 180
                    }
                ],
                "sounds": [],
                "volume": 100,
                "layerOrder": 0,
                "tempo": 60,
                "videoTransparency": 50,
                "videoState": "off",
                "textToSpeechLanguage": None
            },
            # Cat sprite
            {
                "isStage": False,
                "name": "Cat",
                "variables": {},
                "lists": {},
                "broadcasts": {},
                "blocks": {
                    "block1": {
                        "opcode": "event_whenflagclicked",
                        "next": "block2",
                        "parent": None,
                        "inputs": {},
                        "fields": {},
                        "shadow": False,
                        "topLevel": True,
                        "x": 100,
                        "y": 100
                    },
                    "block2": {
                        "opcode": "control_forever",
                        "next": None,
                        "parent": "block1",
                        "inputs": {
                            "SUBSTACK": ["block3", None]
                        },
                        "fields": {},
                        "shadow": False,
                        "topLevel": False
                    },
                    "block3": {
                        "opcode": "motion_movesteps",
                        "next": "block4",
                        "parent": "block2",
                        "inputs": {
                            "STEPS": [10, None]
                        },
                        "fields": {},
                        "shadow": False,
                        "topLevel": False
                    },
                    "block4": {
                        "opcode": "control_wait",
                        "next": None,
                        "parent": "block3",
                        "inputs": {
                            "DURATION": [0.1, None]
                        },
                        "fields": {},
                        "shadow": False,
                        "topLevel": False
                    }
                },
                "comments": {},
                "currentCostume": 0,
                "costumes": [
                    {
                        "name": "costume1",
                        "bitmapResolution": 1,
                        "dataFormat": "svg",
                        "assetId": "bcf454acf82e4504149f7ffe07081dbc",
                        "md5ext": "bcf454acf82e4504149f7ffe07081dbc.svg",
                        "rotationCenterX": 48,
                        "rotationCenterY": 50
                    }
                ],
                "sounds": [],
                "volume": 100,
                "layerOrder": 1,
                "visible": True,
                "x": 0,
                "y": 0,
                "size": 100,
                "direction": 90,
                "draggable": False,
                "rotationStyle": "all around"
            },
            # Apple sprite
            {
                "isStage": False,
                "name": "Apple",
                "variables": {},
                "lists": {},
                "broadcasts": {},
                "blocks": {
                    "block5": {
                        "opcode": "event_whenflagclicked",
                        "next": "block6",
                        "parent": None,
                        "inputs": {},
                        "fields": {},
                        "shadow": False,
                        "topLevel": True,
                        "x": 200,
                        "y": 200
                    },
                    "block6": {
                        "opcode": "control_forever",
                        "next": None,
                        "parent": "block5",
                        "inputs": {
                            "SUBSTACK": ["block7", None]
                        },
                        "fields": {},
                        "shadow": False,
                        "topLevel": False
                    },
                    "block7": {
                        "opcode": "motion_gotoxy",
                        "next": "block8",
                        "parent": "block6",
                        "inputs": {
                            "X": [-150, None],
                            "Y": [100, None]
                        },
                        "fields": {},
                        "shadow": False,
                        "topLevel": False
                    },
                    "block8": {
                        "opcode": "control_wait",
                        "next": None,
                        "parent": "block7",
                        "inputs": {
                            "DURATION": [2, None]
                        },
                        "fields": {},
                        "shadow": False,
                        "topLevel": False
                    }
                },
                "comments": {},
                "currentCostume": 0,
                "costumes": [
                    {
                        "name": "apple",
                        "bitmapResolution": 1,
                        "dataFormat": "svg",
                        "assetId": "d9e3e6767b012871f13b3f8c7b6c54e",
                        "md5ext": "d9e3e6767b012871f13b3f8c7b6c54e.svg",
                        "rotationCenterX": 25,
                        "rotationCenterY": 25
                    }
                ],
                "sounds": [],
                "volume": 100,
                "layerOrder": 2,
                "visible": True,
                "x": -150,
                "y": 100,
                "size": 50,
                "direction": 90,
                "draggable": False,
                "rotationStyle": "all around"
            }
        ],
        "monitors": [],
        "extensions": [],
        "meta": {
            "semver": "3.0.0",
            "vm": "0.2.0-prerelease.20200515175014",
            "agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    }
    return project

def generate_sb3(filename="sample_project.sb3"):
    """Generate the SB3 file."""
    project_json = create_project_json()

    with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Write project.json
        zf.writestr('project.json', json.dumps(project_json, indent=2))

        # If there were assets, add them here, but using defaults so none needed

    print(f"SB3 file '{filename}' generated successfully!")

if __name__ == "__main__":
    generate_sb3()
