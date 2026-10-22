import json
import pygame

class AssetManager:
    _instance = None

    def __init__(self):
        self.textures = {}
        self.metadata = {}
        self.sprites = {}
        self.hitboxes = {}

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = AssetManager()
        return cls._instance

    def load_bundle(self, bundle_name):
        data_path = f"assets/data/{bundle_name}.json"
        with open(data_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        tex_path = f"assets/spritesheets/{meta['texture']}"
        texture = pygame.image.load(tex_path).convert_alpha()
        self.textures[bundle_name] = texture
        self.metadata[bundle_name] = meta
        if isinstance(meta["frames"], list):
            self.sprites[bundle_name] = []
            for item in meta["frames"]:
                rect = pygame.Rect(item["x"], item["y"], item["w"], item["h"])
                self.sprites[bundle_name].append(texture.subsurface(rect).copy())
        elif isinstance(meta["frames"], dict):
            self.sprites[bundle_name] = {}
            for key, item in meta["frames"].items():
                rect = pygame.Rect(item["x"], item["y"], item["w"], item["h"])
                self.sprites[bundle_name][key] = texture.subsurface(rect).copy()

    def get_sprite(self, bundle, frame_key=None):
        if bundle not in self.sprites:
            self.load_bundle(bundle)
        if frame_key is None:
            return self.sprites[bundle]
        if isinstance(self.sprites.get(bundle), dict) and frame_key not in self.sprites[bundle]:
            aliases = {
                "action_0": ["action_lantern_0", "action_shovel_0", "action_slash_0"],
                "action_1": ["action_lantern_1", "action_shovel_1", "action_slash_1"],
                "action_2": ["action_lantern_2", "action_shovel_2", "action_slash_2"],
                "action_3": ["action_lantern_3", "action_shovel_3", "action_slash_3"],
            }
            if frame_key in aliases:
                for alt in aliases[frame_key]:
                    if alt in self.sprites[bundle]:
                        return self.sprites[bundle][alt]
            if frame_key.startswith("walk_"):
                try:
                    idx = int(frame_key.split("_")[1]) % 4
                    alt = f"walk_{idx}"
                    if alt in self.sprites[bundle]:
                        return self.sprites[bundle][alt]
                except (IndexError, ValueError):
                    pass
            if frame_key.startswith("run_"):
                try:
                    idx = int(frame_key.split("_")[1]) % 4
                    for prefix in ("run", "walk"):
                        alt = f"{prefix}_{idx}"
                        if alt in self.sprites[bundle]:
                            return self.sprites[bundle][alt]
                except (IndexError, ValueError):
                    pass
            for fallback in ("idle_0", "talk_0"):
                if fallback in self.sprites[bundle]:
                    return self.sprites[bundle][fallback]
        return self.sprites[bundle][frame_key]

    def get_hitbox(self, bundle, frame_key):
        cache_key = f"{bundle}_{frame_key}"
        if cache_key in self.hitboxes:
            return self.hitboxes[cache_key]
        sprite = self.get_sprite(bundle, frame_key)
        mask = pygame.mask.from_surface(sprite)
        rects = mask.get_bounding_rects()
        if rects:
            union = rects[0].unionall(rects[1:])
            res = (union.width, union.height)
        else:
            res = (sprite.get_width(), sprite.get_height())
        self.hitboxes[cache_key] = res
        return res
