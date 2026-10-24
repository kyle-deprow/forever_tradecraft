from __future__ import annotations

import os
from pathlib import Path

from pydantic import SecretStr, model_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

from crowley.core.game_target import packaged_game_target

_TARGET = packaged_game_target()


def config_path() -> Path:
    if env := os.environ.get("CROWLEY_COMPANION_CONFIG"):
        return Path(env).expanduser()
    base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "crowley" / "companion.toml"


def state_path() -> Path:
    base = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return base / "crowley" / "companion-state.json"


class CompanionSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CROWLEY_", extra="ignore")

    # The game-flavor folder containing WTF/ and Interface/, e.g.
    # ~/.wine/drive_c/Program Files (x86)/World of Warcraft/_forever_
    wow_dir: Path = Path(_TARGET.game_root) / _TARGET.product_dir
    # Over Tailscale this is e.g. http://crowley-server:8080 (MagicDNS name or 100.x address).
    server_url: str = "http://127.0.0.1:8080"
    api_token: SecretStr
    poll_seconds: float = 3.0
    # Re-write Crowley_Data even without new scans so strategy updates reach the game.
    refresh_minutes: float = 5.0
    # Queue identity is explicit: the companion never guesses a house or character
    # from whichever SavedVariables file happens to be present.
    house_key: str | None = None
    character: str | None = None

    @model_validator(mode="after")
    def _validate_packaged_target_identity(self) -> CompanionSettings:
        expected_wow_dir = Path(_TARGET.game_root) / _TARGET.product_dir
        if self.wow_path != expected_wow_dir:
            raise ValueError("wow_dir must match the packaged launch target flavor root")
        if self.house_key is not None and self.house_key != _TARGET.house:
            raise ValueError("house_key must match the packaged launch target house when configured")
        return self

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        toml = TomlConfigSettingsSource(settings_cls, toml_file=config_path())
        return (init_settings, env_settings, toml)

    @property
    def wow_path(self) -> Path:
        return self.wow_dir.expanduser()

    @property
    def addons_dir(self) -> Path:
        return self.wow_path / "Interface" / "AddOns"

    @property
    def data_lua(self) -> Path:
        return self.addons_dir / "Crowley_Data" / "Data.lua"

    @property
    def queue_lua(self) -> Path:
        return self.addons_dir / "Crowley_Data" / "Queue.lua"

    def saved_variables_files(self) -> list[Path]:
        return sorted((self.wow_path / "WTF" / "Account").glob("*/SavedVariables/Crowley.lua"))
