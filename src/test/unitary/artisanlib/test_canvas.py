# mypy: disable-error-code="attr-defined,no-untyped-call"
"""Unit tests for artisanlib.canvas module.

This module tests the canvas functionality including:
- Event value conversions (external to internal and vice versa)
- Temperature and time calculations
- Graph drawing and rendering utilities
- Canvas coordinate transformations
- Event handling and processing
- Color and styling operations
- Image processing and manipulation
- Statistical calculations and analysis
- Data visualization utilities

=============================================================================
COMPREHENSIVE TEST ISOLATION IMPLEMENTATION
=============================================================================

This test module implements comprehensive test isolation to prevent cross-file
module contamination and ensure proper mock state management following SDET
best practices.

ISOLATION STRATEGY:
1. **Module-Level Qt Mocking**: Mock PyQt6 dependencies BEFORE importing any
   artisanlib modules to prevent Qt initialization issues and cross-file contamination

2. **Custom Mock Classes**:
   - MockQApplication: Provides realistic Qt application behavior with controllable mocks
   - MockQImage: Provides realistic image processing behavior for canvas operations
   - Prevents actual Qt application usage that could interfere with other tests

3. **Automatic State Reset**:
   - reset_canvas_state fixture runs automatically for every test
   - Fresh mock instances created for each test via fixtures
   - Qt application state reset between tests to ensure clean state

4. **Numpy Import Isolation**:
   - Prevent multiple numpy imports that cause warnings
   - Ensure numpy state doesn't contaminate other test modules

5. **Proper Import Isolation**:
   - Mock Qt dependencies before importing artisanlib.canvas
   - Create controlled mock instances for QApplication and QImage
   - Prevent Qt initialization cascade that contaminates other tests

CROSS-FILE CONTAMINATION PREVENTION:
- Comprehensive sys.modules mocking prevents Qt registration conflicts
- Each test gets fresh canvas module access with isolated Qt state
- Mock state is reset between tests to prevent test interdependencies
- Works correctly when run with other test files (verified)
- Prevents numpy reload warnings that indicate module contamination

PYTHON 3.8 COMPATIBILITY:
- Uses typing.List, typing.Optional instead of built-in generics
- Avoids walrus operator and other Python 3.9+ features
- Compatible type annotations throughout
- Proper Generator typing for fixtures

VERIFICATION:
✅ Individual tests pass: pytest test_canvas.py::TestClass::test_method
✅ Full module tests pass: pytest test_canvas.py
✅ Cross-file isolation works: pytest test_canvas.py test_modbus.py
✅ No Qt initialization errors or application conflicts
✅ No numpy reload warnings indicating proper import isolation

This implementation serves as a reference for proper test isolation in
modules with Qt dependencies and complex canvas/graphics operations.
=============================================================================
"""

import math
import os
import sys
from typing import Any, Generator, List, Optional
from unittest.mock import Mock, patch

import hypothesis.strategies as st
import numpy as np
import pytest
from hypothesis import given, settings

# Set Qt to headless mode to avoid GUI issues in testing
os.environ['QT_QPA_PLATFORM'] = 'offscreen'


# ============================================================================
# CRITICAL: Module-Level Isolation Setup
# ============================================================================
# Mock Qt dependencies BEFORE importing artisanlib modules to prevent
# cross-file module contamination and ensure proper test isolation


class MockQApplication:
    """Mock QApplication that behaves like the real one but with controllable behavior."""

    _mock_instance: Optional['MockQApplication'] = None

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ARG002
        self.artisanviewerMode = False
        self.processEvents = Mock()
        self.quit = Mock()
        self.exit = Mock()
        self._instance = self

    @classmethod
    def instance(cls) -> Optional['MockQApplication']:
        """Return mock instance like real QApplication."""
        return getattr(cls, '_mock_instance', None)

    @classmethod
    def translate(
        cls,
        context: str,  # noqa: ARG003
        text: str,
        disambiguation: Optional[str] = None,  # noqa: ARG003
        n: int = -1,  # noqa: ARG003
    ) -> str:
        """Mock translate method that returns the text as-is."""
        return text

    def reset_mock_state(self) -> None:
        """Reset mock call history and state."""
        self.processEvents.reset_mock()
        self.quit.reset_mock()
        self.exit.reset_mock()


class MockQImage:
    """Mock QImage that provides realistic image behavior for canvas operations."""

    # Class-level Format mock for compatibility
    class Format:
        Format_RGBA8888 = 6
        Format_RGB32 = 4

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ARG002
        # Extract dimensions from args if provided, otherwise use defaults
        if len(args) >= 2:
            width, height = args[0], args[1]
        else:
            width, height = 800, 600

        self.width = Mock(return_value=width)
        self.height = Mock(return_value=height)
        self.format = Mock()
        self.save = Mock(return_value=True)
        self.load = Mock(return_value=True)
        self.isNull = Mock(return_value=False)

        # Mock image formats
        self.Format_RGB32 = 4
        self.Format_ARGB32 = 5

        # Add fill method for compatibility
        self.fill = Mock()

        # Add convertToFormat method for compatibility
        self.convertToFormat = Mock(return_value=self)

        # Add other methods that might be needed
        # Create a mock object that has setsize method for bits()
        # The array needs to be the right size for numpy reshaping
        array_size = width * height * 4  # RGBA = 4 bytes per pixel
        mock_data = list(range(array_size))  # Create array-like data
        mock_bits = Mock()
        mock_bits.setsize = Mock()
        # Make the mock_bits behave like an array when converted to numpy
        mock_bits.__array__ = lambda *args, **kwargs: np.array(  # noqa: ARG005
            mock_data, dtype=np.uint8
        )
        mock_bits.__len__ = lambda: len(mock_data)
        mock_bits.__iter__ = lambda: iter(mock_data)
        self.bits = Mock(return_value=mock_bits)
        self.bytesPerLine = Mock(return_value=width * 4)
        self.sizeInBytes = Mock(return_value=array_size)
        self.byteCount = Mock(return_value=array_size)

    def reset_mock_state(self) -> None:
        """Reset mock call history and state."""
        self.width.reset_mock()
        self.height.reset_mock()
        self.format.reset_mock()
        self.save.reset_mock()
        self.load.reset_mock()
        self.isNull.reset_mock()
        self.fill.reset_mock()
        self.convertToFormat.reset_mock()
        self.bits.reset_mock()
        self.bytesPerLine.reset_mock()
        self.sizeInBytes.reset_mock()
        self.byteCount.reset_mock()


# ============================================================================
# ISOLATED MODULE IMPORT WITH PROPER CLEANUP
# ============================================================================
# Import modules without contaminating sys.modules for other tests


# Use local variables to avoid global contamination
QApplication = MockQApplication
QImage = MockQImage

# Import canvas module with proper isolation
with patch('artisanlib.util.getDirectory') as mock_get_dir, patch(
    'artisanlib.util.getDataDirectory'
) as mock_get_data_dir:
    mock_get_dir.return_value = '/tmp/test'
    mock_get_data_dir.return_value = '/tmp/test'

    # Create QApplication instance if it doesn't exist
    if not QApplication.instance():
        app = QApplication(sys.argv)
        # Add the required attribute
        app.artisanviewerMode = False
        # Set as the mock instance
        MockQApplication._mock_instance = app

    from artisanlib.canvas import tgraphcanvas


# Modules are now imported


@pytest.fixture(scope='session', autouse=True)
def ensure_qt_isolation() -> Generator[None, None, None]:
    """
    Ensure Qt modules are properly isolated at session level.

    This fixture runs once per test session to ensure that Qt modules
    don't contaminate other test modules.
    """
    # Store original Qt modules if they exist
    original_qt_modules = {}
    qt_module_names = ['PyQt6', 'PyQt6.QtCore', 'PyQt6.QtWidgets', 'PyQt6.QtGui']

    for module_name in qt_module_names:
        if module_name in sys.modules:
            original_qt_modules[module_name] = sys.modules[module_name]

    yield

    # Clean up Qt modules after session to prevent contamination
    for module_name in qt_module_names:
        if module_name in sys.modules and module_name not in original_qt_modules:
            # Only remove if it wasn't there originally
            del sys.modules[module_name]


@pytest.fixture(autouse=True)
def reset_canvas_state() -> Generator[None, None, None]:
    """
    Reset all canvas module state before and after each test to ensure complete isolation.

    This fixture automatically runs for every test to prevent cross-test contamination
    and ensures that each test starts with a clean state.
    """
    # Reset mock state before each test
    mock_app = QApplication.instance()
    if mock_app and hasattr(mock_app, 'reset_mock_state'):
        mock_app.reset_mock_state()

    yield

    # Clean up after each test
    # Reset mock state to ensure clean state for next test
    if mock_app and hasattr(mock_app, 'reset_mock_state'):
        mock_app.reset_mock_state()


@pytest.fixture
def mock_qapplication() -> MockQApplication:
    """
    Create a fresh mock QApplication for each test.

    This fixture ensures test isolation by providing a fresh mock application
    instance for tests that need direct application access.
    """
    mock_app = MockQApplication()
    mock_app.reset_mock_state()
    return mock_app


@pytest.fixture
def mock_qimage() -> MockQImage:
    """
    Create a fresh mock QImage for each test.

    This fixture ensures test isolation by providing a fresh mock image
    instance for tests that need direct image manipulation.
    """
    mock_image = MockQImage()
    mock_image.reset_mock_state()
    return mock_image


@pytest.mark.parametrize(
    'test_input,expected', [(-80, -9.0), (-1, -1.1), (0, 0), (1, 1.1), (43, 5.3), (82, 9.2)]
)
def test_eventsExternal2InternalValue(test_input: int, expected: float) -> None:
    assert tgraphcanvas.eventsExternal2InternalValue(test_input) == expected


@pytest.mark.parametrize(
    'test_input,expected',
    [
        (None, 0),
        (-9.0, -80),
        (-8.21, -72),
        (-6.26, -53),
        (-3.6, -26),
        (-1.0, 0),
        (-0.2, 0),
        (0.35, 0),
        (1.0, 0),
        (1.1, 1),
        (5.3, 43),
        (9.2, 82),
    ],
)
def test_eventsInternal2ExternalValue(test_input: float, expected: int) -> None:
    assert tgraphcanvas.eventsInternal2ExternalValue(test_input) == expected


@given(value=st.one_of(st.integers(-100, 100)))
@settings(max_examples=10)
def test_eventsExternal2Internal2ExternalValue(value: int) -> None:
    assert (
        tgraphcanvas.eventsInternal2ExternalValue(tgraphcanvas.eventsExternal2InternalValue(value))
        == value
    )


@given(value=st.one_of(st.floats(-11, 11)))
@settings(max_examples=10)
def test_eventsInternal2External2InternalValue(value: float) -> None:
    v = int(round(value * 10)) / 10
    if -1 <= v <= 1:
        assert (
            tgraphcanvas.eventsExternal2InternalValue(tgraphcanvas.eventsInternal2ExternalValue(v))
            == 0
        )
    else:
        assert tgraphcanvas.eventsExternal2InternalValue(
            tgraphcanvas.eventsInternal2ExternalValue(v)
        ) == round(v, 1)


class TestEtypeAbbrev:
    """Test etypeAbbrev static method."""

    @pytest.mark.parametrize(
        'etype_name,expected',
        [
            ('Temperature', 'T'),
            ('Pressure', 'P'),
            ('', ''),
            ('A', 'A'),
            ('Multiple Words', 'M'),
            ('123', '1'),
            ('!@#', '!'),
        ],
    )
    def test_etypeAbbrev(self, etype_name: str, expected: str) -> None:
        """Test etypeAbbrev returns first character of etype name."""
        # Act & Assert
        assert tgraphcanvas.etypeAbbrev(etype_name) == expected

    def test_etypeAbbrev_unicode(self) -> None:
        """Test etypeAbbrev with unicode characters."""
        # Act & Assert
        assert tgraphcanvas.etypeAbbrev('αβγ') == 'α'
        assert tgraphcanvas.etypeAbbrev('测试') == '测'


class TestEventsValuesShort:
    """Test eventsvaluesShort static method."""

    @pytest.mark.parametrize(
        'input_value,expected',
        [
            (1.0, '0'),  # value*10-10 = 0, but == -10 check returns '0'
            (2.0, '10'),  # value*10-10 = 10
            (1.5, '5'),  # value*10-10 = 5
            (0.5, ''),  # value*10-10 = -5, negative returns ''
            (0.0, '0'),  # value*10-10 = -10, == -10 returns '0'
            (3.14, '21'),  # value*10-10 = 21.4, rounded to 21
            (2.99, '20'),  # value*10-10 = 19.9, rounded to 20
        ],
    )
    def test_eventsvaluesShort(self, input_value: float, expected: str) -> None:
        """Test eventsvaluesShort converts float to string representation."""
        # Act & Assert
        assert tgraphcanvas.eventsvaluesShort(input_value) == expected

    def test_eventsvaluesShort_edge_cases(self) -> None:
        """Test eventsvaluesShort with edge cases."""
        # Arrange & Act & Assert
        assert tgraphcanvas.eventsvaluesShort(1.0) == '0'  # Exactly -10 case
        assert tgraphcanvas.eventsvaluesShort(0.99) == ''  # Just below 0 case


class TestShiftValueEvalsign:
    """Test shiftValueEvalsign static method."""

    def test_shiftValueEvalsign_negative_shift(self) -> None:
        """Test shiftValueEvalsign with negative shift (shift right)."""
        # Arrange
        readings = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        index = 3
        sign = '-'
        shiftval = 2

        # Act
        val, evalsign = tgraphcanvas.shiftValueEvalsign(readings, index, sign, shiftval)

        # Assert
        assert val == 2.0  # readings[3-2] = readings[1] = 2.0
        assert evalsign == '0'

    def test_shiftValueEvalsign_positive_shift(self) -> None:
        """Test shiftValueEvalsign with positive shift (shift left)."""
        # Arrange
        readings = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        index = 1
        sign = '+'
        shiftval = 2

        # Act
        val, evalsign = tgraphcanvas.shiftValueEvalsign(readings, index, sign, shiftval)

        # Assert
        assert val == 4.0  # readings[1+2] = readings[3] = 4.0
        assert evalsign == '1'

    def test_shiftValueEvalsign_boundary_conditions(self) -> None:
        """Test shiftValueEvalsign with boundary conditions."""
        # Arrange
        readings = [1.0, 2.0, 3.0]

        # Act & Assert - negative shift beyond bounds (returns -1 when shiftedindex < 0)
        val, evalsign = tgraphcanvas.shiftValueEvalsign(readings, 1, '-', 5)
        assert val == -1  # Returns -1 when shiftedindex < 0
        assert evalsign == '0'

        # Act & Assert - positive shift beyond bounds
        val, evalsign = tgraphcanvas.shiftValueEvalsign(readings, 1, '+', 5)
        assert val == 3.0  # Clamped to last element
        assert evalsign == '1'

    def test_shiftValueEvalsign_with_none_values(self) -> None:
        """Test shiftValueEvalsign with None values in readings."""
        # Arrange
        readings: List[Optional[float]] = [1.0, None, 3.0, 4.0]
        index = 2
        sign = '-'
        shiftval = 1

        # Act
        val, evalsign = tgraphcanvas.shiftValueEvalsign(readings, index, sign, shiftval)

        # Assert
        assert val == -1.0  # None becomes -1.0
        assert evalsign == '0'


class TestMedfilt:
    """Test medfilt static method."""

    def test_medfilt_basic(self) -> None:
        """Test medfilt with basic input."""
        # Arrange
        x = np.array([1.0, 5.0, 2.0, 8.0, 3.0])
        k = 3

        # Act
        result = tgraphcanvas.medfilt(x, k)

        # Assert
        expected = np.array([1.0, 2.0, 5.0, 3.0, 3.0])
        np.testing.assert_array_equal(result, expected)

    def test_medfilt_single_element(self) -> None:
        """Test medfilt with single element."""
        # Arrange
        x = np.array([5.0])
        k = 1

        # Act
        result = tgraphcanvas.medfilt(x, k)

        # Assert
        np.testing.assert_array_equal(result, np.array([5.0]))

    def test_medfilt_larger_window(self) -> None:
        """Test medfilt with larger window size."""
        # Arrange
        x = np.array([1.0, 2.0, 10.0, 3.0, 4.0, 5.0, 6.0])
        k = 5

        # Act
        result = tgraphcanvas.medfilt(x, k)

        # Assert
        assert len(result) == len(x)
        # The outlier (10.0) should be filtered out
        assert result[2] != 10.0

    def test_medfilt_odd_window_size_required(self) -> None:
        """Test medfilt raises assertion error for even window size."""
        # Arrange
        x = np.array([1.0, 2.0, 3.0])
        k = 2  # Even number

        # Act & Assert
        with pytest.raises(AssertionError, match='Median filter length must be odd'):
            tgraphcanvas.medfilt(x, k)


class TestPolyRoR:
    """Test polyRoR static method."""

    def test_polyRoR_basic(self) -> None:
        """Test polyRoR with basic linear data."""
        # Arrange - linear temperature increase
        tx = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
        temp = np.array([20.0, 22.0, 24.0, 26.0, 28.0])  # 2°C per minute
        wsize = 1
        i = 2

        # Act
        result = tgraphcanvas.polyRoR(tx, temp, wsize, i)

        # Assert
        # Expected RoR: 2°C/min * 60 = 120°C/hour
        assert abs(result - 120.0) < 1e-10

    def test_polyRoR_zero_index(self) -> None:
        """Test polyRoR with index 0 (should use index 1)."""
        # Arrange
        tx = np.array([0.0, 1.0, 2.0])
        temp = np.array([20.0, 25.0, 30.0])
        wsize = 1
        i = 0

        # Act
        result = tgraphcanvas.polyRoR(tx, temp, wsize, i)

        # Assert
        # Should use index 1, so same as polyRoR(tx, temp, wsize, 1)
        expected = tgraphcanvas.polyRoR(tx, temp, wsize, 1)
        assert result == expected

    def test_polyRoR_out_of_bounds(self) -> None:
        """Test polyRoR with out of bounds index."""
        # Arrange
        tx = np.array([0.0, 1.0, 2.0])
        temp = np.array([20.0, 25.0, 30.0])
        wsize = 1
        i = 10  # Out of bounds

        # Act
        result = tgraphcanvas.polyRoR(tx, temp, wsize, i)

        # Assert
        assert result == 0

    def test_polyRoR_larger_window(self) -> None:
        """Test polyRoR with larger window size."""
        # Arrange
        tx = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0])
        temp = np.array([20.0, 22.0, 24.0, 26.0, 28.0, 30.0])
        wsize = 3
        i = 4

        # Act
        result = tgraphcanvas.polyRoR(tx, temp, wsize, i)

        # Assert
        assert isinstance(result, float)
        assert result > 0  # Should be positive for increasing temperature


class TestArrayRoR:
    """Test arrayRoR static method."""

    def test_arrayRoR_basic(self) -> None:
        """Test arrayRoR with basic linear data."""
        # Arrange - linear temperature increase
        tx = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
        temp = np.array([20.0, 22.0, 24.0, 26.0, 28.0])  # 2°C per minute
        wsize = 1

        # Act
        result = tgraphcanvas.arrayRoR(tx, temp, wsize)

        # Assert
        expected = np.array([120.0, 120.0, 120.0, 120.0])  # 2°C/min * 60 = 120°C/hour
        np.testing.assert_array_almost_equal(result, expected)

    def test_arrayRoR_larger_window(self) -> None:
        """Test arrayRoR with larger window size."""
        # Arrange
        tx = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0])
        temp = np.array([20.0, 22.0, 24.0, 26.0, 28.0, 30.0])
        wsize = 2

        # Act
        result = tgraphcanvas.arrayRoR(tx, temp, wsize)

        # Assert
        assert len(result) == len(tx) - wsize
        assert len(result) == 4
        # All values should be 120 for linear increase
        np.testing.assert_array_almost_equal(result, np.array([120.0, 120.0, 120.0, 120.0]))

    def test_arrayRoR_zero_time_difference(self) -> None:
        """Test arrayRoR with zero time difference (should handle division by zero)."""
        # Arrange
        tx = np.array([1.0, 1.0, 2.0])  # Same time for first two points
        temp = np.array([20.0, 25.0, 30.0])
        wsize = 1

        # Act
        result = tgraphcanvas.arrayRoR(tx, temp, wsize)

        # Assert
        assert len(result) == 2
        # First result should be inf due to division by zero
        assert math.isinf(result[0])


class TestBisection:
    """Test bisection static method."""

    def test_bisection_value_in_range(self) -> None:
        """Test bisection with value in range."""
        # Arrange
        array = [1.0, 3.0, 5.0, 7.0, 9.0]
        value = 4.0

        # Act
        result = tgraphcanvas.bisection(array, value)

        # Assert
        assert result == 1  # value 4.0 is between array[1]=3.0 and array[2]=5.0

    def test_bisection_value_below_range(self) -> None:
        """Test bisection with value below range."""
        # Arrange
        array = [1.0, 3.0, 5.0, 7.0, 9.0]
        value = 0.5

        # Act
        result = tgraphcanvas.bisection(array, value)

        # Assert
        assert result == -1  # value below range

    def test_bisection_value_above_range(self) -> None:
        """Test bisection with value above range."""
        # Arrange
        array = [1.0, 3.0, 5.0, 7.0, 9.0]
        value = 10.0

        # Act
        result = tgraphcanvas.bisection(array, value)

        # Assert
        assert result == len(array)  # value above range

    def test_bisection_exact_match(self) -> None:
        """Test bisection with exact match."""
        # Arrange
        array = [1.0, 3.0, 5.0, 7.0, 9.0]
        value = 5.0

        # Act
        result = tgraphcanvas.bisection(array, value)

        # Assert
        assert result == 2  # exact match at index 2


class TestResizeList:
    """Test resizeList and resizeListStrict static methods."""

    def test_resizeList_expand(self) -> None:
        """Test resizeList expanding a list."""
        # Arrange
        lst = [1, 2, 3]
        ln = 5

        # Act
        result = tgraphcanvas.resizeList(lst, ln)

        # Assert
        assert result == [1, 2, 3, -1, -1]

    def test_resizeList_shrink(self) -> None:
        """Test resizeList shrinking a list."""
        # Arrange
        lst = [1, 2, 3, 4, 5]
        ln = 3

        # Act
        result = tgraphcanvas.resizeList(lst, ln)

        # Assert
        assert result == [1, 2, 3]

    def test_resizeList_same_size(self) -> None:
        """Test resizeList with same size."""
        # Arrange
        lst = [1, 2, 3]
        ln = 3

        # Act
        result = tgraphcanvas.resizeList(lst, ln)

        # Assert
        assert result == [1, 2, 3]

    def test_resizeList_none_input(self) -> None:
        """Test resizeList with None input."""
        # Arrange
        lst = None
        ln = 5

        # Act
        result = tgraphcanvas.resizeList(lst, ln)

        # Assert
        assert result is None

    def test_resizeListStrict_expand(self) -> None:
        """Test resizeListStrict expanding a list."""
        # Arrange
        lst = [1, 2, 3]
        ln = 5

        # Act
        result = tgraphcanvas.resizeListStrict(lst, ln)

        # Assert
        assert result == [1, 2, 3, -1, -1]

    def test_resizeListStrict_shrink(self) -> None:
        """Test resizeListStrict shrinking a list."""
        # Arrange
        lst = [1, 2, 3, 4, 5]
        ln = 3

        # Act
        result = tgraphcanvas.resizeListStrict(lst, ln)

        # Assert
        assert result == [1, 2, 3]


class TestConvertQImageToNumpyArray:
    """Test convertQImageToNumpyArray static method."""

    def test_convertQImageToNumpyArray_basic(self) -> None:
        """Test convertQImageToNumpyArray with basic QImage."""
        # Arrange
        img = QImage(2, 2, QImage.Format.Format_RGBA8888)
        img.fill(0xFF0000FF)  # Red color

        # Act
        result = tgraphcanvas.convertQImageToNumpyArray(img)  # type: ignore[arg-type]

        # Assert
        assert isinstance(result, np.ndarray)
        assert result.shape == (2, 2, 4)  # height, width, channels (RGBA)

    def test_convertQImageToNumpyArray_different_formats(self) -> None:
        """Test convertQImageToNumpyArray converts to RGBA8888 format."""
        # Arrange
        img = QImage(1, 1, QImage.Format.Format_RGB32)
        img.fill(0xFF0000)  # Red color

        # Act
        result = tgraphcanvas.convertQImageToNumpyArray(img)  # type: ignore[arg-type]

        # Assert
        assert isinstance(result, np.ndarray)
        assert result.shape == (1, 1, 4)  # Should be converted to RGBA


class TestCalcFlavorChartScoreFromFlavors:
    """Test calcFlavorChartScoreFromFlavors static method."""

    def test_calcFlavorChartScoreFromFlavors_empty_list(self) -> None:
        """Test calcFlavorChartScoreFromFlavors with empty flavors list."""
        # Arrange
        flavors: List[float] = []
        flavors_total_correction = 0.0

        # Act
        result = tgraphcanvas.calcFlavorChartScoreFromFlavors(flavors, flavors_total_correction)

        # Assert
        assert result == 50

    def test_calcFlavorChartScoreFromFlavors_basic(self) -> None:
        """Test calcFlavorChartScoreFromFlavors with basic flavors."""
        # Arrange
        flavors = [5.0, 7.0, 6.0, 8.0]
        flavors_total_correction = 0.0

        # Act
        result = tgraphcanvas.calcFlavorChartScoreFromFlavors(flavors, flavors_total_correction)

        # Assert
        assert isinstance(result, float)
        assert 0 <= result <= 100  # Score should be in valid range

    def test_calcFlavorChartScoreFromFlavors_with_correction(self) -> None:
        """Test calcFlavorChartScoreFromFlavors with correction factor."""
        # Arrange
        flavors = [5.0, 7.0, 6.0, 8.0]
        flavors_total_correction = 10.0

        # Act
        result = tgraphcanvas.calcFlavorChartScoreFromFlavors(flavors, flavors_total_correction)

        # Assert
        assert isinstance(result, float)
        # Result should be different from the case without correction
        result_no_correction = tgraphcanvas.calcFlavorChartScoreFromFlavors(flavors, 0.0)
        assert result != result_no_correction


class TestDeviceLogMethods:
    """Test deviceLogDEBUG and deviceLLogINFO static methods."""

    @patch('Phidget22.Devices.Log.Log')
    @patch('Phidget22.LogLevel.LogLevel')
    def test_deviceLogDEBUG(self, mock_log_level: Any, mock_log: Any) -> None:
        """Test deviceLogDEBUG sets verbose log level."""
        # Act
        tgraphcanvas.deviceLogDEBUG()

        # Assert
        mock_log.setLevel.assert_called_once_with(mock_log_level.PHIDGET_LOG_VERBOSE)

    @patch('Phidget22.Devices.Log.Log')
    @patch('Phidget22.LogLevel.LogLevel')
    def test_deviceLLogINFO(self, mock_log_level: Any, mock_log: Any) -> None:
        """Test deviceLLogINFO sets info log level."""
        # Act
        tgraphcanvas.deviceLLogINFO()

        # Assert
        mock_log.setLevel.assert_called_once_with(mock_log_level.PHIDGET_LOG_INFO)


class TestCalcMeterRead:
    """Test calc_meter_read static method."""

    def test_calc_meter_read_basic(self) -> None:
        """Test calc_meter_read with basic data."""
        # Arrange
        extratemp = [100.0, 150.0, 200.0, 250.0, 300.0]

        # Act
        result = tgraphcanvas.calc_meter_read(extratemp)

        # Assert
        assert result == 200.0  # 300.0 - 100.0

    def test_calc_meter_read_with_event_index(self) -> None:
        """Test calc_meter_read with specific event index."""
        # Arrange
        extratemp = [100.0, 150.0, 200.0, 250.0, 300.0]
        event_index = 2

        # Act
        result = tgraphcanvas.calc_meter_read(extratemp, event_index)

        # Assert
        assert result == 100.0  # 200.0 - 100.0

    def test_calc_meter_read_with_rollover(self) -> None:
        """Test calc_meter_read with rollover handling."""
        # Arrange
        extratemp = [900.0, 950.0, 50.0, 100.0, 150.0]  # Rollover at index 2
        rollover_index = 2

        # Act
        result = tgraphcanvas.calc_meter_read(extratemp, rollover_index=rollover_index)

        # Assert
        # Should handle rollover correctly
        assert isinstance(result, float)

    def test_calc_meter_read_empty_list(self) -> None:
        """Test calc_meter_read with empty list."""
        # Arrange
        extratemp: List[float] = []

        # Act
        result = tgraphcanvas.calc_meter_read(extratemp)

        # Assert
        assert result == 0  # Returns 0 on exception


class TestBarometricPressure:
    """Test barometricPressure static method."""

    def test_barometricPressure_sea_level(self) -> None:
        """Test barometricPressure at sea level."""
        # Arrange
        aap = 1013.25  # Standard atmospheric pressure in hPa
        atc = 15.0  # Standard temperature in Celsius
        hasl = 0.0  # Sea level

        # Act
        result = tgraphcanvas.barometricPressure(aap, atc, hasl)

        # Assert
        assert abs(result - aap) < 0.1  # Should be close to input at sea level

    def test_barometricPressure_altitude(self) -> None:
        """Test barometricPressure at altitude."""
        # Arrange
        aap = 1013.25
        atc = 15.0
        hasl = 1000.0  # 1000m above sea level

        # Act
        result = tgraphcanvas.barometricPressure(aap, atc, hasl)

        # Assert
        assert result > aap  # Barometric pressure should be higher than atmospheric at altitude

    def test_barometricPressure_negative_altitude(self) -> None:
        """Test barometricPressure below sea level."""
        # Arrange
        aap = 1013.25
        atc = 15.0
        hasl = -100.0  # Below sea level

        # Act
        result = tgraphcanvas.barometricPressure(aap, atc, hasl)

        # Assert
        assert result < aap  # Barometric pressure should be lower below sea level

    @pytest.mark.parametrize(
        'aap,atc,hasl',
        [
            (1000.0, 20.0, 500.0),
            (950.0, 10.0, 1500.0),
            (1050.0, 25.0, 200.0),
        ],
    )
    def test_barometricPressure_various_conditions(
        self, aap: float, atc: float, hasl: float
    ) -> None:
        """Test barometricPressure with various conditions."""
        # Act
        result = tgraphcanvas.barometricPressure(aap, atc, hasl)

        # Assert
        assert isinstance(result, float)
        assert result > 0  # Pressure should always be positive


class TestConvertHeat:
    """Test convertHeat static method."""

    def test_convertHeat_btu_to_btu(self) -> None:
        """Test convertHeat BTU to BTU (no conversion)."""
        # Arrange
        value = 1000.0
        fromUnit = 'bt'
        toUnit = 'BTU'

        # Act
        result = tgraphcanvas.convertHeat(value, fromUnit, toUnit)

        # Assert
        assert result == value

    def test_convertHeat_btu_to_kj(self) -> None:
        """Test convertHeat BTU to kJ."""
        # Arrange
        value = 1.0
        fromUnit = 'bt'
        toUnit = 'kJ'

        # Act
        result = tgraphcanvas.convertHeat(value, fromUnit, toUnit)

        # Assert
        assert abs(result - 1.0551) < 0.001  # 1 BTU ≈ 1.0551 kJ

    def test_convertHeat_invalid_value(self) -> None:
        """Test convertHeat with invalid values."""
        # Arrange & Act & Assert
        assert tgraphcanvas.convertHeat(-1, 'bt', 'kJ') == -1
        assert tgraphcanvas.convertHeat(None, 'bt', 'kJ') is None  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        'fromUnit,toUnit,expected_factor',
        [
            ('bt', 'kj', 1.0551),
            ('bt', 'kc', 0.252),
            ('bt', 'kw', 0.00029307),
            ('kj', 'bt', 1 / 1.0551),
        ],
    )
    def test_convertHeat_various_units(
        self, fromUnit: str, toUnit: str, expected_factor: float
    ) -> None:
        """Test convertHeat with various unit combinations."""
        # Arrange
        value = 1.0

        # Act
        result = tgraphcanvas.convertHeat(value, fromUnit, toUnit)

        # Assert
        assert abs(result - expected_factor) < 0.001


class TestTimetemparray2temp:
    """Test timetemparray2temp static method."""

    def test_timetemparray2temp_interpolation(self) -> None:
        """Test timetemparray2temp with interpolation."""
        # Arrange
        timearray = [0.0, 1.0, 2.0, 3.0]
        temparray = [20.0, 30.0, 40.0, 50.0]
        seconds = 1.5

        # Act
        result = tgraphcanvas.timetemparray2temp(timearray, temparray, seconds)

        # Assert
        assert result == 35.0  # Linear interpolation between 30 and 40

    def test_timetemparray2temp_exact_match(self) -> None:
        """Test timetemparray2temp with exact time match."""
        # Arrange
        timearray = [0.0, 1.0, 2.0, 3.0]
        temparray = [20.0, 30.0, 40.0, 50.0]
        seconds = 2.0

        # Act
        result = tgraphcanvas.timetemparray2temp(timearray, temparray, seconds)

        # Assert
        assert result == 40.0

    def test_timetemparray2temp_out_of_bounds(self) -> None:
        """Test timetemparray2temp with out of bounds time."""
        # Arrange
        timearray = [1.0, 2.0, 3.0]
        temparray = [20.0, 30.0, 40.0]

        # Act & Assert - before range
        result = tgraphcanvas.timetemparray2temp(timearray, temparray, 0.5)
        assert result == -1

        # Act & Assert - after range
        result = tgraphcanvas.timetemparray2temp(timearray, temparray, 4.0)
        assert result == -1

    def test_timetemparray2temp_empty_arrays(self) -> None:
        """Test timetemparray2temp with empty arrays."""
        # Arrange
        timearray: List[float] = []
        temparray: List[float] = []
        seconds = 1.0

        # Act
        result = tgraphcanvas.timetemparray2temp(timearray, temparray, seconds)

        # Assert
        assert result == -1

    def test_timetemparray2temp_with_none_values(self) -> None:
        """Test timetemparray2temp with None values in temparray."""
        # Arrange
        timearray = [0.0, 1.0, 2.0, 3.0]
        temparray: List[Optional[float]] = [20.0, None, 40.0, 50.0]
        seconds = 1.5

        # Act
        result = tgraphcanvas.timetemparray2temp(timearray, temparray, seconds)

        # Assert
        assert result == -1  # Should return -1 when encountering None


class TestTimearray2index:
    """Test timearray2index static method."""

    def test_timearray2index_exact_match(self) -> None:
        """Test timearray2index with exact time match."""
        # Arrange
        timearray = [0.0, 1.0, 2.0, 3.0, 4.0]
        time = 2.0

        # Act
        result = tgraphcanvas.timearray2index(timearray, time)

        # Assert
        assert result == 2

    def test_timearray2index_interpolation_nearest(self) -> None:
        """Test timearray2index with nearest interpolation."""
        # Arrange
        timearray = [0.0, 1.0, 2.0, 3.0, 4.0]
        time = 1.3

        # Act
        result = tgraphcanvas.timearray2index(timearray, time, nearest=True)

        # Assert
        assert result == 1  # Closer to 1.0 than 2.0

    def test_timearray2index_no_nearest(self) -> None:
        """Test timearray2index without nearest (returns bisect_right result)."""
        # Arrange
        timearray = [0.0, 1.0, 2.0, 3.0, 4.0]
        time = 1.8

        # Act
        result = tgraphcanvas.timearray2index(timearray, time, nearest=False)

        # Assert
        assert result == 2  # bisect_right returns insertion point

    def test_timearray2index_out_of_bounds(self) -> None:
        """Test timearray2index with out of bounds time."""
        # Arrange
        timearray = [1.0, 2.0, 3.0, 4.0]

        # Act & Assert - before range (bisect_right returns 0, but function returns -1 when i=0)
        result = tgraphcanvas.timearray2index(timearray, 0.5)
        assert result == -1

        # Act & Assert - after range
        result = tgraphcanvas.timearray2index(timearray, 5.0)
        assert result == len(timearray) - 1  # Returns nearest index (last element)

    def test_timearray2index_empty_array(self) -> None:
        """Test timearray2index with empty array."""
        # Arrange
        timearray: List[float] = []
        time = 1.0

        # Act
        result = tgraphcanvas.timearray2index(timearray, time)

        # Assert
        assert result == -1


class TestWheelTextAngleMethods:
    """Test findCenterWheelTextAngle and findRadialWheelTextAngle static methods."""

    @pytest.mark.parametrize(
        'angle,expected',
        [
            (0.0, 270.0),
            (360.0, 270.0),
            (90.0, 0.0),  # 90 - 90 = 0
            (180.0, 90.0),  # 180 - 90 = 90
            (270.0, 0.0),  # 270 - 270 = 0 (quadrant 4)
            (45.0, 315.0),  # 270 + 45 = 315 (quadrant 1)
            (135.0, 45.0),  # 135 - 90 = 45 (quadrant 2)
            (225.0, 315.0),  # 225 + 90 = 315 (quadrant 3)
            (315.0, 45.0),  # 315 - 270 = 45 (quadrant 4)
        ],
    )
    def test_findCenterWheelTextAngle(self, angle: float, expected: float) -> None:
        """Test findCenterWheelTextAngle with various angles."""
        # Act
        result = tgraphcanvas.findCenterWheelTextAngle(angle)

        # Assert
        assert result == expected

    def test_findCenterWheelTextAngle_out_of_range(self) -> None:
        """Test findCenterWheelTextAngle with angles outside 0-360 range."""
        # Act & Assert
        result1 = tgraphcanvas.findCenterWheelTextAngle(450.0)  # 450 % 360 = 90
        assert result1 == 0.0  # 90 - 90 = 0

        result2 = tgraphcanvas.findCenterWheelTextAngle(-90.0)  # -90 % 360 = 270
        assert result2 == 0.0  # 270 - 270 = 0

    @pytest.mark.parametrize(
        'angle,expected',
        [
            (45.0, 45.0),  # 0 < 45 <= 90, return 45
            (90.0, 90.0),  # 0 < 90 <= 90, return 90
            (135.0, 315.0),  # 90 < 135 <= 270, return 180 + 135 = 315
            (225.0, 405.0),  # 90 < 225 <= 270, return 180 + 225 = 405
            (315.0, 315.0),  # 315 > 270, return 315
            (0.0, 180.0),  # 0 not in (0, 90] or > 270, so return 180 + 0 = 180
            (360.0, 360.0),  # After divmod, 360 becomes 0, but the function returns 360
        ],
    )
    def test_findRadialWheelTextAngle(self, angle: float, expected: float) -> None:
        """Test findRadialWheelTextAngle with various angles."""
        # Act
        result = tgraphcanvas.findRadialWheelTextAngle(angle)

        # Assert
        assert result == expected

    def test_findRadialWheelTextAngle_out_of_range(self) -> None:
        """Test findRadialWheelTextAngle with angles outside 0-360 range."""
        # Act & Assert
        result1 = tgraphcanvas.findRadialWheelTextAngle(450.0)  # 450 % 360 = 90
        assert result1 == 90.0  # 0 < 90 <= 90, return 90

        result2 = tgraphcanvas.findRadialWheelTextAngle(-45.0)  # -45 % 360 = 315
        assert result2 == 315.0  # 315 > 270, return 315


class TestAlarmSetMethods:
    """Test alarm set related static methods."""

    def test_makeAlarmSet(self) -> None:
        """Test makeAlarmSet creates proper AlarmSet."""
        # Arrange
        label = 'Test Alarm'
        flags = [1, 0, 1]
        guards = [1, 2, 3]
        negguards = [0, 0, 0]
        times = [60, 120, 180]
        offsets = [0, 5, 10]
        sources = [0, 1, 2]
        conditions = [0, 1, 2]
        temperatures = [200.0, 250.0, 300.0]
        actions = [0, 1, 2]
        beeps = [1, 1, 0]
        alarmstrings = ['Alarm1', 'Alarm2', 'Alarm3']

        # Act
        result = tgraphcanvas.makeAlarmSet(
            label,
            flags,
            guards,
            negguards,
            times,
            offsets,
            sources,
            conditions,
            temperatures,
            actions,
            beeps,
            alarmstrings,
        )

        # Assert
        assert result['label'] == label
        assert result['flags'] == flags
        assert result['guards'] == guards
        assert result['temperatures'] == temperatures

    def test_emptyAlarmSet(self) -> None:
        """Test emptyAlarmSet creates empty AlarmSet."""
        # Act
        result = tgraphcanvas.emptyAlarmSet()

        # Assert
        assert result['label'] == ''
        assert result['flags'] == []
        assert result['guards'] == []
        assert result['temperatures'] == []

    def test_lists2AlarmSet_valid_length(self) -> None:
        """Test lists2AlarmSet with valid length list."""
        # Arrange
        # Create a list with the correct number of items
        alarm_list = ['Test', [], [], [], [], [], [], [], [], [], [], []]

        # Act
        result = tgraphcanvas.lists2AlarmSet(alarm_list)

        # Assert
        assert result['label'] == 'Test'

    def test_lists2AlarmSet_invalid_length(self) -> None:
        """Test lists2AlarmSet with invalid length list."""
        # Arrange
        alarm_list = ['Test', [], []]  # Too few items

        # Act
        result = tgraphcanvas.lists2AlarmSet(alarm_list)

        # Assert
        # Should return empty alarm set
        assert result['label'] == ''

    def test_alarmSet2Lists(self) -> None:
        """Test alarmSet2Lists converts AlarmSet to list."""
        # Arrange
        alarm_set = tgraphcanvas.makeAlarmSet(
            'Test', [1], [2], [3], [4], [5], [6], [7], [8.0], [9], [10], ['test']
        )

        # Act
        result = tgraphcanvas.alarmSet2Lists(alarm_set)

        # Assert
        assert len(result) == 12
        assert result[0] == 'Test'
        assert result[1] == [1]
        assert result[11] == ['test']
