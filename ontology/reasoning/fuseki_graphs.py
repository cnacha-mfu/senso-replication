#!/usr/bin/env python3
"""Fuseki named-graph helpers (SPARQL 1.1 Graph Store Protocol) for WP1.

Paper 1 - per-repository graphs (design 3.4):

  * ``urn:senso:abox:{repo}``                  asserted measurements,
  * ``urn:senso:abox-derived:{repo}``          post stage-A aggregates,
  * ``urn:senso:inferred:{repo}:{tboxhash}``   inferred labels + provenance,
  * ``urn:senso:explanations:{repo}:{tboxhash}``  justifications.

``PUT /{dataset}/data?graph=<iri>`` replaces a graph atomically and
idempotently; ``GET`` reads it back. Request construction is pure
(``build_*``) so it can be unit-tested without a server; ``put_graph`` etc.
send it. Writes to the protected JSS-era dataset ``seo`` are refused unless
``allow_protected=True`` is passed, so a new run cannot overwrite the data
behind the submitted paper.

Usage:
    python ontology/reasoning/fuseki_graphs.py --selftest
"""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass, field
from typing import Mapping, Optional
from urllib.parse import quote, unquote

logger = logging.getLogger("senso.fuseki")

NTRIPLES = "application/n-triples"
PROTECTED_DATASETS = frozenset({"seo"})


def abox_graph(repo: str) -> str:
    """IRI of the asserted ABox graph of a repository."""
    return f"urn:senso:abox:{repo}"


def derived_graph(repo: str) -> str:
    """IRI of the post stage-A aggregate graph."""
    return f"urn:senso:abox-derived:{repo}"


def inferred_graph(repo: str, tbox_hash: str) -> str:
    """IRI of the inferred graph (hash ties it to the TBox that produced it)."""
    return f"urn:senso:inferred:{repo}:{tbox_hash[:12]}"


def explanations_graph(repo: str, tbox_hash: str) -> str:
    """IRI of the explanations graph."""
    return f"urn:senso:explanations:{repo}:{tbox_hash[:12]}"


@dataclass
class Request:
    """A fully specified HTTP request (method, url, headers, body)."""

    method: str
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    body: Optional[bytes] = None


def _data_url(base_url: str, dataset: str, graph_iri: str) -> str:
    return f"{base_url.rstrip('/')}/{dataset}/data?graph={quote(graph_iri, safe='')}"


def _guard(dataset: str, allow_protected: bool) -> None:
    if dataset in PROTECTED_DATASETS and not allow_protected:
        raise PermissionError(
            f"dataset '{dataset}' holds JSS-era data; pass allow_protected=True to write to it")


def build_put(base_url: str, dataset: str, graph_iri: str, ntriples: str | bytes,
              *, allow_protected: bool = False) -> Request:
    """Graph Store Protocol PUT (replace a named graph)."""
    _guard(dataset, allow_protected)
    body = ntriples.encode("utf-8") if isinstance(ntriples, str) else ntriples
    return Request("PUT", _data_url(base_url, dataset, graph_iri),
                   {"Content-Type": NTRIPLES + "; charset=utf-8"}, body)


def build_get(base_url: str, dataset: str, graph_iri: str) -> Request:
    """Graph Store Protocol GET (read a named graph as N-Triples)."""
    return Request("GET", _data_url(base_url, dataset, graph_iri), {"Accept": NTRIPLES})


def build_delete(base_url: str, dataset: str, graph_iri: str,
                 *, allow_protected: bool = False) -> Request:
    """Graph Store Protocol DELETE."""
    _guard(dataset, allow_protected)
    return Request("DELETE", _data_url(base_url, dataset, graph_iri))


def construct_graph_query(graph_iri: str) -> str:
    """SPARQL CONSTRUCT that reads a whole named graph back (reasoner input)."""
    return f"CONSTRUCT {{ ?s ?p ?o }} FROM <{graph_iri}> WHERE {{ ?s ?p ?o }}"


def build_construct(base_url: str, dataset: str, graph_iri: str) -> Request:
    """POST the CONSTRUCT query to the dataset's query endpoint."""
    body = ("query=" + quote(construct_graph_query(graph_iri), safe="")).encode()
    return Request("POST", f"{base_url.rstrip('/')}/{dataset}/query",
                   {"Content-Type": "application/x-www-form-urlencoded", "Accept": NTRIPLES}, body)


def send(req: Request, *, timeout: int = 120) -> bytes:
    """Send a request; raises for HTTP errors. Untested against a live server."""
    import requests

    r = requests.request(req.method, req.url, headers=req.headers, data=req.body, timeout=timeout)
    r.raise_for_status()
    return r.content


def put_graph(base_url: str, dataset: str, graph_iri: str, ntriples: str | bytes,
              *, allow_protected: bool = False) -> None:
    """Replace a named graph with N-Triples."""
    send(build_put(base_url, dataset, graph_iri, ntriples, allow_protected=allow_protected))


def get_graph(base_url: str, dataset: str, graph_iri: str) -> str:
    """Read a named graph as N-Triples text."""
    return send(build_get(base_url, dataset, graph_iri)).decode("utf-8")


def delete_graph(base_url: str, dataset: str, graph_iri: str,
                 *, allow_protected: bool = False) -> None:
    """Delete a named graph."""
    send(build_delete(base_url, dataset, graph_iri, allow_protected=allow_protected))


def _selftest() -> int:
    """Check request construction (no server needed)."""
    g = abox_graph("pallets/flask")
    r = build_put("http://127.0.0.1:3030/", "seo_v2", g, "<a> <b> <c> .\n")
    assert r.method == "PUT"
    assert r.url == "http://127.0.0.1:3030/seo_v2/data?graph=urn%3Asenso%3Aabox%3Apallets%2Fflask", r.url
    assert r.headers["Content-Type"].startswith("application/n-triples")
    assert r.body == b"<a> <b> <c> .\n"
    gt = build_get("http://h:3030", "d", inferred_graph("o/n", "abcdef0123456789"))
    assert gt.url.endswith("graph=urn%3Asenso%3Ainferred%3Ao%2Fn%3Aabcdef012345"), gt.url
    assert gt.headers == {"Accept": NTRIPLES}
    try:
        build_put("http://h:3030", "seo", g, "")
    except PermissionError:
        pass
    else:
        raise AssertionError("write to protected dataset must be refused")
    assert build_put("http://h:3030", "seo", g, "", allow_protected=True).method == "PUT"
    c = build_construct("http://h:3030", "d", g)
    assert c.method == "POST" and c.url == "http://h:3030/d/query"
    assert unquote(c.body.decode()).startswith("query=CONSTRUCT { ?s ?p ?o } FROM <urn:senso:abox:")
    assert "FROM <urn:senso:abox:pallets/flask>" in construct_graph_query(g)
    print("fuseki_graphs selftest ok")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Fuseki named-graph helpers (Paper 1, WP1)")
    ap.add_argument("--selftest", action="store_true")
    if ap.parse_args().selftest:
        sys.exit(_selftest())
    ap.print_help()
