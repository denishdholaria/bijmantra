import pytest
from app.services.genetic_diversity import GeneticDiversityService

class TestGeneticDiversityLogic:
    @pytest.fixture
    def service(self):
        return GeneticDiversityService()

    def test_calculate_allele_frequencies_homozygous(self, service):
        """Test allele frequency calculation for homozygous genotypes."""
        genotypes = ["0/0", "0/0", "1/1", "1/1"]
        freqs = service._calculate_allele_frequencies(genotypes)

        assert freqs["0"] == 0.5
        assert freqs["1"] == 0.5
        assert sum(freqs.values()) == 1.0

    def test_calculate_allele_frequencies_heterozygous(self, service):
        """Test allele frequency calculation for heterozygous genotypes."""
        genotypes = ["0/1", "0/1", "0/1", "0/1"]
        freqs = service._calculate_allele_frequencies(genotypes)

        assert freqs["0"] == 0.5
        assert freqs["1"] == 0.5

    def test_calculate_allele_frequencies_mixed(self, service):
        """Test allele frequency calculation for mixed genotypes."""
        # 0/0 -> 0,0
        # 0/1 -> 0,1
        # 1/1 -> 1,1
        # Total: 0: 3, 1: 3. Total alleles: 6.
        genotypes = ["0/0", "0/1", "1/1"]
        freqs = service._calculate_allele_frequencies(genotypes)

        assert freqs["0"] == 0.5
        assert freqs["1"] == 0.5

    def test_calculate_allele_frequencies_phased(self, service):
        """Test allele frequency calculation for phased genotypes."""
        genotypes = ["0|1", "1|0", "0|0"]
        freqs = service._calculate_allele_frequencies(genotypes)

        # 0: 1+1+2 = 4
        # 1: 1+1+0 = 2
        # Total: 6
        assert freqs["0"] == 4/6
        assert freqs["1"] == 2/6
        assert abs(freqs["0"] - 0.6666666) < 0.0001

    def test_calculate_allele_frequencies_missing_data(self, service):
        """Test allele frequency calculation with missing data."""
        genotypes = ["0/0", ".", "./.", ".|.", "1/1"]
        freqs = service._calculate_allele_frequencies(genotypes)

        # Should ignore missing
        # 0/0 -> 0,0
        # 1/1 -> 1,1
        # Total alleles: 4
        assert freqs["0"] == 0.5
        assert freqs["1"] == 0.5

    def test_calculate_allele_frequencies_partial_missing(self, service):
        """Test allele frequency calculation with partial missing data."""
        # Note: The implementation logic is:
        # alleles = gt.replace("|", "/").split("/")
        # for allele in alleles:
        #     if allele and allele != ".":
        #         ...

        genotypes = ["0/.", "./1"]
        freqs = service._calculate_allele_frequencies(genotypes)

        # 0/. -> 0 (count 1)
        # ./1 -> 1 (count 1)
        # Total alleles: 2
        assert freqs["0"] == 0.5
        assert freqs["1"] == 0.5

    def test_calculate_allele_frequencies_empty(self, service):
        """Test allele frequency calculation with empty input."""
        assert service._calculate_allele_frequencies([]) == {}

    def test_calculate_allele_frequencies_all_missing(self, service):
        """Test allele frequency calculation with all missing data."""
        assert service._calculate_allele_frequencies([".", "./."]) == {}

    def test_is_heterozygous(self, service):
        """Test heterozygous check."""
        assert service._is_heterozygous("0/1") is True
        assert service._is_heterozygous("0|1") is True
        assert service._is_heterozygous("1/0") is True

        assert service._is_heterozygous("0/0") is False
        assert service._is_heterozygous("1/1") is False

        assert service._is_heterozygous(".") is False
        assert service._is_heterozygous("./.") is False
        assert service._is_heterozygous(None) is False
        assert service._is_heterozygous("") is False

    def test_interpret_heterozygosity(self, service):
        """Test interpretation of heterozygosity."""
        assert service._interpret_heterozygosity(0.8) == "High genetic diversity"
        assert service._interpret_heterozygosity(0.6) == "Moderate genetic diversity"
        assert service._interpret_heterozygosity(0.4) == "Low genetic diversity"
        assert service._interpret_heterozygosity(0.1) == "Very low genetic diversity"

    def test_interpret_inbreeding(self, service):
        """Test interpretation of inbreeding coefficient."""
        assert service._interpret_inbreeding(0.3) == "High inbreeding - consider outcrossing"
        assert service._interpret_inbreeding(0.15) == "Moderate inbreeding"
        assert service._interpret_inbreeding(0.08) == "Low inbreeding"
        assert service._interpret_inbreeding(0.02) == "Minimal inbreeding"
        assert service._interpret_inbreeding(-0.1) == "Excess heterozygosity (negative F)"

    def test_interpret_allelic_richness(self, service):
        """Test interpretation of allelic richness."""
        assert service._interpret_allelic_richness(7.0) == "High allelic richness"
        assert service._interpret_allelic_richness(5.0) == "Good allelic richness"
        assert service._interpret_allelic_richness(3.0) == "Moderate allelic richness"
        assert service._interpret_allelic_richness(1.0) == "Low allelic richness"

    def test_interpret_polymorphism(self, service):
        """Test interpretation of polymorphism percentage."""
        assert service._interpret_polymorphism(95) == "Highly polymorphic markers"
        assert service._interpret_polymorphism(75) == "Moderately polymorphic"
        assert service._interpret_polymorphism(55) == "Low polymorphism"
        assert service._interpret_polymorphism(30) == "Very low polymorphism - consider more markers"

    def test_generate_recommendations(self, service):
        """Test generation of recommendations."""
        # Case 1: High inbreeding, low ar, low poly
        metrics = {
            "inbreeding_coefficient": 0.3,
            "expected_heterozygosity": 0.5,
            "observed_heterozygosity": 0.2, # Ho < He * 0.8
            "allelic_richness": 2.0,
            "polymorphic_loci_percent": 40
        }
        recs = service._generate_recommendations(metrics)
        assert any("High inbreeding detected" in r for r in recs)
        assert any("Observed heterozygosity is lower than expected" in r for r in recs)
        assert any("Low allelic richness" in r for r in recs)
        assert any("Consider increasing marker density" in r for r in recs)

        # Case 2: Good diversity
        metrics_good = {
            "inbreeding_coefficient": 0.0,
            "expected_heterozygosity": 0.5,
            "observed_heterozygosity": 0.5,
            "allelic_richness": 5.0,
            "polymorphic_loci_percent": 95
        }
        recs_good = service._generate_recommendations(metrics_good)
        assert any("Genetic diversity levels appear adequate" in r for r in recs_good)
