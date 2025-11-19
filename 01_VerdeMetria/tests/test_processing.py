"""
Unit tests for processing functions.
"""

import pytest
import numpy as np
from numpy.testing import assert_array_almost_equal, assert_array_equal

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from verdemetria.processing import (
    compute_ndvi_array,
    diff_ndvi,
    mask_threshold,
    calculate_vegetation_metrics
)


class TestComputeNDVI:
    """Tests for NDVI computation."""
    
    def test_basic_ndvi(self):
        """Test basic NDVI computation with simple values."""
        red = np.array([[100, 120], [110, 130]], dtype=np.float32)
        nir = np.array([[150, 180], [160, 190]], dtype=np.float32)
        
        ndvi = compute_ndvi_array(red, nir)
        
        # NDVI = (NIR - Red) / (NIR + Red)
        # For [100, 150]: (150-100)/(150+100) = 50/250 = 0.2
        expected = np.array([[0.2, 0.2], [0.1923077, 0.1875]], dtype=np.float32)
        assert_array_almost_equal(ndvi, expected, decimal=5)
    
    def test_ndvi_range(self):
        """Test that NDVI values are in valid range [-1, 1]."""
        red = np.array([[50, 100, 150]], dtype=np.float32)
        nir = np.array([[200, 100, 50]], dtype=np.float32)
        
        ndvi = compute_ndvi_array(red, nir)
        
        assert np.all((ndvi >= -1) & (ndvi <= 1))
    
    def test_ndvi_with_zeros(self):
        """Test NDVI with zero values (should be NaN)."""
        red = np.array([[0, 100], [0, 50]], dtype=np.float32)
        nir = np.array([[0, 150], [100, 0]], dtype=np.float32)
        
        ndvi = compute_ndvi_array(red, nir)
        
        # [0, 0] should be NaN
        assert np.isnan(ndvi[0, 0])
        # Other values should be valid
        assert not np.isnan(ndvi[0, 1])
    
    def test_ndvi_with_nan(self):
        """Test NDVI with NaN input values."""
        red = np.array([[100, np.nan], [110, 120]], dtype=np.float32)
        nir = np.array([[150, 160], [np.nan, 180]], dtype=np.float32)
        
        ndvi = compute_ndvi_array(red, nir)
        
        assert np.isnan(ndvi[0, 1])  # Red is NaN
        assert np.isnan(ndvi[1, 0])  # NIR is NaN
        assert not np.isnan(ndvi[0, 0])  # Both valid
    
    def test_shape_mismatch(self):
        """Test that mismatched shapes raise ValueError."""
        red = np.array([[100, 120]], dtype=np.float32)
        nir = np.array([[150, 180], [160, 190]], dtype=np.float32)
        
        with pytest.raises(ValueError, match="Shape mismatch"):
            compute_ndvi_array(red, nir)


class TestDiffNDVI:
    """Tests for NDVI difference computation."""
    
    def test_basic_diff(self):
        """Test basic NDVI difference."""
        ndvi1 = np.array([[0.3, 0.4], [0.5, 0.6]], dtype=np.float32)
        ndvi2 = np.array([[0.4, 0.5], [0.3, 0.7]], dtype=np.float32)
        
        diff = diff_ndvi(ndvi1, ndvi2)
        
        expected = np.array([[0.1, 0.1], [-0.2, 0.1]], dtype=np.float32)
        assert_array_almost_equal(diff, expected, decimal=5)
    
    def test_diff_with_nan(self):
        """Test that NaN values are preserved in difference."""
        ndvi1 = np.array([[0.3, np.nan], [0.5, 0.6]], dtype=np.float32)
        ndvi2 = np.array([[0.4, 0.5], [np.nan, 0.7]], dtype=np.float32)
        
        diff = diff_ndvi(ndvi1, ndvi2)
        
        assert np.isnan(diff[0, 1])
        assert np.isnan(diff[1, 0])
        assert not np.isnan(diff[0, 0])
    
    def test_diff_shape_mismatch(self):
        """Test that mismatched shapes raise ValueError."""
        ndvi1 = np.array([[0.3, 0.4]], dtype=np.float32)
        ndvi2 = np.array([[0.4, 0.5], [0.3, 0.7]], dtype=np.float32)
        
        with pytest.raises(ValueError, match="Shape mismatch"):
            diff_ndvi(ndvi1, ndvi2)


class TestMaskThreshold:
    """Tests for threshold masking."""
    
    def test_mask_greater(self):
        """Test greater than threshold."""
        arr = np.array([[0.1, 0.2], [0.3, 0.4]], dtype=np.float32)
        mask = mask_threshold(arr, 0.25, 'greater')
        
        expected = np.array([[False, False], [True, True]])
        assert_array_equal(mask, expected)
    
    def test_mask_less(self):
        """Test less than threshold."""
        arr = np.array([[0.1, 0.2], [0.3, 0.4]], dtype=np.float32)
        mask = mask_threshold(arr, 0.25, 'less')
        
        expected = np.array([[True, True], [False, False]])
        assert_array_equal(mask, expected)
    
    def test_mask_with_nan(self):
        """Test that NaN values are excluded from mask."""
        arr = np.array([[0.1, np.nan], [0.3, 0.4]], dtype=np.float32)
        mask = mask_threshold(arr, 0.25, 'greater')
        
        assert mask[0, 1] == False  # NaN should be False
        assert mask[1, 0] == True
    
    def test_invalid_comparison(self):
        """Test that invalid comparison raises ValueError."""
        arr = np.array([[0.1, 0.2]], dtype=np.float32)
        
        with pytest.raises(ValueError, match="Invalid comparison operator"):
            mask_threshold(arr, 0.25, 'invalid')


class TestVegetationMetrics:
    """Tests for vegetation metrics calculation."""
    
    def test_basic_metrics(self):
        """Test basic metrics calculation."""
        ndvi = np.array([[0.1, 0.3], [0.5, 0.7]], dtype=np.float32)
        metrics = calculate_vegetation_metrics(ndvi)
        
        assert 'mean' in metrics
        assert 'std' in metrics
        assert metrics['mean'] == pytest.approx(0.4)
    
    def test_metrics_with_nan(self):
        """Test metrics with NaN values."""
        ndvi = np.array([[0.1, np.nan], [0.5, 0.7]], dtype=np.float32)
        metrics = calculate_vegetation_metrics(ndvi)
        
        # Should compute on valid values only
        assert not np.isnan(metrics['mean'])
        assert metrics['mean'] == pytest.approx(0.433333, abs=0.01)
    
    def test_empty_array(self):
        """Test metrics with all NaN array."""
        ndvi = np.array([[np.nan, np.nan]], dtype=np.float32)
        metrics = calculate_vegetation_metrics(ndvi)
        
        assert np.isnan(metrics['mean'])
        assert metrics['bare_count'] == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
