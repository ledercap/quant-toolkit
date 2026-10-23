"""quanttk: the shared calculation library behind the quant-toolkit workflows.

Each workflow in `workflows/` is a thin script on top of these modules:

    quanttk.sources     data loaders (SEC EDGAR, Cboe, US Treasury, prices, snapshot lake)
    quanttk.statements  XBRL facts -> standardized, point-in-time annual statements
    quanttk.ratios      the ratio registry computed on top of the statements
    quanttk.pricing     Black-Scholes / Black-76 pricing, implied volatility, Greeks, forwards
    quanttk.options     gamma exposure, volume, volatility surface and VIX replication

Formulas and their citations live in each workflow's README, next to the code that uses them.
"""

__version__ = "0.1.0"
