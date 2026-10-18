"""Synthetic unit tests for mlogcross (no blueprint needed)."""
import sys

sys.path.insert(0, "mindustry-blueprint/tools")

import mlogcross as X

# A declares its own variable; B reads it. No `write` needed -- the readable
# slot IS the target's own variable.
A = X.Unit("A @(0,0)", (0, 0), ["set count 42", "end"], {"B": (5, 0)})
B = X.Unit("B @(5,0)", (5, 0),
           ['read n A "count"', "print n", "end"], {"A": (0, 0)})
print(X.format_report(X.analyze_units([A, B]), "own variable, constant"))
print()

# A's variable is null -> the read is always null.
A2 = X.Unit("A @(0,0)", (0, 0), ["set flag null", "end"], {"B": (5, 0)})
B2 = X.Unit("B @(5,0)", (5, 0),
            ['read f A "flag"', "end"], {"A": (0, 0)})
print(X.format_report(X.analyze_units([A2, B2]), "own variable, null"))
print()

# Nobody assigns "ghost" on A -> never assigned.
B3 = X.Unit("B @(5,0)", (5, 0),
            ['read g A "ghost"', "end"], {"A": (0, 0)})
A3 = X.Unit("A @(0,0)", (0, 0), ["end"], {"B": (5, 0)})
print(X.format_report(X.analyze_units([A3, B3]), "never assigned"))
print()

# A's variable takes two different values -> widens to TOP, no finding.
A4 = X.Unit("A @(0,0)", (0, 0),
            ["set v 1", "set v 2", "end"], {"B": (5, 0)})
B4 = X.Unit("B @(5,0)", (5, 0),
            ['read x A "v"', "print x", "end"], {"A": (0, 0)})
print(X.format_report(X.analyze_units([A4, B4]), "widened"))
print()

# explicit write nobody reads
A5 = X.Unit("A @(0,0)", (0, 0), ['write 7 B "unused"', "end"], {"B": (5, 0)})
B5 = X.Unit("B @(5,0)", (5, 0), ["end"], {"A": (0, 0)})
print(X.format_report(X.analyze_units([A5, B5]), "dead write"))
