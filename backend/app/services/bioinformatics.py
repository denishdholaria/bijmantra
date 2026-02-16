"""
Bioinformatics Service for Plant Breeding
Sequence analysis, primer design, and molecular marker tools

Features:
- DNA/RNA sequence analysis
- Primer design (Tm calculation, GC content)
- Restriction enzyme analysis
- Sequence alignment (pairwise)
- Marker validation tools
"""

import re
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import math
import logging

logger = logging.getLogger(__name__)


class SequenceType(str, Enum):
    DNA = "dna"
    RNA = "rna"
    PROTEIN = "protein"


@dataclass
class SequenceStats:
    """Statistics for a nucleotide sequence"""
    length: int
    gc_content: float
    at_content: float
    a_count: int
    t_count: int
    g_count: int
    c_count: int
    n_count: int
    molecular_weight: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "length": self.length,
            "gc_content": round(self.gc_content, 2),
            "at_content": round(self.at_content, 2),
            "composition": {
                "A": self.a_count,
                "T": self.t_count,
                "G": self.g_count,
                "C": self.c_count,
                "N": self.n_count,
            },
            "molecular_weight": round(self.molecular_weight, 2),
        }


@dataclass
class PrimerResult:
    """Primer design result"""
    sequence: str
    length: int
    tm: float
    gc_content: float
    self_complementarity: int
    hairpin_score: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sequence": self.sequence,
            "length": self.length,
            "tm": round(self.tm, 1),
            "gc_content": round(self.gc_content, 1),
            "self_complementarity": self.self_complementarity,
            "hairpin_score": self.hairpin_score,
            "quality": self._assess_quality(),
        }

    def _assess_quality(self) -> str:
        score = 0
        if 18 <= self.length <= 25: score += 1
        if 55 <= self.tm <= 65: score += 1
        if 40 <= self.gc_content <= 60: score += 1
        if self.self_complementarity < 4: score += 1
        if self.hairpin_score < 3: score += 1

        if score >= 4: return "excellent"
        if score >= 3: return "good"
        if score >= 2: return "acceptable"
        return "poor"


@dataclass
class RestrictionSite:
    """Restriction enzyme cut site"""
    enzyme: str
    position: int
    recognition_seq: str
    cut_position: int
    overhang: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enzyme": self.enzyme,
            "position": self.position,
            "recognition_sequence": self.recognition_seq,
            "cut_position": self.cut_position,
            "overhang": self.overhang,
        }


# Common restriction enzymes for plant molecular breeding
RESTRICTION_ENZYMES = {
    "EcoRI": {"seq": "GAATTC", "cut": 1, "overhang": "5'"},
    "BamHI": {"seq": "GGATCC", "cut": 1, "overhang": "5'"},
    "HindIII": {"seq": "AAGCTT", "cut": 1, "overhang": "5'"},
    "XbaI": {"seq": "TCTAGA", "cut": 1, "overhang": "5'"},
    "SalI": {"seq": "GTCGAC", "cut": 1, "overhang": "5'"},
    "PstI": {"seq": "CTGCAG", "cut": 5, "overhang": "3'"},
    "SmaI": {"seq": "CCCGGG", "cut": 3, "overhang": "blunt"},
    "KpnI": {"seq": "GGTACC", "cut": 5, "overhang": "3'"},
    "SacI": {"seq": "GAGCTC", "cut": 5, "overhang": "3'"},
    "NotI": {"seq": "GCGGCCGC", "cut": 2, "overhang": "5'"},
    "XhoI": {"seq": "CTCGAG", "cut": 1, "overhang": "5'"},
    "NcoI": {"seq": "CCATGG", "cut": 1, "overhang": "5'"},
    "NdeI": {"seq": "CATATG", "cut": 2, "overhang": "5'"},
    "BglII": {"seq": "AGATCT", "cut": 1, "overhang": "5'"},
    "ClaI": {"seq": "ATCGAT", "cut": 2, "overhang": "5'"},
}

# Molecular weights (Da)
DNA_MW = {"A": 331.2, "T": 322.2, "G": 347.2, "C": 307.2}


class BioinformaticsService:
    """
    Bioinformatics tools for plant molecular breeding
    """

    def __init__(self):
        self.complement = str.maketrans("ATGCN", "TACGN")

    def clean_sequence(self, sequence: str) -> str:
        """Clean and validate DNA sequence"""
        seq = sequence.upper().replace(" ", "").replace("\n", "")
        seq = re.sub(r"[^ATGCNRYSWKMBDHV]", "", seq)
        return seq

    def analyze_sequence(self, sequence: str) -> SequenceStats:
        """
        Analyze DNA sequence composition
        
        Args:
            sequence: DNA sequence string
            
        Returns:
            SequenceStats with composition and properties
        """
        seq = self.clean_sequence(sequence)
        length = len(seq)

        if length == 0:
            return SequenceStats(0, 0, 0, 0, 0, 0, 0, 0, 0)

        a_count = seq.count("A")
        t_count = seq.count("T")
        g_count = seq.count("G")
        c_count = seq.count("C")
        n_count = seq.count("N")

        gc_content = (g_count + c_count) / length * 100
        at_content = (a_count + t_count) / length * 100

        # Molecular weight calculation
        mw = sum(DNA_MW.get(base, 0) for base in seq)

        return SequenceStats(
            length=length,
            gc_content=gc_content,
            at_content=at_content,
            a_count=a_count,
            t_count=t_count,
            g_count=g_count,
            c_count=c_count,
            n_count=n_count,
            molecular_weight=mw,
        )

    def reverse_complement(self, sequence: str) -> str:
        """Get reverse complement of DNA sequence"""
        seq = self.clean_sequence(sequence)
        return seq.translate(self.complement)[::-1]

    def calculate_tm(self, sequence: str, method: str = "nearest_neighbor") -> float:
        """
        Calculate melting temperature (Tm) of primer
        
        Methods:
        - basic: 4°C × (G+C) + 2°C × (A+T)
        - wallace: 2(A+T) + 4(G+C)
        - nearest_neighbor: More accurate thermodynamic calculation
        """
        seq = self.clean_sequence(sequence)
        length = len(seq)

        if length == 0:
            return 0.0

        gc = seq.count("G") + seq.count("C")
        at = seq.count("A") + seq.count("T")

        if method == "basic" or length < 14:
            # Basic formula for short oligos
            return 4 * gc + 2 * at

        elif method == "wallace":
            return 2 * at + 4 * gc

        else:
            # Nearest-neighbor method (simplified)
            # Tm = 81.5 + 16.6*log10([Na+]) + 41*(GC/N) - 675/N
            # Assuming 50mM Na+
            na_conc = 0.05
            gc_fraction = gc / length
            tm = 81.5 + 16.6 * math.log10(na_conc) + 41 * gc_fraction - 675 / length
            return tm

    def design_primers(
        self,
        sequence: str,
        target_start: int,
        target_end: int,
        primer_length: Tuple[int, int] = (18, 25),
        tm_range: Tuple[float, float] = (55, 65),
        gc_range: Tuple[float, float] = (40, 60),
    ) -> Dict[str, List[PrimerResult]]:
        """
        Design forward and reverse primers for a target region
        
        Args:
            sequence: Template DNA sequence
            target_start: Start of target region (0-indexed)
            target_end: End of target region
            primer_length: (min, max) primer length
            tm_range: (min, max) melting temperature
            gc_range: (min, max) GC content
            
        Returns:
            Dict with forward and reverse primer candidates
        """
        seq = self.clean_sequence(sequence)
        min_len, max_len = primer_length

        forward_primers = []
        reverse_primers = []

        # Design forward primers (upstream of target)
        for length in range(min_len, max_len + 1):
            start = max(0, target_start - length - 50)
            end = target_start

            for i in range(start, end):
                if i + length > len(seq):
                    break

                primer_seq = seq[i:i + length]
                primer = self._evaluate_primer(primer_seq)

                if (tm_range[0] <= primer.tm <= tm_range[1] and
                    gc_range[0] <= primer.gc_content <= gc_range[1]):
                    forward_primers.append(primer)

        # Design reverse primers (downstream of target)
        for length in range(min_len, max_len + 1):
            start = target_end
            end = min(len(seq), target_end + 50)

            for i in range(start, end):
                if i + length > len(seq):
                    break

                primer_seq = self.reverse_complement(seq[i:i + length])
                primer = self._evaluate_primer(primer_seq)

                if (tm_range[0] <= primer.tm <= tm_range[1] and
                    gc_range[0] <= primer.gc_content <= gc_range[1]):
                    reverse_primers.append(primer)

        # Sort by quality
        forward_primers.sort(key=lambda p: (p.self_complementarity, abs(p.tm - 60)))
        reverse_primers.sort(key=lambda p: (p.self_complementarity, abs(p.tm - 60)))

        return {
            "forward": [p.to_dict() for p in forward_primers[:5]],
            "reverse": [p.to_dict() for p in reverse_primers[:5]],
        }

    def _evaluate_primer(self, sequence: str) -> PrimerResult:
        """Evaluate primer quality"""
        seq = self.clean_sequence(sequence)
        length = len(seq)
        gc = (seq.count("G") + seq.count("C")) / length * 100 if length > 0 else 0
        tm = self.calculate_tm(seq)

        # Check self-complementarity
        rev_comp = self.reverse_complement(seq)
        self_comp = self._count_complementary_bases(seq, rev_comp)

        # Check hairpin potential
        hairpin = self._check_hairpin(seq)

        return PrimerResult(
            sequence=seq,
            length=length,
            tm=tm,
            gc_content=gc,
            self_complementarity=self_comp,
            hairpin_score=hairpin,
        )

    def _count_complementary_bases(self, seq1: str, seq2: str) -> int:
        """Count maximum complementary stretch"""
        max_comp = 0
        for i in range(len(seq1)):
            for j in range(len(seq2)):
                comp = 0
                while (i + comp < len(seq1) and j + comp < len(seq2) and
                       self._is_complement(seq1[i + comp], seq2[j + comp])):
                    comp += 1
                max_comp = max(max_comp, comp)
        return max_comp

    def _is_complement(self, base1: str, base2: str) -> bool:
        """Check if two bases are complementary"""
        pairs = {("A", "T"), ("T", "A"), ("G", "C"), ("C", "G")}
        return (base1, base2) in pairs

    def _check_hairpin(self, sequence: str) -> int:
        """Check for hairpin formation potential"""
        # Simplified hairpin check
        length = len(sequence)
        if length < 8:
            return 0

        max_hairpin = 0
        for loop_size in range(4, 8):
            for i in range(length - loop_size - 4):
                stem1 = sequence[i:i + 4]
                stem2 = self.reverse_complement(sequence[i + 4 + loop_size:i + 8 + loop_size])
                matches = sum(1 for a, b in zip(stem1, stem2) if a == b)
                max_hairpin = max(max_hairpin, matches)

        return max_hairpin

    def find_restriction_sites(
        self,
        sequence: str,
        enzymes: Optional[List[str]] = None
    ) -> List[RestrictionSite]:
        """
        Find restriction enzyme cut sites in sequence
        
        Args:
            sequence: DNA sequence
            enzymes: List of enzyme names (None = all)
            
        Returns:
            List of RestrictionSite objects
        """
        seq = self.clean_sequence(sequence)
        sites = []

        enzymes_to_check = enzymes or list(RESTRICTION_ENZYMES.keys())

        for enzyme in enzymes_to_check:
            if enzyme not in RESTRICTION_ENZYMES:
                continue

            info = RESTRICTION_ENZYMES[enzyme]
            pattern = info["seq"]

            # Find all occurrences
            for match in re.finditer(pattern, seq):
                sites.append(RestrictionSite(
                    enzyme=enzyme,
                    position=match.start(),
                    recognition_seq=pattern,
                    cut_position=match.start() + info["cut"],
                    overhang=info["overhang"],
                ))

        sites.sort(key=lambda s: s.position)
        return sites

    def translate_sequence(self, sequence: str, frame: int = 0) -> str:
        """
        Translate DNA to protein sequence
        
        Args:
            sequence: DNA sequence
            frame: Reading frame (0, 1, or 2)
            
        Returns:
            Amino acid sequence
        """
        codon_table = {
            "TTT": "F", "TTC": "F", "TTA": "L", "TTG": "L",
            "TCT": "S", "TCC": "S", "TCA": "S", "TCG": "S",
            "TAT": "Y", "TAC": "Y", "TAA": "*", "TAG": "*",
            "TGT": "C", "TGC": "C", "TGA": "*", "TGG": "W",
            "CTT": "L", "CTC": "L", "CTA": "L", "CTG": "L",
            "CCT": "P", "CCC": "P", "CCA": "P", "CCG": "P",
            "CAT": "H", "CAC": "H", "CAA": "Q", "CAG": "Q",
            "CGT": "R", "CGC": "R", "CGA": "R", "CGG": "R",
            "ATT": "I", "ATC": "I", "ATA": "I", "ATG": "M",
            "ACT": "T", "ACC": "T", "ACA": "T", "ACG": "T",
            "AAT": "N", "AAC": "N", "AAA": "K", "AAG": "K",
            "AGT": "S", "AGC": "S", "AGA": "R", "AGG": "R",
            "GTT": "V", "GTC": "V", "GTA": "V", "GTG": "V",
            "GCT": "A", "GCC": "A", "GCA": "A", "GCG": "A",
            "GAT": "D", "GAC": "D", "GAA": "E", "GAG": "E",
            "GGT": "G", "GGC": "G", "GGA": "G", "GGG": "G",
        }

        seq = self.clean_sequence(sequence)
        seq = seq[frame:]

        protein = []
        for i in range(0, len(seq) - 2, 3):
            codon = seq[i:i + 3]
            aa = codon_table.get(codon, "X")
            protein.append(aa)

        return "".join(protein)


# Singleton
_bioinfo_service: Optional[BioinformaticsService] = None


def get_bioinformatics_service() -> BioinformaticsService:
    """Get or create bioinformatics service singleton"""
    global _bioinfo_service
    if _bioinfo_service is None:
        _bioinfo_service = BioinformaticsService()
    return _bioinfo_service
