# BlockAnimator\blockanimator\consensus\manager.py

import pygame

class ConsensusManager:
    def __init__(self):
        self.dag_instance = None

    def register_dag(self, dag_instance, scene):
        """Register the single DAG instance for rendering access to its sprites."""
        self.dag_instance = dag_instance
        # When a DAG is registered, ensure its sprites' animation proxies know about the scene
        for sprite_id, sprite in dag_instance.sprite_registry.items():
            if hasattr(sprite, 'animate'):
                sprite.animate.scene = scene

    def get_all_sprites(self):
        """Get all sprites from the registered DAG instance for rendering."""
        if self.dag_instance:
            return self.dag_instance.sprites
        else:
            return pygame.sprite.LayeredUpdates()

    def get_sprite_by_id(self, sprite_id):
        """Find a sprite by ID in the DAG instance."""
        if self.dag_instance and sprite_id in self.dag_instance.sprite_registry:
            return self.dag_instance.sprite_registry[sprite_id]
        return None

    def get_sprite_registry(self):
        """Get the sprite registry from the registered DAG instance."""
        if self.dag_instance:
            return self.dag_instance.sprite_registry
        return {}

    def has_dag(self):
        """Check if a DAG instance is registered."""
        return self.dag_instance is not None