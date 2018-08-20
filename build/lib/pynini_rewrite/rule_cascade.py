# For general information on the Pynini grammar compilation library, see
# pynini.opengrm.org.


"""Rule cascade object for Pynini.

This module provides a class for applying rewrite rules (stored in a FAR) to
strings. It makes use of various functions (and a similar API) to the rewrite
library itself. Note that much of this functionality requires a semiring with
the path property.
"""

import pynini

from . import rewrite


class Error(Exception):
  """Custom exception for this module."""

  pass


class RuleCascade(object):
  """A rule cascade is a series of rules to be applied in order to a string.

  The caller must provide the path to a FAR file, and a set of rules before
  calling any other methods.
  """

  def __init__(self, far_path):
    self.far = pynini.Far(far_path)
    self.rules = []

  def _validate_and_arcsort_rules(self, rules):
    """Validates rules by testing for their presence in the input FAR.

  Args:
    rules: An iterable of strings naming rules in the input FAR.

  Yields:
     The requested rules, arc-sorted.

  Raises:
     Error: Cannot find rule.
  """
    for rule in rules:
      if self.far.find(rule):
        yield self.far.get_fst().arcsort(sort_type="ilabel")
      else:
        raise Error("Cannot find rule: {}".format(rule))

  def set_rules(self, rules):
    """Initializes a rule cascade.

  Args:
    rules: An iterable of strings naming rules in the input FAR.
  """
    self.rules = tuple(self._validate_and_arcsort_rules(rules))

  def _rewrite_lattice(self, istring):
    """Applies all rules to an input string.

  Args:
    istring: Input string or FST.

  Returns:
    The lattice of output strings.

  Raises:
    Error: No rules requested.
  """
    if not self.rules:
      raise Error("No rules requested")
    lattice = istring
    for rule in self.rules:
      lattice = rewrite.rewrite_lattice(lattice, rule)
    return lattice

  def top_rewrite(self, istring, token_type="byte"):
    """Returns one top rewrite.

  Args:
    istring: Input string or FST.
    token_type: Output token type, or symbol table.

  Returns:
    The top string.
  """
    lattice = self._rewrite_lattice(istring)
    return rewrite.lattice_to_top_string(lattice, token_type)

  def one_top_rewrite(self, istring, token_type="byte", state_multiplier=4):
    """Returns one top rewrite, unless there is a tie.

  Args:
    istring: Input string or FST.
    token_type: Output token type, or symbol table.
    state_multiplier: Max ratio for the number of states in the DFA lattice to
      the NFA lattice; if exceeded, a warning is logged.

  Returns:
    The top string.
  """
    lattice = self._rewrite_lattice(istring)
    lattice = rewrite.lattice_to_dfa(lattice, True, state_multiplier)
    return rewrite.lattice_to_one_top_string(lattice, token_type)

  def rewrites(self, istring, token_type="byte", state_multiplier=4):
    """Returns all rewrites.

  Args:
    istring: Input string or FST.
    token_type: Output token type, or symbol table.
    state_multiplier: Max ratio for the number of states in the DFA lattice to
      the NFA lattice; if exceeded, a warning is logged.

  Returns:
    A tuple of output strings.
  """
    lattice = self._rewrite_lattice(istring)
    lattice = rewrite.lattice_to_dfa(lattice, False, state_multiplier)
    return rewrite.lattice_to_strings(lattice, token_type)

  def top_rewrites(self, istring, nshortest, token_type="byte"):
    """Returns the top n rewrites.

  Args:
    istring: Input string or FST.
    nshortest: The maximum number of rewrites to return.
    token_type: Output token type, or symbol table.

  Returns:
    A tuple of output strings.
  """
    lattice = self._rewrite_lattice(istring)
    lattice = rewrite.lattice_to_shortest(lattice, nshortest)
    return rewrite.lattice_to_strings(lattice, token_type)

  def optimal_rewrites(self, istring, token_type="byte", state_multiplier=4):
    """Returns all optimal rewrites.

  Args:
    istring: Input string or FST.
    token_type: Output token type, or symbol table.
    state_multiplier: Max ratio for the number of states in the DFA lattice to
     the NFA lattice; if exceeded, a warning is logged.

  Returns:
    A tuple of output strings.
  """
    lattice = self._rewrite_lattice(istring)
    lattice = rewrite.lattice_to_dfa(lattice, True, state_multiplier)
    return rewrite.lattice_to_strings(lattice, token_type)

  def matches(self, istring, ostring):
    """Returns whether or not the rule cascade allows an input/output pair.

  Args:
    istring: Input string or FST.
    ostring: Expected output string or FST.

  Returns:
    True iff the lattice contains ostring.
  """
    lattice = self._rewrite_lattice(istring)
    return pynini.matches(lattice, ostring, compose_filter="alt_sequence")
