"""Test services configuration schema validation and registration."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import homeassistant.helpers.service as service_helper
import pytest
import yaml

from custom_components.nl_weather.const import NLWeatherEntityFeature
from custom_components.nl_weather.weather import (
    SERVICE_GET_MINUTE_FORECAST,
    NLWeatherCombined,
    NLWeatherForecast,
    NLWeatherObservations,
    async_setup_entry,
)


def test_services_yaml_schema_validation() -> None:
    """Test that services.yaml conforms to Home Assistant service schema requirements."""
    services_file = (
        Path(__file__).resolve().parents[1]
        / "custom_components"
        / "nl_weather"
        / "services.yaml"
    )
    assert services_file.is_file()

    with services_file.open("r", encoding="utf-8") as f:
        services_data = yaml.safe_load(f)

    # Validate against Home Assistant's service schema parser
    validated = service_helper._SERVICES_SCHEMA(services_data)

    assert SERVICE_GET_MINUTE_FORECAST in validated
    target_entity = validated[SERVICE_GET_MINUTE_FORECAST]["target"]["entity"][0]
    assert target_entity["domain"] == ["weather"]
    assert target_entity["integration"] == "nl_weather"
    assert target_entity["supported_features"] == [32]

    # Verify that the feature bitmask matches FORECAST_MINUTE
    assert NLWeatherEntityFeature.FORECAST_MINUTE == 32

    # Verify that NLWeatherForecast and NLWeatherCombined support FORECAST_MINUTE, while Observations does not
    mock_entry = MagicMock()
    mock_subentry = MagicMock()
    mock_subentry.data = {"name": "Test"}
    mock_coord = MagicMock()

    forecast_entity = NLWeatherForecast(
        mock_coord, mock_coord, mock_entry, mock_subentry
    )
    combined_entity = NLWeatherCombined(
        mock_coord, mock_coord, mock_coord, mock_entry, mock_subentry
    )
    obs_entity = NLWeatherObservations(mock_coord, mock_entry, mock_subentry)

    assert bool(
        forecast_entity.supported_features and forecast_entity.supported_features & 32
    )
    assert bool(
        combined_entity.supported_features and combined_entity.supported_features & 32
    )
    assert not bool(
        obs_entity.supported_features and obs_entity.supported_features & 32
    )


@pytest.mark.asyncio
async def test_async_setup_entry_registers_required_features() -> None:
    """Test that async_setup_entry registers SERVICE_GET_MINUTE_FORECAST with required_features."""
    hass = MagicMock()
    config_entry = MagicMock()
    config_entry.subentries = {}
    async_add_entities = MagicMock()

    platform_mock = MagicMock()
    with patch(
        "homeassistant.helpers.entity_platform.async_get_current_platform",
        return_value=platform_mock,
    ):
        await async_setup_entry(hass, config_entry, async_add_entities)

    platform_mock.async_register_entity_service.assert_called_once()
    _, kwargs = platform_mock.async_register_entity_service.call_args
    assert kwargs["name"] == SERVICE_GET_MINUTE_FORECAST
    assert kwargs["func"] == "async_get_minute_forecast"
    assert kwargs["required_features"] == [NLWeatherEntityFeature.FORECAST_MINUTE]
