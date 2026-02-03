"""
Breeding Science Knowledge Base

Contains foundational knowledge, methods, and citations for plant breeding.
Used by DevGuru to provide accurate, cited explanations and recommendations.
"""

from typing import List, Dict, Optional, Any

class BreedingKnowledgeBase:
    """Knowledge base for plant breeding concepts and citations"""

    TOPICS = {
        "genomic_selection": {
            "title": "Genomic Selection (GS)",
            "description": "A form of marker-assisted selection in which genetic markers covering the whole genome are used so that all QTL are in linkage disequilibrium with at least one marker. It predicts breeding values (GEBVs) for individuals based on their genome-wide markers.",
            "key_methods": ["GBLUP (Genomic Best Linear Unbiased Prediction)", "rrBLUP", "Bayesian Alphabet (BayesA, BayesB, BayesCpi)", "Machine Learning (Random Forest, SVM)"],
            "citations": [
                {
                    "title": "Prediction of total genetic value using genome-wide dense marker maps",
                    "authors": ["Meuwissen, T.H.E.", "Hayes, B.J.", "Goddard, M.E."],
                    "year": 2001,
                    "journal": "Genetics",
                    "doi": "10.1093/genetics/157.4.1819",
                    "url": "https://academic.oup.com/genetics/article/157/4/1819/6061320"
                },
                {
                    "title": "Genomic selection in plant breeding: from theory to practice",
                    "authors": ["Jannink, J.L.", "Lorenz, A.J.", "Iwata, H."],
                    "year": 2010,
                    "journal": "Briefings in Functional Genomics",
                    "doi": "10.1093/bfgp/elq001"
                }
            ]
        },
        "gwas": {
            "title": "Genome-Wide Association Study (GWAS)",
            "description": "An observational study of a genome-wide set of genetic variants in different individuals to see if any variant is associated with a trait. In plants, it connects phenotype to genotype using historical recombination events.",
            "key_methods": ["GLM (General Linear Model)", "MLM (Mixed Linear Model)", "FarmCPU", "BLINK"],
            "citations": [
                {
                    "title": "Unified mixed-model method for association mapping that accounts for multiple levels of relatedness",
                    "authors": ["Yu, J.", "Pressoir, G.", "Briggs, W.H.", "Bi, I.V.", "Yamasaki, M.", "Doebley, J.F.", "McMullen, M.D.", "Gaut, B.S.", "Nielsen, D.M.", "Holland, J.B.", "Kresovich, S.", "Buckler, E.S."],
                    "year": 2006,
                    "journal": "Nature Genetics",
                    "doi": "10.1038/ng1702"
                }
            ]
        },
        "marker_assisted_selection": {
            "title": "Marker-Assisted Selection (MAS)",
            "description": "An indirect selection process where a trait of interest is selected based on a marker (morphological, biochemical or DNA/RNA variation) linked to a trait of interest, rather than on the trait itself.",
            "key_methods": ["Foreground Selection", "Background Selection", "MABC (Marker-Assisted Backcrossing)", "MARS (Marker-Assisted Recurrent Selection)"],
            "citations": [
                {
                    "title": "Marker-assisted selection: an approach for precision plant breeding",
                    "authors": ["Collard, B.C.Y.", "Mackill, D.J."],
                    "year": 2008,
                    "journal": "Heredity",
                    "doi": "10.1038/sj.hdy.6801042"
                }
            ]
        },
        "speed_breeding": {
            "title": "Speed Breeding",
            "description": "A set of techniques designed to shorten the breeding cycle and accelerate crop research. It involves extending the daily photoperiod and controlling temperature to enable rapid generation turnover.",
            "key_methods": ["Extended Photoperiod", "Temperature Control", "Embryo Rescue", "Single Seed Descent (SSD)"],
            "citations": [
                {
                    "title": "Speed breeding is a powerful tool to accelerate crop research and breeding",
                    "authors": ["Watson, A.", "Ghosh, S.", "Williams, M.J.", "Cuddy, W.S.", "Simmonds, J.", "Rey, M.D.", "Hatta, M.A.M.", "Hinchliffe, A.", "Steed, A.", "Reynolds, D.", "Adamski, N.M.", "Breakspear, A.", "Korolev, A.", "Rayner, T.", "Dixon, L.E.", "Riaz, A.", "Martin, W.", "Duffus, M.", "Uttam, A.", "Moghe, P.", "Tscheuschler, A.", "Wells, J.", "Suzuki, T.", "Takagi, H.", "Ishikawa, R.", "Shitsukawa, N.", "Terauchi, R.", "Hickey, L.T.", "Wulff, B.B.H."],
                    "year": 2018,
                    "journal": "Nature Plants",
                    "doi": "10.1038/s41477-017-0083-8"
                }
            ]
        },
        "high_throughput_phenotyping": {
            "title": "High-Throughput Phenotyping (HTP)",
            "description": "The use of automated sensing, data acquisition, and data analysis tools to characterize phenotypes of organisms on a large scale. It addresses the 'phenotyping bottleneck' in modern breeding.",
            "key_methods": ["Remote Sensing (UAV/Drone)", "Ground-based Platforms", "Computer Vision", "Spectral Imaging (RGB, Multispectral, Hyperspectral)"],
            "citations": [
                {
                    "title": "High-throughput phenotyping to provide platform for intense selection and precise mapping of loci for complex traits",
                    "authors": ["Araus, J.L.", "Cairns, J.E."],
                    "year": 2014,
                    "journal": "Trends in Plant Science",
                    "doi": "10.1016/j.tplants.2013.09.008"
                }
            ]
        },
         "gblup": {
            "title": "Genomic Best Linear Unbiased Prediction (GBLUP)",
            "description": "A statistical method used in genomic selection where the genetic relationships between individuals are estimated using genome-wide markers (G-matrix) instead of pedigree data (A-matrix).",
            "key_methods": ["G-Matrix Construction", "REML (Restricted Maximum Likelihood)"],
            "citations": [
                {
                    "title": "Prediction of total genetic value using genome-wide dense marker maps",
                    "authors": ["Meuwissen, T.H.E.", "Hayes, B.J.", "Goddard, M.E."],
                    "year": 2001,
                    "journal": "Genetics",
                    "doi": "10.1093/genetics/157.4.1819"
                },
                {
                    "title": "Efficient methods to compute genomic predictions",
                    "authors": ["VanRaden, P.M."],
                    "year": 2008,
                    "journal": "Journal of Dairy Science",
                    "doi": "10.3168/jds.2007-0980"
                }
            ]
        },
        "pedigree_analysis": {
            "title": "Pedigree Analysis",
            "description": "The study of an organism's ancestral history to understand genetic inheritance patterns. In breeding, it is used to estimate relatedness (Kinship) and inbreeding coefficients.",
            "key_methods": ["A-Matrix Construction", "Coefficient of Coancestry", "Path Analysis"],
            "citations": [
                {
                    "title": "Coefficients of inbreeding and relationship",
                    "authors": ["Wright, S."],
                    "year": 1922,
                    "journal": "The American Naturalist",
                    "doi": "10.1086/279872"
                }
            ]
        }
    }

    @classmethod
    def get_topics(cls) -> List[str]:
        """Get list of available topics"""
        return sorted([t["title"] for t in cls.TOPICS.values()])

    @classmethod
    def get_topic_info(cls, topic_key: str) -> Optional[Dict[str, Any]]:
        """Get detailed info for a topic by key"""
        return cls.TOPICS.get(topic_key)

    @classmethod
    def find_topic(cls, query: str) -> Optional[Dict[str, Any]]:
        """Fuzzy search for a topic"""
        query = query.lower().strip()

        # 1. Exact match on key
        if query in cls.TOPICS:
            return cls.TOPICS[query]

        # 2. Match on title
        for key, data in cls.TOPICS.items():
            if query in data["title"].lower():
                return data

        # 3. Match on method alias (e.g. "mabc" in MAS)
        for key, data in cls.TOPICS.items():
            if any(query in method.lower() for method in data.get("key_methods", [])):
                return data

        # 4. Partial match on key (e.g. "genomic" matches "genomic_selection")
        for key, data in cls.TOPICS.items():
            if query in key.replace("_", " "):
                return data

        return None
