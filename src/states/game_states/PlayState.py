"""
ISPPV1 2023
Study Case: Super Martian (Platformer)

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the class PlayState.
"""

from typing import Dict, Any

import pygame

from gale.camera import Camera
from gale.input_handler import InputData
from gale.state import BaseState
from gale.text import render_text
from gale.timer import Timer

import settings
from src.Clock import Clock
from src.GameLevel import GameLevel
from src.Player import Player


class PlayState(BaseState):
    def enter(self, **enter_params: Dict[str, Any]) -> None:
        self.level = enter_params.get("level", 1)
        self.game_level = enter_params.get("game_level")
        if self.game_level is None:
            self.game_level = GameLevel(self.level)
            pygame.mixer.music.load(
                settings.BASE_DIR / "assets" / "sounds" / "music_grassland.ogg"
            )
            pygame.mixer.music.play(loops=-1)

        self.tilemap = self.game_level.tilemap
        self.player = enter_params.get("player")
        if self.player is None:
            # Resting exactly on the ground tile's surface (row 9, one tile
            # below the platform's top edge) rather than a few pixels into
            # it, so gale.tilemap's one-way platform collision (which
            # requires the entity to already be at/above the surface) picks
            # it up on the very first frame instead of falling through.
            spawn_y = 95 - 20
            self.player = Player(20, spawn_y, self.game_level)
            self.player.change_state("idle")

        self.camera = enter_params.get("camera")

        if self.camera is None:
            self.camera = Camera(settings.VIRTUAL_WIDTH, settings.VIRTUAL_HEIGHT)
            self.camera.follow(self.player, rate=settings.CAMERA_FOLLOW_RATE)
            self.camera.bounds = self.game_level.get_rect()
            self.camera.x, self.camera.y = self.player.x, self.player.y
            self.camera.update(0)

        self.clock = enter_params.get("clock")

        if self.clock is None:
            self.clock = Clock(50)

            def countdown_timer():
                if getattr(self.player, "has_key", False):
                    return

                self.clock.count_down()

                if 0 < self.clock.time <= 5:
                    settings.SOUNDS["timer"].play()

                if self.clock.time == 0:
                    self.player.change_state("dead")

            Timer.every(1, countdown_timer)
        else:
            Timer.resume()

        self.fade_alpha = 0
        self.is_fading_out = False
        self.key_spawned = False

    def update(self, dt: float) -> None:
        if self.player.is_dead and not self.player.has_key:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            Timer.clear()
            self.state_machine.change("game_over", self.player)

        if self.is_fading_out:
            return

        key_block_rect = self.game_level.triggers.get("key_block")

        if key_block_rect and not self.key_spawned:

            # Verificamos la colision con el sensor
            if self.player.get_collision_rect().colliderect(key_block_rect):

                if self.player.vy < 0 and self.player.score >= self.game_level.goal_score:
                    self.key_spawned = True
                    self.player.vy = 0

                    self.game_level.add_item({
                        "item_name": "keys",
                        "frame_index": 0,
                        "x": key_block_rect.x,
                        "y": key_block_rect.y,
                        "width": 16,
                        "height": 16
                    })

                    new_key = self.game_level.items[-1]
                    Timer.tween(
                        0.5,
                        [(new_key, {"y": new_key.y - 16})]
                    )

        self.player.update(dt)
        self.camera.update(dt)
        self.game_level.update(dt)

        if not self.player.has_key:

            if self.player.y >= self.tilemap.pixel_height:
                self.player.change_state("dead")

            for creature in self.game_level.creatures:
                if self.player.collides(creature):
                    self.player.change_state("dead")

        for item in self.game_level.items:
            if not item.active or not item.collidable:
                continue

            if self.player.has_key:
                continue

            if self.player.collides(item):
                item.on_collide(self.player)
                item.on_consume(self.player)

        # Efecto Fade-out
        if self.player.has_key and not self.is_fading_out:
            def finish_level():
                settings.SOUNDS["victory"].stop()
                self.state_machine.change("start")

            self.is_fading_out = True
            settings.SOUNDS["victory"].play()

            # Congelamos al jugador
            self.player.vx = 0
            self.player.vy = 0
            self.player.move_direction = 0
            self.player.change_state("idle")

            Timer.tween(
                5,
                [(self, {"fade_alpha": 255})],
                on_finish=finish_level  # Cuando termine el fade, volvemos a la pantalla de inicio
            )

    def render(self, surface: pygame.Surface) -> None:
        self.game_level.render(surface, self.camera)
        self.player.render(surface, self.camera)

        render_text(
            surface,
            f"Score: {self.player.score} / {self.game_level.goal_score}",
            settings.FONTS["small"],
            5,
            5,
            (255, 255, 255),
            shadowed=True,
        )

        render_text(
            surface,
            f"Time: {self.clock.time}",
            settings.FONTS["small"],
            settings.VIRTUAL_WIDTH - 60,
            5,
            (255, 255, 255),
            shadowed=True,
        )

        if self.fade_alpha > 0:
            fade_surface = pygame.Surface(
                (settings.VIRTUAL_WIDTH, settings.VIRTUAL_HEIGHT), 
                pygame.SRCALPHA
            )
            
            fade_surface.fill((0, 0, 0, int(self.fade_alpha)))
            
            surface.blit(fade_surface, (0, 0))

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if self.player.has_key:
            return
        
        if input_id == "pause" and input_data.pressed:
            Timer.pause()
            self.state_machine.change(
                "pause",
                level=self.level,
                camera=self.camera,
                game_level=self.game_level,
                player=self.player,
                clock=self.clock,
            )
        else:
            self.player.on_input(input_id, input_data)
