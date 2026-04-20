
import numpy as np


class YieldMatrixMath:
    """
    Mathematical operations for yield matrices (Genotypes x Environments or Spatial Grids).
    """

    @staticmethod
    def fill_missing_values(matrix: np.ndarray, method: str = "mean") -> np.ndarray:
        """
        Fill missing values (NaN) in the matrix using the specified method.

        Args:
            matrix: Input 2D numpy array with potential NaNs.
            method: 'mean' (column mean), 'zero', or 'median' (column median).

        Returns:
            New matrix with filled values.
        """
        filled_matrix = matrix.copy()
        if method == "zero":
            filled_matrix[np.isnan(filled_matrix)] = 0.0
            return filled_matrix

        # Column-wise filling
        for col in range(filled_matrix.shape[1]):
            col_data = filled_matrix[:, col]
            mask = np.isnan(col_data)
            if np.any(mask):
                if method == "mean":
                    fill_val = np.nanmean(col_data)
                elif method == "median":
                    fill_val = np.nanmedian(col_data)
                else:
                    raise ValueError(f"Unknown fill method: {method}")

                # If all are nan, fill with 0
                if np.isnan(fill_val):
                    fill_val = 0.0

                filled_matrix[mask, col] = fill_val

        return filled_matrix

    @staticmethod
    def normalize_matrix(matrix: np.ndarray, axis: int = 0) -> np.ndarray:
        """
        Normalize matrix (Z-score normalization) along the specified axis.

        Args:
            matrix: Input 2D numpy array.
            axis: 0 for column-wise, 1 for row-wise.

        Returns:
            Normalized matrix.
        """
        mean = np.nanmean(matrix, axis=axis, keepdims=True)
        std = np.nanstd(matrix, axis=axis, keepdims=True)

        # Avoid division by zero
        std[std == 0] = 1.0

        return (matrix - mean) / std

    @staticmethod
    def calculate_covariance_matrix(matrix: np.ndarray) -> np.ndarray:
        """
        Calculate the covariance matrix of the input matrix columns.
        Rows are observations, columns are variables.

        Args:
            matrix: Input 2D numpy array.

        Returns:
            Covariance matrix.
        """
        masked_matrix = np.ma.masked_invalid(matrix)
        cov = np.ma.cov(masked_matrix, rowvar=False)
        return cov.data if isinstance(cov, np.ma.MaskedArray) else cov

    @staticmethod
    def calculate_correlation_matrix(matrix: np.ndarray) -> np.ndarray:
        """
        Calculate the correlation matrix (Pearson) of the input matrix columns.

        Args:
            matrix: Input 2D numpy array.

        Returns:
            Correlation matrix.
        """
        masked_matrix = np.ma.masked_invalid(matrix)
        corr = np.ma.corrcoef(masked_matrix, rowvar=False)
        return corr.data if isinstance(corr, np.ma.MaskedArray) else corr

    @staticmethod
    def apply_spatial_smoothing(matrix: np.ndarray, kernel_size: int = 3) -> np.ndarray:
        """
        Apply spatial smoothing (mean filter) to the matrix.
        Assumes matrix represents a spatial grid.

        Args:
            matrix: Input 2D numpy array (spatial grid).
            kernel_size: Size of the smoothing kernel (must be odd).

        Returns:
            Smoothed matrix.
        """
        if kernel_size % 2 == 0:
            raise ValueError("Kernel size must be odd.")

        pad_size = kernel_size // 2
        padded_matrix = np.pad(matrix, pad_size, mode='edge')
        smoothed_matrix = np.zeros_like(matrix)

        rows, cols = matrix.shape

        for r in range(rows):
            for c in range(cols):
                # Extract window
                window = padded_matrix[r:r+kernel_size, c:c+kernel_size]
                smoothed_matrix[r, c] = np.nanmean(window)

        return smoothed_matrix
