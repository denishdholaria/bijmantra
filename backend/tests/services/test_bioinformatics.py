import math

import pytest

from app.services.bioinformatics import BioinformaticsService, SequenceStats


class TestBioinformaticsService:
    @pytest.fixture
    def service(self):
        return BioinformaticsService()

    def test_find_restriction_sites_single_match(self, service):
        sequence = "AAAGAATTCCC"
        sites = service.find_restriction_sites(sequence, enzymes=["EcoRI"])
        assert len(sites) == 1
        assert sites[0].enzyme == "EcoRI"
        assert sites[0].position == 3
        assert sites[0].cut_position == 4
        assert sites[0].recognition_seq == "GAATTC"
        assert sites[0].overhang == "5'"

    def test_find_restriction_sites_multiple_matches(self, service):
        sequence = "GGATCCAAAGGATCC"
        sites = service.find_restriction_sites(sequence, enzymes=["BamHI"])
        assert len(sites) == 2
        assert sites[0].position == 0
        assert sites[1].position == 9

    def test_find_restriction_sites_multiple_enzymes(self, service):
        sequence = "GAATTCGGATCC"
        sites = service.find_restriction_sites(sequence, enzymes=["EcoRI", "BamHI"])
        assert len(sites) == 2
        assert sites[0].enzyme == "EcoRI"
        assert sites[0].position == 0
        assert sites[1].enzyme == "BamHI"
        assert sites[1].position == 6

    def test_find_restriction_sites_no_match(self, service):
        assert service.find_restriction_sites("AAAAAA") == []

    def test_find_restriction_sites_filter_enzymes(self, service):
        sequence = "GAATTCGGATCC"
        sites = service.find_restriction_sites(sequence, enzymes=["EcoRI"])
        assert len(sites) == 1
        assert sites[0].enzyme == "EcoRI"

    def test_find_restriction_sites_empty_sequence(self, service):
        assert service.find_restriction_sites("") == []

    def test_find_restriction_sites_clean_sequence(self, service):
        sequence = " gaa \n ttc "
        sites = service.find_restriction_sites(sequence, enzymes=["EcoRI"])
        assert len(sites) == 1
        assert sites[0].enzyme == "EcoRI"
        assert sites[0].position == 0

    def test_find_restriction_sites_invalid_enzyme(self, service):
        sites = service.find_restriction_sites("GAATTC", enzymes=["InvalidEnzyme"])
        assert len(sites) == 0

    def test_find_restriction_sites_all_enzymes_default(self, service):
        sites = service.find_restriction_sites("GAATTC")
        assert any(s.enzyme == "EcoRI" for s in sites)

    def test_calculate_tm_empty(self, service):
        assert service.calculate_tm("") == 0.0

    def test_calculate_tm_short_sequence(self, service):
        seq = "ATGC"
        expected = 12.0
        assert service.calculate_tm(seq, method="basic") == expected
        assert service.calculate_tm(seq, method="wallace") == expected
        assert service.calculate_tm(seq, method="nearest_neighbor") == expected

    def test_calculate_tm_basic_method(self, service):
        seq = "AAAAAATTTTTTGGGGGG"
        expected = 4 * 6 + 2 * 12
        assert service.calculate_tm(seq, method="basic") == expected

    def test_calculate_tm_wallace_method(self, service):
        seq = "AAAAAATTTTTTGGGGGG"
        expected = 2 * 12 + 4 * 6
        assert service.calculate_tm(seq, method="wallace") == expected

    def test_calculate_tm_nearest_neighbor(self, service):
        seq = "GGGGGGGGGGCCCCCCCCCC"
        length = 20
        gc = 20
        na_conc = 0.05
        gc_fraction = gc / length
        expected = 81.5 + 16.6 * math.log10(na_conc) + 41 * gc_fraction - 675 / length

        result = service.calculate_tm(seq, method="nearest_neighbor")
        assert result == pytest.approx(expected, abs=0.01)

    def test_calculate_tm_cleaning(self, service):
        assert service.calculate_tm(" aTgC \n") == 12.0

    def test_calculate_tm_invalid_chars(self, service):
        assert service.calculate_tm("ATGCN") == 12.0
        assert service.calculate_tm("ATGCZ") == 12.0

    def test_calculate_tm_nearest_neighbor_with_n(self, service):
        seq = "GGGGGGGGGGCCCCCCCCCCNN"
        length = 22
        gc = 20
        na_conc = 0.05
        gc_fraction = gc / length
        expected = 81.5 + 16.6 * math.log10(na_conc) + 41 * gc_fraction - 675 / length

        result = service.calculate_tm(seq, method="nearest_neighbor")
        assert result == pytest.approx(expected, abs=0.01)

    def test_analyze_sequence_empty(self, service):
        stats = service.analyze_sequence("")
        assert stats.length == 0
        assert stats.gc_content == 0
        assert stats.at_content == 0
        assert stats.a_count == 0
        assert stats.molecular_weight == 0

    def test_analyze_sequence_simple(self, service):
        stats = service.analyze_sequence("ATGC")

        assert stats.length == 4
        assert stats.a_count == 1
        assert stats.t_count == 1
        assert stats.g_count == 1
        assert stats.c_count == 1
        assert stats.n_count == 0
        assert stats.gc_content == 50.0
        assert stats.at_content == 50.0
        assert stats.molecular_weight == pytest.approx(1307.8)

    def test_analyze_sequence_cleaning(self, service):
        stats = service.analyze_sequence(" at gc \n")
        assert stats.length == 4
        assert stats.gc_content == 50.0

    def test_analyze_sequence_invalid_characters(self, service):
        stats = service.analyze_sequence("ATGC123!")
        assert stats.length == 4
        assert stats.a_count == 1
        assert stats.t_count == 1
        assert stats.g_count == 1
        assert stats.c_count == 1

    def test_analyze_sequence_ambiguous_bases(self, service):
        stats = service.analyze_sequence("ANTG")

        assert stats.length == 4
        assert stats.n_count == 1
        assert stats.a_count == 1
        assert stats.t_count == 1
        assert stats.g_count == 1
        assert stats.c_count == 0
        assert stats.gc_content == 25.0
        assert stats.at_content == 50.0
        assert stats.molecular_weight == pytest.approx(1000.6)

    def test_analyze_sequence_extended_iupac(self, service):
        stats = service.analyze_sequence("ATRY")
        assert stats.length == 4
        assert stats.a_count == 1
        assert stats.t_count == 1
        assert stats.g_count == 0
        assert stats.c_count == 0
        assert stats.n_count == 0
        assert stats.gc_content == 0.0
        assert stats.at_content == 50.0

    def test_analyze_sequence_all_gc(self, service):
        stats = service.analyze_sequence("GGCC")
        assert stats.length == 4
        assert stats.gc_content == 100.0
        assert stats.at_content == 0.0

    def test_analyze_sequence_all_at(self, service):
        stats = service.analyze_sequence("AATT")
        assert stats.length == 4
        assert stats.gc_content == 0.0
        assert stats.at_content == 100.0

    def test_sequencestats_to_dict(self):
        stats = SequenceStats(
            length=10,
            gc_content=50.123,
            at_content=49.876,
            a_count=2,
            t_count=3,
            g_count=2,
            c_count=3,
            n_count=0,
            molecular_weight=3000.55,
        )

        data = stats.to_dict()
        assert data["length"] == 10
        assert data["gc_content"] == 50.12
        assert data["at_content"] == 49.88
        assert data["composition"]["A"] == 2
        assert data["composition"]["T"] == 3
        assert data["molecular_weight"] == 3000.55

    def test_translate_sequence_happy_path(self, service):
        assert service.translate_sequence("ATGGGTTAA") == "MG*"

    def test_translate_sequence_frames(self, service):
        sequence = "ATGGGTTAA"
        assert service.translate_sequence(sequence, frame=0) == "MG*"
        assert service.translate_sequence(sequence, frame=1) == "WV"
        assert service.translate_sequence(sequence, frame=2) == "GL"

    def test_translate_sequence_stop_codons(self, service):
        assert service.translate_sequence("TAATAGTGA") == "***"

    def test_translate_sequence_ambiguity(self, service):
        assert service.translate_sequence("NNNATG") == "XM"

    def test_translate_sequence_lowercase_whitespace(self, service):
        assert service.translate_sequence("  atg ggt taa  \n") == "MG*"

    def test_translate_sequence_empty(self, service):
        assert service.translate_sequence("") == ""

    def test_translate_sequence_partial_codon(self, service):
        assert service.translate_sequence("AT") == ""
        assert service.translate_sequence("ATGG") == "M"

    def test_translate_sequence_invalid_chars(self, service):
        assert service.translate_sequence("ATGZGTAA") == "MV"

    def test_translate_large_sequence(self, service):
        sequence = "ATGGCCATTGTAATGGCCATTGTAATGGCC"
        assert service.translate_sequence(sequence) == "MAIVMAIVMA"
