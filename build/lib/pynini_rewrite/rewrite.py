# For general information on the Pynini grammar compilation library, see
# pynini.opengrm.org.


"""Rewriter functions for Pynini.

This module provides functions for rewriting strings using WFST rules,
addressing some common pitfalls.
"""

import logging

import pynini


class Error(Exception):
  """Custom exception for this module."""

  pass


def _check_nonempty_and_cleanup(lattice):
  """Checks wellformedness of lattice and cleans up.

  Args:
  lattice:

  Returns:
  An epsilon-free WFSA.

  Raises:
  Error: Composition failure.
  """
  if lattice.start() == pynini.NO_STATE_ID:
    raise Error("Composition failure")
  return lattice.project(project_output=True).rmepsilon()


def rewrite_lattice(string, rule):
  """Constructs a weighted lattice of output strings.

  Constructs a weighted, epsilon-free lattice of output strings given an
  input FST (or string) and a rule FST.

  Args:
  string: Input string or FST.
  rule: Input rule WFST.

  Returns:
  An epsilon-free WFSA.
  """
  # TODO(kbg): Consider adding for PDT and MPDT composition.
  lattice = pynini.compose(string, rule, compose_filter="alt_sequence")
  return _check_nonempty_and_cleanup(lattice)


def lattice_to_dfa(lattice, optimal_only, state_multiplier=4):
  """Constructs a (possibly pruned) weighted DFA of output strings.

  Given an epsilon-free lattice of output strings (such as produced by
  rewrite_lattice), attempts to determinize it, pruning non-optimal paths if
  optimal_only is true. This is valid only in a semiring with the path property.

  To prevent unexpected blowup during determinization, a state threshold is
  also used and a warning is logged if this exact threshold is reached. The
  threshold is a multiplier of the size of input lattice (by default, 4), plus
  a small constant factor. This is intended by a sensible default and is not an
  inherently meaningful value in and of itself.

  Args:
  lattice: Epsilon-free non-deterministic finite acceptor.
  optimal_only: Should we only preserve optimal paths?
  state_multiplier: Max ratio for the number of states in the DFA lattice to
     the NFA lattice; if exceeded, a warning is logged.

  Returns:
  Epsilon-free deterministic finite acceptor.
  """
  weight_type = lattice.weight_type()
  weight_threshold = (
    pynini.Weight.One(weight_type)
    if optimal_only
    else pynini.Weight.Zero(weight_type)
  )
  state_threshold = 256 + state_multiplier * lattice.num_states()
  lattice = pynini.determinize(
    lattice, nstate=state_threshold, weight=weight_threshold
  )
  if lattice.num_states() == state_threshold:
    logging.warning(
      "Unexpected hit state threshold; consider a higher value "
      "for state_multiplier"
    )
  return lattice


def lattice_to_shortest(lattice, nshortest):
  """Returns the n-shortest unique paths.

  Given an epsilon-free lattice of output strings (such as produced by
  rewrite_lattice), extracts the n-shortest unique strings. This is valid only
  in a path semiring.

  Args:
  lattice: Epsilon-free finite acceptor.
  nshortest: Maximum number of shortest paths desired.

  Returns:
  A lattice of the n-shortest unique paths.
  """
  return pynini.shortestpath(lattice, nshortest=nshortest, unique=True)


def lattice_to_top_string(lattice, token_type="byte"):
  """Returns the top string in the lattice.

  Given an epsilon-free lattice of output strings (such as produced by
  rewrite_lattice), extracts a single top string. This is valid only in a path
  semiring.

  Args:
  lattice: Epsilon-free finite acceptor.
  token_type: Output token type, or symbol table.

  Returns:
  The top string.
  """
  return pynini.shortestpath(lattice).stringify(token_type)


def lattice_to_one_top_string(lattice, token_type="byte"):
  """Returns the top string in the lattice, raising an error if there's a tie.

  Given a pruned DFA of output strings (such as produced by lattice_to_dfa
  with optimal_only), extracts a single top string, raising an error if there's
  a tie.

  Args:
  lattice: Epsilon-free deterministic finite acceptor.
  token_type: Output token type, or symbol table.

  Returns:
  The top string.

  Raises:
  Error: Multiple top rewrites found.
  """
  spaths = lattice.paths(token_type)
  output = spaths.ostring()
  spaths.next()
  if not spaths.done():
    raise Error(
      "Multiple top rewrites found: {} and {} (weight: {})".format(
        output, spaths.ostring(), spaths.weight()
      )
    )
  return output


def lattice_to_strings(lattice, token_type="byte"):
  """Returns tuple of output strings.

  Args:
  lattice: Epsilon-free acyclic WFSA.
  token_type: Output token type, or symbol table.

  Returns:
  An tuple of output strings.
  """
  return tuple(lattice.paths(token_type).ostrings())
  
  
def lattice_to_strings_and_weights(lattice, input_token_type="byte", output_token_type="byte"):
    """Returns list of tuples of ARPA phones, sorted by weight.
    
    Args:
    lattice: Epsilon-free acyclic WFSA.
    token_type: Output token type, or symbol table.
    
    Returns:
    A list of tuples of output ARPA phones, sorted by lowest to highest weight.
    """
    lattice = _check_nonempty_and_cleanup(lattice)
    sorted_arpa = sorted(lattice.paths(output_token_type=output_token_type), key=lambda path: float(path[2]))
    return [tuple(y.split()) for (x,y,z) in sorted_arpa]


def top_rewrite(string, rule, token_type="byte"):
  """Returns one top rewrite.

  Args:
  string: Input string or FST.
  rule: Input rule WFST.
  token_type: Output token type, or symbol table.

  Returns:
  The top string.
  """
  lattice = rewrite_lattice(string, rule)
  return lattice_to_top_string(lattice, token_type)


def one_top_rewrite(string, rule, token_type="byte", state_multiplier=4):
  """Returns one top rewrite, unless there is a tie.

  Args:
  string: Input string or FST.
  rule: Input rule WFST.
  token_type: Output token type, or symbol table.
  state_multiplier: Max ratio for the number of states in the DFA lattice to
     the NFA lattice; if exceeded, a warning is logged.

  Returns:
  The top string.
  """
  lattice = rewrite_lattice(string, rule)
  lattice = lattice_to_dfa(lattice, True, state_multiplier)
  return lattice_to_one_top_string(lattice, token_type)


def rewrites(string, rule, token_type="byte", state_multiplier=4):
  """Returns all rewrites.

  Args:
  string: Input string or FST.
  rule: Input rule WFST.
  token_type: Output token type, or symbol table.
  state_multiplier: Max ratio for the number of states in the DFA lattice to
     the NFA lattice; if exceeded, a warning is logged.

  Returns:
  A tuple of output strings.
  """
  lattice = rewrite_lattice(string, rule)
  lattice = lattice_to_dfa(lattice, False, state_multiplier)
  return lattice_to_strings(lattice, token_type)


def top_rewrites(string, rule, nshortest, token_type="byte"):
  """Returns the top n rewrites.

  Args:
  string: Input string or FST.
  rule: Input rule WFST.
  nshortest: The maximum number of rewrites to return.
  token_type: Output token type, or symbol table.

  Returns:
  A tuple of output strings.
  """
  lattice = rewrite_lattice(string, rule)
  lattice = lattice_to_shortest(lattice, nshortest)
  return lattice_to_strings(lattice, token_type)


def optimal_rewrites(string, rule, token_type="byte", state_multiplier=4):
  """Returns all optimal rewrites.

  Args:
  string: Input string or FST.
  rule: Input rule WFST.
  token_type: Output token type, or symbol table.
  state_multiplier: Max ratio for the number of states in the DFA lattice to
     the NFA lattice; if exceeded, a warning is logged.

  Returns:
  A tuple of output strings.
  """
  lattice = rewrite_lattice(string, rule)
  lattice = lattice_to_dfa(lattice, True, state_multiplier)
  return lattice_to_strings(lattice, token_type)


def matches(istring, ostring, rule):
  """Returns whether or not a rule generates an input/output pair.

  Args:
  istring: Input string or FST.
  ostring: Expected output string or FST.
  rule: Input rule WFST.

  Returns:
  True iff the lattice contains ostring.
  """
  lattice = rewrite_lattice(istring, rule)
  return pynini.matches(lattice, ostring, compose_filter="alt_sequence")
