"""
GWAS PLINK Adapter
Service for interfacing with PLINK (Whole Genome Association Analysis Toolset)

This adapter provides methods to run PLINK commands for:
- Data conversion (VCF <-> BED/BIM/FAM)
- Quality Control (QC)
- LD Pruning
- PCA (Principal Component Analysis)
- Association Analysis (Linear/Logistic)

Dependencies:
- plink (executable must be in PATH or provided)
- polars (for efficient data handling)
- pandas (fallback/compatibility)
"""

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Literal

import pandas as pd
import polars as pl

logger = logging.getLogger(__name__)


class GWASPlinkAdapter:
    """
    Adapter for running PLINK commands and parsing results.
    """

    def __init__(self, plink_executable: str = "plink"):
        """
        Initialize the adapter.

        Args:
            plink_executable: Path to the PLINK executable (default: "plink").
        """
        self.plink_executable = plink_executable
        self._verify_executable()

    def _verify_executable(self) -> None:
        """Check if PLINK is executable."""
        if not shutil.which(self.plink_executable):
            logger.warning(
                f"PLINK executable '{self.plink_executable}' not found in "
                "PATH. Ensure PLINK is installed and accessible."
            )

    def _run_command(
        self,
        args: list[str],
        cwd: Path | None = None,
    ) -> subprocess.CompletedProcess:
        """
        Run a PLINK command.

        Args:
            args: List of command arguments.
            cwd: Working directory.

        Returns:
            CompletedProcess object.

        Raises:
            subprocess.CalledProcessError: If the command fails.
        """
        cmd = [self.plink_executable] + args
        logger.info(f"Running PLINK command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True
            )
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"PLINK command failed: {e.stderr}")
            raise e

    def convert_vcf_to_bed(
        self, vcf_path: Path | str, output_prefix: Path | str
    ) -> Path:
        """
        Convert VCF to PLINK binary format (BED/BIM/FAM).

        Args:
            vcf_path: Path to input VCF file.
            output_prefix: Prefix for output files.

        Returns:
            Path to the .bed file.
        """
        vcf_path = str(vcf_path)
        output_prefix = str(output_prefix)

        args = [
            "--vcf", vcf_path,
            "--make-bed",
            "--out", output_prefix,
            "--allow-extra-chr",  # Allow non-human chromosome names
            "--const-fid",        # Set FID to 0 (useful for non-pedigree VCFs)
        ]

        self._run_command(args)

        return Path(f"{output_prefix}.bed")

    def convert_bed_to_vcf(
        self, bfile: Path | str, output_prefix: Path | str
    ) -> Path:
        """
        Convert PLINK binary format (BED/BIM/FAM) to VCF.

        Args:
            bfile: Input binary file prefix.
            output_prefix: Prefix for output files.

        Returns:
            Path to the .vcf file.
        """
        bfile = str(bfile)
        output_prefix = str(output_prefix)

        args = [
            "--bfile", bfile,
            "--recode", "vcf",
            "--out", output_prefix,
            "--allow-extra-chr",
        ]

        self._run_command(args)

        return Path(f"{output_prefix}.vcf")

    def filter_samples_snps(
        self,
        bfile: Path | str,
        output_prefix: Path | str,
        mind: float = 0.1,
        geno: float = 0.1,
        maf: float = 0.05,
        hwe: float = 1e-6,
    ) -> Path:
        """
        Perform Quality Control (QC) filtering.

        Args:
            bfile: Input binary file prefix (without extension).
            output_prefix: Output file prefix.
            mind: Max per-individual missingness rate (default 0.1).
            geno: Max per-SNP missingness rate (default 0.1).
            maf: Minor allele frequency threshold (default 0.05).
            hwe: Hardy-Weinberg Equilibrium p-value threshold (default 1e-6).

        Returns:
            Path to the filtered .bed file.
        """
        bfile = str(bfile)
        output_prefix = str(output_prefix)

        args = [
            "--bfile", bfile,
            "--mind", str(mind),
            "--geno", str(geno),
            "--maf", str(maf),
            "--hwe", str(hwe),
            "--make-bed",
            "--out", output_prefix,
            "--allow-extra-chr",
        ]

        self._run_command(args)
        return Path(f"{output_prefix}.bed")

    def ld_pruning(
        self,
        bfile: Path | str,
        output_prefix: Path | str,
        window_size: int = 50,
        step_size: int = 5,
        r2_threshold: float = 0.2,
    ) -> dict[str, Path]:
        """
        Perform LD pruning to generate independent markers.

        Args:
            bfile: Input binary file prefix.
            output_prefix: Output file prefix.
            window_size: Window size in SNPs (default 50).
            step_size: Step size in SNPs (default 5).
            r2_threshold: r^2 threshold (default 0.2).

        Returns:
            Dictionary with paths to .prune.in and .prune.out files.
        """
        bfile = str(bfile)
        output_prefix = str(output_prefix)

        args = [
            "--bfile", bfile,
            "--indep-pairwise",
            str(window_size),
            str(step_size),
            str(r2_threshold),
            "--out", output_prefix,
            "--allow-extra-chr",
        ]

        self._run_command(args)

        return {
            "prune_in": Path(f"{output_prefix}.prune.in"),
            "prune_out": Path(f"{output_prefix}.prune.out"),
        }

    def calculate_pca(
        self,
        bfile: Path | str,
        output_prefix: Path | str,
        n_pcs: int = 10,
    ) -> Path:
        """
        Calculate Principal Components (PCA).

        Args:
            bfile: Input binary file prefix.
            output_prefix: Output file prefix.
            n_pcs: Number of principal components (default 10).

        Returns:
            Path to the .eigenvec file.
        """
        bfile = str(bfile)
        output_prefix = str(output_prefix)

        args = [
            "--bfile", bfile,
            "--pca", str(n_pcs),
            "--out", output_prefix,
            "--allow-extra-chr",
        ]

        self._run_command(args)
        return Path(f"{output_prefix}.eigenvec")

    def run_association(
        self,
        bfile: Path | str,
        output_prefix: Path | str,
        phenotype_file: Path | str | None = None,
        covariates_file: Path | str | None = None,
        method: Literal["linear", "logistic", "assoc"] = "linear",
        adjust: bool = False,
    ) -> Path:
        """
        Run association analysis.

        Args:
            bfile: Input binary file prefix.
            output_prefix: Output file prefix.
            phenotype_file: Path to phenotype file (optional if in .fam).
            covariates_file: Path to covariates file (optional).
            method: Association method ('linear', 'logistic', 'assoc').
            adjust: Whether to produce multiple testing adjusted p-values.

        Returns:
            Path to the primary results file (.assoc, .assoc.linear, etc.).
        """
        bfile = str(bfile)
        output_prefix = str(output_prefix)

        args = [
            "--bfile", bfile,
            f"--{method}",
            "--out", output_prefix,
            "--allow-extra-chr",
            "--allow-no-sex",
        ]

        if phenotype_file:
            args.extend(["--pheno", str(phenotype_file)])

        if covariates_file:
            args.extend(["--covar", str(covariates_file)])

        if adjust:
            args.append("--adjust")

        self._run_command(args)

        # Determine output file extension
        ext = "assoc"
        if method == "linear":
            ext = "assoc.linear"
        elif method == "logistic":
            ext = "assoc.logistic"

        return Path(f"{output_prefix}.{ext}")

    def parse_assoc_results(self, result_file: Path | str) -> pl.DataFrame:
        """
        Parse association results file into a Polars DataFrame.

        Args:
            result_file: Path to the association result file.

        Returns:
            Polars DataFrame with results.
        """
        # PLINK results are whitespace-separated with variable spaces
        # Pandas is more robust for this than Polars read_csv
        try:
            # delim_whitespace=True handles variable spaces nicely
            df_pd = pd.read_csv(str(result_file), sep=r"\s+")
            return pl.from_pandas(df_pd)
        except Exception as e:
            logger.error(f"Failed to parse association results: {e}")
            raise e

    def parse_pca_eigenvec(self, eigenvec_file: Path | str) -> pl.DataFrame:
        """
        Parse PCA eigenvectors file.

        Args:
            eigenvec_file: Path to .eigenvec file.

        Returns:
            Polars DataFrame with FID, IID, and PCs.
        """
        try:
            # PLINK .eigenvec has FID IID PC1 PC2 ...
            # Using pandas for robust whitespace parsing
            df_pd = pd.read_csv(str(eigenvec_file), sep=r"\s+", header=None)

            # Rename columns
            n_cols = df_pd.shape[1]
            # First two columns are FID, IID
            col_names = ["FID", "IID"] + [
                f"PC{i}" for i in range(1, n_cols - 1)
            ]
            df_pd.columns = col_names

            return pl.from_pandas(df_pd)
        except Exception as e:
            logger.error(f"Failed to parse PCA results: {e}")
            raise e

    def parse_ld_pruning_results(self, prune_in_file: Path | str) -> list[str]:
        """
        Read the list of kept SNPs from .prune.in file.

        Args:
            prune_in_file: Path to .prune.in file.

        Returns:
            List of SNP IDs.
        """
        try:
            with open(prune_in_file, 'r') as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            logger.warning(f"Prune file not found: {prune_in_file}")
            return []
