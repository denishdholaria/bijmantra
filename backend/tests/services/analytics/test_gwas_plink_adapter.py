import shutil
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import polars as pl
import pytest

from app.modules.genomics.compute.analytics.gwas_plink_adapter import GWASPlinkAdapter


@pytest.fixture
def mock_shutil_which():
    with patch("shutil.which") as mock:
        mock.return_value = "/usr/bin/plink"
        yield mock


@pytest.fixture
def adapter(mock_shutil_which):
    return GWASPlinkAdapter(plink_executable="plink")


def test_init(mock_shutil_which):
    adapter = GWASPlinkAdapter()
    assert adapter.plink_executable == "plink"
    mock_shutil_which.assert_called_with("plink")


def test_init_custom_path(mock_shutil_which):
    adapter = GWASPlinkAdapter(plink_executable="/custom/plink")
    assert adapter.plink_executable == "/custom/plink"
    mock_shutil_which.assert_called_with("/custom/plink")


@patch("subprocess.run")
def test_run_command_success(mock_run, adapter):
    mock_run.return_value = subprocess.CompletedProcess(
        args=["plink", "--help"], returncode=0, stdout="Success", stderr=""
    )

    result = adapter._run_command(["--help"])

    assert result.returncode == 0
    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    assert args[0] == ["plink", "--help"]
    assert kwargs["check"] is True


@patch("subprocess.run")
def test_run_command_failure(mock_run, adapter):
    mock_run.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd=["plink"], stderr="Error"
    )

    with pytest.raises(subprocess.CalledProcessError):
        adapter._run_command(["--help"])


@patch("subprocess.run")
def test_convert_vcf_to_bed(mock_run, adapter):
    adapter.convert_vcf_to_bed("input.vcf", "output")

    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert cmd[:3] == ["plink", "--vcf", "input.vcf"]
    assert "--make-bed" in cmd
    assert "--out" in cmd


@patch("subprocess.run")
def test_convert_bed_to_vcf(mock_run, adapter):
    adapter.convert_bed_to_vcf("input", "output")

    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert "--bfile" in cmd
    assert "--recode" in cmd
    assert "vcf" in cmd
    assert "--out" in cmd


@patch("subprocess.run")
def test_filter_samples_snps(mock_run, adapter):
    adapter.filter_samples_snps("input", "output", mind=0.05, maf=0.01)

    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert "--mind" in cmd
    assert cmd[cmd.index("--mind") + 1] == "0.05"
    assert "--maf" in cmd
    assert cmd[cmd.index("--maf") + 1] == "0.01"
    assert "--make-bed" in cmd


@patch("subprocess.run")
def test_ld_pruning(mock_run, adapter):
    res = adapter.ld_pruning("input", "output", window_size=100, r2_threshold=0.5)

    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert "--indep-pairwise" in cmd
    assert cmd[cmd.index("--indep-pairwise") + 1] == "100"
    assert cmd[cmd.index("--indep-pairwise") + 3] == "0.5"

    assert res["prune_in"] == Path("output.prune.in")


@patch("subprocess.run")
def test_calculate_pca(mock_run, adapter):
    adapter.calculate_pca("input", "output", n_pcs=5)

    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert "--pca" in cmd
    assert cmd[cmd.index("--pca") + 1] == "5"


@patch("subprocess.run")
def test_run_association_linear(mock_run, adapter):
    adapter.run_association("input", "output", method="linear", adjust=True)

    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert "--linear" in cmd
    assert "--adjust" in cmd
    assert "--allow-no-sex" in cmd


@patch("subprocess.run")
def test_run_association_logistic_covar(mock_run, adapter):
    adapter.run_association(
        "input", "output",
        method="logistic",
        covariates_file="covar.txt",
        phenotype_file="pheno.txt"
    )

    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert "--logistic" in cmd
    assert "--covar" in cmd
    assert "covar.txt" in cmd
    assert "--pheno" in cmd
    assert "pheno.txt" in cmd


def test_parse_assoc_results(adapter, tmp_path):
    # Create dummy .assoc file
    assoc_file = tmp_path / "test.assoc"
    content = """CHR SNP BP A1 F_A P OR
    1 rs1 100 A 0.5 0.01 1.2
    1 rs2 200 G 0.4 0.5 0.9
    """
    assoc_file.write_text(content)

    df = adapter.parse_assoc_results(assoc_file)

    assert isinstance(df, pl.DataFrame)
    assert df.height == 2
    assert df["SNP"][0] == "rs1"
    assert df["P"][0] == 0.01


def test_parse_pca_eigenvec(adapter, tmp_path):
    # Create dummy .eigenvec file
    # Format: FID IID PC1 PC2 ...
    eigenvec_file = tmp_path / "test.eigenvec"
    content = """fid1 iid1 0.1 -0.2
    fid2 iid2 -0.1 0.2
    """
    eigenvec_file.write_text(content)

    df = adapter.parse_pca_eigenvec(eigenvec_file)

    assert isinstance(df, pl.DataFrame)
    assert df.height == 2
    assert df.columns == ["FID", "IID", "PC1", "PC2"]
    assert df["FID"][0] == "fid1"
    assert df["PC1"][0] == 0.1


def test_parse_ld_pruning_results(adapter, tmp_path):
    prune_in_file = tmp_path / "test.prune.in"
    content = "rs1\nrs2\nrs3\n"
    prune_in_file.write_text(content)

    snps = adapter.parse_ld_pruning_results(prune_in_file)

    assert len(snps) == 3
    assert snps == ["rs1", "rs2", "rs3"]


def test_parse_ld_pruning_results_missing(adapter):
    snps = adapter.parse_ld_pruning_results("non_existent.file")
    assert snps == []
