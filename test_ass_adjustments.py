#!/usr/bin/env python3
"""Test script to verify ASS adjustment implementation"""

import sys
from pathlib import Path

# Add subtuner to path
sys.path.insert(0, str(Path(__file__).parent))

from subtuner.config import GlobalConfig, ProcessingConfig
from subtuner.writers.ass_writer import ASSWriter
from subtuner.parsers.base import Subtitle

def test_config():
    """Test that configuration accepts ASS adjustment parameters"""
    print("Testing configuration...")
    
    config = GlobalConfig.from_args(
        ass_font_size_adjust=2,
        ass_y_position_adjust=100
    )
    
    assert config.processing.ass_font_size_adjust == 2
    assert config.processing.ass_y_position_adjust == 100
    print("✓ Configuration test passed")

def test_writer():
    """Test that writer has adjustment methods"""
    print("\nTesting ASS writer...")
    
    writer = ASSWriter()
    
    # Check that set_adjustments method exists
    assert hasattr(writer, 'set_adjustments')
    
    # Test setting adjustments
    writer.set_adjustments(font_size_adjust=2, y_position_adjust=100)
    assert writer.font_size_adjust == 2
    assert writer.y_position_adjust == 100
    
    # Check that helper methods exist
    assert hasattr(writer, '_identify_dialog_style')
    assert hasattr(writer, '_apply_style_adjustments')
    
    print("✓ ASS writer test passed")

def test_cli_options():
    """Test that CLI has the new options"""
    print("\nTesting CLI options...")
    
    from subtuner.cli import main
    import click.testing
    
    runner = click.testing.CliRunner()
    result = runner.invoke(main, ['--help'])
    
    # Check that help text contains new options
    assert '--ass-font-size-adjust' in result.output
    assert '--ass-y-position-adjust' in result.output
    
    print("✓ CLI options test passed")

if __name__ == '__main__':
    try:
        test_config()
        test_writer()
        test_cli_options()
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)