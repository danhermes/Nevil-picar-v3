#!/usr/bin/env python3
"""
Test script to verify speech recognition to AI cognition flow works
"""

import os
import sys
import time
import threading
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from nevil_framework.launcher import NevilLauncher

def test_speech_flow():
    """Test the speech recognition to AI cognition flow"""
    print("Testing speech recognition to AI cognition flow...")
    
    try:
        # Initialize launcher
        launcher = NevilLauncher()
        
        # Start the system
        print("Starting Nevil system...")
        success = launcher.start_system()
        
        if not success:
            print("❌ Failed to start system")
            return False
        
        print("✅ System started successfully")
        print("🎙️  Speech recognition is now active")
        print("💬 AI cognition is ready to process voice commands")
        print("🔊 Text-to-speech is ready to respond")
        print("\nTry speaking to test the flow:")
        print("1. Say something (e.g., 'hello')")
        print("2. The system should recognize your speech")
        print("3. AI cognition should process it")
        print("4. Text-to-speech should respond")
        print("\nPress Ctrl+C to stop...")
        
        # Keep the system running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping system...")
            launcher.stop_system()
            print("✅ System stopped")
            return True
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

if __name__ == "__main__":
    success = test_speech_flow()
    sys.exit(0 if success else 1)
