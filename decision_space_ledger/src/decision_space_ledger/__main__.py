"""Allow running as: python -m decision_space_ledger <snapshot_a.json> <snapshot_b.json>"""

import sys

from .cli import main

sys.exit(main())
