"""Scenario template schema and validation rules."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class ControlAudience(StrEnum):
    PRODUCT = "product"
    ADVANCED = "advanced"


class ControlType(StrEnum):
    CHOICE = "choice"
    NUMBER = "number"
    BOOLEAN = "boolean"


class RuntimeProfile(StrEnum):
    QUICK_LOOK = "quick_look"
    STANDARD = "standard"
    DEEP_OVERNIGHT = "deep_overnight"


class ScenarioValidationError(ValueError):
    """Raised when a scenario template fails validation."""


class ControlOption(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: str
    label: str
    description: str | None = None


class NumericRange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min: float
    max: float
    step: float | None = None
    units: str | None = None

    @model_validator(mode="after")
    def validate_range(self) -> NumericRange:
        if self.max <= self.min:
            raise ValueError("numeric range max must be greater than min")
        if self.step is not None and self.step <= 0:
            raise ValueError("numeric range step must be positive")
        return self


class ScenarioControl(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    description: str
    type: ControlType
    audience: ControlAudience = ControlAudience.PRODUCT
    default: str | float | bool
    options: list[ControlOption] = Field(default_factory=list)
    range: NumericRange | None = None
    validation: list[str] = Field(default_factory=list)
    cm1_mapping_notes: str

    @model_validator(mode="after")
    def validate_control_shape(self) -> ScenarioControl:
        if self.type == ControlType.CHOICE:
            if not self.options:
                raise ValueError(f"choice control {self.id!r} must define options")
            option_values = {option.value for option in self.options}
            if not isinstance(self.default, str) or self.default not in option_values:
                raise ValueError(f"choice control {self.id!r} default must match an option value")
        if self.type == ControlType.NUMBER:
            if self.range is None:
                raise ValueError(f"number control {self.id!r} must define a range")
            if not isinstance(self.default, int | float):
                raise ValueError(f"number control {self.id!r} default must be numeric")
            if not self.range.min <= float(self.default) <= self.range.max:
                raise ValueError(f"number control {self.id!r} default must be inside range")
        if self.type == ControlType.BOOLEAN and not isinstance(self.default, bool):
            raise ValueError(f"boolean control {self.id!r} default must be boolean")
        return self


class RunSizePreset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: RuntimeProfile
    label: str
    purpose: str
    expected_runtime: str
    confidence: str
    output_notes: str


class ExpectedDiagnostics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cloud_formed: bool = True
    first_cloud_time: str | None = None
    cloud_base_top: str | None = None
    max_updraft: str | None = None
    cloud_water_summary: str | None = None
    rain_onset: str | None = None
    notes: list[str] = Field(default_factory=list)


class CM1TemplateReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    namelist_template: str
    input_sounding_template: str
    runtime_files_needed: list[str] = Field(default_factory=list)
    mapping_notes: str


class VariationPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    baseline_scenario_id: str
    one_control_at_a_time: bool = True
    suggested_controls: list[str] = Field(default_factory=list)
    non_goals: list[str] = Field(default_factory=list)


class VisualizationDefaults(BaseModel):
    model_config = ConfigDict(extra="forbid")

    primary_field: str
    secondary_fields: list[str] = Field(default_factory=list)
    camera: str
    rendering_method: str
    provenance_label: str = "Visualizer interpretation of CM1 output"


class ScenarioTemplate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"]
    id: str
    display_name: str
    category: str
    description: str
    physical_question: str
    learning_goals: list[str]
    intended_behavior: str
    expected_behavior: str
    controls: list[ScenarioControl]
    run_size_presets: list[RunSizePreset]
    expected_diagnostics: ExpectedDiagnostics
    cm1_template: CM1TemplateReference
    visualization_defaults: VisualizationDefaults
    variation_policy: VariationPolicy | None = None
    warnings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    advanced_settings_notes: str

    @model_validator(mode="after")
    def validate_template_contract(self) -> ScenarioTemplate:
        product_controls = [
            control for control in self.controls if control.audience == ControlAudience.PRODUCT
        ]
        if not product_controls:
            raise ValueError("scenario must define at least one product-facing control")

        preset_ids = {preset.id for preset in self.run_size_presets}
        required_presets = set(RuntimeProfile)
        if preset_ids != required_presets:
            missing = ", ".join(sorted(profile.value for profile in required_presets - preset_ids))
            extra = ", ".join(sorted(profile.value for profile in preset_ids - required_presets))
            details = "; ".join(
                part
                for part in [
                    f"missing {missing}" if missing else "",
                    f"extra {extra}" if extra else "",
                ]
                if part
            )
            raise ValueError(
                f"scenario run_size_presets must define quick/standard/deep profiles: {details}"
            )

        control_ids = {control.id for control in self.controls}
        if self.variation_policy is not None:
            unknown = sorted(set(self.variation_policy.suggested_controls) - control_ids)
            if unknown:
                raise ValueError(
                    "variation policy references unknown controls: " + ", ".join(unknown)
                )
        return self


def validate_scenario_template(data: object) -> ScenarioTemplate:
    try:
        return ScenarioTemplate.model_validate(data)
    except ValidationError as exc:
        raise ScenarioValidationError(str(exc)) from exc
