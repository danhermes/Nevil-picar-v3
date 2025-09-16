# Robot Hat Compatibility Notes

## Grayscale Module Missing Issue

### Problem
The current version of `robot_hat` installed via pip no longer includes the `Grayscale` or `Grayscale_Module` class, which is required by PiCar-X for line following functionality.

### Solution
Code must be modified to handle the missing Grayscale module gracefully:

```python
# Import pattern for handling missing Grayscale
try:
    from robot_hat import Grayscale as Grayscale_Module
except ImportError:
    # Grayscale_Module not available in this version of robot_hat
    Grayscale_Module = None

# In the initialization code
if Grayscale_Module is not None:
    self.grayscale = Grayscale_Module(adc0, adc1, adc2, reference=self.DEFAULT_LINE_REF)
else:
    self.grayscale = None
```

### Affected Files
- `/usr/local/lib/python3.11/dist-packages/picarx-*/picarx/picarx.py` (system package)
- `/home/dan/Nevil-picar-v3/nodes/navigation/picarx.py` (local v3 copy)
- `/home/dan/Nevil-picar-v3/v1.0/picarlibs/picarx.py` (v1.0 copy)

### Impact
- Line following functionality will be disabled
- Cliff detection will be disabled
- All other PiCar-X functions (motors, servos, ultrasonic) continue to work

### Other Import Changes Required
1. `FileDB` must be imported as: `from robot_hat import FileDB as fileDB`
2. `reset_mcu` is directly in robot_hat, not in utils: `from robot_hat import reset_mcu`

### Notes
This appears to be a regression in the robot_hat package. The Grayscale sensor hardware is still present on the PiCar-X, but the software support has been removed from the robot_hat library.

### Date Documented
September 15, 2025