"""Options flow for samsung_frame."""

from __future__ import annotations

from typing import TYPE_CHECKING

import probatio
from homeassistant.config_entries import ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.helpers import selector

from .const import DEFAULT_SCAN_INTERVAL_SECONDS, MIN_SCAN_INTERVAL_SECONDS

if TYPE_CHECKING:
    from .data import SamsungFrameOptionsData


class SamsungFrameOptionsFlow(OptionsFlow):
    """Options flow for Samsung The Frame."""

    async def async_step_init(
        self,
        user_input: SamsungFrameOptionsData | None = None,
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=dict(user_input))

        current_value: int = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            DEFAULT_SCAN_INTERVAL_SECONDS,
        )

        return self.async_show_form(
            step_id="init",
            data_schema=probatio.Schema(
                {
                    probatio.Optional(
                        CONF_SCAN_INTERVAL,
                        default=current_value,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=MIN_SCAN_INTERVAL_SECONDS,
                            step=10,
                            unit_of_measurement="s",
                            mode=selector.NumberSelectorMode.BOX,
                        ),
                    ),
                },
            ),
        )
