# BlockAnimator\blockanimator\utils\module_ops.py

import importlib.util
import inspect
import sys
import re
import types
from pathlib import Path
from typing import Any, List, Type, TYPE_CHECKING


# Simplified config object
class Config:
    def __init__(self):
        self.scene_names = []
        self.write_all = False


config = Config()

# Constants (messages are still defined)
SCENE_NOT_FOUND_MESSAGE = "\n{} is not in the script"
CHOOSE_NUMBER_MESSAGE = "\nChoose number corresponding to desired scene/arguments.\n(Use comma separated list for multiple entries)\nChoice(s): "
INVALID_NUMBER_MESSAGE = "Invalid scene numbers have been specified. Aborting."
NO_SCENE_MESSAGE = "\nThere are no scenes inside that module"

if TYPE_CHECKING:
    from blockanimator.core.scene import Scene


def get_module(file_name: Path) -> types.ModuleType:
    if not file_name.exists():
        raise FileNotFoundError(f"{file_name} not found")
    if file_name.suffix != ".py":
        raise ValueError(f"{file_name} is not a valid Python script.")

    module_name = file_name.stem
    spec = importlib.util.spec_from_file_location(module_name, file_name)
    if isinstance(spec, importlib.machinery.ModuleSpec):
        module = types.ModuleType(module_name)
        sys.modules[module_name] = module
        sys.path.insert(0, str(file_name.parent.absolute()))
        assert spec.loader
        spec.loader.exec_module(module)
        return module
    raise FileNotFoundError(f"{file_name} not found")


def get_scene_classes_from_module(module: types.ModuleType) -> List[Type['Scene']]:
    from ..core.scene import Scene

    def is_child_scene(obj: Any) -> bool:
        return (
                inspect.isclass(obj)
                and issubclass(obj, Scene)
                and obj != Scene
                and obj.__module__ == module.__name__
        )

    return [
        member[1]
        for member in inspect.getmembers(module, is_child_scene)
    ]


def get_scenes_to_render(scene_classes: List[Type['Scene']]) -> List[Type['Scene']]:
    if not scene_classes:
        return []

    result = []
    if config.scene_names:
        for scene_name in config.scene_names:
            found = False
            for scene_class in scene_classes:
                if scene_class.__name__ == scene_name:
                    result.append(scene_class)
                    found = True
                    break
            if not found and (scene_name != ""):
                pass
        if result:
            return result

    if len(scene_classes) == 1:
        config.scene_names = [scene_classes[0].__name__]
        return [scene_classes[0]]

    return prompt_user_for_choice(scene_classes)


def prompt_user_for_choice(scene_classes: List[Type['Scene']]) -> List[Type['Scene']]:
    num_to_class = {}
    for count, scene_class in enumerate(scene_classes, 1):
        name = scene_class.__name__
        print(f"{count}: {name}")
        num_to_class[count] = scene_class
    try:
        user_input = input(
            f"{CHOOSE_NUMBER_MESSAGE}",
        )
        scene_classes = [
            num_to_class[int(num_str)]
            for num_str in re.split(r"\s*,\s*", user_input.strip())
        ]
        config.scene_names = [scene_class.__name__ for scene_class in scene_classes]
        return scene_classes
    except KeyError:
        print(INVALID_NUMBER_MESSAGE)
        sys.exit(2)
    except EOFError:
        sys.exit(1)
    except ValueError:
        print("No scenes were selected. Exiting.")
        sys.exit(1)


def scene_classes_from_file(file_path: Path) -> List[Type['Scene']]:
    module = get_module(file_path)
    all_scene_classes = get_scene_classes_from_module(module)
    scene_classes_to_render = get_scenes_to_render(all_scene_classes)
    return scene_classes_to_render