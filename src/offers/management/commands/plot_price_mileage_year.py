import os

from django.conf import settings
from django.core.management.base import BaseCommand

from offers.models import AudioSystem, CarOffer, convert_price_to_pln


def _repo_root():
    """Repository root (parent of Django BASE_DIR, which lives under src/)."""
    return os.path.normpath(os.path.join(settings.BASE_DIR, ".."))


def _default_output_path():
    return os.path.join(_repo_root(), "out", "price_by_mileage_year.png")


def _resolve_output_path(output_option):
    """Absolute paths unchanged; relative paths go under <repo>/out/ (not CWD)."""
    if output_option is None:
        return _default_output_path()
    if os.path.isabs(output_option):
        return output_option
    return os.path.normpath(os.path.join(_repo_root(), "out", output_option))


def _trend_median_bins(x_arr, y_arr, log_y=False, n_bins=22):
    """
    Robust cloud-following curve: median PLN in mileage quantile bins,
    lightly smoothed, then interpolated. Works well when one parametric model is off.
    """
    import numpy as np

    n = len(x_arr)
    if n < 10:
        return None, ""
    nb = min(max(8, n_bins), max(6, n // 4))
    order = np.argsort(x_arr)
    xs, ys = x_arr[order], y_arr[order]
    qs = np.linspace(0.0, 1.0, nb + 1)
    edges = np.unique(np.quantile(xs, qs))
    if len(edges) < 3:
        return None, ""
    centers = []
    medians = []
    for i in range(len(edges) - 1):
        lo, hi = edges[i], edges[i + 1]
        if i == len(edges) - 2:
            mask = (xs >= lo) & (xs <= hi)
        else:
            mask = (xs >= lo) & (xs < hi)
        if np.count_nonzero(mask) < 2:
            continue
        centers.append(float(np.median(xs[mask])))
        medians.append(float(np.median(ys[mask])))
    if len(centers) < 3:
        return None, ""
    centers = np.asarray(centers, dtype=float)
    medians = np.asarray(medians, dtype=float)
    smoothed = np.copy(medians)
    smoothed[1:-1] = (
        0.25 * medians[:-2] + 0.5 * medians[1:-1] + 0.25 * medians[2:]
    )
    x_line = np.linspace(float(xs[0]), float(xs[-1]), 500)
    y_line = np.interp(x_line, centers, smoothed)
    floor = 1.0 if log_y else 0.0
    y_line = np.maximum(y_line, floor)
    return (x_line, y_line), "Trend: mediana w koszykach przebiegu"


def _trend_loglog(x_arr, y_arr, log_y=False):
    """Power law in mileage: price ≈ exp(c0) * mileage^c1 (fit in log-log)."""
    import numpy as np

    mask = (x_arr > 0) & (y_arr > 0)
    xf, yf = x_arr[mask], y_arr[mask]
    if len(xf) < 3:
        return None, ""
    lx = np.log(xf)
    ly = np.log(yf)
    coeffs = np.polyfit(lx, ly, 1)
    lo = max(1.0, float(np.min(x_arr)))
    hi = float(np.max(x_arr))
    if lo >= hi:
        lo = max(0.5, float(np.min(x_arr)))
    x_line = np.linspace(lo, hi, 400)
    y_line = np.exp(np.polyval(coeffs, np.log(x_line)))
    y_line = np.maximum(y_line, 1.0 if log_y else 0.0)
    return (x_line, y_line), "Trend: potęgowy (log–log MNK)"


def _trend_poly2(x_arr, y_arr, log_y=False):
    """Quadratic in mileage (MNK); with log_y fits quadratic to log(price)."""
    import numpy as np

    mask = (y_arr > 0) if log_y else np.ones_like(y_arr, dtype=bool)
    xf, yf = x_arr[mask], y_arr[mask]
    if log_y:
        yf = np.log(yf)
    if len(xf) < 4:
        return None, ""
    coeffs = np.polyfit(xf, yf, 2)
    x_line = np.linspace(float(np.min(x_arr)), float(np.max(x_arr)), 400)
    fitted = np.polyval(coeffs, x_line)
    if log_y:
        y_line = np.exp(fitted)
        y_line = np.maximum(y_line, 1.0)
    else:
        y_line = fitted
        y_line = np.maximum(y_line, 0.0)
    return (x_line, y_line), "Trend: wielomian 2. st. (MNK)"


def _inverse_mileage_trend_line(x_arr, y_arr, log_y=False):
    """
    Least-squares fit in 1/mileage: price ≈ c0 + c1/mileage (linear y),
    or log(price) ≈ c0 + c1/mileage when log_y (then curve is exp of that).
    Uses only points with mileage > 0 (and price > 0 if log_y).
    Returns ((x_line, y_line), label) or (None, "").
    """
    import numpy as np

    mask = x_arr > 0
    if log_y:
        mask = mask & (y_arr > 0)
    xf = x_arr[mask]
    yf = y_arr[mask]
    if len(xf) < 2:
        return None, ""
    inv_x = 1.0 / xf
    dep = np.log(yf) if log_y else yf
    coeffs = np.polyfit(inv_x, dep, 1)
    xmin = float(np.min(x_arr))
    xmax = float(np.max(x_arr))
    lo = max(xmin, 1.0)
    if lo >= xmax:
        lo = max(xmin, 0.5)
    x_line = np.linspace(lo, xmax, 400)
    inv_line = 1.0 / x_line
    fitted = np.polyval(coeffs, inv_line)
    if log_y:
        y_line = np.exp(fitted)
        y_line = np.maximum(y_line, 1.0)
    else:
        y_line = fitted
        y_line = np.maximum(y_line, 0.0)
    label = (
        "Trend: log(cena) ≈ a + b/przebieg"
        if log_y
        else "Trend: cena ≈ a + b/przebieg (MNK)"
    )
    return (x_line, y_line), label


def _compute_trend(trend_name, x_arr, y_arr, log_y, n_bins):
    trend_name = (trend_name or "median_bin").strip().lower()
    if trend_name == "median_bin":
        return _trend_median_bins(x_arr, y_arr, log_y=log_y, n_bins=n_bins)
    if trend_name == "loglog":
        return _trend_loglog(x_arr, y_arr, log_y=log_y)
    if trend_name == "poly2":
        return _trend_poly2(x_arr, y_arr, log_y=log_y)
    if trend_name == "inverse":
        return _inverse_mileage_trend_line(x_arr, y_arr, log_y=log_y)
    return None, ""


class Command(BaseCommand):
    help = (
        "Scatter plot: price (PLN) vs mileage (km), point color = year, plus a trend curve. "
        "Default trend follows the point cloud (median in mileage bins). "
        "Points: color=year; markers = audio (○ standard, □ HK, ▲ B&W). "
        "Uses offers with price convertible to PLN, non-null mileage and year."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "-o",
            "--output",
            default=None,
            help="Output image path (PNG). Default: <repo>/out/price_by_mileage_year.png. "
            "Relative paths are resolved under <repo>/out/, not the shell CWD.",
        )
        parser.add_argument(
            "--source",
            default="",
            help="Optional CarOffer.source filter (e.g. otomoto, autoscout24).",
        )
        parser.add_argument("--min-year", type=int, default=None)
        parser.add_argument("--max-year", type=int, default=None)
        parser.add_argument(
            "--log-y",
            action="store_true",
            help="Use log scale for price (PLN).",
        )
        parser.add_argument(
            "--trend",
            default="median_bin",
            choices=("median_bin", "loglog", "poly2", "inverse"),
            help=(
                "Trend curve: median_bin (default, follows the cloud), loglog (power law), "
                "poly2 (quadratic), inverse (a+b/mileage)."
            ),
        )
        parser.add_argument(
            "--trend-bins",
            type=int,
            default=22,
            help="Number of mileage quantile bins for median_bin trend (default 22).",
        )

    def handle(self, *args, **options):
        try:
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            from matplotlib.colors import Normalize

            import numpy as np
        except ImportError as e:
            raise SystemExit(
                "matplotlib is required. Install with: uv add matplotlib"
            ) from e

        qs = CarOffer.objects.filter(
            mileage_km__isnull=False,
            year__isnull=False,
            price_amount__isnull=False,
        )
        src = (options.get("source") or "").strip()
        if src:
            qs = qs.filter(source=src)
        if options.get("min_year") is not None:
            qs = qs.filter(year__gte=options["min_year"])
        if options.get("max_year") is not None:
            qs = qs.filter(year__lte=options["max_year"])

        mileage = []
        price_pln = []
        years = []
        audio_systems = []

        for mk, yr, amt, cur, audio in qs.values_list(
            "mileage_km", "year", "price_amount", "price_currency", "audio_system"
        ).iterator():
            pln = convert_price_to_pln(amt, cur)
            if pln is None:
                continue
            mileage.append(mk)
            price_pln.append(float(pln))
            years.append(yr)
            audio_systems.append(audio or "")

        n = len(mileage)
        if n == 0:
            self.stderr.write("No rows with mileage, year, and PLN-convertible price.")
            return

        out_path = _resolve_output_path(options["output"])
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

        fig, ax = plt.subplots(figsize=(10, 6))
        year_np = np.asarray(years, dtype=float)
        y_min, y_max = float(np.min(year_np)), float(np.max(year_np))
        if y_min == y_max:
            y_min -= 0.5
            y_max += 0.5
        norm = Normalize(vmin=y_min, vmax=y_max)
        cmap_name = "viridis"

        audio_np = np.array(audio_systems, dtype=object)
        is_bw = audio_np == AudioSystem.BOWERS_WILKINS
        is_hk = audio_np == AudioSystem.HARMAN_KARDON
        is_std = ~(is_bw | is_hk)

        x_all = np.asarray(mileage, dtype=float)
        y_all = np.asarray(price_pln, dtype=float)

        def _scatter_audio(mask, marker, size, alpha, edgecolors, linewidths, label, z):
            if not np.any(mask):
                return
            ax.scatter(
                x_all[mask],
                y_all[mask],
                c=year_np[mask],
                cmap=cmap_name,
                norm=norm,
                alpha=alpha,
                s=size,
                marker=marker,
                edgecolors=edgecolors,
                linewidths=linewidths,
                label=label,
                zorder=z,
            )

        _scatter_audio(
            is_std,
            marker="o",
            size=22,
            alpha=0.5,
            edgecolors="none",
            linewidths=0,
            label="Standard / brak / inne premium",
            z=2,
        )
        _scatter_audio(
            is_hk,
            marker="s",
            size=38,
            alpha=0.62,
            edgecolors="0.25",
            linewidths=0.35,
            label="Harman Kardon",
            z=3,
        )
        _scatter_audio(
            is_bw,
            marker="^",
            size=52,
            alpha=0.78,
            edgecolors="0.2",
            linewidths=0.45,
            label="B&W (Bowers & Wilkins)",
            z=4,
        )

        sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap_name)
        sm.set_array(year_np)
        cb = fig.colorbar(sm, ax=ax)
        cb.set_label("Year")
        ax.set_xlabel("Mileage (km)")
        ax.set_ylabel("Price (PLN)")
        if options.get("log_y"):
            ax.set_yscale("log")
            ax.set_ylabel("Price (PLN), log scale")

        x_arr = x_all
        y_arr = y_all
        log_y = bool(options.get("log_y"))
        (trend_xy, trend_label) = _compute_trend(
            options["trend"],
            x_arr,
            y_arr,
            log_y,
            int(options["trend_bins"]),
        )
        if trend_xy is not None and trend_label:
            x_line, y_line = trend_xy
            ax.plot(
                x_line,
                y_line,
                color="crimson",
                linewidth=2.4,
                label=trend_label,
                zorder=5,
            )
        ax.legend(loc="upper right", framealpha=0.92, fontsize=9)
        title = (
            f"Price vs mileage (n={n}, kolor=rok, ○std □HK ▲B&W, trend={options['trend']})"
        )
        if src:
            title += f", source={src}"
        ax.set_title(title)
        fig.tight_layout()
        fig.savefig(out_path, dpi=150)
        plt.close(fig)

        self.stdout.write(self.style.SUCCESS(f"Wrote {n} points to {out_path}"))
