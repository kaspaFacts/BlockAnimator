# BlockAnimator\blockanimator\core\coordinate_system.py

class CoordinateSystem:
    """Converts grid coordinates to screen pixels with camera support."""

    def __init__(self, screen_width, screen_height, field_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Calculate grid size to fit exactly field_height units vertically
        self.grid_size = screen_height / field_height

        # Origin at bottom-left corner (0,0)
        self.origin_x = 0
        self.origin_y = screen_height  # Bottom of screen in pygame coordinates

        # Camera offset in grid coordinates
        self.camera_x = 0.0
        self.camera_y = 0.0

    def grid_to_pixel(self, grid_x, grid_y):
        """Convert grid coordinates to screen pixels, accounting for camera."""
        # Apply camera offset
        adjusted_x = grid_x - self.camera_x
        adjusted_y = grid_y - self.camera_y

        pixel_x = self.origin_x + (adjusted_x * self.grid_size)
        pixel_y = self.origin_y - (adjusted_y * self.grid_size)
        return pixel_x, pixel_y

    def set_camera_position(self, grid_x, grid_y):
        """Set camera position in grid coordinates."""
        self.camera_x = grid_x
        self.camera_y = grid_y

    def move_camera(self, delta_x, delta_y):
        """Move camera by delta amount."""
        self.camera_x += delta_x
        self.camera_y += delta_y
