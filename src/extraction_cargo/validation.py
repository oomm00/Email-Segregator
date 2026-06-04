from src.extraction_cargo.models import CargoVcExtraction


def validate_extraction(extraction: CargoVcExtraction) -> CargoVcExtraction:

    # quantity_min should be <= quantity_max
    if extraction.quantity_min_mt and extraction.quantity_max_mt:
        try:
            vmin = float(extraction.quantity_min_mt.value.replace(",", ""))
            vmax = float(extraction.quantity_max_mt.value.replace(",", ""))
            if vmin > vmax:
                extraction.quantity_min_mt, extraction.quantity_max_mt = (
                    extraction.quantity_max_mt, extraction.quantity_min_mt
                )
            if vmin == vmax:
                extraction.quantity_max_mt = None
        except (ValueError, AttributeError):
            pass

    # commission sanity: must be reasonable percentage
    if extraction.commission_pct and extraction.commission_pct.value:
        try:
            raw = extraction.commission_pct.value
            comma_dec = float(raw.replace(",", "."))
            comma_thou = float(raw.replace(",", ""))
            if (comma_dec < 0 or comma_dec > 100) and (comma_thou < 0 or comma_thou > 100):
                extraction.commission_pct = None
            else:
                best = min([comma_dec, comma_thou], key=lambda x: abs(abs(x) - 2.5))
                if abs(comma_dec - best) < abs(comma_thou - best):
                    extraction.commission_pct.value = raw.replace(",", ".")
        except (ValueError, AttributeError):
            extraction.commission_pct = None

    # loading_port and discharge_port must differ
    if (extraction.loading_port and extraction.discharge_port and
            extraction.loading_port.value.upper() == extraction.discharge_port.value.upper()):
        extraction.discharge_port = None

    # cargo_name and cargo_type shouldn't be identical
    if (extraction.cargo_name and extraction.cargo_type and
            extraction.cargo_name.value.upper() == extraction.cargo_type.value.upper()):
        extraction.cargo_type = None

    return extraction
