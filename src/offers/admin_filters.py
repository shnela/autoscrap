from django.contrib import admin


class NullableBooleanListFilter(admin.SimpleListFilter):
    """Filter nullable BooleanField: Yes / No / Unknown (NULL)."""

    field_name = ""

    def lookups(self, request, model_admin):
        return (
            ("yes", "Yes"),
            ("no", "No"),
            ("unknown", "Unknown"),
        )

    def queryset(self, request, queryset):
        v = self.value()
        if v == "yes":
            return queryset.filter(**{self.field_name: True})
        if v == "no":
            return queryset.filter(**{self.field_name: False})
        if v == "unknown":
            return queryset.filter(**{f"{self.field_name}__isnull": True})
        return queryset


def _nb_filter(title, field_name, param=None):
    param = param or field_name

    class _F(NullableBooleanListFilter):
        pass

    _F.title = title
    _F.parameter_name = param
    _F.field_name = field_name
    _F.__name__ = "CarOfferFilter_%s" % field_name
    return _F


CarOfferFeatureFilters = [
    _nb_filter("AWD (vs FWD)", "feature_awd"),
    _nb_filter("Increased clearance & Off-Road mode", "feature_increased_clearance_off_road_mode"),
    _nb_filter("Hill Descent Control", "feature_hill_descent_control"),
    _nb_filter("Rear air suspension (adaptive / self-levelling)", "feature_rear_air_suspension"),
    _nb_filter("Pilot Assist", "feature_pilot_assist"),
    _nb_filter("City Safety (AEB)", "feature_city_safety"),
    _nb_filter("Cross Traffic Alert + auto-brake (reverse)", "feature_cross_traffic_alert_reverse_brake"),
    _nb_filter("360° surround-view camera", "feature_surround_view_camera_360"),
    _nb_filter("Front & rear parking sensors", "feature_front_rear_parking_sensors"),
    _nb_filter("Panoramic roof / glass roof", "feature_panoramic_roof"),
    _nb_filter("Four-zone climate", "feature_four_zone_climate"),
    _nb_filter("Power tailgate", "feature_power_tailgate"),
    _nb_filter("Remote rear seatback release (cargo)", "feature_remote_rear_seatback_release"),
    _nb_filter("Folding rear headrests", "feature_folding_rear_headrests"),
    _nb_filter("Google built-in infotainment", "feature_google_built_in_infotainment"),
    _nb_filter("Wood or metal inlays", "feature_wood_or_metal_inlays"),
    _nb_filter("Crystal gear selector", "feature_crystal_gear_selector"),
    _nb_filter("Ambient lighting package", "feature_ambient_lighting_package"),
]
