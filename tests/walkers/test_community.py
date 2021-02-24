import itertools

import pytest

from pyrdf2vec.graphs import KG, Vertex
from pyrdf2vec.walkers import CommunityWalker

LOOP = [
    ["Alice", "knows", "Bob"],
    ["Alice", "knows", "Dean"],
    ["Bob", "knows", "Dean"],
    ["Dean", "loves", "Alice"],
]
LONG_CHAIN = [
    ["Alice", "knows", "Bob"],
    ["Alice", "knows", "Dean"],
    ["Bob", "knows", "Mathilde"],
    ["Mathilde", "knows", "Alfy"],
    ["Alfy", "knows", "Stephane"],
    ["Stephane", "knows", "Alfred"],
    ["Alfred", "knows", "Emma"],
    ["Emma", "knows", "Julio"],
]
URL = "http://pyRDF2Vec"

KG_LOOP = KG()
KG_CHAIN = KG()

DEPTHS = range(6)
KGS = [KG_LOOP, KG_CHAIN]
MAX_WALKS = range(6)
IS_REVERSE = (False, True)
ROOTS_WITHOUT_URL = ["Alice", "Bob", "Dean"]
WITH_REVERSE = (False, True)


class TestCommunityWalker:
    @pytest.fixture(scope="session")
    def setup(self):
        for i, graph in enumerate([LOOP, LONG_CHAIN]):
            for row in graph:
                subj = Vertex(f"{URL}#{row[0]}")
                obj = Vertex((f"{URL}#{row[2]}"))
                pred = Vertex(
                    (f"{URL}#{row[1]}"), predicate=True, vprev=subj, vnext=obj
                )
                if i == 0:
                    KG_LOOP.add_walk(subj, pred, obj)
                else:
                    KG_CHAIN.add_walk(subj, pred, obj)

    @pytest.mark.parametrize(
        "kg, root, depth, is_reverse",
        list(itertools.product(KGS, ROOTS_WITHOUT_URL, DEPTHS, IS_REVERSE)),
    )
    def test_bfs(self, setup, kg, root, depth, is_reverse):
        root = f"{URL}#{root}"
        walker = CommunityWalker(depth, None, random_state=42)
        walker._community_detection(kg)
        walks = walker._bfs(kg, Vertex(root), is_reverse)
        for walk in walks:
            assert len(walk) <= (depth * 2) + 1
            if is_reverse:
                assert walk[-1].name == root
            else:
                assert walk[0].name == root

    @pytest.mark.parametrize(
        "kg, root, depth, max_walks, is_reverse",
        list(
            itertools.product(
                KGS, ROOTS_WITHOUT_URL, DEPTHS, MAX_WALKS, IS_REVERSE
            )
        ),
    )
    def test_dfs(self, setup, kg, root, depth, max_walks, is_reverse):
        root = f"{URL}#{root}"
        walker = CommunityWalker(depth, max_walks, random_state=42)
        walker._community_detection(kg)
        walks = walker._dfs(kg, Vertex(root), is_reverse)
        for walk in walks:
            assert len(walk) <= (depth * 2) + 1
            if is_reverse:
                assert walk[-1].name == root
            else:
                assert walk[0].name == root

    @pytest.mark.parametrize(
        "kg, root, depth, max_walks, with_reverse",
        list(
            itertools.product(
                KGS, ROOTS_WITHOUT_URL, DEPTHS, MAX_WALKS, WITH_REVERSE
            )
        ),
    )
    def test_extract(self, setup, kg, root, depth, max_walks, with_reverse):
        root = f"{URL}#{root}"
        walker = CommunityWalker(
            depth, max_walks, with_reverse=with_reverse, random_state=42
        )
        walker._community_detection(kg)
        walks = walker._extract(kg, Vertex(root))[root]
        if max_walks is not None:
            if with_reverse:
                assert len(walks) <= max_walks * max_walks
            else:
                assert len(walks) <= max_walks
        for walk in walks:
            for obj in walk[2::2]:
                assert obj.startswith("b'")
            if not with_reverse:
                assert walk[0] == root
                assert len(walk) <= (depth * 2) + 1
            else:
                assert len(walk) <= ((depth * 2) + 1) * 2
