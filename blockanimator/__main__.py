# BlockAnimator\blockanimator\__main__.py

import click
from pathlib import Path
from .utils.module_ops import scene_classes_from_file, config  # Import config from your module_ops or central config
from .utils.config import DisplayConfig  # Import DisplayConfig for resolution info

# Define quality presets (as previously discussed)
QUALITY_PRESETS = {
    "fast": {"resolution": "432,240", "fps": 15},
    "low": {"resolution": "848,480", "fps": 24},
    "reg": {"resolution": "1280,720", "fps": 30},
    "high": {"resolution": "1920,1080", "fps": 60}
}


@click.command()
@click.argument('file', type=click.Path(exists=True, path_type=Path))
@click.argument('scene_names', nargs=-1)  # This will capture the scene names provided by the user
@click.option('-q', '--quality', type=click.Choice(list(QUALITY_PRESETS.keys()), case_sensitive=False),
              help='Render quality preset (fast, low, reg, high). Overrides --resolution and --fps.')
@click.option('-r', '--resolution', help='Resolution in "W,H" (e.g., 1280,720).')
@click.option('--fps', type=float, help='Frames per second.')
def main(file, scene_names, quality, resolution, fps):
    """Render scenes from a Python file."""

    # Set config.scene_names based on CLI arguments
    # This is crucial for get_scenes_to_render to know which scenes to look for
    config.scene_names = list(scene_names)  # Convert tuple to list

    # Determine final resolution and fps based on precedence
    final_resolution = None
    final_fps = None

    if quality:
        preset_info = QUALITY_PRESETS[quality]
        final_resolution = preset_info["resolution"]
        final_fps = preset_info["fps"]
    elif resolution:
        final_resolution = resolution

    if fps:
        final_fps = fps

        # Use the modified scene_classes_from_file to get the scenes to render
    # This function now handles the interactive selection logic
    scenes_to_render = scene_classes_from_file(file)

    if not scenes_to_render:
        # If no scenes were selected or found after all logic, exit
        return

    for scene_class in scenes_to_render:
        # Prepare kwargs for scene_class.__init__
        scene_kwargs = {}

        # Only pass resolution and fps if they were explicitly set via CLI or quality preset
        if final_resolution:
            scene_kwargs['resolution'] = final_resolution
        if final_fps:
            scene_kwargs['fps'] = final_fps

            # Instantiate scene, passing only explicitly set CLI args
        scene = scene_class(**scene_kwargs)
        scene.construct()
        scene.render()


if __name__ == "__main__":
    main()