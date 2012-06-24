# Note that this file only exists for backwards compatibility.  The
# marks need no defining and are documented in plugin.py.  And the
# transaction_test_case mark has been replaced with
# the djangodb(transaction=True) mark.

import pytest

transaction_test_case = pytest.mark.transaction_test_case
