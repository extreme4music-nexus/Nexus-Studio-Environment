# Development

Run Python 3.12 or newer. Create a local virtual environment outside the reference trees. Run `python -m unittest discover -s tests`. Package directories are `modules/nse_<name>`; module design documents are in `modules/<name>`. Only `nse_*` packages are included in distribution discovery. Never run recursive compilation or test collection over legacy references.

New module: define a port and DTOs in contracts, document ownership, inject implementation in the composition root, add contract fixtures, and verify all three OS targets.
